from __future__ import annotations

import hashlib
import json
import os
import secrets
import statistics
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = 1
DEFAULT_STATE_ROOT = Path.home() / ".local" / "state" / "chatgpt-video" / "studio-validation"
CONTAMINATION_STATES = {"BLINDED", "PARTIALLY_BLINDED", "NOT_BLINDED"}
SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3}

TAXONOMY = {
    "freeze": {"modality": "continuous_video", "tolerance_seconds": 0.50, "severity": "high"},
    "transition_discontinuity": {"modality": "continuous_video", "tolerance_seconds": 0.35, "severity": "medium"},
    "text_readability": {"modality": "still_image", "tolerance_seconds": 0.75, "severity": "medium"},
    "tonal_hum": {"modality": "auditory", "tolerance_seconds": None, "severity": "medium"},
    "av_sync": {"modality": "synchronized_av", "tolerance_seconds": 0.30, "severity": "high"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def _run_ffmpeg(args: list[str]) -> None:
    p = subprocess.run(["ffmpeg", "-y", "-v", "error", *args], stdin=subprocess.DEVNULL, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or b"ffmpeg failed").decode("utf-8", "replace"))


def _fixture_base(path: Path, *, filter_complex: str, audio_filter: str = "sine=frequency=330:sample_rate=24000:duration=6") -> None:
    _run_ffmpeg([
        "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24:duration=6",
        "-f", "lavfi", "-i", audio_filter,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "64k", "-shortest", str(path),
    ])


def generate_seeded_media(out_dir: Path, fixture_ids: list[str]) -> dict[str, dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    if len(fixture_ids) != 6:
        raise ValueError("expected six opaque fixture IDs")
    answer: dict[str, dict[str, Any]] = {}

    # clean control: ordinary continuously moving test pattern and tone
    clean = out_dir / f"{fixture_ids[0]}.mp4"
    _fixture_base(clean, filter_complex="[0:v]null[v]")
    answer[fixture_ids[0]] = {"control": True, "expected": []}

    # frozen motion from 2.0-3.0 s
    freeze = out_dir / f"{fixture_ids[1]}.mp4"
    _fixture_base(
        freeze,
        filter_complex="[0:v]split=2[src][rep];[src][rep]freezeframes=first=48:last=72:replace=48[v]",
    )
    answer[fixture_ids[1]] = {
        "control": False,
        "expected": [{"code": "freeze", "severity": "high", "modality": "continuous_video", "start_seconds": 2.0, "end_seconds": 3.0}],
    }

    # brief black transition discontinuity around 3 s
    flash = out_dir / f"{fixture_ids[2]}.mp4"
    _fixture_base(
        flash,
        filter_complex="[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='between(t,2.95,3.15)'[v]",
    )
    answer[fixture_ids[2]] = {
        "control": False,
        "expected": [{"code": "transition_discontinuity", "severity": "medium", "modality": "continuous_video", "start_seconds": 2.95, "end_seconds": 3.15}],
    }

    # deliberately tiny low-contrast text between 1-3 s
    text_path = out_dir / f"{fixture_ids[3]}.mp4"
    _fixture_base(
        text_path,
        filter_complex="[0:v]drawtext=text='CRITICAL READOUT':x=120:y=12:fontsize=7:fontcolor=0x404040:enable='between(t,1,3)'[v]",
    )
    answer[fixture_ids[3]] = {
        "control": False,
        "expected": [{"code": "text_readability", "severity": "medium", "modality": "still_image", "start_seconds": 1.0, "end_seconds": 3.0}],
    }

    # audible 60 Hz hum mixed with a quieter normal tone
    hum = out_dir / f"{fixture_ids[4]}.mp4"
    _fixture_base(
        hum,
        filter_complex="[0:v]null[v]",
        audio_filter="aevalsrc='0.28*sin(2*PI*60*t)+0.06*sin(2*PI*330*t)':s=24000:d=6",
    )
    answer[fixture_ids[4]] = {
        "control": False,
        "expected": [{"code": "tonal_hum", "severity": "medium", "modality": "auditory"}],
    }

    # visual flash at 2.0, beep at 2.5 => known 500 ms A/V offset
    sync = out_dir / f"{fixture_ids[5]}.mp4"
    _run_ffmpeg([
        "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24:duration=6",
        "-f", "lavfi", "-i", "aevalsrc='if(between(t,2.48,2.58),0.6*sin(2*PI*900*t),0)':s=24000:d=6",
        "-filter_complex", "[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='between(t,1.98,2.08)'[v]",
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "64k", "-shortest", str(sync),
    ])
    answer[fixture_ids[5]] = {
        "control": False,
        "expected": [{"code": "av_sync", "severity": "high", "modality": "synchronized_av", "start_seconds": 1.98, "end_seconds": 2.58}],
    }
    return answer


def freeze_benchmark(output_dir: Path, *, state_root: Path = DEFAULT_STATE_ROOT) -> dict[str, Any]:
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_id = f"studio-{secrets.token_hex(8)}"
    fixture_ids = [secrets.token_hex(8) for _ in range(6)]
    fixtures_dir = output_dir / "fixtures"
    answer = generate_seeded_media(fixtures_dir, fixture_ids)

    fixtures = []
    for fixture_id in fixture_ids:
        path = fixtures_dir / f"{fixture_id}.mp4"
        fixtures.append({
            "fixture_id": fixture_id,
            "media": f"fixtures/{path.name}",
            "sha256": _sha(path),
            "duration_seconds": 6.0,
        })

    hashes = [row["sha256"] for row in fixtures]
    if len(set(hashes)) != len(hashes):
        raise RuntimeError("seeded benchmark contains duplicate media hashes; fixture generation is invalid")

    package = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_id": benchmark_id,
        "created_at": _now(),
        "purpose": "controlled_perception_validation",
        "fixtures": fixtures,
        "taxonomy": {
            code: {"modality": row["modality"], "severity": row["severity"]}
            for code, row in TAXONOMY.items()
        },
        "instructions": [
            "Inspect every opaque fixture independently; do not stop after the first apparent finding.",
            "For still-image review, inspect multiple time samples from every fixture when image extraction is available.",
            "Report only observed taxonomy defects with severity and time range when localizable.",
            "Do not infer a transition/motion defect from one static frame; continuous-video codes require actual continuous-video perception.",
            "Do not infer a defect from filenames or fixture order.",
            "Report unavailable modalities explicitly instead of guessing, and never submit a finding whose taxonomy modality you marked unavailable.",
            "Clean controls may contain no reportable defect.",
        ],
        "findings_schema": {
            "unavailable_modalities": ["modality_name"],
            "fixtures": {
                "<every fixture_id>": {
                    "findings": [{
                        "code": "taxonomy_code",
                        "severity": "info|low|medium|high",
                        "start_seconds": 0.0,
                        "end_seconds": 0.0,
                        "claim_type": "perceived|measured|inferred",
                        "notes": "observation",
                    }]
                }
            },
        },
        "answer_key_in_package": False,
        "findings_frozen_before_reveal": False,
        "user_holdout_included": False,
    }
    package_path = output_dir / "benchmark-package.json"
    _atomic_json(package_path, package)

    secret_dir = state_root / benchmark_id
    key = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_id": benchmark_id,
        "package_sha256": _sha(package_path),
        "fixtures": answer,
        "taxonomy": TAXONOMY,
        "created_at": package["created_at"],
    }
    _atomic_json(secret_dir / "answer-key.json", key)
    return {
        "benchmark_id": benchmark_id,
        "package_path": str(package_path),
        "package_sha256": _sha(package_path),
        "fixture_count": len(fixtures),
        "answer_key_path_hash": hashlib.sha256(str(secret_dir / "answer-key.json").encode()).hexdigest(),
    }


def freeze_findings(
    package_path: Path,
    findings_path: Path,
    *,
    contamination_status: str,
    state_root: Path = DEFAULT_STATE_ROOT,
    context_exposure: list[str] | None = None,
) -> dict[str, Any]:
    if contamination_status not in CONTAMINATION_STATES:
        raise ValueError("invalid contamination_status")
    package = json.loads(package_path.read_text("utf-8"))
    findings = json.loads(findings_path.read_text("utf-8"))
    if not isinstance(findings, dict) or not isinstance(findings.get("fixtures"), dict):
        raise ValueError("findings must be an object with fixtures mapping")
    benchmark_id = str(package["benchmark_id"])
    expected_fixture_ids = {str(x["fixture_id"]) for x in package.get("fixtures", [])}
    submitted_fixture_ids = {str(x) for x in findings.get("fixtures", {}).keys()}
    if submitted_fixture_ids != expected_fixture_ids:
        missing = sorted(expected_fixture_ids - submitted_fixture_ids)
        extra = sorted(submitted_fixture_ids - expected_fixture_ids)
        raise ValueError(f"findings fixture IDs must exactly match package; missing={missing} extra={extra}")
    unavailable_raw = findings.get("unavailable_modalities") or []
    if not isinstance(unavailable_raw, list) or not all(isinstance(x, str) for x in unavailable_raw):
        raise ValueError("unavailable_modalities must be an array of modality strings")
    unavailable_set = set(unavailable_raw)
    for fixture_id, fixture_row in findings["fixtures"].items():
        if not isinstance(fixture_row, Mapping) or not isinstance(fixture_row.get("findings"), list):
            raise ValueError(f"fixture {fixture_id} must contain findings array")
        for finding in fixture_row["findings"]:
            if not isinstance(finding, Mapping):
                raise ValueError(f"fixture {fixture_id} finding must be an object")
            code = str(finding.get("code") or "")
            if code not in TAXONOMY:
                raise ValueError(f"fixture {fixture_id} uses unknown taxonomy code {code!r}")
            modality = str(TAXONOMY[code]["modality"])
            if modality in unavailable_set:
                raise ValueError(f"fixture {fixture_id} reports {code} while modality {modality} is unavailable")
            if finding.get("severity") not in SEVERITY_RANK:
                raise ValueError(f"fixture {fixture_id} finding severity is invalid")
            if finding.get("claim_type") not in {"perceived", "measured", "inferred"}:
                raise ValueError(f"fixture {fixture_id} finding claim_type is invalid")
    record = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_id": benchmark_id,
        "package_sha256": _sha(package_path),
        "findings_sha256": _sha(findings_path),
        "contamination_status": contamination_status,
        "context_exposure": list(context_exposure or []),
        "findings_frozen_at": _now(),
        "findings_frozen_before_reveal": True,
        "unavailable_modalities": sorted(set(map(str, findings.get("unavailable_modalities") or []))),
        "fixtures": findings["fixtures"],
    }
    target = state_root / benchmark_id / "frozen-findings.json"
    if target.exists():
        old = json.loads(target.read_text("utf-8"))
        if old != record:
            raise ValueError("findings are already frozen for this benchmark")
    else:
        _atomic_json(target, record)
    return {
        "benchmark_id": benchmark_id,
        "contamination_status": contamination_status,
        "findings_sha256": record["findings_sha256"],
        "frozen_at": record["findings_frozen_at"],
        "findings_frozen_before_reveal": True,
    }


def _localization_error(expected: Mapping[str, Any], finding: Mapping[str, Any]) -> float | None:
    if "start_seconds" not in expected:
        return None
    try:
        es = float(expected["start_seconds"])
        ee = float(expected.get("end_seconds", es))
        fs = float(finding.get("start_seconds", finding.get("at_seconds")))
        fe = float(finding.get("end_seconds", fs))
    except (TypeError, ValueError):
        return float("inf")
    ec = (es + ee) / 2
    fc = (fs + fe) / 2
    return abs(ec - fc)


def score_benchmark(package_path: Path, *, state_root: Path = DEFAULT_STATE_ROOT) -> dict[str, Any]:
    package = json.loads(package_path.read_text("utf-8"))
    benchmark_id = str(package["benchmark_id"])
    secret_dir = state_root / benchmark_id
    key_path = secret_dir / "answer-key.json"
    frozen_path = secret_dir / "frozen-findings.json"
    if not frozen_path.is_file():
        raise ValueError("findings must be frozen before answer-key reveal/scoring")
    key = json.loads(key_path.read_text("utf-8"))
    frozen = json.loads(frozen_path.read_text("utf-8"))
    if key["package_sha256"] != _sha(package_path) or frozen["package_sha256"] != _sha(package_path):
        raise ValueError("benchmark package hash changed after freeze")

    unavailable = set(frozen.get("unavailable_modalities") or [])
    tp = fn = fp = 0
    clean_controls = clean_false_alarm_controls = 0
    unavailable_expected = 0
    localization: list[float] = []
    severity_exact = severity_within_one = severity_compared = 0
    fixture_rows = []

    for fixture in package["fixtures"]:
        fid = fixture["fixture_id"]
        expected_rows = list((key["fixtures"].get(fid) or {}).get("expected") or [])
        is_control = bool((key["fixtures"].get(fid) or {}).get("control"))
        observed = list((frozen["fixtures"].get(fid) or {}).get("findings") or [])
        if is_control:
            clean_controls += 1
            if observed:
                clean_false_alarm_controls += 1

        matched_obs: set[int] = set()
        fixture_tp = fixture_fn = fixture_unavailable = 0
        for expected in expected_rows:
            modality = str(expected.get("modality"))
            if modality in unavailable:
                unavailable_expected += 1
                fixture_unavailable += 1
                continue
            code = str(expected.get("code"))
            tolerance = TAXONOMY.get(code, {}).get("tolerance_seconds")
            best = None
            best_err = None
            for i, obs in enumerate(observed):
                if i in matched_obs or str(obs.get("code")) != code:
                    continue
                err = _localization_error(expected, obs)
                if tolerance is not None and (err is None or err == float("inf") or err > float(tolerance)):
                    continue
                if best is None or (err or 0.0) < (best_err or float("inf")):
                    best, best_err = i, err
            if best is None:
                fn += 1
                fixture_fn += 1
                continue
            matched_obs.add(best)
            tp += 1
            fixture_tp += 1
            if best_err is not None:
                localization.append(float(best_err))
            expected_sev = str(expected.get("severity"))
            observed_sev = str(observed[best].get("severity"))
            if expected_sev in SEVERITY_RANK and observed_sev in SEVERITY_RANK:
                severity_compared += 1
                delta = abs(SEVERITY_RANK[expected_sev] - SEVERITY_RANK[observed_sev])
                severity_exact += int(delta == 0)
                severity_within_one += int(delta <= 1)

        fixture_fp = len(observed) - len(matched_obs)
        fp += fixture_fp
        fixture_rows.append({
            "fixture_id": fid,
            "control": is_control,
            "true_positive": fixture_tp,
            "false_negative": fixture_fn,
            "false_positive": fixture_fp,
            "unavailable_expected": fixture_unavailable,
        })

    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    report = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_id": benchmark_id,
        "package_sha256": _sha(package_path),
        "findings_sha256": frozen["findings_sha256"],
        "scored_at": _now(),
        "contamination_status": frozen["contamination_status"],
        "context_exposure": frozen.get("context_exposure") or [],
        "findings_frozen_before_reveal": True,
        "user_holdout_status": "NOT_REVEALED_NOT_SCORED",
        "unavailable_modalities": sorted(unavailable),
        "summary": {
            "true_positive": tp,
            "false_negative": fn,
            "false_positive": fp,
            "unavailable_expected": unavailable_expected,
            "precision": None if precision is None else round(precision, 6),
            "recall": None if recall is None else round(recall, 6),
            "clean_control_false_alarm_rate": None if not clean_controls else round(clean_false_alarm_controls / clean_controls, 6),
            "median_localization_error_seconds": None if not localization else round(statistics.median(localization), 6),
            "severity_exact_rate": None if not severity_compared else round(severity_exact / severity_compared, 6),
            "severity_within_one_rate": None if not severity_compared else round(severity_within_one / severity_compared, 6),
        },
        "fixtures": fixture_rows,
    }
    _atomic_json(secret_dir / "score.json", report)
    return report


def make_operational_handoff(
    output_path: Path,
    *,
    bridge_commit: str,
    video_commit: str,
    expected_profile: str = "core-production",
) -> dict[str, Any]:
    package = {
        "schema_version": 1,
        "purpose": "fresh_session_operability_validation",
        "created_at": _now(),
        "bridge_commit": bridge_commit,
        "video_commit": video_commit,
        "expected_profile": expected_profile,
        "instructions": [
            "Start with repository and bridge status; do not use prior chat context.",
            "Confirm exact active production tool names/schemas, not only counts.",
            "Run studio_preflight.",
            "Locate the final-screening contract and explain what blocks ASSISTANT_ACCEPTED.",
            "Create or reuse a small media_review_bundle, page it to delivery completion, and report coverage without conflating sampled/measurement evidence with perception.",
            "Do not modify production media or reveal any controlled-benchmark answer key.",
        ],
        "scoring": {
            "tool_discovery": 1,
            "preflight": 1,
            "promotion_contract": 1,
            "bundle_resume_or_page": 1,
            "coverage_semantics": 1,
        },
    }
    _atomic_json(output_path, package)
    return package

def score_operational_handoff(package_path: Path, report_path: Path) -> dict[str, Any]:
    package = json.loads(package_path.read_text("utf-8"))
    report = json.loads(report_path.read_text("utf-8"))
    if report.get("purpose") != "fresh_session_operability_validation_report":
        raise ValueError("invalid operational report purpose")
    if report.get("bridge_commit") != package.get("bridge_commit"):
        raise ValueError("operational report bridge commit mismatch")
    if report.get("video_commit") != package.get("video_commit"):
        raise ValueError("operational report video commit mismatch")
    criteria = report.get("criteria")
    if not isinstance(criteria, Mapping):
        raise ValueError("operational report criteria must be an object")
    weights = package.get("scoring") or {}
    rows = {}
    earned = total = 0
    for name, weight in weights.items():
        weight = int(weight)
        total += weight
        row = criteria.get(name)
        passed = isinstance(row, Mapping) and row.get("status") == "PASS"
        if passed:
            earned += weight
        rows[name] = {
            "status": row.get("status") if isinstance(row, Mapping) else "MISSING",
            "evidence": row.get("evidence") if isinstance(row, Mapping) else None,
            "weight": weight,
            "earned": weight if passed else 0,
        }
    return {
        "schema_version": 1,
        "purpose": "fresh_session_operability_validation_score",
        "package_sha256": _sha(package_path),
        "report_sha256": _sha(report_path),
        "bridge_commit": package.get("bridge_commit"),
        "video_commit": package.get("video_commit"),
        "score": earned,
        "max_score": total,
        "pass": earned == total,
        "criteria": rows,
        "perception_score_included": False,
    }

