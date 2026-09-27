"""Creative QA signals for local video review.

Automated signals are triage evidence, never a substitute for normal-speed visual review.
"""
from __future__ import annotations

import json, math, re, subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from src.core.media import probe_media, sha256_file, extract_review_clip, extract_frame, build_contact_sheet

def _run(argv, timeout=180):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, check=False)

def _video_dims(info):
    v=next((s for s in info["streams"] if s.get("codec_type")=="video"),None)
    if not v: raise ValueError("media has no video stream")
    return int(v["width"]),int(v["height"])

def motion_signal(path: str|Path, *, sample_fps=4.0, width=160, height=90, pixel_threshold=6):
    p=Path(path).resolve()
    frame_bytes=width*height
    proc=_run([
        "ffmpeg","-v","error","-i",str(p),"-an",
        "-vf",f"fps={sample_fps},scale={width}:{height}:flags=area,format=gray",
        "-f","rawvideo","-pix_fmt","gray","-"
    ],timeout=240)
    if proc.returncode: raise ValueError((proc.stderr or b"ffmpeg motion analysis failed").decode(errors="replace")[-4000:])
    raw=proc.stdout
    n=len(raw)//frame_bytes
    if n<2: raise ValueError("not enough sampled frames for motion analysis")
    arr=np.frombuffer(raw[:n*frame_bytes],dtype=np.uint8).reshape(n,height,width).astype(np.int16)
    delta=np.abs(np.diff(arr,axis=0))
    mean_delta=delta.mean(axis=(1,2))/255.0
    changed=(delta>=int(pixel_threshold)).mean(axis=(1,2))
    times=np.arange(1,n,dtype=float)/float(sample_fps)
    return {
        "sample_fps":sample_fps,"sample_size":[width,height],"sampled_frames":n,
        "mean_delta":float(mean_delta.mean()),"median_delta":float(np.median(mean_delta)),
        "p10_delta":float(np.percentile(mean_delta,10)),
        "mean_changed_ratio":float(changed.mean()),"p10_changed_ratio":float(np.percentile(changed,10)),
        "series":[{"time_seconds":round(float(t),3),"mean_delta":round(float(d),6),"changed_ratio":round(float(c),6)}
                  for t,d,c in zip(times,mean_delta,changed)]
    }

def freeze_signal(path: str|Path, *, noise_db=-50.0, min_duration=1.0):
    p=Path(path).resolve()
    proc=subprocess.run([
        "ffmpeg","-nostats","-v","info","-i",str(p),"-an",
        "-vf",f"freezedetect=n={noise_db}dB:d={min_duration}","-f","null","-"
    ],text=True,capture_output=True,timeout=240,check=False)
    if proc.returncode: raise ValueError((proc.stderr or "freeze analysis failed")[-4000:])
    starts=[]; segments=[]
    active=None
    for line in proc.stderr.splitlines():
        m=re.search(r"freeze_start:\s*([-+0-9.eE]+)",line)
        if m: active=float(m.group(1)); starts.append(active)
        m=re.search(r"freeze_end:\s*([-+0-9.eE]+)\s*\|\s*freeze_duration:\s*([-+0-9.eE]+)",line)
        if m:
            end=float(m.group(1)); dur=float(m.group(2))
            start=active if active is not None else end-dur
            segments.append({"start_seconds":round(start,6),"end_seconds":round(end,6),"duration_seconds":round(dur,6)})
            active=None
    return {"noise_db":noise_db,"min_duration":min_duration,"segments":segments,"count":len(segments),
            "longest_seconds":max((x["duration_seconds"] for x in segments),default=0.0)}

def camera_family(text: str) -> str:
    low=(text or "").lower()
    rules=[
      ("orbit",("orbit","arc around")),
      ("push",("push","dolly in","zoom in")),
      ("pull",("pull back","dolly out","zoom out")),
      ("travel",("lateral","translation","travel","parallax","tracking")),
      ("elevation",("elevation","rise","crane","descend")),
      ("drift",("drift","float")),
      ("hold",("hold","static","locked")),
      ("move",("move","movement")),
    ]
    for family,words in rules:
        if any(w in low for w in words): return family
    tokens=re.findall(r"[a-z0-9]+",low)
    return " ".join(tokens[:4]) or "unspecified"

def camera_repetition(execution: dict[str,Any]):
    rows=[]
    for shot in execution.get("shots",[]):
        text=((shot.get("motion") or {}).get("camera") or "")
        rows.append({"shot_id":shot.get("id"),"camera":text,"family":camera_family(text)})
    consecutive=[]
    for a,b in zip(rows,rows[1:]):
        if a["family"]==b["family"] and a["family"]!="unspecified":
            consecutive.append({"shots":[a["shot_id"],b["shot_id"]],"family":a["family"]})
    counts=Counter(x["family"] for x in rows if x["family"]!="unspecified")
    total=max(1,len(rows))
    dominant=[{"family":k,"count":v,"ratio":round(v/total,4)} for k,v in counts.items() if v/total>=0.40]
    return {"shots":rows,"families":dict(counts),"consecutive_repeats":consecutive,"dominant_families":dominant}

def segment_motion(signal: dict[str,Any], execution: dict[str,Any], *, weak_changed_ratio=0.015):
    series=signal["series"]
    result=[]
    for shot in execution.get("shots",[]):
        a=float(shot["start_seconds"]); b=float(shot["end_seconds"])
        rows=[x for x in series if a < float(x["time_seconds"]) <= b]
        if rows:
            changed=sum(x["changed_ratio"] for x in rows)/len(rows)
            delta=sum(x["mean_delta"] for x in rows)/len(rows)
        else: changed=delta=0.0
        result.append({
          "shot_id":shot["id"],"start_seconds":a,"end_seconds":b,
          "mean_changed_ratio":round(changed,6),"mean_delta":round(delta,6),
          "weak_motion_signal":changed < weak_changed_ratio,
          "expected_motion":{
            "subject":(shot.get("motion") or {}).get("subject"),
            "environment":(shot.get("motion") or {}).get("environment"),
            "camera":(shot.get("motion") or {}).get("camera"),
          }
        })
    return result

def layout_checks(layout: dict[str,Any]|None, *, master_width:int, master_height:int, phone_width=360, min_phone_font_px=11):
    if not layout:
        return {"metadata_present":False,"manual_text_review_required":True,"items":[],"violations":[],
                "note":"No overlay/layout metadata supplied; automated QA cannot truthfully certify text bounds/readability from pixels alone."}
    safe=float(layout.get("safe_margin_ratio",0.04))
    items=[]; violations=[]
    scale=phone_width/master_width
    for item in layout.get("text_items",[]):
        bbox=item.get("bbox_norm")
        ident=item.get("id","unnamed")
        row={"id":ident,"bbox_norm":bbox,"font_px":item.get("font_px")}
        if not isinstance(bbox,list) or len(bbox)!=4:
            violations.append({"id":ident,"code":"invalid_bbox"}); items.append(row); continue
        x,y,w,h=map(float,bbox)
        safe_ok=x>=safe and y>=safe and x+w<=1-safe and y+h<=1-safe
        row["inside_safe_area"]=safe_ok
        if not safe_ok: violations.append({"id":ident,"code":"safe_area"})
        font=item.get("font_px")
        if isinstance(font,(int,float)):
            phone_font=float(font)*scale
            row["phone_font_px"]=round(phone_font,2)
            row["phone_font_ok"]=phone_font>=min_phone_font_px
            if phone_font<min_phone_font_px: violations.append({"id":ident,"code":"phone_font","actual":round(phone_font,2),"minimum":min_phone_font_px})
        else:
            row["phone_font_ok"]=None
            violations.append({"id":ident,"code":"font_size_missing"})
        items.append(row)
    return {"metadata_present":True,"manual_text_review_required":False,"safe_margin_ratio":safe,
            "phone_width":phone_width,"min_phone_font_px":min_phone_font_px,"items":items,"violations":violations}

def build_creative_qa(media_path: str|Path, execution_path: str|Path, output_dir: str|Path, layout_path: str|Path|None=None,
                      *, review_clip_limit=12):
    media=Path(media_path).resolve(); execution_path=Path(execution_path).resolve(); out=Path(output_dir).resolve()
    out.mkdir(parents=True,exist_ok=True)
    execution=json.loads(execution_path.read_text())
    layout=json.loads(Path(layout_path).resolve().read_text()) if layout_path else None
    info=probe_media(media); width,height=_video_dims(info)
    motion=motion_signal(media); freeze=freeze_signal(media)
    per_shot=segment_motion(motion,execution)
    cameras=camera_repetition(execution)
    layout_result=layout_checks(layout,master_width=width,master_height=height)

    phone_dir=out/"phone-frames"; phone_dir.mkdir(exist_ok=True)
    clip_dir=out/"normal-speed"; clip_dir.mkdir(exist_ok=True)
    evidence=[]
    anchors=[]
    for shot in execution.get("shots",[]):
        points=shot.get("review_points") or []
        if points: anchors.append((shot["id"],float(points[0]["absolute_seconds"]),float(points[0].get("clip_seconds",2))))
    for sid,at,dur in anchors[:review_clip_limit]:
        frame=phone_dir/f"{sid}.jpg"; clip=clip_dir/f"{sid}.mp4"
        extract_frame(media,frame,time_seconds=at,max_width=360)
        extract_review_clip(media,clip,center_seconds=at,duration_seconds=max(1.5,min(4.0,dur)),max_width=720)
        evidence.append({"shot_id":sid,"at_seconds":at,"phone_frame":str(frame.relative_to(out)),"normal_speed_clip":str(clip.relative_to(out)),
                         "frame_sha256":sha256_file(frame),"clip_sha256":sha256_file(clip)})
    contact=out/"contact-sheet.jpg"
    build_contact_sheet(media,contact,count=min(16,max(8,len(execution.get("shots",[])))),columns=4,cell_width=240)

    weak=[x["shot_id"] for x in per_shot if x["weak_motion_signal"]]
    warnings=[]
    if freeze["segments"]: warnings.append({"code":"freeze_spans","detail":freeze["segments"]})
    if weak: warnings.append({"code":"weak_motion_shots","detail":weak})
    if cameras["consecutive_repeats"]: warnings.append({"code":"consecutive_camera_family","detail":cameras["consecutive_repeats"]})
    if cameras["dominant_families"]: warnings.append({"code":"dominant_camera_family","detail":cameras["dominant_families"]})
    if layout_result["violations"]: warnings.append({"code":"layout_violations","detail":layout_result["violations"]})
    if layout_result["manual_text_review_required"]: warnings.append({"code":"text_metadata_missing","detail":"Phone/text readability requires assistant visual review."})
    result={
      "schema_version":1,"media":str(media),"media_sha256":sha256_file(media),
      "execution_plan":str(execution_path),"execution_plan_sha256":sha256_file(execution_path),
      "signals":{
        "motion_global":{k:v for k,v in motion.items() if k!="series"},
        "freeze":freeze,"motion_by_shot":per_shot,"camera_repetition":cameras,"layout":layout_result,
      },
      "evidence":{"contact_sheet":str(contact.relative_to(out)),"contact_sheet_sha256":sha256_file(contact),"review_points":evidence},
      "warnings":warnings,
      "manual_review_required":[
        "composition and focal hierarchy",
        "phone-scale text/image readability",
        "motion meaning at normal speed",
        "camera movement quality rather than mere difference",
        "story/emotional clarity"
      ],
      "summary":{"freeze_count":freeze["count"],"weak_motion_shot_count":len(weak),
                 "camera_repeat_count":len(cameras["consecutive_repeats"]),
                 "layout_violation_count":len(layout_result["violations"]),"warning_count":len(warnings)}
    }
    (out/"creative-qa.json").write_text(json.dumps(result,indent=2)+"\n")
    review={
      "schema_version":1,"candidate_sha256":result["media_sha256"],"creative_qa_sha256":sha256_file(out/"creative-qa.json"),
      "criteria":{
        "composition":{"pass":False,"notes":"","evidence":[]},
        "phone_scale_readability":{"pass":False,"notes":"","evidence":[]},
        "visible_motion":{"pass":False,"notes":"","evidence":[]},
        "camera_variety":{"pass":False,"notes":"","evidence":[]},
        "normal_speed_story_read":{"pass":False,"notes":"","evidence":[]}
      },
      "defects":[],"next_change":""
    }
    (out/"assistant-review-template.json").write_text(json.dumps(review,indent=2)+"\n")
    return result

def validate_report_evidence(report_path: str|Path):
    report_path=Path(report_path).resolve()
    report=json.loads(report_path.read_text())
    root=report_path.parent
    errors=[]
    evidence=report.get("evidence") or {}
    refs=[]
    contact=evidence.get("contact_sheet")
    if contact:
        refs.append(("contact_sheet",contact,evidence.get("contact_sheet_sha256")))
    for item in evidence.get("review_points",[]):
        refs.append((f"{item.get('shot_id')} phone",item.get("phone_frame"),item.get("frame_sha256")))
        refs.append((f"{item.get('shot_id')} clip",item.get("normal_speed_clip"),item.get("clip_sha256")))
    for label,relative,expected in refs:
        if not isinstance(relative,str) or not relative:
            errors.append(f"{label}: evidence path missing"); continue
        path=(root/relative).resolve()
        try: path.relative_to(root)
        except ValueError:
            errors.append(f"{label}: evidence escapes QA directory"); continue
        if not path.is_file():
            errors.append(f"{label}: evidence file missing"); continue
        if not isinstance(expected,str) or len(expected)!=64:
            errors.append(f"{label}: evidence SHA missing")
        elif sha256_file(path)!=expected:
            errors.append(f"{label}: evidence SHA mismatch")
    return {"pass":not errors,"errors":errors,"evidence_count":len(refs)}

def validate_assistant_review(report_path: str|Path, review_path: str|Path):
    report_path=Path(report_path).resolve(); review_path=Path(review_path).resolve()
    report=json.loads(report_path.read_text()); review=json.loads(review_path.read_text())
    errors=[]
    if review.get("candidate_sha256")!=report.get("media_sha256"): errors.append("review candidate SHA does not match report")
    if review.get("creative_qa_sha256")!=sha256_file(report_path): errors.append("review is not bound to current creative QA report")
    required={"composition","phone_scale_readability","visible_motion","camera_variety","normal_speed_story_read"}
    allowed={str((report.get("evidence") or {}).get("contact_sheet") or "")}
    for item in (report.get("evidence") or {}).get("review_points",[]):
        allowed.add(str(item.get("phone_frame") or ""))
        allowed.add(str(item.get("normal_speed_clip") or ""))
    allowed.discard("")
    criteria=review.get("criteria") or {}
    if set(criteria)!=required: errors.append("review criteria set is incomplete")
    for key in required:
        item=criteria.get(key) or {}
        if not isinstance(item.get("pass"),bool): errors.append(f"{key}: pass must be boolean")
        if not str(item.get("notes","")).strip(): errors.append(f"{key}: notes required")
        evidence=item.get("evidence") or []
        if not evidence: errors.append(f"{key}: evidence required")
        elif any(str(x) not in allowed for x in evidence): errors.append(f"{key}: evidence must reference generated creative-QA artifacts")
    failed=[k for k,v in criteria.items() if not v.get("pass")]
    if (failed or review.get("defects")) and not str(review.get("next_change","")).strip():
        errors.append("failed review requires next_change")
    return {"pass":not errors and not failed and not review.get("defects"),"valid":not errors,"errors":errors,"failed_criteria":failed}