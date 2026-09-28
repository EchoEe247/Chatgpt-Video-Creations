"""Compile a durable director brief into an agent-independent execution plan."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

RENDERER_ALIASES = {
    "python": ("python", "Python/Pillow/NumPy deterministic renderer"),
    "pillow": ("python", "Python/Pillow/NumPy deterministic renderer"),
    "numpy": ("python", "Python/Pillow/NumPy deterministic renderer"),
    "canvas": ("canvas_handdrawn", "Canvas2D hand-drawn renderer"),
    "hand-drawn": ("canvas_handdrawn", "Canvas2D hand-drawn renderer"),
    "hand drawn": ("canvas_handdrawn", "Canvas2D hand-drawn renderer"),
    "three.js": ("threejs", "Three.js/WebGL renderer"),
    "threejs": ("threejs", "Three.js/WebGL renderer"),
    "webgl": ("threejs", "Three.js/WebGL renderer"),
    "blender": ("blender", "Blender renderer"),
    "ffmpeg": ("ffmpeg", "FFmpeg compositor"),
}

ASSET_DECISIONS = {"reuse_local", "source_free", "author_local", "hybrid", "unresolved"}
DEVELOPMENT_DECISIONS = {"required", "not_required", "unresolved"}
DEVELOPMENT_STATUSES = {"pending", "approved", "not_required"}
COMPOSITING_MODES = {"beauty_only", "multipass", "hybrid", "not_applicable", "unresolved"}
QUALITY_DELIVERY_LEVELS = {"final", "prototype", "unresolved"}
QUALITY_VISUAL_MODES = {"cinematic_3d", "stylized_2d", "motion_graphics", "unresolved"}
QUALITY_CHARACTER_MODES = {"none", "incidental", "performance", "unresolved"}
QUALITY_ENVIRONMENT_MODES = {"graphic", "spatial", "unresolved"}
BLENDER_PASS_NAMES = {
    "beauty", "depth", "normal", "vector",
    "diffuse_direct", "diffuse_indirect",
    "glossy_direct", "glossy_indirect",
    "emission", "shadow", "mist",
    "ambient_occlusion", "object_index", "material_index",
    "cryptomatte_object", "cryptomatte_material",
}

ADAPTERS = {
    "python": {"ready": True, "entrypoint": "python {repo}/scripts/python_shot_adapter.py {request}", "fallback_lanes": []},
    "canvas_handdrawn": {"ready": True, "entrypoint": "python {repo}/scripts/browser_shot_adapter.py {request}", "fallback_lanes": ["python"]},
    "threejs": {
        "ready": False,
        "entrypoint": "python {repo}/scripts/browser_shot_adapter.py {request}",
        "fallback_lanes": ["blender", "canvas_handdrawn"],
        "runtime_note": "Standardized browser contract exists, but current Pixel headless Chromium does not expose a WebGL context. Use Blender for spatial 3D or Canvas for non-WebGL motion until rendererctl reports WebGL ready.",
    },
    "blender": {"ready": True, "entrypoint": "python {repo}/scripts/blender_termux_adapter.py {request}", "fallback_lanes": ["python"]},
    "ffmpeg": {"ready": True, "entrypoint": "python {repo}/scripts/ffmpeg_shot_adapter.py {request}", "fallback_lanes": ["python"]},
    "unresolved": {"ready": False, "entrypoint": None, "fallback_lanes": []},
}

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _lane(value: str) -> tuple[str, str]:
    low=(value or "").lower()
    for key, result in RENDERER_ALIASES.items():
        if key in low:
            return result
    return ("unresolved", "Renderer must be selected before production")

def _asset_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a["asset_id"]: a for a in catalog.get("assets", [])}

def _resolve_asset(ref: Any, assets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if isinstance(ref, dict):
        key=ref.get("asset_id")
        label=ref.get("name") or key or str(ref)
    else:
        key=str(ref)
        label=key
    if key in assets:
        a=assets[key]
        return {
            "request": ref,
            "asset_id": key,
            "name": a["name"],
            "kind": a.get("kind"),
            "resolved": True,
            "source_url": a["source"]["url"],
            "license": a["license"]["id"],
            "distribution_mode": a["distribution"]["mode"],
            "local_hint": a["distribution"].get("local_hint"),
        }
    # Deterministic human-name resolution: exact name first, then a unique
    # canonical-name token subset (e.g. creator prefix + canonical asset name).
    matches=[a for a in assets.values() if a.get("kind")!="provider" and a.get("name","").lower()==label.lower()]
    if not matches:
        tokens=lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))
        req=tokens(label)
        matches=[a for a in assets.values() if a.get("kind")!="provider" and tokens(a.get("name","")) and tokens(a.get("name","")).issubset(req)]
    if len(matches)==1:
        a=matches[0]
        return {
            "request": ref, "asset_id": a["asset_id"], "name": a["name"], "kind": a.get("kind"),
            "resolved": True, "source_url": a["source"]["url"],
            "license": a["license"]["id"], "distribution_mode": a["distribution"]["mode"],
            "local_hint": a["distribution"].get("local_hint"),
        }
    return {"request": ref, "asset_id": None, "name": label, "resolved": False}

def _compile_asset_strategy(data: dict[str, Any], assets: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    strategy=data.get("asset_strategy")
    if strategy is None:
        return {
            "reviewed": False,
            "principle": "source_nouns_author_verbs",
            "requirements": [],
        }, [{"code":"asset_strategy_missing","detail":"Legacy brief has no high-impact make-vs-source review. New serious productions should declare asset_strategy before rendering."}]
    requirements=[]
    warnings=[]
    for req in strategy.get("requirements",[]):
        decision=req["decision"]
        resolved_assets=[_resolve_asset(a,assets) for a in req.get("assets",[])]
        reasons=[]
        if decision=="unresolved":
            reasons.append("decision_unresolved")
        if decision in {"reuse_local","source_free","hybrid"}:
            if not resolved_assets:
                reasons.append("no_selected_asset")
            if any(not a["resolved"] for a in resolved_assets):
                reasons.append("selected_asset_unresolved")
            if any(a.get("kind")=="provider" for a in resolved_assets):
                reasons.append("provider_not_concrete_asset")
            if not str(req.get("adaptation_plan","")).strip():
                reasons.append("adaptation_plan_missing")
        if decision in {"author_local","hybrid"} and not req.get("local_authorship"):
            reasons.append("local_authorship_missing")
        compiled={
            "id":req["id"],
            "kind":req["kind"],
            "need":req["need"],
            "decision":decision,
            "assets":resolved_assets,
            "structural_requirements":req.get("structural_requirements",[]),
            "license_requirements":req.get("license_requirements",[]),
            "adaptation_plan":req.get("adaptation_plan",""),
            "local_authorship":req.get("local_authorship",[]),
            "proof_artifact":req.get("proof_artifact",""),
            "resolved":not reasons,
            "blockers":reasons,
        }
        requirements.append(compiled)
        if reasons:
            warnings.append({"requirement_id":req["id"],"code":"asset_strategy_unresolved","detail":reasons})
    return {
        "reviewed": True,
        "principle": strategy.get("principle","source_nouns_author_verbs"),
        "requirements": requirements,
    }, warnings

def _compile_visual_development(data: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    vd=data.get("visual_development")
    if vd is None:
        return {
            "reviewed": False,
            "gates": {},
        }, [{"code":"visual_development_missing","detail":"Legacy brief has no explicit previs/look-dev gate. New serious 3D productions should declare visual_development before expensive rendering."}]
    gates={}
    warnings=[]
    for name in ("previs","lookdev"):
        src=vd.get(name,{})
        decision=src.get("decision","unresolved")
        status=src.get("status","pending")
        blockers=[]
        if decision=="unresolved":
            blockers.append("decision_unresolved")
        elif decision=="required":
            if status!="approved":
                blockers.append("not_approved")
            if not str(src.get("artifact","")).strip():
                blockers.append("artifact_missing")
            if name=="lookdev" and not src.get("review_focus"):
                blockers.append("review_focus_missing")
        elif decision=="not_required" and status!="not_required":
            blockers.append("status_must_be_not_required")
        gate={
            "decision":decision,
            "status":status,
            "artifact":src.get("artifact",""),
            "review_focus":src.get("review_focus",[]),
            "notes":src.get("notes",""),
            "resolved":not blockers,
            "blockers":blockers,
        }
        gates[name]=gate
        if blockers:
            warnings.append({"gate":name,"code":"visual_development_unresolved","detail":blockers})
    return {"reviewed":True,"gates":gates}, warnings

def _compile_quality_floor(
    data: dict[str, Any],
    asset_strategy: dict[str, Any],
    visual_development: dict[str, Any],
    shots: list[dict[str, Any]],
    *,
    height: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    src=data.get("quality_floor")
    if src is None:
        return {
            "reviewed":False,
            "delivery_level":"legacy_unspecified",
            "visual_mode":"legacy_unspecified",
            "character_mode":"legacy_unspecified",
            "environment_mode":"legacy_unspecified",
            "proxy_assets_allowed":None,
            "minimum_delivery_height":None,
            "resolved":True,
            "final_delivery_ready":False,
            "blockers":[],
        }, [{"code":"quality_floor_missing","detail":"Legacy brief has no explicit quality floor. New user-facing productions must declare one before final rendering."}]
    delivery=src.get("delivery_level","unresolved")
    visual=src.get("visual_mode","unresolved")
    character=src.get("character_mode","unresolved")
    environment=src.get("environment_mode","unresolved")
    proxy=src.get("proxy_assets_allowed")
    min_height=src.get("minimum_delivery_height",720)
    blockers=[]
    for name,value in (("delivery_level",delivery),("visual_mode",visual),("character_mode",character),("environment_mode",environment)):
        if value=="unresolved":
            blockers.append(name+"_unresolved")
    if not isinstance(proxy,bool):
        blockers.append("proxy_assets_allowed_unresolved")
    if not isinstance(min_height,int) or isinstance(min_height,bool) or min_height<=0:
        blockers.append("minimum_delivery_height_invalid")
    requirements=asset_strategy.get("requirements",[])
    char_reqs=[r for r in requirements if r.get("kind")=="character"]
    env_reqs=[r for r in requirements if r.get("kind")=="environment"]
    gates=visual_development.get("gates",{})
    if delivery=="final":
        if proxy is not False:
            blockers.append("final_proxy_assets_not_allowed")
        if isinstance(min_height,int) and height<min_height:
            blockers.append("delivery_height_below_floor")
        if character=="performance":
            if not char_reqs:
                blockers.append("character_requirement_missing")
            elif not any(r.get("resolved") for r in char_reqs):
                blockers.append("character_requirement_unresolved")
            if char_reqs and not any(str(r.get("proof_artifact","")).strip() for r in char_reqs):
                blockers.append("character_asset_proof_missing")
        if environment=="spatial":
            if not env_reqs:
                blockers.append("environment_requirement_missing")
            elif not any(r.get("resolved") for r in env_reqs):
                blockers.append("environment_requirement_unresolved")
            if env_reqs and not any(str(r.get("proof_artifact","")).strip() for r in env_reqs):
                blockers.append("environment_asset_proof_missing")
        if visual=="cinematic_3d":
            for name in ("previs","lookdev"):
                gate=gates.get(name,{})
                if gate.get("decision")!="required":
                    blockers.append(name+"_required_for_cinematic_3d")
                elif gate.get("status")!="approved" or not gate.get("artifact"):
                    blockers.append(name+"_not_approved_for_cinematic_3d")
            if not any(s.get("renderer",{}).get("lane")=="blender" for s in shots):
                blockers.append("blender_lane_required_for_cinematic_3d")
        if visual=="stylized_2d":
            gate=gates.get("lookdev",{})
            if gate.get("decision")!="required":
                blockers.append("lookdev_required_for_stylized_2d")
            elif gate.get("status")!="approved" or not gate.get("artifact"):
                blockers.append("lookdev_not_approved_for_stylized_2d")
            if float(data.get("goal",{}).get("runtime_seconds") or 0)>30:
                pg=gates.get("previs",{})
                if pg.get("decision")!="required":
                    blockers.append("previs_required_for_long_stylized_2d")
                elif pg.get("status")!="approved" or not pg.get("artifact"):
                    blockers.append("previs_not_approved_for_long_stylized_2d")
    unresolved_enums=any(b.endswith("_unresolved") for b in blockers)
    resolved=not blockers if delivery=="final" else not unresolved_enums
    final_ready=delivery=="final" and not blockers
    compiled={
        "reviewed":True,
        "delivery_level":delivery,
        "visual_mode":visual,
        "character_mode":character,
        "environment_mode":environment,
        "proxy_assets_allowed":proxy,
        "minimum_delivery_height":min_height,
        "notes":src.get("notes",""),
        "resolved":resolved,
        "final_delivery_ready":final_ready,
        "blockers":blockers,
    }
    warnings=[]
    if blockers:
        warnings.append({"code":"quality_floor_blocked","detail":blockers})
    return compiled,warnings

def _compile_compositing(shot: dict[str, Any], lane: str) -> tuple[dict[str, Any], list[str]]:
    src=shot.get("compositing")
    if src is None:
        if lane=="blender":
            return {
                "reviewed":False,
                "mode":"legacy_unspecified",
                "passes":[],
                "goals":[],
                "resolved":True,
                "blockers":[],
            }, ["blender_compositing_strategy_missing"]
        return {
            "reviewed":False,
            "mode":"not_applicable",
            "passes":[],
            "goals":[],
            "resolved":True,
            "blockers":[],
        }, []
    mode=src.get("mode","unresolved")
    passes=src.get("passes",[])
    goals=src.get("goals",[])
    blockers=[]
    if lane=="blender":
        if mode=="unresolved":
            blockers.append("mode_unresolved")
        if mode in {"multipass","hybrid"} and not passes:
            blockers.append("passes_missing")
        unknown=[p for p in passes if p not in BLENDER_PASS_NAMES and not str(p).startswith("aov:")]
        if unknown:
            blockers.append("unsupported_passes:"+",".join(sorted(map(str,unknown))))
        if mode in {"multipass","hybrid"} and not goals:
            blockers.append("goals_missing")
    elif mode=="unresolved":
        mode="not_applicable"
    return {
        "reviewed":True,
        "mode":mode,
        "passes":passes,
        "goals":goals,
        "output":src.get("output",""),
        "notes":src.get("notes",""),
        "resolved":not blockers,
        "blockers":blockers,
    }, []

def validate_director_brief(data: dict[str, Any]) -> list[str]:
    errors=[]
    if data.get("schema_version") != 1:
        errors.append("director brief schema_version must be 1")
    goal=data.get("goal") or {}
    runtime=goal.get("runtime_seconds")
    if not isinstance(runtime,(int,float)) or runtime <= 0:
        errors.append("goal.runtime_seconds must be > 0")
    shots=data.get("shots")
    if not isinstance(shots,list) or not shots:
        errors.append("shots must be a non-empty list")
        return errors
    seen=set()
    total=0.0
    for i,s in enumerate(shots):
        p=f"shots[{i}]"
        sid=s.get("id")
        if not isinstance(sid,str) or not sid:
            errors.append(f"{p}.id is required")
        elif sid in seen:
            errors.append(f"{p}.id duplicates {sid}")
        else:
            seen.add(sid)
        d=s.get("duration_seconds")
        if not isinstance(d,(int,float)) or d <= 0:
            errors.append(f"{p}.duration_seconds must be > 0")
        else:
            total += float(d)
        for key in ("narrative_purpose","visible_event","camera","subject_motion","environment_motion","audio_cue","renderer"):
            if not isinstance(s.get(key),str) or not s.get(key).strip():
                errors.append(f"{p}.{key} is required")
        rp=s.get("review_points_seconds",[])
        if not isinstance(rp,list) or any(not isinstance(x,(int,float)) or x < 0 or (isinstance(d,(int,float)) and x>d) for x in rp):
            errors.append(f"{p}.review_points_seconds invalid")
    if isinstance(runtime,(int,float)) and abs(total-float(runtime)) > .05:
        errors.append(f"shot durations total {total:g}s but goal.runtime_seconds is {runtime:g}s")
    strategy=data.get("asset_strategy")
    if strategy is not None:
        if not isinstance(strategy,dict):
            errors.append("asset_strategy must be an object")
        else:
            requirements=strategy.get("requirements")
            if not isinstance(requirements,list):
                errors.append("asset_strategy.requirements must be a list")
            else:
                req_ids=set()
                for i,req in enumerate(requirements):
                    p=f"asset_strategy.requirements[{i}]"
                    if not isinstance(req,dict):
                        errors.append(f"{p} must be an object")
                        continue
                    rid=req.get("id")
                    if not isinstance(rid,str) or not rid.strip():
                        errors.append(f"{p}.id is required")
                    elif rid in req_ids:
                        errors.append(f"{p}.id duplicates {rid}")
                    else:
                        req_ids.add(rid)
                    for key in ("kind","need"):
                        if not isinstance(req.get(key),str) or not req.get(key).strip():
                            errors.append(f"{p}.{key} is required")
                    decision=req.get("decision")
                    if decision not in ASSET_DECISIONS:
                        errors.append(f"{p}.decision must be one of {sorted(ASSET_DECISIONS)}")
                    for key in ("assets","structural_requirements","license_requirements","local_authorship"):
                        if key in req and not isinstance(req.get(key),list):
                            errors.append(f"{p}.{key} must be a list")
                    if "proof_artifact" in req and not isinstance(req.get("proof_artifact"),str):
                        errors.append(f"{p}.proof_artifact must be a string")
    qf=data.get("quality_floor")
    if qf is not None:
        if not isinstance(qf,dict):
            errors.append("quality_floor must be an object")
        else:
            if qf.get("delivery_level") not in QUALITY_DELIVERY_LEVELS:
                errors.append(f"quality_floor.delivery_level must be one of {sorted(QUALITY_DELIVERY_LEVELS)}")
            if qf.get("visual_mode") not in QUALITY_VISUAL_MODES:
                errors.append(f"quality_floor.visual_mode must be one of {sorted(QUALITY_VISUAL_MODES)}")
            if qf.get("character_mode") not in QUALITY_CHARACTER_MODES:
                errors.append(f"quality_floor.character_mode must be one of {sorted(QUALITY_CHARACTER_MODES)}")
            if qf.get("environment_mode") not in QUALITY_ENVIRONMENT_MODES:
                errors.append(f"quality_floor.environment_mode must be one of {sorted(QUALITY_ENVIRONMENT_MODES)}")
            if not isinstance(qf.get("proxy_assets_allowed"),bool):
                errors.append("quality_floor.proxy_assets_allowed must be boolean")
            mh=qf.get("minimum_delivery_height")
            if not isinstance(mh,int) or isinstance(mh,bool) or mh<=0:
                errors.append("quality_floor.minimum_delivery_height must be a positive integer")
    vd=data.get("visual_development")
    if vd is not None:
        if not isinstance(vd,dict):
            errors.append("visual_development must be an object")
        else:
            for name in ("previs","lookdev"):
                gate=vd.get(name)
                p=f"visual_development.{name}"
                if not isinstance(gate,dict):
                    errors.append(f"{p} must be an object")
                    continue
                if gate.get("decision") not in DEVELOPMENT_DECISIONS:
                    errors.append(f"{p}.decision must be one of {sorted(DEVELOPMENT_DECISIONS)}")
                if gate.get("status") not in DEVELOPMENT_STATUSES:
                    errors.append(f"{p}.status must be one of {sorted(DEVELOPMENT_STATUSES)}")
                if "review_focus" in gate and not isinstance(gate.get("review_focus"),list):
                    errors.append(f"{p}.review_focus must be a list")
    for i,s in enumerate(shots):
        comp=s.get("compositing")
        if comp is not None:
            p=f"shots[{i}].compositing"
            if not isinstance(comp,dict):
                errors.append(f"{p} must be an object")
            else:
                if comp.get("mode") not in COMPOSITING_MODES:
                    errors.append(f"{p}.mode must be one of {sorted(COMPOSITING_MODES)}")
                for key in ("passes","goals"):
                    if key in comp and not isinstance(comp.get(key),list):
                        errors.append(f"{p}.{key} must be a list")
    heroes=data.get("hero_shots",[])
    unknown=[x for x in heroes if x not in seen]
    if unknown:
        errors.append("hero_shots reference unknown ids: "+", ".join(unknown))
    return errors

def validate_source_bindings(data: dict[str, Any]) -> list[str]:
    errors=[]
    source=data.get("source") or {}
    for path_key, hash_key in (("director_brief","director_sha256"),("asset_catalog","asset_catalog_sha256")):
        value=source.get(path_key)
        expected=source.get(hash_key)
        if not isinstance(value,str) or not value:
            errors.append(f"source.{path_key} missing")
            continue
        path=Path(value).expanduser()
        if not path.is_absolute():
            path=ROOT/path
        if not path.is_file():
            errors.append(f"source.{path_key} missing on disk: {value}")
            continue
        actual=_sha(path)
        if actual != expected:
            errors.append(f"source.{hash_key} stale: expected {expected}, actual {actual}")
    return errors

def validate_execution_plan(data: dict[str, Any]) -> list[str]:
    errors=[]
    if data.get("schema_version") != 1:
        errors.append("execution plan schema_version must be 1")
    shots=data.get("shots")
    if not isinstance(shots,list) or not shots:
        return errors+["shots must be a non-empty list"]
    cursor=0.0
    ids=set()
    for i,s in enumerate(shots):
        p=f"shots[{i}]"
        if s.get("id") in ids: errors.append(f"{p}.id duplicate")
        ids.add(s.get("id"))
        if abs(float(s.get("start_seconds",-1))-cursor) > .001:
            errors.append(f"{p}.start_seconds is not contiguous")
        d=float(s.get("duration_seconds",0))
        if d<=0: errors.append(f"{p}.duration_seconds must be > 0")
        cursor += d
        if abs(float(s.get("end_seconds",-1))-cursor) > .001:
            errors.append(f"{p}.end_seconds incorrect")
        if s.get("renderer",{}).get("lane") not in ADAPTERS:
            errors.append(f"{p}.renderer.lane invalid")
    if abs(cursor-float(data.get("runtime_seconds",0))) > .05:
        errors.append("plan runtime does not equal shot runtime")
    return errors

def compile_plan(brief_path: Path, catalog_path: Path, *, width=1280, height=720, fps=24, max_default_shot=8.0) -> dict[str, Any]:
    brief=json.loads(brief_path.read_text(encoding="utf-8"))
    errors=validate_director_brief(brief)
    if errors:
        raise ValueError("invalid director brief:\n- "+"\n- ".join(errors))
    catalog=json.loads(catalog_path.read_text(encoding="utf-8"))
    assets=_asset_index(catalog)
    heroes=set(brief.get("hero_shots",[]))
    asset_strategy, asset_warnings=_compile_asset_strategy(brief,assets)
    visual_development, development_warnings=_compile_visual_development(brief)
    shots=[]
    warnings=list(asset_warnings)+list(development_warnings)
    cursor=0.0
    for idx,s in enumerate(brief["shots"]):
        duration=float(s["duration_seconds"])
        lane,lane_desc=_lane(s["renderer"])
        adapter=ADAPTERS[lane]
        resolved_assets=[_resolve_asset(a,assets) for a in s.get("assets",[])]
        unresolved=[a["name"] for a in resolved_assets if not a["resolved"]]
        if unresolved:
            warnings.append({"shot_id":s["id"],"code":"unresolved_assets","detail":unresolved})
        if lane=="unresolved":
            warnings.append({"shot_id":s["id"],"code":"renderer_unresolved","detail":s["renderer"]})
        if duration > max_default_shot:
            warnings.append({
                "shot_id":s["id"],"code":"shot_density_review",
                "detail":f"{duration:g}s exceeds {max_default_shot:g}s heuristic; keep only if viewer reads justify the hold, otherwise subdivide in the director brief."
            })
        if not adapter["ready"]:
            warnings.append({"shot_id":s["id"],"code":"adapter_not_standardized","detail":lane})
        compositing, comp_warnings=_compile_compositing(s,lane)
        for code in comp_warnings:
            warnings.append({"shot_id":s["id"],"code":code,"detail":"Declare beauty_only, multipass, or hybrid for new Blender shots."})
        if not compositing["resolved"]:
            warnings.append({"shot_id":s["id"],"code":"compositing_unresolved","detail":compositing["blockers"]})
        reviews=[]
        for t in s.get("review_points_seconds",[]):
            reviews.append({"local_seconds":float(t),"absolute_seconds":cursor+float(t),"clip_seconds":2.0})
        shots.append({
            "id":s["id"],
            "order":idx+1,
            "start_seconds":cursor,
            "duration_seconds":duration,
            "end_seconds":cursor+duration,
            "hero":s["id"] in heroes,
            "intent":{
                "narrative_purpose":s["narrative_purpose"],
                "visible_event":s["visible_event"],
                "viewer_reads":[s["visible_event"]],
            },
            "motion":{
                "subject":s["subject_motion"],
                "environment":s["environment_motion"],
                "camera":s["camera"],
            },
            "look":{
                "palette":s.get("palette",""),
                "depth_layers":s.get("depth_layers",[]),
            },
            "transition":{"in":s.get("transition_in",""),"out":s.get("transition_out","")},
            "audio":{"cue":s["audio_cue"],"sync_required":bool(s["audio_cue"].strip())},
            "renderer":{
                "requested":s["renderer"],
                "lane":lane,
                "description":lane_desc,
                "adapter_ready":adapter["ready"],
                "entrypoint":adapter["entrypoint"],
                "fallback_lanes":adapter.get("fallback_lanes",[]),
                "runtime_note":adapter.get("runtime_note"),
            },
            "assets":resolved_assets,
            "compositing":compositing,
            "continuity_dependencies":s.get("continuity_dependencies",[]),
            "review_points":reviews,
            "failure_modes":s.get("failure_modes",[]),
            "qa_required":["composition","phone_scale_readability","visible_motion","continuity","normal_speed_review"],
            "state":"PLANNED",
        })
        cursor += duration
    quality_floor, quality_warnings=_compile_quality_floor(
        brief, asset_strategy, visual_development, shots, height=height
    )
    warnings.extend(quality_warnings)
    plan={
        "schema_version":1,
        "title":brief["title"],
        "source":{
            "director_brief":str(brief_path.relative_to(ROOT)) if brief_path.is_relative_to(ROOT) else str(brief_path),
            "director_sha256":_sha(brief_path),
            "asset_catalog":str(catalog_path.relative_to(ROOT)) if catalog_path.is_relative_to(ROOT) else str(catalog_path),
            "asset_catalog_sha256":_sha(catalog_path),
        },
        "execution_policy":{
            "owner_mode":"single_agent_default",
            "cooperation_required":False,
            "parallelism":"optional_only_when_beneficial",
            "state_authority":"repository_files",
        },
        "delivery":{"width":width,"height":height,"fps":fps},
        "runtime_seconds":cursor,
        "story":brief["story"],
        "global_grammar":{
            "visual":brief["visual_grammar"],
            "camera":brief["camera_grammar"],
            "audio":brief["audio_grammar"],
            "editing":brief["editing_grammar"],
        },
        "handoff":brief.get("handoff",{}),
        "asset_strategy":asset_strategy,
        "visual_development":visual_development,
        "quality_floor":quality_floor,
        "shots":shots,
        "warnings":warnings,
        "summary":{
            "shot_count":len(shots),
            "hero_shot_count":sum(1 for s in shots if s["hero"]),
            "renderer_lanes":sorted({s["renderer"]["lane"] for s in shots}),
            "unresolved_asset_count":sum(1 for s in shots for a in s["assets"] if not a["resolved"]),
            "asset_strategy_reviewed":asset_strategy["reviewed"],
            "unresolved_asset_requirement_count":sum(1 for r in asset_strategy["requirements"] if not r["resolved"]),
            "visual_development_reviewed":visual_development["reviewed"],
            "unresolved_development_gate_count":sum(1 for g in visual_development["gates"].values() if not g["resolved"]),
            "unresolved_compositing_shot_count":sum(1 for s in shots if not s["compositing"]["resolved"]),
            "quality_floor_reviewed":quality_floor["reviewed"],
            "quality_floor_blocker_count":len(quality_floor["blockers"]),
            "final_delivery_ready":quality_floor["final_delivery_ready"],
            "warning_count":len(warnings),
            "blocked_shot_count":sum(1 for s in shots if not s["renderer"]["adapter_ready"] or any(not a["resolved"] for a in s["assets"]) or not s["compositing"]["resolved"]),
            "execution_ready":all(s["renderer"]["adapter_ready"] and all(a["resolved"] for a in s["assets"]) and s["compositing"]["resolved"] for s in shots) and all(r["resolved"] for r in asset_strategy["requirements"]) and all(g["resolved"] for g in visual_development["gates"].values()) and quality_floor["resolved"],
        },
    }
    plan_errors=validate_execution_plan(plan)
    if plan_errors:
        raise ValueError("compiler produced invalid execution plan:\n- "+"\n- ".join(plan_errors))
    return plan