"""Review coverage and authored-intent checks; signals never certify perception."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from src.core.experience_qa import _audio, _rms_db, _peak_db, _run

def _stereo_audio(path,sr):
    result=_run(["ffmpeg","-v","error","-i",str(Path(path).resolve()),"-vn","-ac","2","-ar",str(sr),"-f","f32le","-"])
    if result.returncode:raise ValueError(result.stderr.decode(errors="replace")[-2000:])
    return np.frombuffer(result.stdout,dtype="<f4").reshape(-1,2).copy()

def review_anchors(execution, layout=None):
    """Keep every authored point; include text visibility and unannotated shots."""
    rows=[]
    shots=execution.get("shots", [])
    for shot in shots:
        a,b=float(shot["start_seconds"]),float(shot["end_seconds"])
        points=shot.get("review_points") or [{"absolute_seconds":(a+b)/2,"clip_seconds":2}]
        for i,p in enumerate(points,1):
            at=float(p.get("absolute_seconds", a+float(p.get("local_seconds",0))))
            if not a<=at<b:
                raise ValueError(f"{shot['id']}: review point outside shot")
            rows.append({"id":f"{shot['id']}-rp{i:02d}", "shot_id":shot["id"],
                         "at_seconds":at,"clip_seconds":float(p.get("clip_seconds",2)),
                         "purpose":"authored_event","expected_event":(shot.get("intent") or {}).get("visible_event","")})
    for i,item in enumerate((layout or {}).get("text_items",[]),1):
        if "start_seconds" not in item or "end_seconds" not in item: continue
        a,b=float(item["start_seconds"]),float(item["end_seconds"])
        at=(a+b)/2
        shot=next((s for s in shots if float(s["start_seconds"])<=at<float(s["end_seconds"])),None)
        if b<=a or not shot or a<float(shot["start_seconds"]) or b>float(shot["end_seconds"]):
            raise ValueError(f"{item.get('id')}: text interval outside one shot")
        rows.append({"id":f"{shot['id']}-text{i:02d}","shot_id":shot["id"],
                     "at_seconds":at,"clip_seconds":min(4,b-a),"purpose":"text_visibility",
                     "text_id":item.get("id"),"expected_event":"Read the rendered text at phone scale."})
    return rows

def transition_windows(execution, finish=None):
    cfg={(x["from"],x["to"]):x for x in (finish or {}).get("transitions",[])}
    rows=[]
    shots=execution.get("shots",[])
    for left,right in zip(shots,shots[1:]):
        at=float(left["end_seconds"]);tr=cfg.get((left["id"],right["id"]),{})
        d=max(0,float(tr.get("duration_seconds",0)))
        # Inspect outside both shoulders, as well as the shared-color midpoint.
        radius=max(.55,d+.25)
        lo=max(float(left["start_seconds"])+.01,at-radius)
        hi=min(float(right["end_seconds"])-.01,at+radius)
        rows.append({"from":left["id"],"to":right["id"],"at_seconds":at,
                     "shoulder_seconds":d,"start_seconds":lo,"end_seconds":hi,
                     "sample_times":[lo,at-d/2 if d else at-.18,at-.04,at+.04,
                                     at+d/2 if d else at+.18,hi],
                     "authored_motif":tr.get("motif"),"implementation":"color_fade" if "color" in tr else "unclassified"})
    fades=[r for r in rows if r["implementation"]=="color_fade"]
    return {"boundaries":rows,"color_fade_count":len(fades),"boundary_count":len(rows),
            "color_fade_ratio":len(fades)/max(1,len(rows)),
            "note":"Repeated color fades require rhythm review; lower cut distance does not prove coherent staging."}

def silence_measure(samples, sr, start, duration, threshold=-50.0):
    a=int(start*sr);b=int((start+duration)*sr)
    if start<0 or duration<=0 or b>len(samples)+1:
        return {"measurable":False,"warning":True,"reason":"interval_outside_audio"}
    x=samples[a:b];block=max(1,int(.05*sr))
    levels=[_rms_db(x[i:i+block]) for i in range(0,len(x),block)]
    return {"measurable":True,"rms_dbfs":round(_rms_db(x),2),"peak_dbfs":round(_peak_db(x),2),
            "threshold_dbfs":threshold,"loudest_50ms_rms_dbfs":round(max(levels,default=-120),2),
            "warning":any(v>threshold for v in levels)}

def authored_audio_intent(media, timeline_path, stems_dir=None, sr=16000):
    if not timeline_path or not Path(timeline_path).is_file():
        return {"available":False,"events":[],"warnings":[]}
    timeline=json.loads(Path(timeline_path).read_text())
    master=_stereo_audio(media,sr);rows=[];warnings=[]
    for e in timeline.get("events",[]):
        if e.get("kind")!="designed_silence":continue
        start=float(e.get("at_seconds",0));duration=float(e.get("duration_seconds",0))
        threshold=float(e.get("silence_threshold_dbfs",-50))
        row={"event_id":e.get("id"),"at_seconds":start,"duration_seconds":duration,
             "declared_stem":e.get("stem"),"scope":e.get("silence_scope","unspecified"),
             "master":silence_measure(master,sr,start,duration,threshold)}
        if stems_dir and e.get("stem"):
            f=Path(stems_dir)/(str(e["stem"])+".wav")
            if f.is_file():
                row["stem"]=silence_measure(_stereo_audio(f,sr),sr,start,duration,threshold)
        # Distinguish scoped score drops from promises of silence in the final mix.
        row["review_required"]=row["scope"]=="unspecified" or (
            row["master"]["warning"] if row["scope"]=="master" else
            row.get("stem",{"warning":True})["warning"])
        rows.append(row)
        if row["review_required"]:warnings.append(row)
    return {"available":True,"analysis_channels":2,"events":rows,"warnings":warnings,
            "note":"Unspecified silence scope requires review. Master silence must be checked after all mixing/encoding."}

def active_speech_windows(voice, bed, sr, start_seconds=0, window_seconds=.20, margin_db=4):
    """Avoid hiding a brief collision inside a whole-shot average."""
    n=min(len(voice),len(bed));step=max(1,int(sr*window_seconds));rows=[]
    for a in range(0,n,step):
        b=min(n,a+step);v=_rms_db(voice[a:b])
        if v<=-45:continue
        bed_db=_rms_db(bed[a:b]);margin=v-bed_db
        rows.append({"start_seconds":round(start_seconds+a/sr,3),"end_seconds":round(start_seconds+b/sr,3),
                     "voice_margin_db":round(margin,2),"masking_risk":margin<margin_db})
    return {"active_window_count":len(rows),"minimum_margin_db":min((x["voice_margin_db"] for x in rows),default=None),
            "risk_windows":[x for x in rows if x["masking_risk"]],
            "note":"A level-margin risk is a listening target, not proof of audible masking."}

def validate_perceptual_review(report, review):
    """Schema-v3 prevents metrics/stills being labeled as watching/listening."""
    errors=[];criteria=review.get("criteria") or {}
    playback={"visible_motion","camera_variety","normal_speed_story_read","motion_smoothness","transition_coherence"}
    listening={"audio_continuity","narration_clarity"}
    for key,item in criteria.items():
        if not item.get("pass"):continue
        method=item.get("method")
        allowed={"still_inspection","normal_speed_playback","audiovisual_playback"}
        if key in playback:allowed={"normal_speed_playback","audiovisual_playback"}
        if key in listening:allowed={"audio_listening","audiovisual_playback"}
        if key=="av_sync":allowed={"audiovisual_playback"}
        if method not in allowed:errors.append(f"{key}: PASS requires direct inspection with appropriate modality")
        if key in playback|listening|{"av_sync"}:
            refs=item.get("evidence") or []
            if not any(str(x).endswith((".mp4",".wav",".m4a")) for x in refs):
                errors.append(f"{key}: PASS requires temporal media evidence")
    coverage=report.get("review_coverage") or {}
    if coverage.get("missing_point_ids"):errors.append("review evidence omits required points")
    expected={p["id"] for p in coverage.get("required_points",[])}
    obs=review.get("observations") or []
    ids=[o.get("point_id") for o in obs if isinstance(o,dict)]
    if set(ids)!=expected or len(ids)!=len(set(ids)):
        errors.append("observations must cover every required point exactly once")
    by_id={p.get("id"):p for p in (report.get("evidence") or {}).get("review_points",[])}
    for o in obs:
        if not isinstance(o,dict):errors.append("observation must be an object");continue
        p=by_id.get(o.get("point_id"),{})
        if not str(o.get("observed","")).strip():errors.append("observation requires visible-event finding")
        if not isinstance(o.get("intent_match"),bool):errors.append("observation requires intent_match boolean")
        if o.get("intent_match") is not True and all(x.get("pass") for x in criteria.values()):errors.append(f"{o.get('point_id')}: unresolved shot-intent mismatch")
        allowed={p.get("phone_frame"),p.get("normal_speed_clip")}
        refs=o.get("evidence") or []
        if not refs or any(x not in allowed for x in refs):errors.append("observation evidence must match its own point")
    if all(x.get("pass") for x in criteria.values()):
        replay=review.get("full_film_review") or {}
        if replay.get("candidate_sha256")!=report.get("media_sha256"):
            errors.append("full-film review must bind candidate")
        if replay.get("method")!="audiovisual_playback" or replay.get("completed") is not True:
            errors.append("overall PASS requires completed audiovisual full-film review")
        if not str(replay.get("observed","")).strip():errors.append("full-film review requires findings")
    return errors
