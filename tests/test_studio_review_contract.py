import copy
import json
from pathlib import Path

from src.core.production_runtime import apply_runtime_defaults, ready_for_user_review
from src.core.studio_review import (
    ASSISTANT_ACCEPTED,
    REFINEMENT_REQUIRED,
    USER_ACCEPTED,
    VERIFICATION_REQUIRED,
    derive_promotion_state,
    legacy_review_aliases,
    validate_studio_review,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = json.loads((ROOT / "templates/production-v2.json").read_text())


def candidate_base():
    data = copy.deepcopy(TEMPLATE)
    data["production_id"] = "studio-contract-test"
    data["source"]["show"] = "test-show"
    data["workflow"]["creative_qa_required"] = False
    data["artifacts"].update(
        {
            "candidate_master": "candidate.mp4",
            "candidate_sha256": "a" * 64,
            "artifact_receipt": "receipt.json",
            "review_pack": "review-pack.json",
        }
    )
    data["gates"]["technical"].update(
        {"status": "PASS", "candidate_sha256": "a" * 64}
    )
    data["gates"]["assistant"].update(
        {"status": "PASS", "candidate_sha256": "a" * 64}
    )
    return data


def test_velocity_style_specialized_failure_vetoes_legacy_assistant_pass():
    data = candidate_base()
    data["gates"]["cinematic"] = {
        "status": "REFINEMENT_REQUIRED",
        "candidate_sha256": "a" * 64,
    }
    data["review"]["assistant"] = "PASS"
    assert derive_promotion_state(data) == REFINEMENT_REQUIRED
    assert legacy_review_aliases(data)["assistant"] == "PENDING"
    apply_runtime_defaults(data)
    assert data["gates"]["assistant"]["status"] == "PASS"
    assert data["gates"]["cinematic"]["status"] == "REFINEMENT_REQUIRED"
    assert data["review"]["assistant"] == "PENDING"
    assert not ready_for_user_review(data)


def test_required_studio_review_missing_is_verification_required():
    data = candidate_base()
    data["workflow"]["studio_review_required"] = True
    data.pop("studio_review", None)
    assert derive_promotion_state(data) == VERIFICATION_REQUIRED
    assert not ready_for_user_review(data)


def test_not_applicable_is_distinct_from_unverified():
    review = {
        "schema_version": 1,
        "required": True,
        "candidate_sha256": "a" * 64,
        "criteria": {
            "narration": {
                "applicability": "NOT_APPLICABLE",
                "status": None,
                "reason": "Production contains no narration.",
                "blocking": True,
                "evidence": [],
            },
            "picture": {
                "applicability": "APPLICABLE",
                "status": "UNVERIFIED",
                "blocking": True,
                "evidence": [],
            },
        },
        "evidence": {},
    }
    assert validate_studio_review(review, candidate_sha256="a" * 64) == []
    data = candidate_base()
    data["workflow"]["studio_review_required"] = True
    data["studio_review"] = review
    assert derive_promotion_state(data) == VERIFICATION_REQUIRED


def test_not_applicable_requires_reason():
    review = {
        "required": True,
        "candidate_sha256": "a" * 64,
        "criteria": {
            "music": {
                "applicability": "NOT_APPLICABLE",
                "status": None,
                "reason": "",
                "evidence": [],
            }
        },
        "evidence": {},
    }
    errors = validate_studio_review(review, candidate_sha256="a" * 64)
    assert any("NOT_APPLICABLE requires reason" in error for error in errors)


def test_generated_evidence_is_not_reviewed_evidence():
    review = {
        "required": True,
        "candidate_sha256": "a" * 64,
        "criteria": {
            "composition": {
                "applicability": "APPLICABLE",
                "status": "PASS",
                "blocking": True,
                "evidence": ["frame-1"],
            }
        },
        "evidence": {
            "frame-1": {
                "state": "GENERATED",
                "history": [
                    {"state": "PLANNED"},
                    {"state": "GENERATED"},
                ],
            }
        },
    }
    errors = validate_studio_review(review, candidate_sha256="a" * 64)
    assert any("PASS requires REVIEWED evidence frame-1" in error for error in errors)
    data = candidate_base()
    data["workflow"]["studio_review_required"] = True
    data["studio_review"] = review
    assert derive_promotion_state(data) == VERIFICATION_REQUIRED


def test_reviewed_evidence_can_support_blocking_pass():
    review = {
        "required": True,
        "candidate_sha256": "a" * 64,
        "criteria": {
            "composition": {
                "applicability": "APPLICABLE",
                "status": "PASS",
                "blocking": True,
                "evidence": ["frame-1"],
            }
        },
        "evidence": {
            "frame-1": {
                "state": "REVIEWED",
                "history": [
                    {"state": "PLANNED"},
                    {"state": "GENERATED"},
                    {"state": "DELIVERED"},
                    {"state": "REVIEWED"},
                ],
            }
        },
    }
    assert validate_studio_review(review, candidate_sha256="a" * 64) == []
    data = candidate_base()
    data["workflow"]["studio_review_required"] = True
    data["studio_review"] = review
    assert derive_promotion_state(data) == ASSISTANT_ACCEPTED
    assert ready_for_user_review(data)


def test_stale_studio_review_binding_is_verification_required():
    data = candidate_base()
    data["workflow"]["studio_review_required"] = True
    data["studio_review"] = {
        "required": True,
        "candidate_sha256": "b" * 64,
        "criteria": {
            "composition": {
                "applicability": "APPLICABLE",
                "status": "PASS",
                "blocking": True,
                "evidence": ["frame"],
            }
        },
        "evidence": {"frame": {"state": "REVIEWED"}},
    }
    assert derive_promotion_state(data) == VERIFICATION_REQUIRED


def test_blocking_criterion_failure_requires_refinement():
    data = candidate_base()
    data["workflow"]["studio_review_required"] = True
    data["studio_review"] = {
        "required": True,
        "candidate_sha256": "a" * 64,
        "criteria": {
            "continuity": {
                "applicability": "APPLICABLE",
                "status": "FAIL",
                "blocking": True,
                "evidence": ["cut-7"],
            }
        },
        "evidence": {"cut-7": {"state": "REVIEWED"}},
    }
    assert derive_promotion_state(data) == REFINEMENT_REQUIRED


def test_user_acceptance_is_derived_not_alias_driven():
    data = candidate_base()
    data["gates"]["user"].update(
        {"status": "PASS", "candidate_sha256": "a" * 64}
    )
    data["review"]["user"] = "PENDING"
    assert derive_promotion_state(data) == USER_ACCEPTED
    assert legacy_review_aliases(data) == {"assistant": "PASS", "user": "PASS"}


def test_evidence_history_cannot_move_backward():
    review = {
        "required": True,
        "candidate_sha256": "a" * 64,
        "criteria": {
            "composition": {
                "applicability": "APPLICABLE",
                "status": "UNVERIFIED",
                "blocking": True,
                "evidence": ["frame"],
            }
        },
        "evidence": {
            "frame": {
                "state": "DELIVERED",
                "history": [
                    {"state": "GENERATED"},
                    {"state": "DELIVERED"},
                    {"state": "GENERATED"},
                    {"state": "DELIVERED"},
                ],
            }
        },
    }
    errors = validate_studio_review(review, candidate_sha256="a" * 64)
    assert any("cannot move backward" in error for error in errors)
