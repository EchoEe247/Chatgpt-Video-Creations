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

def test_asset_strategy_blocks_unresolved_high_impact_source(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]={
        "principle":"source_nouns_author_verbs",
        "requirements":[{
            "id":"hero-character",
            "kind":"character",
            "need":"A controllable biped hero",
            "decision":"source_free",
            "assets":[],
            "structural_requirements":["rigged biped"],
            "license_requirements":["commercial video permitted"],
            "adaptation_plan":"",
            "local_authorship":["performance","camera","lighting"],
        }],
    }
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    req=plan["asset_strategy"]["requirements"][0]
    assert req["resolved"] is False
    assert "no_selected_asset" in req["blockers"]
    assert "adaptation_plan_missing" in req["blockers"]
    assert plan["summary"]["unresolved_asset_requirement_count"]==1
    assert plan["summary"]["execution_ready"] is False
    assert any(w["code"]=="asset_strategy_unresolved" for w in plan["warnings"])


def test_asset_strategy_author_local_is_intentional_and_resolved(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]={
        "principle":"source_nouns_author_verbs",
        "requirements":[{
            "id":"custom-route",
            "kind":"environment",
            "need":"A production-specific route",
            "decision":"author_local",
            "assets":[],
            "structural_requirements":["continuous world-space path"],
            "license_requirements":[],
            "adaptation_plan":"",
            "local_authorship":["route geometry","world layout"],
        }],
    }
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    req=plan["asset_strategy"]["requirements"][0]
    assert req["resolved"] is True
    assert req["blockers"]==[]
    assert plan["summary"]["unresolved_asset_requirement_count"]==0
    assert plan["summary"]["execution_ready"] is True


def test_asset_strategy_resolves_catalogued_source_with_adaptation(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]={
        "principle":"source_nouns_author_verbs",
        "requirements":[{
            "id":"hero-spaceship",
            "kind":"vehicle",
            "need":"Controllable hero spacecraft",
            "decision":"source_free",
            "assets":["model.quaternius-ultimate-space-spaceship"],
            "structural_requirements":["stable transform"],
            "license_requirements":["commercial use","modification"],
            "adaptation_plan":"Scale, material-match and light locally.",
            "local_authorship":["flight path","camera","lighting"],
        }],
    }
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    req=plan["asset_strategy"]["requirements"][0]
    assert req["resolved"] is True
    assert req["assets"][0]["asset_id"]=="model.quaternius-ultimate-space-spaceship"


def test_asset_strategy_rejects_unknown_decision():
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]={
        "requirements":[{
            "id":"hero",
            "kind":"character",
            "need":"hero",
            "decision":"magic",
            "assets":[],
        }]
    }
    errors=validate_director_brief(brief)
    assert any("decision must be one of" in e for e in errors)

def test_provider_entry_does_not_satisfy_concrete_asset_requirement(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]={
        "principle":"source_nouns_author_verbs",
        "requirements":[{
            "id":"hero-character",
            "kind":"character",
            "need":"A concrete rigged biped hero",
            "decision":"source_free",
            "assets":["provider.mixamo"],
            "structural_requirements":["rigged biped"],
            "license_requirements":["commercial video permitted"],
            "adaptation_plan":"Retarget and direct the performance locally.",
            "local_authorship":["performance","camera","lighting"],
        }],
    }
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    req=plan["asset_strategy"]["requirements"][0]
    assert req["resolved"] is False
    assert "provider_not_concrete_asset" in req["blockers"]
    assert req["assets"][0]["kind"]=="provider"

def _resolved_asset_strategy():
    return {
        "principle":"source_nouns_author_verbs",
        "requirements":[{
            "id":"custom-world",
            "kind":"environment",
            "need":"Production-specific world",
            "decision":"author_local",
            "assets":[],
            "structural_requirements":[],
            "license_requirements":[],
            "adaptation_plan":"",
            "local_authorship":["world layout"],
        }],
    }


def test_visual_development_required_gates_block_execution(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]=_resolved_asset_strategy()
    brief["visual_development"]={
        "previs":{
            "decision":"required",
            "status":"pending",
            "artifact":"",
            "review_focus":["timing","camera"],
            "notes":"",
        },
        "lookdev":{
            "decision":"required",
            "status":"pending",
            "artifact":"",
            "review_focus":["materials","lighting"],
            "notes":"",
        },
    }
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    assert plan["summary"]["unresolved_development_gate_count"]==2
    assert plan["summary"]["execution_ready"] is False
    assert "not_approved" in plan["visual_development"]["gates"]["previs"]["blockers"]
    assert "artifact_missing" in plan["visual_development"]["gates"]["lookdev"]["blockers"]


def test_visual_development_approved_gates_allow_execution(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]=_resolved_asset_strategy()
    brief["visual_development"]={
        "previs":{
            "decision":"required",
            "status":"approved",
            "artifact":"development/previs.mp4",
            "review_focus":["timing","camera","screen geography"],
            "notes":"",
        },
        "lookdev":{
            "decision":"required",
            "status":"approved",
            "artifact":"development/lookdev/hero-night.png",
            "review_focus":["materials","lighting","reflections","contact"],
            "notes":"",
        },
    }
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    assert plan["summary"]["unresolved_development_gate_count"]==0
    assert plan["summary"]["execution_ready"] is True


def test_blender_multipass_requires_passes_and_goals(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]=_resolved_asset_strategy()
    brief["visual_development"]={
        "previs":{"decision":"not_required","status":"not_required","artifact":"","review_focus":[],"notes":""},
        "lookdev":{"decision":"not_required","status":"not_required","artifact":"","review_focus":[],"notes":""},
    }
    brief["shots"][0]["renderer"]="blender"
    brief["shots"][0]["compositing"]={"mode":"multipass","passes":[],"goals":[],"output":"","notes":""}
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    comp=plan["shots"][0]["compositing"]
    assert comp["resolved"] is False
    assert "passes_missing" in comp["blockers"]
    assert "goals_missing" in comp["blockers"]
    assert plan["summary"]["unresolved_compositing_shot_count"]==1
    assert plan["summary"]["execution_ready"] is False


def test_blender_hybrid_compositing_contract_resolves(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]=_resolved_asset_strategy()
    brief["visual_development"]={
        "previs":{"decision":"not_required","status":"not_required","artifact":"","review_focus":[],"notes":""},
        "lookdev":{"decision":"not_required","status":"not_required","artifact":"","review_focus":[],"notes":""},
    }
    brief["shots"][0]["renderer"]="blender"
    brief["shots"][0]["compositing"]={
        "mode":"hybrid",
        "passes":["beauty","depth","cryptomatte_object","emission"],
        "goals":["depth atmosphere","hero isolation","emission control"],
        "output":"composite/shot-01.exr",
        "notes":"",
    }
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    assert plan["shots"][0]["compositing"]["resolved"] is True
    assert plan["summary"]["unresolved_compositing_shot_count"]==0
    assert plan["summary"]["execution_ready"] is True


def test_visual_development_and_compositing_enums_are_validated():
    brief=json.loads(BRIEF.read_text())
    brief["visual_development"]={
        "previs":{"decision":"sometimes","status":"pending","review_focus":[]},
        "lookdev":{"decision":"required","status":"maybe","review_focus":[]},
    }
    brief["shots"][0]["compositing"]={"mode":"magic","passes":[],"goals":[]}
    errors=validate_director_brief(brief)
    assert any("visual_development.previs.decision" in e for e in errors)
    assert any("visual_development.lookdev.status" in e for e in errors)
    assert any("shots[0].compositing.mode" in e for e in errors)

def test_blender_compositing_rejects_unknown_pass_name(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]=_resolved_asset_strategy()
    brief["visual_development"]={
        "previs":{"decision":"not_required","status":"not_required","artifact":"","review_focus":[],"notes":""},
        "lookdev":{"decision":"not_required","status":"not_required","artifact":"","review_focus":[],"notes":""},
    }
    brief["shots"][0]["renderer"]="blender"
    brief["shots"][0]["compositing"]={
        "mode":"multipass",
        "passes":["beauty","magic_pass"],
        "goals":["control finishing"],
        "output":"composite/shot-01.exr",
        "notes":"",
    }
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    blockers=plan["shots"][0]["compositing"]["blockers"]
    assert any(b.startswith("unsupported_passes:") for b in blockers)
    assert plan["summary"]["execution_ready"] is False


def test_blender_custom_aov_namespace_is_allowed(tmp_path):
    brief=json.loads(BRIEF.read_text())
    brief["asset_strategy"]=_resolved_asset_strategy()
    brief["visual_development"]={
        "previs":{"decision":"not_required","status":"not_required","artifact":"","review_focus":[],"notes":""},
        "lookdev":{"decision":"not_required","status":"not_required","artifact":"","review_focus":[],"notes":""},
    }
    brief["shots"][0]["renderer"]="blender"
    brief["shots"][0]["compositing"]={
        "mode":"multipass",
        "passes":["beauty","depth","aov:hero_edge"],
        "goals":["depth atmosphere","hero edge control"],
        "output":"composite/shot-01.exr",
        "notes":"",
    }
    p=tmp_path/"brief.json"
    p.write_text(json.dumps(brief))
    plan=compile_plan(p,CATALOG)
    assert plan["shots"][0]["compositing"]["resolved"] is True

def test_rejected_eighth_hour_pattern_is_blocked_by_quality_floor():
    fixture=ROOT/"tests/fixtures/eighth-hour-quality-regression.json"
    plan=compile_plan(fixture,CATALOG)
    blockers=plan["quality_floor"]["blockers"]
    assert plan["summary"]["execution_ready"] is False
    assert plan["summary"]["final_delivery_ready"] is False
    assert "previs_required_for_cinematic_3d" in blockers
    assert "lookdev_required_for_cinematic_3d" in blockers
    assert "blender_lane_required_for_cinematic_3d" in blockers
    assert "character_requirement_missing" in blockers
    assert "environment_asset_proof_missing" in blockers


def test_final_cinematic_quality_floor_passes_only_with_real_production_decisions(tmp_path):
    brief=json.loads((ROOT/"templates/director-brief.json").read_text())
    brief["title"]="quality-floor-pass"
    brief["goal"]={
        "audience":"test",
        "runtime_seconds":6,
        "one_sentence_promise":"A finished cinematic character shot.",
        "ending_takeaway":""
    }
    brief["story"]={"setup":"A","escalation":"B","turn":"C","resolution":"D","emotional_arc":[]}
    brief["quality_floor"]={
        "delivery_level":"final",
        "visual_mode":"cinematic_3d",
        "character_mode":"performance",
        "environment_mode":"spatial",
        "proxy_assets_allowed":False,
        "minimum_delivery_height":720,
        "notes":""
    }
    brief["asset_strategy"]={
        "principle":"source_nouns_author_verbs",
        "requirements":[
            {
                "id":"hero-character","kind":"character","need":"Rigged hero",
                "decision":"author_local","assets":[],"structural_requirements":["rigged"],
                "license_requirements":[],"adaptation_plan":"",
                "local_authorship":["rig","performance"],"proof_artifact":"development/hero-proof.blend"
            },
            {
                "id":"hero-environment","kind":"environment","need":"Spatial office",
                "decision":"author_local","assets":[],"structural_requirements":["spatial"],
                "license_requirements":[],"adaptation_plan":"",
                "local_authorship":["set","lighting"],"proof_artifact":"development/office-proof.blend"
            }
        ]
    }
    brief["visual_development"]={
        "previs":{
            "decision":"required","status":"approved","artifact":"development/previs.mp4",
            "review_focus":["timing","blocking","camera"],"notes":""
        },
        "lookdev":{
            "decision":"required","status":"approved","artifact":"development/lookdev.png",
            "review_focus":["materials","lighting","reflections","contact"],"notes":""
        }
    }
    brief["hero_shots"]=["shot-01"]
    brief["shots"]=[{
        "id":"shot-01","duration_seconds":6,"narrative_purpose":"hero action",
        "visible_event":"Hero crosses office","camera":"dolly","subject_motion":"walk",
        "environment_motion":"practicals react","depth_layers":["fg","hero","bg"],"palette":"neutral",
        "transition_in":"cut","transition_out":"cut","audio_cue":"room tone",
        "renderer":"blender","assets":[],"continuity_dependencies":[],
        "review_points_seconds":[3],"failure_modes":[],
        "compositing":{"mode":"beauty_only","passes":[],"goals":[],"output":"","notes":""}
    }]
    path=tmp_path/"director.json"
    path.write_text(json.dumps(brief))
    plan=compile_plan(path,CATALOG)
    assert plan["quality_floor"]["blockers"]==[]
    assert plan["summary"]["execution_ready"] is True
    assert plan["summary"]["final_delivery_ready"] is True


def test_prototype_quality_floor_never_reports_final_delivery_ready(tmp_path):
    brief=json.loads((ROOT/"tests/fixtures/eighth-hour-quality-regression.json").read_text())
    brief["quality_floor"].update({
        "delivery_level":"prototype",
        "visual_mode":"stylized_2d",
        "character_mode":"incidental",
        "environment_mode":"graphic",
        "proxy_assets_allowed":True,
    })
    path=tmp_path/"director.json"
    path.write_text(json.dumps(brief))
    plan=compile_plan(path,CATALOG)
    assert plan["quality_floor"]["resolved"] is True
    assert plan["summary"]["execution_ready"] is True
    assert plan["summary"]["final_delivery_ready"] is False
