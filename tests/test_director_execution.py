import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.core.director_execution import compile_plan, validate_director_brief, validate_execution_plan, validate_source_bindings

ROOT=Path(__file__).resolve().parents[1]
BRIEF=ROOT/"productions"/"standalone"/"mercy-engine"/"source"/"director-brief.json"
CATALOG=ROOT/"assets"/"catalog.json"


def test_mercy_brief_compiles_to_unblocked_durable_plan():
    plan=compile_plan(BRIEF,CATALOG)
    assert validate_execution_plan(plan)==[]
    assert plan["runtime_seconds"]==180
    assert plan["summary"]["shot_count"]==12
    assert plan["summary"]["hero_shot_count"]==7
    assert plan["summary"]["renderer_lanes"]==["python"]
    assert plan["summary"]["unresolved_asset_count"]==0
    assert plan["execution_policy"]["cooperation_required"] is False
    assert plan["source"]["director_brief"].startswith("productions/")
    orbit=next(s for s in plan["shots"] if s["id"]=="scene-07")
    assert orbit["assets"][0]["asset_id"]=="model.quaternius-ultimate-space-spaceship"
    assert orbit["assets"][0]["license"]=="CC0-1.0"
    assert [p["absolute_seconds"] for p in orbit["review_points"]]==[92.0,97.0,102.0]


def test_long_shots_are_flagged_not_silently_split():
    plan=compile_plan(BRIEF,CATALOG,max_default_shot=8)
    density=[w for w in plan["warnings"] if w["code"]=="shot_density_review"]
    assert len(density)==12
    assert len(plan["shots"])==12


def test_brief_runtime_mismatch_is_rejected():
    brief=json.loads(BRIEF.read_text())
    brief=deepcopy(brief)
    brief["goal"]["runtime_seconds"]=179
    errors=validate_director_brief(brief)
    assert any("durations total" in e for e in errors)


def test_unknown_renderer_is_explicitly_blocked(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["shots"][0]["renderer"]="mystery renderer"
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    shot=plan["shots"][0]
    assert shot["renderer"]["lane"]=="unresolved"
    assert shot["renderer"]["adapter_ready"] is False
    assert any(w["code"]=="renderer_unresolved" for w in plan["warnings"])


def test_execution_plan_is_hash_bound_to_inputs():
    plan=compile_plan(BRIEF,CATALOG)
    assert len(plan["source"]["director_sha256"])==64
    assert len(plan["source"]["asset_catalog_sha256"])==64

def test_source_binding_detects_stale_plan():
    plan=compile_plan(BRIEF,CATALOG)
    assert validate_source_bindings(plan)==[]
    plan["source"]["director_sha256"]="0"*64
    assert any("director_sha256 stale" in e for e in validate_source_bindings(plan))
