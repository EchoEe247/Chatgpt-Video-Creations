import json
from pathlib import Path

import pytest

from src.core import studio_validation as sv


def _package(tmp_path, monkeypatch):
    state = tmp_path / "state"
    out = tmp_path / "public"
    monkeypatch.setattr(sv, "DEFAULT_STATE_ROOT", state)
    result = sv.freeze_benchmark(out, state_root=state)
    return out / "benchmark-package.json", state, result


def test_freeze_package_hides_answer_key(tmp_path, monkeypatch):
    package_path, state, result = _package(tmp_path, monkeypatch)
    package = json.loads(package_path.read_text())
    assert package["answer_key_in_package"] is False
    encoded = package_path.read_text()
    assert '"expected"' not in encoded
    assert len(package["fixtures"]) == 6
    assert (state / result["benchmark_id"] / "answer-key.json").is_file()


def test_scoring_requires_frozen_findings(tmp_path, monkeypatch):
    package_path, state, _ = _package(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="frozen"):
        sv.score_benchmark(package_path, state_root=state)


def test_score_detection_false_alarm_and_unavailable(tmp_path, monkeypatch):
    package_path, state, result = _package(tmp_path, monkeypatch)
    key = json.loads((state / result["benchmark_id"] / "answer-key.json").read_text())
    fixtures = {}
    unavailable = ["auditory", "synchronized_av"]
    for fid, row in key["fixtures"].items():
        findings = []
        for exp in row["expected"]:
            if exp["modality"] in unavailable:
                continue
            finding = {
                "code": exp["code"],
                "severity": exp["severity"],
                "claim_type": "measured",
                "notes": "fixture expectation reproduced in scorer test",
            }
            if "start_seconds" in exp:
                finding["start_seconds"] = exp["start_seconds"]
                finding["end_seconds"] = exp["end_seconds"]
            findings.append(finding)
        fixtures[fid] = {"findings": findings}
    findings_path = package_path.parent / "findings.json"
    findings_path.write_text(json.dumps({
        "unavailable_modalities": unavailable,
        "fixtures": fixtures,
    }))
    sv.freeze_findings(
        package_path,
        findings_path,
        contamination_status="PARTIALLY_BLINDED",
        state_root=state,
        context_exposure=["implementation author"],
    )
    score = sv.score_benchmark(package_path, state_root=state)
    assert score["summary"]["false_negative"] == 0
    assert score["summary"]["false_positive"] == 0
    assert score["summary"]["unavailable_expected"] == 2
    assert score["summary"]["precision"] == 1.0
    assert score["summary"]["recall"] == 1.0
    assert score["user_holdout_status"] == "NOT_REVEALED_NOT_SCORED"


def test_clean_control_false_alarm_counts(tmp_path, monkeypatch):
    package_path, state, result = _package(tmp_path, monkeypatch)
    key = json.loads((state / result["benchmark_id"] / "answer-key.json").read_text())
    control = next(fid for fid,row in key["fixtures"].items() if row["control"])
    findings = {fid: {"findings": []} for fid in key["fixtures"]}
    findings[control]["findings"] = [{"code":"freeze","severity":"medium","start_seconds":1,"end_seconds":2,"claim_type":"perceived","notes":"intentional false alarm fixture"}]
    findings_path = package_path.parent / "findings.json"
    findings_path.write_text(json.dumps({
        "unavailable_modalities": ["auditory", "synchronized_av"],
        "fixtures": findings,
    }))
    sv.freeze_findings(package_path, findings_path, contamination_status="NOT_BLINDED", state_root=state)
    score = sv.score_benchmark(package_path, state_root=state)
    assert score["summary"]["false_positive"] == 1
    assert score["summary"]["clean_control_false_alarm_rate"] == 1.0


def test_frozen_findings_are_immutable(tmp_path, monkeypatch):
    package_path, state, result = _package(tmp_path, monkeypatch)
    package = json.loads(package_path.read_text())
    fixtures = {row["fixture_id"]: {"findings": []} for row in package["fixtures"]}
    findings_path = package_path.parent / "findings.json"
    findings_path.write_text(json.dumps({"unavailable_modalities": [], "fixtures": fixtures}))
    sv.freeze_findings(package_path, findings_path, contamination_status="BLINDED", state_root=state)
    findings_path.write_text(json.dumps({"unavailable_modalities": ["auditory"], "fixtures": fixtures}))
    with pytest.raises(ValueError, match="already frozen"):
        sv.freeze_findings(package_path, findings_path, contamination_status="BLINDED", state_root=state)


def test_operational_handoff_contains_no_benchmark_answer_key(tmp_path):
    path = tmp_path / "handoff.json"
    package = sv.make_operational_handoff(
        path,
        bridge_commit="b" * 40,
        video_commit="v" * 40,
    )
    encoded = path.read_text()
    assert "answer-key" not in encoded
    assert package["purpose"] == "fresh_session_operability_validation"
    assert package["scoring"]["coverage_semantics"] == 1

def test_operational_handoff_score_is_separate_from_perception(tmp_path):
    package_path = tmp_path / "handoff.json"
    sv.make_operational_handoff(
        package_path,
        bridge_commit="b" * 40,
        video_commit="v" * 40,
    )
    report = {
        "purpose": "fresh_session_operability_validation_report",
        "bridge_commit": "b" * 40,
        "video_commit": "v" * 40,
        "criteria": {
            name: {"status": "PASS", "evidence": f"verified {name}"}
            for name in (
                "tool_discovery",
                "preflight",
                "promotion_contract",
                "bundle_resume_or_page",
                "coverage_semantics",
            )
        },
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report))
    score = sv.score_operational_handoff(package_path, report_path)
    assert score["pass"] is True
    assert score["score"] == score["max_score"] == 5
    assert score["perception_score_included"] is False

def test_freeze_rejects_finding_for_unavailable_modality(tmp_path, monkeypatch):
    package_path, state, result = _package(tmp_path, monkeypatch)
    package = json.loads(package_path.read_text())
    findings = {
        "unavailable_modalities": ["continuous_video"],
        "fixtures": {
            row["fixture_id"]: {"findings": []}
            for row in package["fixtures"]
        },
    }
    first = package["fixtures"][0]["fixture_id"]
    findings["fixtures"][first]["findings"] = [{
        "code": "freeze",
        "severity": "high",
        "start_seconds": 2.0,
        "end_seconds": 3.0,
        "claim_type": "perceived",
        "notes": "contradictory",
    }]
    findings_path = package_path.parent / "findings.json"
    findings_path.write_text(json.dumps(findings))
    with pytest.raises(ValueError, match="modality continuous_video is unavailable"):
        sv.freeze_findings(
            package_path,
            findings_path,
            contamination_status="PARTIALLY_BLINDED",
            state_root=state,
        )


def test_freeze_requires_all_fixture_ids(tmp_path, monkeypatch):
    package_path, state, result = _package(tmp_path, monkeypatch)
    package = json.loads(package_path.read_text())
    findings = {
        "unavailable_modalities": [],
        "fixtures": {
            package["fixtures"][0]["fixture_id"]: {"findings": []}
        },
    }
    findings_path = package_path.parent / "findings.json"
    findings_path.write_text(json.dumps(findings))
    with pytest.raises(ValueError, match="exactly match package"):
        sv.freeze_findings(
            package_path,
            findings_path,
            contamination_status="BLINDED",
            state_root=state,
        )

