"""Unified audiovisual timeline shared by picture and sound."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
STEMS={"narration","score","ambience","effects"}
TARGETS={"picture","audio","qa"}

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def _portable(path: Path) -> str:
    path=path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)

def validate_event_spec(data: dict[str,Any], runtime: float) -> list[str]:
    errors=[]
    if data.get("schema_version") != 1: errors.append("event spec schema_version must be 1")
    ids=set()
    for i,e in enumerate(data.get("events") or []):
        p=f"events[{i}]"
        eid=e.get("id")
        if not isinstance(eid,str) or not eid: errors.append(f"{p}.id required")
        elif eid in ids: errors.append(f"{p}.id duplicate {eid}")
        else: ids.add(eid)
        at=e.get("at_seconds")
        if not isinstance(at,(int,float)) or at<0 or at>runtime: errors.append(f"{p}.at_seconds out of range")
        dur=e.get("duration_seconds",0)
        if not isinstance(dur,(int,float)) or dur<0 or (isinstance(at,(int,float)) and at+dur>runtime+.001): errors.append(f"{p}.duration_seconds invalid")
        targets=e.get("targets")
        if not isinstance(targets,list) or not targets or any(x not in TARGETS for x in targets): errors.append(f"{p}.targets invalid")
        stem=e.get("stem")
        if stem is not None and stem not in STEMS: errors.append(f"{p}.stem invalid")
        if not isinstance(e.get("kind"),str) or not e.get("kind"): errors.append(f"{p}.kind required")
        if not isinstance(e.get("label"),str) or not e.get("label"): errors.append(f"{p}.label required")
    return errors

def validate_timeline(data: dict[str,Any]) -> list[str]:
    errors=[]
    if data.get("schema_version") != 1: errors.append("timeline schema_version must be 1")
    fps=data.get("fps"); sr=data.get("sample_rate"); runtime=data.get("runtime_seconds")
    if not isinstance(fps,(int,float)) or fps<=0: errors.append("fps must be > 0")
    if not isinstance(sr,int) or sr<8000: errors.append("sample_rate must be >= 8000")
    if not isinstance(runtime,(int,float)) or runtime<=0: errors.append("runtime_seconds must be > 0")
    if errors: return errors
    ids=set()
    for i,e in enumerate(data.get("events") or []):
        p=f"events[{i}]"
        eid=e.get("id")
        if eid in ids: errors.append(f"{p}.id duplicate")
        ids.add(eid)
        at=e.get("at_seconds")
        if not isinstance(at,(int,float)) or at<0 or at>runtime: errors.append(f"{p}.at_seconds invalid"); continue
        if e.get("frame") != round(float(at)*float(fps)): errors.append(f"{p}.frame does not match at_seconds")
        if e.get("sample") != round(float(at)*int(sr)): errors.append(f"{p}.sample does not match at_seconds")
        dur=float(e.get("duration_seconds",0))
        if dur<0 or float(at)+dur>float(runtime)+.001: errors.append(f"{p}.duration_seconds invalid")
        targets=e.get("targets") or []
        if not targets or any(x not in TARGETS for x in targets): errors.append(f"{p}.targets invalid")
        if e.get("stem") is not None and e["stem"] not in STEMS: errors.append(f"{p}.stem invalid")
    if [e["at_seconds"] for e in data.get("events",[])] != sorted(e["at_seconds"] for e in data.get("events",[])):
        errors.append("events must be sorted by at_seconds")
    return errors

def validate_bindings(data: dict[str,Any]) -> list[str]:
    errors=[]
    src=data.get("source") or {}
    for pk,hk in (("execution_plan","execution_plan_sha256"),("custom_events","custom_events_sha256")):
        value=src.get(pk)
        if value is None and pk=="custom_events": continue
        if not isinstance(value,str) or not value: errors.append(f"source.{pk} missing"); continue
        path=Path(value).expanduser()
        if not path.is_absolute(): path=ROOT/path
        if not path.is_file(): errors.append(f"source.{pk} missing on disk: {value}"); continue
        actual=sha256_file(path)
        if actual != src.get(hk): errors.append(f"source.{hk} stale: expected {src.get(hk)}, actual {actual}")
    return errors

def _event(eid, at, kind, label, targets, fps, sr, **extra):
    event={
        "id":eid,"at_seconds":round(float(at),6),"frame":round(float(at)*fps),
        "sample":round(float(at)*sr),"kind":kind,"label":label,
        "targets":targets,"duration_seconds":round(float(extra.pop("duration_seconds",0)),6),
    }
    event.update(extra)
    return event

def compile_timeline(execution_path: Path, custom_events_path: Path|None=None, *, sample_rate=48000) -> dict[str,Any]:
    execution=json.loads(execution_path.read_text(encoding="utf-8"))
    runtime=float(execution["runtime_seconds"])
    fps=float(execution["delivery"]["fps"])
    events=[]
    for shot in execution["shots"]:
        sid=shot["id"]; start=float(shot["start_seconds"]); end=float(shot["end_seconds"])
        events.append(_event(f"{sid}.start",start,"shot_start",shot["intent"]["visible_event"],["picture"],fps,sample_rate,shot_id=sid))
        cue=(shot.get("audio") or {}).get("cue","").strip()
        if cue:
            events.append(_event(f"{sid}.audio-cue",start,"audio_cue",cue,["audio","picture"],fps,sample_rate,shot_id=sid,stem=None))
        trans=(shot.get("transition") or {}).get("out","").strip()
        if trans and end < runtime:
            events.append(_event(f"{sid}.transition-out",end,"transition",trans,["picture","audio"],fps,sample_rate,shot_id=sid))
        for n,rp in enumerate(shot.get("review_points") or [],1):
            at=float(rp["absolute_seconds"])
            events.append(_event(f"{sid}.review-{n:02d}",at,"review_anchor",f"{sid} review {n}",["qa"],fps,sample_rate,shot_id=sid,duration_seconds=float(rp.get("clip_seconds",2))))
    custom=None
    if custom_events_path:
        custom=json.loads(custom_events_path.read_text(encoding="utf-8"))
        errs=validate_event_spec(custom,runtime)
        if errs: raise ValueError("invalid custom event spec:\n- "+"\n- ".join(errs))
        for e in custom.get("events",[]):
            extras={k:v for k,v in e.items() if k not in {"id","at_seconds","kind","label","targets","duration_seconds"}}
            events.append(_event(e["id"],e["at_seconds"],e["kind"],e["label"],e["targets"],fps,sample_rate,duration_seconds=e.get("duration_seconds",0),**extras))
    ids=set()
    for e in events:
        if e["id"] in ids: raise ValueError(f"duplicate unified event id: {e['id']}")
        ids.add(e["id"])
    events.sort(key=lambda e:(e["at_seconds"],e["id"]))
    src={"execution_plan":_portable(execution_path),"execution_plan_sha256":sha256_file(execution_path),"custom_events":None,"custom_events_sha256":None}
    if custom_events_path:
        src["custom_events"]=_portable(custom_events_path); src["custom_events_sha256"]=sha256_file(custom_events_path)
    result={
        "schema_version":1,"title":execution["title"],"runtime_seconds":runtime,"fps":fps,"sample_rate":sample_rate,
        "stems":{
            "narration":{"role":"speech/dialogue","default_headroom_db":-4.0},
            "score":{"role":"music","default_headroom_db":-8.0},
            "ambience":{"role":"environment/room tone","default_headroom_db":-12.0},
            "effects":{"role":"sfx/transitions/impacts","default_headroom_db":-6.0}
        },
        "source":src,
        "events":events,
        "policy":{
            "single_clock":True,
            "picture_timebase":"seconds + frame index",
            "audio_timebase":"seconds + sample index",
            "default_master_target_lufs":-16.0,
            "default_true_peak_ceiling_dbfs":-1.5,
        },
        "summary":{
            "event_count":len(events),
            "audio_targeted":sum("audio" in e["targets"] for e in events),
            "picture_targeted":sum("picture" in e["targets"] for e in events),
            "qa_targeted":sum("qa" in e["targets"] for e in events),
            "custom_event_count":len(custom.get("events",[])) if custom else 0,
        }
    }
    errs=validate_timeline(result)
    if errs: raise ValueError("compiler produced invalid timeline:\n- "+"\n- ".join(errs))
    return result
