"""Reference-specific alignment evidence for the canonical video production lanes.

Built on this repository's media/shot/review architecture; not a replacement
for productionctl, shotctl, studio review or the user's final acceptance.
Exact source clips, cropping, shot time maps and output identity are immutable
once locked. Metrics flag visual differences, not artistic quality.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping
import json
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from src.core.media import probe_media, sha256_file, validate_master


class ReferenceAlignmentError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ReferenceAlignmentError(message)


def _numeric(value: Any, name: str, *, minimum: float = 0.0) -> float:
    require(type(value) in (int, float) and math.isfinite(value) and value >= minimum,
            f"{name} must be finite and >= {minimum}")
    return float(value)


def _frames(value: Any, name: str, *, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, f"{name} must be an integer >= {minimum}")
    return value


def _fps(value: Any) -> Fraction:
    try:
        rate = Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ReferenceAlignmentError("invalid fps") from exc
    require(0 < rate <= 120, "fps must be in (0,120]")
    return rate


def _video(info: Mapping[str, Any]) -> Mapping[str, Any]:
    videos = [s for s in info["streams"] if s.get("codec_type") == "video"]
    require(len(videos) >= 1, "reference/candidate requires a video stream")
    return videos[0]


def _crop(crop: str, video: Mapping[str, Any]) -> list[int]:
    try:
        values = [int(x) for x in crop.split(":")]
    except (TypeError, ValueError) as exc:
        raise ReferenceAlignmentError("crop must be exact W:H:X:Y pixel integers") from exc
    require(len(values) == 4, "crop must be W:H:X:Y")
    w,h,x,y = values
    require(w >= 2 and h >= 2 and x >= 0 and y >= 0
            and x+w <= video["width"] and y+h <= video["height"],
            "crop outside reference video bounds")
    return values


def _shots(shots: Any, reference_length: float, target_frames: int) -> list[dict[str, Any]]:
    require(isinstance(shots,list) and len(shots) >= 1, "shot map requires at least one shot")
    used = set()
    previous_end=0
    previous_source=0.0
    out=[]
    for i,shot in enumerate(shots):
        require(isinstance(shot,dict), f"shot[{i}] must be an object")
        sid = shot.get("id")
        require(isinstance(sid,str) and sid.isascii() and sid.replace("_","").replace("-","").isalnum()
                and sid not in used, f"shot[{i}] needs a unique safe id")
        used.add(sid)
        a = _frames(shot.get("target_start_frame"), f"{sid}.target_start_frame")
        b = _frames(shot.get("target_end_frame"), f"{sid}.target_end_frame",minimum=1)
        s = _numeric(shot.get("source_start_seconds"), f"{sid}.source_start_seconds")
        e = _numeric(shot.get("source_end_seconds"), f"{sid}.source_end_seconds")
        require(a == previous_end and a < b <= target_frames,
                f"{sid}: target shots must tile all output frames without gaps/overlap")
        require(e > s and e <= reference_length + .03 and s >= previous_source - 1e-3,
                f"{sid}: source shots must be ordered and inside the reference")
        require(shot.get("complexity") in ("normal","high"),
                f"{sid}: complexity must be normal or high")
        require(isinstance(shot.get("visual_intent"),str) and len(shot["visual_intent"].strip()) >= 8,
                f"{sid}: visual_intent is required")
        previous_end=b
        previous_source=e
        out.append(dict(shot))
    require(previous_end == target_frames, "shot map must include all final frames")
    require(shots[0]["source_start_seconds"] <= .3
            and reference_length - previous_source <= .5,
            "source footage must be mapped from near beginning through ending; document explicit trims separately")
    return out


def make_lock(reference: str | Path, crop: str, shot_map: Any, *,
              width: int, height: int, fps: str, duration_seconds: float,
              crop_verified: bool, aspect_override_reason: str | None = None,
              audio_override_reason: str | None = None) -> dict[str, Any]:
    path=Path(reference).expanduser().resolve()
    info=probe_media(path)
    require(crop_verified is True, "creative crop requires explicit visual verification")
    w,h,_,_=_crop(crop,_video(info))
    width=_frames(width,"output width",minimum=2)
    height=_frames(height,"output height",minimum=2)
    require(width%2==0 and height%2==0, "H.264 web dimensions must be even")
    rate=_fps(fps)
    duration=_numeric(duration_seconds,"duration_seconds",minimum=.01)
    count=Fraction(str(duration))*rate
    require(count.denominator == 1, "duration/fps must specify an exact integer number of frames")
    total=_frames(int(count),"target frame count",minimum=2)
    source_duration=_numeric(info["duration_seconds"],"reference duration",minimum=.01)
    aspect_delta=abs(float(Fraction(width,height)/Fraction(w,h))-1)
    if aspect_delta > .005:
        require(isinstance(aspect_override_reason,str) and len(aspect_override_reason.strip())>=20,
                "aspect ratio differs >0.5%; provide a specific signed-off override")
    if info["audio_streams"] and audio_override_reason is not None:
        require(isinstance(audio_override_reason,str) and len(audio_override_reason.strip())>=20,
                "source audio omission requires a meaningful reason")
    return {
        "schema":"chatgpt-video-reference-alignment-v1",
        "reference":{"path":str(path),"sha256":sha256_file(path),
                     "duration_seconds":source_duration,
                     "video_width":_video(info)["width"],
                     "video_height":_video(info)["height"],
                     "creative_crop":crop,"crop_verified":True,
                     "has_audio":bool(info["audio_streams"])},
        "target":{"width":width,"height":height,"fps":str(rate),
                  "frames":total,"duration_seconds":float(Fraction(total,1)/rate),
                  "aspect_override_reason":aspect_override_reason if aspect_delta>.005 else None,
                  "audio_override_reason":audio_override_reason},
        "shots":_shots(shot_map,source_duration,total),
        "status":"source_locked_for_reference_analysis",
        "notes":["This is optional reference-alignment evidence for existing production review and repair.",
                 "It is not a productionctl DONE state, an assistant visual review, or a user acceptance."]
    }


def verify_lock(lock: Mapping[str,Any]) -> None:
    require(lock.get("schema")=="chatgpt-video-reference-alignment-v1","wrong reference alignment schema")
    ref=lock["reference"]
    path=Path(ref["path"])
    require(path.is_file() and sha256_file(path)==ref["sha256"],
            "locked source is missing or has changed")
    info=probe_media(path)
    _crop(ref["creative_crop"],_video(info))
    require(ref.get("crop_verified") is True,"crop was not verified")
    require(abs(info["duration_seconds"]-ref["duration_seconds"]) <= .03,
            "reference duration changed")
    target=lock["target"]
    fps=_fps(target["fps"])
    require(Fraction(str(target["duration_seconds"]))*fps==target["frames"],
            "locked duration/fps/frames disagree")
    cw,ch,*_=_crop(ref["creative_crop"],_video(info))
    delta=abs(float(Fraction(target["width"],target["height"])/Fraction(cw,ch))-1)
    require(delta<=.005 or (isinstance(target.get("aspect_override_reason"),str)
                            and len(target["aspect_override_reason"].strip())>=20),
            "unapproved output aspect drift")
    _shots(lock["shots"],info["duration_seconds"],target["frames"])


def _decode_at(path: str, at: float, *, crop: str | None, dims=(240,135)) -> np.ndarray:
    """Decode a single exact sought source/candidate frame; bounded memory."""
    filters=[]
    if crop:
        w,h,x,y=[int(v) for v in crop.split(":")]
        filters.append(f"crop={w}:{h}:{x}:{y}")
    filters += [f"scale={dims[0]}:{dims[1]}:flags=area","format=rgb24"]
    cmd=["ffmpeg","-hide_banner","-loglevel","error",
         "-ss",f"{at:.6f}","-i",path,"-frames:v","1",
         "-an","-vf",",".join(filters),"-f","rawvideo","-pix_fmt","rgb24","-"]
    run=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=35,check=False)
    expected=dims[0]*dims[1]*3
    require(run.returncode==0 and len(run.stdout)==expected,
            "reference frame decode failed at "+str(at)+": "+run.stderr.decode(errors="replace")[-350:])
    return np.frombuffer(run.stdout,dtype=np.uint8).reshape(dims[1],dims[0],3).copy()


def _luma(frame: np.ndarray) -> np.ndarray:
    f=frame.astype(np.float32)/255
    return f[...,0]*.2126 + f[...,1]*.7152 + f[...,2]*.0722


def _pair_frames(lock: Mapping[str,Any],candidate: str,shot: Mapping[str,Any],parts=6):
    """Both shots sampled by proportional local progress, handling deliberate retiming."""
    fps=float(_fps(lock["target"]["fps"]))
    t0=shot["target_start_frame"]/fps
    tlen=(shot["target_end_frame"]-shot["target_start_frame"])/fps
    s0=shot["source_start_seconds"]
    slen=shot["source_end_seconds"]-s0
    a,b=[],[]
    for i in range(parts):
        pos=(i+.5)/parts
        a.append(_decode_at(lock["reference"]["path"],s0+pos*slen,
                            crop=lock["reference"]["creative_crop"]))
        b.append(_decode_at(candidate,t0+pos*tlen,crop=None))
    return a,b


def _boundary(path,at,crop):
    """Two frames straddling a boundary; a cut-strength diagnostic only."""
    a=_luma(_decode_at(path,max(0,at-.09),crop=crop))
    b=_luma(_decode_at(path,at+.09,crop=crop))
    return float(np.mean(np.abs(a-b)))


def compare(lock: Mapping[str,Any], candidate: str | Path, *, board: str | Path | None = None) -> dict[str,Any]:
    verify_lock(lock)
    file=Path(candidate).expanduser().resolve()
    info=probe_media(file)
    video=_video(info)
    target=lock["target"]
    require((video["width"],video["height"])==(target["width"],target["height"]),
            "candidate geometry differs from locked reference target")
    require(abs(float(video["frame_rate"])-float(_fps(target["fps"])))<=.02,
            "candidate FPS differs from lock")
    qa=validate_master(file,width=target["width"],height=target["height"],
                       fps=float(_fps(target["fps"])),
                       duration_seconds=target["duration_seconds"],
                       duration_tolerance=max(.09,1/float(_fps(target["fps"]))),
                       audio_required=lock["reference"]["has_audio"] and not target.get("audio_override_reason"))
    require(qa["pass"], "candidate fails existing studio technical QA: "+
            ", ".join(item["name"] for item in qa["checks"] if not item["pass"]))
    frames=[]
    rows=[]
    for shot in lock["shots"]:
        source,cand=_pair_frames(lock,str(file),shot)
        lum_s=np.stack([_luma(x) for x in source])
        lum_c=np.stack([_luma(x) for x in cand])
        mae=float(np.mean(np.abs(lum_s-lum_c)))
        activity_s=float(np.mean(np.abs(np.diff(lum_s,axis=0))))
        activity_c=float(np.mean(np.abs(np.diff(lum_c,axis=0))))
        rows.append({"shot_id":shot["id"],"complexity":shot["complexity"],
                     "source_interval_seconds":[shot["source_start_seconds"],shot["source_end_seconds"]],
                     "target_interval_frames":[shot["target_start_frame"],shot["target_end_frame"]],
                     "luma_mae":round(mae,5),"source_motion_activity":round(activity_s,5),
                     "candidate_motion_activity":round(activity_c,5),
                     "activity_ratio":round(activity_c/max(activity_s,.000001),4),
                     "review_required":True})
        frames.append((shot["id"],source[len(source)//2],cand[len(cand)//2]))
    boundaries=[]
    fps=float(_fps(target["fps"]))
    for left,right in zip(lock["shots"],lock["shots"][1:]):
        source_t=right["source_start_seconds"]
        candidate_t=right["target_start_frame"]/fps
        a=_boundary(lock["reference"]["path"],source_t,lock["reference"]["creative_crop"])
        b=_boundary(str(file),candidate_t,None)
        boundaries.append({"from":left["id"],"to":right["id"],
                           "source_cut_strength":round(a,5),
                           "candidate_cut_strength":round(b,5),
                           "weak_relative_cut":bool(a>.09 and b < a*.4),
                           "reference_time":source_t,"candidate_time":candidate_t})
    rows.sort(key=lambda x:x["luma_mae"],reverse=True)
    report={"schema":"chatgpt-video-reference-comparison-v1",
            "reference_sha256":lock["reference"]["sha256"],
            "candidate_sha256":sha256_file(file),
            "technical_qa_passed":qa["pass"],
            "per_shot_diagnostics":rows,
            "shot_boundaries":boundaries,
            "repair_priority":[x["shot_id"] for x in rows],
            "state":"requires_real_moving_visual_review",
            "notes":["Metrics are sampled, compression/retiming sensitive, not a fidelity score.",
                     "Weak cuts are review candidates, not proof of incorrect scene semantics.",
                     "Use this report with existing shotctl/productionctl repair gates; do not simulate assistant or user acceptance."]}
    if board:
        path=Path(board)
        path.parent.mkdir(parents=True,exist_ok=True)
        from PIL import Image
        canvas=Image.new("RGB",(480,160*len(frames)),(16,16,20))
        draw=ImageDraw.Draw(canvas)
        for i,(id,src,dst) in enumerate(frames):
            off=i*160
            canvas.paste(Image.fromarray(src),(0,off+25))
            canvas.paste(Image.fromarray(dst),(240,off+25))
            draw.text((8,off+5),f"{id} | source / recreation",fill=(245,245,245))
        canvas.save(path)
        report["comparison_board"]=str(path.resolve())
    return report
