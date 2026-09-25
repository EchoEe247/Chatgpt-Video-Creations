#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.media import (
    MediaToolError,
    compare_video,
    sha256_file,
    validate_master,
)
from src.core.production_manifest import validate_production_v2
from src.core.production_runtime import (
    FAIL,
    PASS,
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


def _iteration_dir(manifest: Path, data: dict[str, Any]) -> Path:
    cycle = int(data["workflow"].get("repair_cycle", 0))
    return manifest.parent / "iterations" / f"iteration-{cycle:02d}"


def _copy_candidate_immutable(manifest: Path, data: dict[str, Any], source: Path) -> tuple[Path, str]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(str(source))

    iteration_dir = _iteration_dir(manifest, data)
    iteration_dir.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower() or ".mp4"
    destination = iteration_dir / f"candidate{suffix}"

    if destination.exists():
        existing_sha = sha256_file(destination)
        source_sha = sha256_file(source)
        if existing_sha != source_sha:
            raise ValueError(
                f"immutable iteration candidate already exists with different bytes: {destination}"
            )
        return destination, existing_sha

    shutil.copy2(source, destination)
    digest = sha256_file(destination)
    if digest != sha256_file(source):
        destination.unlink(missing_ok=True)
        raise IOError("candidate copy hash mismatch")
    return destination, digest


def _verify_candidate_binding(manifest: Path, data: dict[str, Any]) -> tuple[Path, str]:
    artifacts = data.get("artifacts") or {}
    candidate = _resolve(manifest, artifacts.get("candidate_master"))
    expected = artifacts.get("candidate_sha256")
    if candidate is None or not candidate.is_file():
        raise FileNotFoundError("candidate_master is missing")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("candidate_sha256 is missing or invalid")
    actual = sha256_file(candidate)
    if actual != expected:
        raise ValueError(
            f"candidate hash mismatch: expected {expected}, actual {actual}"
        )
    return candidate, actual


def _verify_review_evidence(manifest: Path, data: dict[str, Any]) -> dict[str, Any]:
    candidate, digest = _verify_candidate_binding(manifest, data)
    artifacts = data.get("artifacts") or {}

    receipt_path = _resolve(manifest, artifacts.get("artifact_receipt"))
    review_pack_path = _resolve(manifest, artifacts.get("review_pack"))
    technical_path = _resolve(
        manifest,
        (data.get("gates") or {}).get("technical", {}).get("evidence"),
    )
    for label, path in (
        ("artifact_receipt", receipt_path),
        ("review_pack", review_pack_path),
        ("technical evidence", technical_path),
    ):
        if path is None or not path.is_file():
            raise FileNotFoundError(f"{label} is missing")

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("sha256") != digest:
        raise ValueError("artifact receipt is not bound to the current candidate SHA-256")

    technical = json.loads(technical_path.read_text(encoding="utf-8"))
    if technical.get("artifact_sha256") != digest:
        raise ValueError("technical QA evidence is not bound to the current candidate SHA-256")
    if not technical.get("pass"):
        raise ValueError("technical QA evidence does not pass")

    review_pack = json.loads(review_pack_path.read_text(encoding="utf-8"))
    if review_pack.get("candidate_sha256") != digest:
        raise ValueError("review pack is not bound to the current candidate SHA-256")
    pack_video = Path(str(review_pack.get("video") or "")).expanduser()
    if not pack_video.is_absolute() or pack_video.resolve() != candidate:
        raise ValueError("review pack points at a different candidate")

    pack_root = review_pack_path.parent
    evidence_refs: list[tuple[str, str]] = []
    for key in ("receipt", "contact_sheet"):
        value = review_pack.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"review pack is missing {key}")
        evidence_refs.append((key, value))
    for index, boundary in enumerate(review_pack.get("boundaries") or [], 1):
        if not isinstance(boundary, dict):
            raise ValueError(f"review pack boundary {index} is invalid")
        for key in ("before", "after"):
            value = boundary.get(key)
            if not isinstance(value, str) or not value:
                raise ValueError(f"review pack boundary {index} is missing {key}")
            evidence_refs.append((f"boundary {index} {key}", value))
    for index, point in enumerate(review_pack.get("review_points") or [], 1):
        if not isinstance(point, dict):
            raise ValueError(f"review point {index} is invalid")
        for key in ("frame", "clip"):
            value = point.get(key)
            if not isinstance(value, str) or not value:
                raise ValueError(f"review point {index} is missing {key}")
            evidence_refs.append((f"review point {index} {key}", value))

    for label, relative in evidence_refs:
        evidence_path = (pack_root / relative).resolve()
        try:
            evidence_path.relative_to(pack_root.resolve())
        except ValueError as exc:
            raise ValueError(f"{label} escapes the review-pack directory") from exc
        if not evidence_path.is_file():
            raise FileNotFoundError(f"{label} is missing: {evidence_path}")

    receipt_ref = (pack_root / str(review_pack["receipt"])).resolve()
    if receipt_ref != receipt_path.resolve():
        raise ValueError("review pack references a different artifact receipt")

    baseline_path = _resolve(manifest, artifacts.get("baseline_comparison"))
    if artifacts.get("baseline_comparison"):
        if baseline_path is None or not baseline_path.is_file():
            raise FileNotFoundError("baseline comparison evidence is missing")
        baseline_data = json.loads(baseline_path.read_text(encoding="utf-8"))
        if baseline_data.get("candidate_sha256") != digest:
            raise ValueError("baseline comparison is not bound to the current candidate SHA-256")

    return {
        "candidate": str(candidate),
        "candidate_sha256": digest,
        "receipt": str(receipt_path),
        "review_pack": str(review_pack_path),
        "technical": str(technical_path),
        "baseline_comparison": str(baseline_path) if baseline_path else None,
    }


def _record_candidate(manifest: Path, data: dict[str, Any], source: Path) -> None:
    candidate, digest = _copy_candidate_immutable(manifest, data, source)
    artifacts = data.setdefault("artifacts", {})
    artifacts["candidate_master"] = _relative(manifest, candidate)
    artifacts["candidate_sha256"] = digest
    artifacts["iteration_dir"] = _relative(manifest, candidate.parent)
    artifacts["artifact_receipt"] = None
    artifacts["review_pack"] = None
    artifacts["baseline_comparison"] = None

    data["gates"]["technical"] = {"status": PENDING, "evidence": None}
    data["gates"]["assistant"] = {"status": PENDING, "notes": None}
    data["gates"]["user"] = {"status": PENDING, "notes": None}
    data["status"] = "CANDIDATE"
    data["workflow"]["escalation_reason"] = None
    render_job = data["workflow"].get("render_job") or {}
    if render_job.get("job_id"):
        render_job["state"] = "COMPLETED"
        if render_job.get("completed_at") is None:
            render_job["completed_at"] = _now()
        if render_job.get("exit_code") is None:
            render_job["exit_code"] = 0
    data["workflow"]["last_action"] = {
        "action": "candidate_recorded",
        "at": _now(),
        "artifact": artifacts["candidate_master"],
        "sha256": digest,
    }


def _archive_iteration(data: dict[str, Any]) -> None:
    artifacts = data.get("artifacts") or {}
    if not artifacts.get("candidate_master") and not data["workflow"].get("render_job", {}).get("job_id"):
        return
    history = data.setdefault("history", [])
    history.append(
        {
            "at": _now(),
            "repair_cycle": data["workflow"].get("repair_cycle", 0),
            "status": data.get("status"),
            "artifacts": deepcopy(artifacts),
            "gates": deepcopy(data.get("gates") or {}),
            "render_job": deepcopy(data["workflow"].get("render_job") or {}),
        }
    )


def _reset_for_next_render(data: dict[str, Any]) -> None:
    data["status"] = "PLANNED"
    data["gates"]["technical"] = {"status": PENDING, "evidence": None}
    data["gates"]["assistant"] = {"status": PENDING, "notes": None}
    data["gates"]["user"] = {"status": PENDING, "notes": None}
    data["artifacts"]["candidate_master"] = None
    data["artifacts"]["candidate_sha256"] = None
    data["artifacts"]["iteration_dir"] = None
    data["artifacts"]["artifact_receipt"] = None
    data["artifacts"]["review_pack"] = None
    data["artifacts"]["baseline_comparison"] = None
    data["workflow"]["render_job"] = {
        "job_id": None,
        "state": "NONE",
        "command": None,
        "cwd": None,
        "output": None,
        "started_at": None,
        "completed_at": None,
        "exit_code": None,
    }


def command_status(args) -> int:
    manifest, data = _load(args.manifest)
    summary = status_summary(data)
    summary["valid"] = True
    if data.get("status") in {"ASSISTANT_REVIEW", "USER_REVIEW", "DONE"}:
        try:
            summary["artifact_integrity"] = {
                "pass": True,
                **_verify_review_evidence(manifest, data),
            }
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            summary["artifact_integrity"] = {"pass": False, "error": str(exc)}
            if data.get("status") == "DONE":
                summary["next_action"] = "repair_integrity"
    _dump(summary)
    return 0 if summary.get("artifact_integrity", {"pass": True})["pass"] else 1


def command_render_spec(args) -> int:
    manifest, data = _load(args.manifest)
    render = data.get("render") or {}
    delivery = data.get("delivery") or {}
    command = render.get("command") or []
    cwd = _resolve(manifest, render.get("cwd") or ".")
    output = _resolve(manifest, render.get("output"))

    errors = []
    if not command:
        errors.append("render.command is empty")
    if output is None:
        errors.append("render.output is not configured")
    expected_duration = delivery.get("expected_duration_seconds")
    if not isinstance(expected_duration, (int, float)) or expected_duration <= 0:
        errors.append("delivery.expected_duration_seconds must be configured before rendering")
    if delivery.get("audio_required") and delivery.get("max_unintended_silence_seconds") is None:
        errors.append("audio-required productions must configure max_unintended_silence_seconds")
    if errors:
        raise ValueError("; ".join(errors))

    result = {
        "command": command,
        "cwd": str(cwd) if cwd else str(manifest.parent),
        "output": str(output),
        "execution": "Local Workspace command_start",
        "reason": "renders may exceed the synchronous command ceiling",
    }
    _dump(result)
    return 0


def command_rendering(args) -> int:
    manifest, data = _load(args.manifest)
    render = data.get("render") or {}
    cwd = _resolve(manifest, render.get("cwd") or ".")
    output = _resolve(manifest, render.get("output"))
    data["status"] = "RENDERING"
    data["workflow"]["render_job"] = {
        "job_id": args.job_id,
        "state": "RUNNING",
        "command": list(render.get("command") or []),
        "cwd": str(cwd) if cwd else str(manifest.parent),
        "output": str(output) if output else None,
        "started_at": _now(),
        "completed_at": None,
        "exit_code": None,
    }
    data["workflow"]["last_action"] = {
        "action": "render_started",
        "at": _now(),
        "job_id": args.job_id,
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_reconcile_render(args) -> int:
    manifest, data = _load(args.manifest)
    if data.get("status") != "RENDERING":
        raise ValueError("reconcile-render requires RENDERING state")
    job = data["workflow"].get("render_job") or {}
    if not job.get("job_id"):
        raise ValueError("RENDERING state has no persisted render job ID")

    state = args.state.upper()
    job["state"] = state
    if args.exit_code is not None:
        job["exit_code"] = args.exit_code

    if state == "RUNNING":
        data["workflow"]["last_action"] = {
            "action": "render_reconciled_running",
            "at": _now(),
            "job_id": job["job_id"],
        }
        _write(manifest, data)
        _dump(status_summary(data))
        return 0

    job["completed_at"] = _now()
    if state == "COMPLETED" and (job.get("exit_code") in {None, 0}):
        job["exit_code"] = 0
        output = Path(str(job.get("output") or "")).expanduser()
        if not output.is_file():
            state = "MISSING"
            job["state"] = state
        else:
            _record_candidate(manifest, data, output)
            _write(manifest, data)
            _dump(status_summary(data))
            return 0

    data["workflow"]["last_action"] = {
        "action": "render_failed",
        "at": _now(),
        "job_id": job["job_id"],
        "state": state,
        "exit_code": job.get("exit_code"),
    }
    if repair_budget_remaining(data) > 0:
        data["status"] = "REFINEMENT_REQUIRED"
    else:
        data["status"] = "BLOCKED"
        data["workflow"]["escalation_reason"] = "autonomous_repair_budget_exhausted"
    _write(manifest, data)
    _dump(status_summary(data))
    return 1


def command_candidate(args) -> int:
    manifest, data = _load(args.manifest)
    _record_candidate(manifest, data, Path(args.path).expanduser().resolve())
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_prepare_review(args) -> int:
    manifest, data = _load(args.manifest)
    candidate, digest = _verify_candidate_binding(manifest, data)
    artifacts = data["artifacts"]
    delivery = data["delivery"]

    render = data.get("render") or {}
    scene_plan_value = render.get("scene_plan")
    scene_plan = _resolve(manifest, scene_plan_value)
    if scene_plan_value and (scene_plan is None or not scene_plan.is_file()):
        raise FileNotFoundError(f"configured scene plan is missing: {scene_plan_value}")

    baseline_value = artifacts.get("baseline_master")
    baseline = _resolve(manifest, baseline_value)
    if baseline_value and (baseline is None or not baseline.is_file()):
        raise FileNotFoundError(f"configured baseline is missing: {baseline_value}")

    qa = validate_master(
        candidate,
        width=delivery.get("width"),
        height=delivery.get("height"),
        fps=delivery.get("fps"),
        duration_seconds=delivery.get("expected_duration_seconds"),
        duration_tolerance=delivery.get("duration_tolerance_seconds", 0.15),
        audio_required=delivery.get("audio_required", True),
        video_codec=delivery.get("video_codec"),
        pixel_format=delivery.get("pixel_format"),
        audio_codec=delivery.get("audio_codec"),
        silence_threshold_db=delivery.get("silence_threshold_db", -55.0),
        silence_min_duration=delivery.get("silence_min_duration_seconds", 0.5),
        max_silence_seconds=delivery.get("max_unintended_silence_seconds"),
        intentional_silence_intervals=delivery.get("intentional_silence_intervals") or [],
    )
    qa["artifact_sha256"] = digest

    iteration_dir = _resolve(manifest, artifacts.get("iteration_dir"))
    if iteration_dir is None:
        raise ValueError("candidate iteration directory is missing")
    qa_dir = iteration_dir / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    technical_path = qa_dir / "technical-qa.json"
    technical_path.write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    data["gates"]["technical"] = {
        "status": PASS if qa["pass"] else FAIL,
        "evidence": _relative(manifest, technical_path),
    }

    artifacts["baseline_comparison"] = None
    if baseline is not None:
        comparison = compare_video(
            baseline,
            candidate,
            sample_fps=float(delivery.get("baseline_compare_fps", 2.0)),
            max_duration_seconds=None,
        )
        comparison["candidate_sha256"] = digest
        comparison_path = qa_dir / "baseline-comparison.json"
        comparison_path.write_text(
            json.dumps(comparison, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        artifacts["baseline_comparison"] = _relative(manifest, comparison_path)

    if not qa["pass"]:
        data["workflow"]["last_action"] = {
            "action": "technical_qa_failed",
            "at": _now(),
            "evidence": data["gates"]["technical"]["evidence"],
            "candidate_sha256": digest,
        }
        if repair_budget_remaining(data) > 0:
            data["status"] = "REFINEMENT_REQUIRED"
        else:
            data["status"] = "BLOCKED"
            data["workflow"]["escalation_reason"] = "autonomous_repair_budget_exhausted"
        _write(manifest, data)
        _dump(status_summary(data))
        return 1

    receipt_data = {
        "artifact": str(candidate),
        "sha256": digest,
        "probe": qa["probe"],
        "decode": qa["decode"],
        "audio": qa["audio"],
    }
    review_dir = qa_dir / "review-pack"
    review = build_review_pack(
        candidate,
        review_dir,
        scene_plan=scene_plan,
        silence_threshold_db=delivery.get("silence_threshold_db", -55.0),
        silence_min_duration=delivery.get("silence_min_duration_seconds", 0.5),
        receipt_data=receipt_data,
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
        "candidate_sha256": digest,
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_assistant_pass(args) -> int:
    manifest, data = _load(args.manifest)
    if data["gates"]["technical"]["status"] != PASS:
        raise ValueError("assistant PASS requires technical gate PASS")
    integrity = _verify_review_evidence(manifest, data)

    data["gates"]["assistant"] = {
        "status": PASS,
        "notes": args.notes or "Assistant technical/visual/audio review passed.",
        "candidate_sha256": integrity["candidate_sha256"],
    }
    data["gates"]["user"] = {"status": PENDING, "notes": None}
    data["status"] = "USER_REVIEW"
    data["workflow"]["last_action"] = {
        "action": "assistant_review_passed",
        "at": _now(),
        "candidate_sha256": integrity["candidate_sha256"],
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_assistant_fail(args) -> int:
    manifest, data = _load(args.manifest)
    _verify_candidate_binding(manifest, data)
    data["gates"]["assistant"] = {
        "status": FAIL,
        "notes": args.notes or "Assistant review found a defect requiring repair.",
        "candidate_sha256": data["artifacts"].get("candidate_sha256"),
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
    _reset_for_next_render(data)
    data["workflow"]["last_action"] = {
        "action": "repair_started",
        "at": _now(),
        "reason": args.reason,
    }
    data["workflow"]["escalation_reason"] = None
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_user_accept(args) -> int:
    manifest, data = _load(args.manifest)
    if not ready_for_user_review(data):
        raise ValueError("production is not ready for final user review")
    integrity = _verify_review_evidence(manifest, data)
    assistant_sha = data["gates"]["assistant"].get("candidate_sha256")
    if assistant_sha != integrity["candidate_sha256"]:
        raise ValueError("assistant review is not bound to the current candidate")

    data["gates"]["user"] = {
        "status": PASS,
        "notes": args.notes or "Final candidate accepted by user.",
        "candidate_sha256": integrity["candidate_sha256"],
    }
    data["status"] = "DONE"
    data["workflow"]["last_action"] = {
        "action": "user_accepted",
        "at": _now(),
        "candidate_sha256": integrity["candidate_sha256"],
    }
    _write(manifest, data)
    _dump(status_summary(data))
    return 0


def command_user_reject(args) -> int:
    manifest, data = _load(args.manifest)
    if not ready_for_user_review(data):
        raise ValueError("production is not at final user-review gate")
    integrity = _verify_review_evidence(manifest, data)
    data["gates"]["user"] = {
        "status": FAIL,
        "notes": args.notes or "User requested refinement.",
        "candidate_sha256": integrity["candidate_sha256"],
    }
    data["status"] = "REFINEMENT_REQUIRED"
    data["workflow"]["last_action"] = {
        "action": "user_requested_refinement",
        "at": _now(),
        "candidate_sha256": integrity["candidate_sha256"],
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
    data["status"] = "REFINEMENT_REQUIRED" if data.get("artifacts", {}).get("candidate_master") else "PLANNED"
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
        ("status", command_status, "Show validated state, artifact integrity, and next action."),
        ("render-spec", command_render_spec, "Return the render argv/cwd/output for Local Workspace."),
        ("prepare-review", command_prepare_review, "Run technical QA and build immutable review evidence."),
        ("assistant-pass", command_assistant_pass, "Mark internal assistant review PASS and open final user review."),
        ("assistant-fail", command_assistant_fail, "Mark internal assistant review FAIL without involving the user."),
        ("repair-start", command_repair_start, "Archive the iteration and open the next autonomous render cycle."),
        ("user-accept", command_user_accept, "Verify artifact bindings, accept the final candidate, and mark DONE."),
        ("user-reject", command_user_reject, "Record final-review feedback and return to refinement."),
        ("block", command_block, "Record a genuine human-decision blocker."),
        ("resume", command_resume, "Clear a resolved blocker and return to work."),
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

    p = sub.add_parser("rendering", help="Persist a Local Workspace render job identity.")
    p.add_argument("manifest")
    p.add_argument("--job-id", required=True)
    p.set_defaults(func=command_rendering)

    p = sub.add_parser("reconcile-render", help="Reconcile the persisted Local Workspace render job after resume/poll.")
    p.add_argument("manifest")
    p.add_argument("--state", required=True, choices=["running", "completed", "failed", "missing"])
    p.add_argument("--exit-code", type=int)
    p.set_defaults(func=command_reconcile_render)

    p = sub.add_parser("candidate", help="Copy a rendered candidate into the immutable iteration directory.")
    p.add_argument("manifest")
    p.add_argument("path")
    p.set_defaults(func=command_candidate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, json.JSONDecodeError, MediaToolError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())