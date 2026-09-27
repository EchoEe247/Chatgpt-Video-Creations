from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "cinematicqactl.py"
SPEC = spec_from_file_location("cinematicqactl", MODULE_PATH)
cinematic = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(cinematic)


def test_constant_speed_profile_passes_continuity():
    profile = {
        "duration_seconds": 4,
        "ramp_half_seconds": 0,
        "segments": [{"start": 0, "end": 4, "speed_mps": 20}],
    }
    result = cinematic.check_speed(profile)
    assert result["pass"]
    assert result["max_frame_speed_step_mps"] == 0


def test_instant_speed_step_is_detected():
    profile = {
        "duration_seconds": 4,
        "ramp_half_seconds": 0,
        "segments": [
            {"start": 0, "end": 2, "speed_mps": 20},
            {"start": 2, "end": 4, "speed_mps": 35},
        ],
    }
    result = cinematic.check_speed(profile)
    assert not result["pass"]
    assert result["max_frame_speed_step_mps"] > result["limits"]["frame_step_mps"]


def test_camera_periodicity_flags_repeating_pattern():
    plan = {
        "shots": [
            {"motion": {"camera": camera}}
            for camera in ["rear", "side", "rear", "side", "rear", "side", "rear", "side"]
        ]
    }
    result = cinematic.check_camera_periodicity(plan)
    assert not result["pass"]
    assert result["best_periodic_lag"] == 2
    assert result["best_match_ratio"] == 1.0


def test_camera_variety_can_clear_periodicity_signal():
    plan = {
        "shots": [
            {"motion": {"camera": camera}}
            for camera in ["rear", "side", "aerial", "hood", "front", "wheel", "long", "orbit"]
        ]
    }
    result = cinematic.check_camera_periodicity(plan)
    assert result["pass"]
