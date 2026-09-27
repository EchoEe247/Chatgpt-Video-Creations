import json
from copy import deepcopy
from pathlib import Path

from src.core.av_timeline import compile_timeline, validate_timeline, validate_bindings

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"productions"/"standalone"/"mercy-engine"/"source"/"execution-plan.json"
EVENTS=ROOT/"productions"/"standalone"/"mercy-engine"/"source"/"av-events.json"


def test_mercy_unified_timeline_compiles_cleanly():
    timeline=compile_timeline(PLAN,EVENTS)
    assert validate_timeline(timeline)==[]
    assert validate_bindings(timeline)==[]
    assert timeline["runtime_seconds"]==180
    assert timeline["fps"]==24
    assert timeline["sample_rate"]==48000
    assert timeline["summary"]["custom_event_count"]==12
    assert timeline["summary"]["audio_targeted"] > 0
    assert timeline["summary"]["picture_targeted"] > 0


def test_same_event_has_picture_frame_and_audio_sample_coordinates():
    timeline=compile_timeline(PLAN,EVENTS)
    event=next(e for e in timeline["events"] if e["id"]=="scene-07.narration-start")
    assert event["at_seconds"]==91.15
    assert event["frame"]==2188
    assert event["sample"]==4375200
    assert event["targets"]==["audio","picture"]


def test_stale_execution_plan_binding_is_detected():
    timeline=compile_timeline(PLAN,EVENTS)
    assert validate_bindings(timeline)==[]
    timeline=deepcopy(timeline)
    timeline["source"]["execution_plan_sha256"]="0"*64
    assert any("execution_plan_sha256 stale" in e for e in validate_bindings(timeline))


def test_events_are_chronologically_sorted():
    timeline=compile_timeline(PLAN,EVENTS)
    times=[e["at_seconds"] for e in timeline["events"]]
    assert times==sorted(times)
