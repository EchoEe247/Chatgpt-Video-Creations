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
            "request": ref, "asset_id": a["asset_id"], "name": a["name"],
            "resolved": True, "source_url": a["source"]["url"],
            "license": a["license"]["id"], "distribution_mode": a["distribution"]["mode"],
            "local_hint": a["distribution"].get("local_hint"),
        }
    return {"request": ref, "asset_id": None, "name": label, "resolved": False}

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
    shots=[]
    warnings=[]
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
            "continuity_dependencies":s.get("continuity_dependencies",[]),
            "review_points":reviews,
            "failure_modes":s.get("failure_modes",[]),
            "qa_required":["composition","phone_scale_readability","visible_motion","continuity","normal_speed_review"],
            "state":"PLANNED",
        })
        cursor += duration
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
        "shots":shots,
        "warnings":warnings,
        "summary":{
            "shot_count":len(shots),
            "hero_shot_count":sum(1 for s in shots if s["hero"]),
            "renderer_lanes":sorted({s["renderer"]["lane"] for s in shots}),
            "unresolved_asset_count":sum(1 for s in shots for a in s["assets"] if not a["resolved"]),
            "warning_count":len(warnings),
            "blocked_shot_count":sum(1 for s in shots if not s["renderer"]["adapter_ready"] or any(not a["resolved"] for a in s["assets"])),
        },
    }
    plan_errors=validate_execution_plan(plan)
    if plan_errors:
        raise ValueError("compiler produced invalid execution plan:\n- "+"\n- ".join(plan_errors))
    return plan