import json
from pathlib import Path
from src.core.production_manifest import STATUSES

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"productions"/"standalone"/"second-earth-benchmark"


def load(name):
    return json.loads((P/"source"/name).read_text())


def test_second_earth_director_plan_hits_benchmark_scope():
    plan=load("execution-plan.json")
    acceptance=load("benchmark-acceptance.json")
    req=acceptance["required_before_render"]
    assert plan["runtime_seconds"]==req["runtime_seconds"]
    assert len(plan["shots"])>=req["min_shots"]
    assert max(s["duration_seconds"] for s in plan["shots"])<=req["max_default_shot_seconds"]
    assert set(req["required_renderer_lanes"])<=set(plan["summary"]["renderer_lanes"])
    assert plan["summary"]["hero_shot_count"]>=req["min_hero_shots"]
    assert plan["summary"]["unresolved_asset_count"]==0
    assert plan["summary"]["blocked_shot_count"]==0
    assert plan["summary"]["warning_count"]==0


def test_second_earth_timeline_is_shared_and_dense():
    timeline=load("av-timeline.json")
    assert timeline["runtime_seconds"]==150
    assert timeline["fps"]==24
    assert timeline["sample_rate"]==48000
    assert timeline["summary"]["custom_event_count"]==28
    assert timeline["summary"]["audio_targeted"]>50
    assert timeline["summary"]["picture_targeted"]>70
    assert timeline["summary"]["qa_targeted"]>30


def test_second_earth_uses_no_online_video_generation_and_requires_creative_qa():
    production=json.loads((P/"production.json").read_text())
    acceptance=load("benchmark-acceptance.json")
    assert acceptance["required_before_render"]["online_video_generation"] is False
    assert production["workflow"]["creative_qa_required"] is True
    assert production["status"] in STATUSES


def test_second_earth_local_asset_resolution_has_no_blockers():
    assets=load("asset-resolution.json")
    assert assets["required_new_downloads"]==0
    assert assets["blocked"]==[]
    assert all(a["status"].startswith("verified") for a in assets["local_ready"])


def test_second_earth_layout_metadata_is_phone_safe_by_declared_geometry():
    layout=load("layout-qa.json")
    safe=layout["safe_margin_ratio"]
    for item in layout["text_items"]:
        x,y,w,h=item["bbox_norm"]
        assert x>=safe and y>=safe
        assert x+w<=1-safe and y+h<=1-safe
        assert item["font_px"]*(360/1280)>=11

def test_second_earth_implementation_map_covers_every_shot_once():
    plan=load("execution-plan.json")
    impl=load("implementation-map.json")
    visual=[g for g in impl["groups"] if g["lane"] in {"python","canvas_handdrawn","blender","ffmpeg"}]
    covered=[sid for g in visual for sid in g.get("shots",[])]
    expected=[s["id"] for s in plan["shots"]]
    assert sorted(covered)==sorted(expected)
    assert len(covered)==len(set(covered))
    assert impl["render_order"][-1]=="master_assembly"

def test_second_earth_implementation_sources_are_present():
    impl=load("implementation-map.json")
    expected={
        "render_benchmark.py",
        "audio/build_audio.py",
        "renderers/python_frames.py",
        "renderers/canvas_world.html",
        "renderers/render_canvas_shots.mjs",
        "renderers/build_blender_physical.py",
        "renderers/build_blender_probe.py",
    }
    for rel in expected:
        assert (P/rel).is_file(), rel
    assert impl["groups"][0]["source"]=="renderers/python_frames.py"
    assert impl["groups"][-1]["source"]=="render_benchmark.py"