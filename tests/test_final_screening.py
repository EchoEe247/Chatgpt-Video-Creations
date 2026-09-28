import copy
import json
from pathlib import Path

from src.core.final_screening import (
    DEPARTMENTS,
    MODALITIES,
    make_blind_audit_package,
    validate_final_screening,
)
from src.core.studio_review import ASSISTANT_ACCEPTED, VERIFICATION_REQUIRED, derive_promotion_state

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = json.loads((ROOT / "templates/production-v2.json").read_text())


def _screening(candidate="a" * 64, duration=10.0):
    departments = {}
    for name in DEPARTMENTS:
        if name in {"music", "dialogue_narration", "vfx"}:
            departments[name] = {
                "applicability": "NOT_APPLICABLE",
                "status": None,
                "reason": f"{name} not used in fixture",
                "evidence": [],
            }
        else:
            departments[name] = {
                "applicability": "APPLICABLE",
                "status": "PASS",
                "evidence": ["ev-main"],
                "observations": ["reviewed exact candidate"],
                "claim_types": ["perceived", "measured"],
            }
    modalities = {
        "still_image": {
            "applicability": "APPLICABLE",
            "status": "PASS",
            "evidence": ["ev-main"],
        },
        "sampled_temporal": {
            "applicability": "APPLICABLE",
            "status": "PASS",
            "evidence": ["ev-main"],
        },
        "continuous_video": {
            "applicability": "APPLICABLE",
            "status": "PASS",
            "evidence": ["ev-continuous"],
        },
        "auditory": {
            "applicability": "NOT_APPLICABLE",
            "status": None,
            "reason": "fixture is reviewed without required subjective audio",
            "evidence": [],
        },
        "synchronized_av": {
            "applicability": "NOT_APPLICABLE",
            "status": None,
            "reason": "fixture has no sync-critical event",
            "evidence": [],
        },
    }
    return {
        "candidate_sha256": candidate,
        "duration_seconds": duration,
        "departments": departments,
        "modalities": modalities,
        "coverage": {
            "still_image": [{"start_seconds": 0, "end_seconds": 0.1}],
            "sampled_temporal": [{"start_seconds": 0, "end_seconds": duration}],
            "continuous_video": [{"start_seconds": 0, "end_seconds": duration}],
            "auditory": [],
            "synchronized_av": [],
        },
        "evidence_ids": ["ev-main", "ev-continuous"],
        "opening_reviewed": True,
        "ending_reviewed": True,
        "authored_points": {"planned_ids": ["cut-1"], "reviewed_ids": ["cut-1"]},
        "second_pass": {"required": False, "status": "NOT_REQUIRED", "targets": [], "disposed_ids": []},
        "declaration": {
            "reviewer": "model_plus_human",
            "reviewed_at": "2026-09-28T00:00:00Z",
            "modalities_actually_perceived": ["still_image", "sampled_temporal", "continuous_video"],
            "candidate_sha256": candidate,
        },
    }


def _production():
    data = copy.deepcopy(TEMPLATE)
    data["workflow"]["creative_qa_required"] = False
    data["workflow"]["studio_review_required"] = True
    data["delivery"]["expected_duration_seconds"] = 10.0
    data["delivery"]["audio_required"] = False
    data["artifacts"].update({
        "candidate_master": "candidate.mp4",
        "candidate_sha256": "a" * 64,
        "artifact_receipt": "receipt.json",
        "review_pack": "review.json",
    })
    data["gates"]["technical"].update({"status": "PASS", "candidate_sha256": "a" * 64})
    data["gates"]["assistant"].update({"status": "PASS", "candidate_sha256": "a" * 64})
    data["studio_review"] = {
        "schema_version": 2,
        "required": True,
        "candidate_sha256": "a" * 64,
        "criteria": {
            "final_screening": {
                "applicability": "APPLICABLE",
                "status": "PASS",
                "blocking": True,
                "evidence": ["ev-main"],
            }
        },
        "evidence": {
            "ev-main": {
                "state": "REVIEWED",
                "candidate_sha256": "a" * 64,
                "modalities": ["still_image", "sampled_temporal"],
            },
            "ev-continuous": {
                "state": "REVIEWED",
                "candidate_sha256": "a" * 64,
                "modalities": ["continuous_video"],
            },
        },
        "final_screening": _screening(),
        "notes": None,
    }
    return data


def test_complete_final_screening_can_support_assistant_acceptance():
    data = _production()
    assert validate_final_screening(
        data["studio_review"],
        candidate_sha256="a" * 64,
        duration_seconds=10.0,
    ) == []
    assert derive_promotion_state(data) == ASSISTANT_ACCEPTED


def test_continuous_video_gap_blocks_promotion():
    data = _production()
    data["studio_review"]["final_screening"]["coverage"]["continuous_video"] = [
        {"start_seconds": 0, "end_seconds": 4.0},
        {"start_seconds": 4.5, "end_seconds": 10.0},
    ]
    assert derive_promotion_state(data) == VERIFICATION_REQUIRED


def test_required_unavailable_modality_remains_unverified():
    data = _production()
    audio = data["studio_review"]["final_screening"]["modalities"]["auditory"]
    audio.clear()
    audio.update({
        "applicability": "APPLICABLE",
        "status": "UNVERIFIED",
        "evidence": [],
    })
    assert derive_promotion_state(data) == VERIFICATION_REQUIRED


def test_unresolved_suspicion_second_pass_blocks_promotion():
    data = _production()
    data["studio_review"]["final_screening"]["second_pass"] = {
        "required": True,
        "status": "UNVERIFIED",
        "targets": [{"id": "risk-001"}],
        "disposed_ids": [],
    }
    assert derive_promotion_state(data) == VERIFICATION_REQUIRED


def test_resolved_suspicion_second_pass_can_pass():
    data = _production()
    data["studio_review"]["final_screening"]["second_pass"] = {
        "required": True,
        "status": "PASS",
        "targets": [{"id": "risk-001"}],
        "disposed_ids": ["risk-001"],
    }
    assert derive_promotion_state(data) == ASSISTANT_ACCEPTED


def test_missing_department_is_not_silently_ignored():
    data = _production()
    del data["studio_review"]["final_screening"]["departments"]["continuity"]
    errors = validate_final_screening(
        data["studio_review"],
        candidate_sha256="a" * 64,
        duration_seconds=10.0,
    )
    assert any("departments.continuity is required" in error for error in errors)




def test_screening_evidence_id_must_resolve_to_reviewed_authoritative_record():
    data = _production()
    del data["studio_review"]["evidence"]["ev-continuous"]
    errors = validate_final_screening(
        data["studio_review"],
        candidate_sha256="a" * 64,
        duration_seconds=10.0,
    )
    assert any("ev-continuous is missing from authoritative studio_review.evidence" in error for error in errors)
    assert derive_promotion_state(data) == VERIFICATION_REQUIRED

def test_blind_audit_package_excludes_prior_findings_and_repairs():
    package = make_blind_audit_package(
        {
            "candidate_sha256": "a" * 64,
            "candidate_duration_seconds": 10.0,
            "evidence": [{"id": "frame-1"}, {"id": "audio-1"}],
            "triage": {"findings": ["secret"]},
            "repair_history": ["secret"],
        },
        requirements=["inspect candidate", "localize defects"],
    )
    encoded = json.dumps(package)
    assert "secret" not in encoded
    assert package["findings_frozen_before_reveal"] is False
    assert "prior audit findings" in package["excluded_context"]
