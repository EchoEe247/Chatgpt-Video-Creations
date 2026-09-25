#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.media import compare_video, validate_master
from src.core.production_manifest import validate_production_v2
from src.core.production_runtime import (
    PASS,
    FAIL,
    PENDING,
    apply_runtime_defaults,
    next_action,
    ready_for_user_review,
    repair_budget_remaining,
    status_summary,
    sync_review_aliases,
)
from src.core.review_pack import build_review_pack


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load(path: str) -> tuple[Path, dict[str, Any]]:
    manifest = Path(path).expanduser().resolve()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    apply_runtime_defaults(data)
    errors = validate_production_v2(data)
    if errors:
        raise ValueError("invalid production manifest:\n- " + "\n- ".join(errors))
    return manifest, data


def _write(manifest: Path, data: dict[str, Any]) -> None:
    sync_review_aliases(data)
    errors = validate_production_v2(data)
    if errors:
        raise ValueError("refusing to write invalid production manifest:\n- " + "\n- ".join(errors))
    tmp = manifest.with_suffix(manifest.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, manifest)


def _relative(manifest: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(manifest.parent))
    except ValueError:
        return str(path.resolve())


def _resolve(manifest: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = manifest.parent / path
    return path.resolve()


def _dump(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def command_status(args) -> int:
    _manifest, data = _load(args.manifest)
    summary = status_summary(data)
    summary["valid"] = True
    _dump(summary)
    return 0


def command_render_spec(args) -> int:
    manifest, data = _load(args.manifest)
    render = data.get("render") or {}
    command = render.get("command") or []
    cwd = _resolve(manifest, render.get("cwd") or ".")
    output = _resolve(manifest, render.get("output"))
    result = {
        "command": command,
        "cwd": str(cwd) if cwd else str(manifest.parent),
        "output": str(output) if output else None,
        "execution": "Local Workspace command_start",
        "reason": "renders may exceed the synchronous command ceiling",
    }
    _dump(result)
    return 0 if command else 2


def command_rendering(args) -> int:
    manifest, data = _load(args.manifest)
    data["status"] = "RENDERING"
    data["workflow"]["last_action"] = {
        "action": "render_started",
        "at": _now(),
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_candidate(args) -> int:
    manifest, data = _load(args.manifest)
    candidate = Path(args.path).expanduser().resolve()
    if not candidate.is_file():
        raise FileNotFoundError(str(candidate))

    data.setdefault("artifacts", {})["candidate_master"] = _relative(manifest, candidate)
    data["artifacts"]["artifact_receipt"] = None
    data["artifacts"]["review_pack"] = None
    data["artifacts"]["baseline_comparison"] = None
    data["gates"]["technical"] = {"status": PENDING, "evidence": None}
    data["gates"]["assistant"] = {"status": PENDING, "notes": None}
    data["gates"]["user"] = {"status": PENDING, "notes": None}
    data["status"] = "CANDIDATE"
    data["workflow"]["escalation_reason"] = None
    data["workflow"]["last_action"] = {
        "action": "candidate_recorded",
        "at": _now(),
        "artifact": data["artifacts"]["candidate_master"],
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_prepare_review(args) -> int:
    manifest, data = _load(args.manifest)
    artifacts = data["artifacts"]
    candidate = _resolve(manifest, artifacts.get("candidate_master"))
    if candidate is None or not candidate.is_file():
        raise FileNotFoundError("candidate_master is missing")

    delivery = data["delivery"]
    qa = validate_master(
        candidate,
        width=delivery.get("width"),
        height=delivery.get("height"),
        fps=delivery.get("fps"),
        duration_seconds=delivery.get("expected_duration_seconds"),
        duration_tolerance=delivery.get("duration_tolerance_seconds", 0.15),
        audio_required=delivery.get("audio_required", True),
        silence_threshold_db=delivery.get("silence_threshold_db", -55.0),
        silence_min_duration=delivery.get("silence_min_duration_seconds", 0.5),
        max_silence_seconds=delivery.get("max_unintended_silence_seconds"),
    )

    qa_dir = manifest.parent / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    technical_path = qa_dir / "technical-qa.json"
    technical_path.write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    data["gates"]["technical"] = {
        "status": PASS if qa["pass"] else FAIL,
        "evidence": _relative(manifest, technical_path),
    }

    baseline_value = artifacts.get("baseline_master")
    artifacts["baseline_comparison"] = None
    if baseline_value:
        baseline = _resolve(manifest, baseline_value)
        if baseline and baseline.is_file():
            comparison = compare_video(baseline, candidate)
            comparison_path = qa_dir / "baseline-comparison.json"
            comparison_path.write_text(
                json.dumps(comparison, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            artifacts["baseline_comparison"] = _relative(manifest, comparison_path)

    if not qa["pass"]:
        data["status"] = "REFINEMENT_REQUIRED"
        data["workflow"]["last_action"] = {
            "action": "technical_qa_failed",
            "at": _now(),
            "evidence": data["gates"]["technical"]["evidence"],
        }
        _write(manifest, data)
        _dump(status_summary(data))
        return 1

    render = data.get("render") or {}
    scene_plan = _resolve(manifest, render.get("scene_plan"))
    review_dir = qa_dir / "review-pack"
    review = build_review_pack(
        candidate,
        review_dir,
        scene_plan=scene_plan if scene_plan and scene_plan.is_file() else None,
        silence_threshold_db=delivery.get("silence_threshold_db", -55.0),
        silence_min_duration=delivery.get("silence_min_duration_seconds", 0.5),
    )
    artifacts["artifact_receipt"] = _relative(manifest, Path(review["receipt_path"]))
    artifacts["review_pack"] = _relative(manifest, Path(review["manifest_path"]))
    data["gates"]["assistant"] = {"status": PENDING, "notes": None}
    data["gates"]["user"] = {"status": PENDING, "notes": None}
    data["status"] = "ASSISTANT_REVIEW"
    data["workflow"]["last_action"] = {
        "action": "review_evidence_built",
        "at": _now(),
        "review_pack": artifacts["review_pack"],
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_assistant_pass(args) -> int:
    manifest, data = _load(args.manifest)
    if data["gates"]["technical"]["status"] != PASS:
        raise ValueError("assistant PASS requires technical gate PASS")
    if not data["artifacts"].get("review_pack"):
        raise ValueError("assistant PASS requires a review pack")

    data["gates"]["assistant"] = {
        "status": PASS,
        "notes": args.notes or "Assistant technical/visual/audio review passed.",
    }
    data["gates"]["user"] = {"status": PENDING, "notes": None}
    data["status"] = "USER_REVIEW"
    data["workflow"]["last_action"] = {
        "action": "assistant_review_passed",
        "at": _now(),
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_assistant_fail(args) -> int:
    manifest, data = _load(args.manifest)
    data["gates"]["assistant"] = {
        "status": FAIL,
        "notes": args.notes or "Assistant review found a defect requiring repair.",
    }
    data["gates"]["user"] = {"status": PENDING, "notes": None}
    data["status"] = "REFINEMENT_REQUIRED"
    data["workflow"]["last_action"] = {
        "action": "assistant_review_failed",
        "at": _now(),
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def _archive_iteration(data: dict[str, Any]) -> None:
    artifacts = data.get("artifacts") or {}
    if not artifacts.get("candidate_master"):
        return
    history = data.setdefault("history", [])
    history.append(
        {
            "at": _now(),
            "repair_cycle": data["workflow"].get("repair_cycle", 0),
            "status": data.get("status"),
            "artifacts": deepcopy(artifacts),
            "gates": deepcopy(data.get("gates") or {}),
        }
    )


def command_repair_start(args) -> int:
    manifest, data = _load(args.manifest)
    remaining = repair_budget_remaining(data)
    if remaining <= 0:
        data["status"] = "BLOCKED"
        data["workflow"]["escalation_reason"] = "autonomous_repair_budget_exhausted"
        data["workflow"]["last_action"] = {
            "action": "repair_budget_exhausted",
            "at": _now(),
        }
        _write(manifest, data)
        _dump(status_summary(data))
        return 2

    _archive_iteration(data)
    data["workflow"]["repair_cycle"] += 1
    data["workflow"]["last_action"] = {
        "action": "repair_started",
        "at": _now(),
        "reason": args.reason,
    }
    data["workflow"]["escalation_reason"] = None
    data["status"] = "RENDERING"
    data["gates"]["technical"] = {"status": PENDING, "evidence": None}
    data["gates"]["assistant"] = {"status": PENDING, "notes": None}
    data["gates"]["user"] = {"status": PENDING, "notes": None}
    data["artifacts"]["artifact_receipt"] = None
    data["artifacts"]["review_pack"] = None
    data["artifacts"]["baseline_comparison"] = None
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_user_accept(args) -> int:
    manifest, data = _load(args.manifest)
    if not ready_for_user_review(data):
        raise ValueError("production is not ready for final user review")
    data["gates"]["user"] = {
        "status": PASS,
        "notes": args.notes or "Final candidate accepted by user.",
    }
    data["status"] = "DONE"
    data["workflow"]["last_action"] = {
        "action": "user_accepted",
        "at": _now(),
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_user_reject(args) -> int:
    manifest, data = _load(args.manifest)
    if not ready_for_user_review(data):
        raise ValueError("production is not at final user-review gate")
    data["gates"]["user"] = {
        "status": FAIL,
        "notes": args.notes or "User requested refinement.",
    }
    data["status"] = "REFINEMENT_REQUIRED"
    data["workflow"]["last_action"] = {
        "action": "user_requested_refinement",
        "at": _now(),
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_block(args) -> int:
    manifest, data = _load(args.manifest)
    data["status"] = "BLOCKED"
    data["workflow"]["escalation_reason"] = args.reason
    data["workflow"]["last_action"] = {
        "action": "blocked",
        "at": _now(),
        "reason": args.reason,
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_resume(args) -> int:
    manifest, data = _load(args.manifest)
    data["workflow"]["escalation_reason"] = None
    data["status"] = "REFINEMENT_REQUIRED"
    data["workflow"]["last_action"] = {
        "action": "resumed",
        "at": _now(),
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stateful production workflow controller for Chatgpt-Video-Creations."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for name, func, help_text in [
        ("status", command_status, "Show validated state and the next required action."),
        ("render-spec", command_render_spec, "Return the render argv/cwd/output for Local Workspace."),
        ("rendering", command_rendering, "Mark the production as actively rendering."),
        ("prepare-review", command_prepare_review, "Run technical QA and build review evidence."),
        ("assistant-pass", command_assistant_pass, "Mark internal assistant review PASS and open final user review."),
        ("assistant-fail", command_assistant_fail, "Mark internal assistant review FAIL without involving the user."),
        ("repair-start", command_repair_start, "Archive the candidate and start another autonomous repair cycle."),
        ("user-accept", command_user_accept, "Accept the final candidate and mark DONE."),
        ("user-reject", command_user_reject, "Record final-review feedback and return to refinement."),
        ("block", command_block, "Record a genuine human-decision blocker."),
        ("resume", command_resume, "Clear a resolved blocker and return to refinement."),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("manifest")
        if name in {"assistant-pass", "assistant-fail", "user-accept", "user-reject"}:
            p.add_argument("--notes")
        if name == "repair-start":
            p.add_argument("--reason", required=True)
        if name == "block":
            p.add_argument("--reason", required=True)
        p.set_defaults(func=func)

    p = sub.add_parser("candidate", help="Record a newly rendered candidate and reset review gates.")
    p.add_argument("manifest")
    p.add_argument("path")
    p.set_defaults(func=command_candidate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())