"""Optional native Earshot v0.3 effects stem bound to this repo's AV clock.

Uses the actual installed earshot.forge.bank renderer, never an adapted
simulation. The existing AV timeline remains authoritative; this is an
unmastered effects WAV, not narration/music/full film audio.
"""
from __future__ import annotations

import json
import math
import wave
from fractions import Fraction
from pathlib import Path

import numpy as np
from src.core.av_timeline import validate_timeline, validate_bindings


def compile_effects(timeline: dict, cues: list[dict], *, bank=None, check_sources=True):
    errors=validate_timeline(timeline)
    if errors:
        raise ValueError("invalid AV timeline: "+"; ".join(errors))
    if check_sources and timeline.get("source"):
        failures=validate_bindings(timeline)
        if failures: raise ValueError("AV timeline source changed: "+"; ".join(failures))
    sr=timeline["sample_rate"]
    if sr!=48000:
        raise ValueError("native Earshot adapter currently requires 48 kHz timeline")
    if not isinstance(cues,list) or not cues:
        raise ValueError("nonempty cue list required")
    if bank is None:
        try:
            from earshot.forge import bank
        except ImportError as exc:
            raise RuntimeError("native Earshot is not installed in this production runtime") from exc
    length=round(float(timeline["runtime_seconds"])*sr)
    if not 0<length<=sr*600:
        raise ValueError("effects stem duration is out of supported bounds")
    events={e["id"]:e for e in timeline["events"]}
    out=np.zeros((length,2),dtype=np.float64)
    rows=[]
    cache={}
    for index,cue in enumerate(cues):
        if not isinstance(cue,dict):
            raise ValueError("cue must be an object")
        eid=cue.get("event_id")
        event=events.get(eid)
        if event is None or "audio" not in event["targets"]:
            raise ValueError(f"cue[{index}] event must exist and target audio")
        if cue.get("stem","effects")!="effects":
            raise ValueError("Earshot cues belong on effects stem")
        sound=cue.get("sound_id")
        if not isinstance(sound,str) or "/" not in sound:
            raise ValueError("native bank sound_id required")
        align=cue.get("align","peak")
        if align not in {"start","onset","peak","end"}:
            raise ValueError("align must be start/onset/peak/end")
        db=cue.get("gain_db",-15.)
        if type(db) not in (int,float) or not math.isfinite(db) or not -80<=db<=12:
            raise ValueError("gain_db outside safe range")
        params={k:cue[k] for k in ("seed","dur","apex","pitch","weight")
                if k in cue and cue[k] is not None}
        key=json.dumps([sound,params],sort_keys=True)
        if key not in cache:
            samples,meta=bank.render(sound,**params)
            if not isinstance(samples,np.ndarray) or samples.ndim!=2 or samples.shape[1]!=2:
                raise ValueError("Earshot returned non-stereo waveform")
            cache[key]=(samples,meta)
        sound_samples,meta=cache[key]
        landmark=float(meta.get(align+"_s",0.)) if align!="start" else 0.
        if not math.isfinite(landmark) or landmark<0:
            raise ValueError("invalid Earshot cue landmark")
        target=int(event["sample"])
        start=target-round(landmark*sr)
        left=max(0,start)
        right=min(length,start+len(sound_samples))
        if right<=left:
            raise ValueError(f"{eid}: effect lies outside timeline")
        amp=10**(db/20)
        out[left:right]+=sound_samples[left-start:right-start]*amp
        rows.append({"event_id":eid,"sound_id":sound,"target_sample":target,
                     "render_start_sample":start,"alignment":align,"landmark_seconds":landmark,
                     "gain_db":float(db),"seed":meta.get("seed"),"params":params,
                     "bank_check_ok":bool(meta.get("checks",{}).get("ok",True)),
                     "truncated_at_start":start<0,
                     "truncated_at_end":start+len(sound_samples)>length})
    peak=float(np.max(np.abs(out)))
    protect=min(1.,.89/max(peak,1e-12))
    out=(out*protect).astype(np.float32)
    return out,{"source":"native_earshot.forge.bank.render",
                "bank_version":str(getattr(bank,"VERSION","unknown")),
                "sample_rate":sr,"channels":2,
                "timeline_sample_count":length,
                "cues":rows,"bank_render_count":len(cache),
                "limiter_protection_db":round(20*math.log10(protect),4),
                "requires_listening_review":True,
                "note":"This is an unmastered SFX stem, not a complete film soundtrack."}


def write_wav(path: str | Path, audio: np.ndarray, sample_rate=48000):
    out=Path(path)
    out.parent.mkdir(parents=True,exist_ok=True)
    pcm=np.clip(audio,-1,1)
    data=np.rint(pcm*32767).astype("<i2")
    with wave.open(str(out),"wb") as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        file.writeframes(data.tobytes())
    return out
