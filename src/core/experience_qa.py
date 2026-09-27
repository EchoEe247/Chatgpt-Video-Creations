"""Temporal, transition, visual-style, and audio-continuity QA signals."""
from __future__ import annotations
import json,math,subprocess
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from src.core.media import extract_frame,extract_review_clip,sha256_file

def _run(argv,timeout=300):
    return subprocess.run(argv,stdin=subprocess.DEVNULL,capture_output=True,timeout=timeout,check=False)
def _rms_db(x):
    if x.size==0:return -120.0
    return 20*math.log10(max(float(np.sqrt(np.mean(x.astype(np.float64)**2))),1e-8))
def _peak_db(x):
    if x.size==0:return -120.0
    return 20*math.log10(max(float(np.max(np.abs(x))),1e-8))
def _audio(path,sr=16000):
    r=_run(["ffmpeg","-v","error","-i",str(Path(path).resolve()),"-vn","-ac","1","-ar",str(sr),"-f","f32le","-"])
    if r.returncode:raise ValueError((r.stderr or b"audio decode failed").decode(errors="replace")[-3000:])
    return np.frombuffer(r.stdout,dtype="<f4").copy()
def _band(x,sr,lo,hi):
    if len(x)<256:return 0.0
    maxn=sr*8
    if len(x)>maxn:
        step=max(1,len(x)//maxn);x=x[::step][:maxn];sr=sr/step
    x=x.astype(np.float64)-float(np.mean(x));sp=np.abs(np.fft.rfft(x*np.hanning(len(x))))**2
    f=np.fft.rfftfreq(len(x),1/sr);total=sp[(f>=90)&(f<=min(7800,sr/2))].sum()
    return float(sp[(f>=lo)&(f<=min(hi,sr/2))].sum()/max(total,1e-12))
def _centroid(x,sr):
    if len(x)<128:return 0.0
    x=x.astype(np.float64)-float(np.mean(x));sp=np.abs(np.fft.rfft(x*np.hanning(len(x))))
    f=np.fft.rfftfreq(len(x),1/sr);mask=(f>=60)&(f<=min(7800,sr/2));w=sp[mask]
    return float(np.sum(f[mask]*w)/max(np.sum(w),1e-12))

def motion_smoothness(signal:dict[str,Any],execution:dict[str,Any],transition_finish:dict[str,Any]|None=None):
    rows=[]
    incoming={};outgoing={}
    for tr in (transition_finish or {}).get("transitions",[]):
        try:d=float(tr.get("duration_seconds") or 0)
        except:d=0.0
        to_id=str(tr.get("to") or "");from_id=str(tr.get("from") or "")
        incoming[to_id]=max(incoming.get(to_id,0.0),d)
        outgoing[from_id]=max(outgoing.get(from_id,0.0),d)
    for s in execution.get("shots",[]):
        a,b=float(s["start_seconds"]),float(s["end_seconds"])
        base=min(.45,max(0,(b-a)*.10))
        start_pad=max(base,incoming.get(s["id"],0.0)+.12)
        end_pad=max(base,outgoing.get(s["id"],0.0)+.12)
        cap=max(.20,(b-a)*.34)
        start_pad=min(start_pad,cap);end_pad=min(end_pad,cap)
        lo,hi=a+start_pad,b-end_pad
        v=np.array([float(x["mean_delta"]) for x in signal.get("series",[]) if lo<float(x["time_seconds"])<=hi])
        ch=np.array([float(x["changed_ratio"]) for x in signal.get("series",[]) if lo<float(x["time_seconds"])<=hi])
        if len(v)<3:
            rows.append({"shot_id":s["id"],"sample_count":len(v),"cadence_warning":True,"reasons":["insufficient_motion_samples"]});continue
        mean=float(v.mean());med=float(np.median(v));p95=float(np.percentile(v,95))
        jerk=float(np.median(np.abs(np.diff(v))))/max(mean,1e-6);spike=p95/max(med,1e-5);mx=float(v.max())/max(med,1e-5);zero=float(np.mean(ch<.002))
        reasons=[]
        if jerk>.95 and mean>.003:reasons.append("irregular_motion_energy")
        if mx>8:reasons.append("isolated_motion_spikes")
        if zero>.45:reasons.append("many_near_static_samples")
        rows.append({"shot_id":s["id"],"sample_count":len(v),"excluded_start_seconds":round(start_pad,3),"excluded_end_seconds":round(end_pad,3),
                     "mean_delta":round(mean,6),"median_delta":round(med,6),"p95_delta":round(p95,6),
                     "jerk_index":round(jerk,4),"spike_ratio":round(spike,3),"max_spike_ratio":round(mx,3),"near_static_ratio":round(zero,4),
                     "cadence_warning":bool(reasons),"reasons":reasons})
    return {"shots":rows,"warning_shots":[x["shot_id"] for x in rows if x.get("cadence_warning")]}

def _rgb_samples(path,fps=2,width=160,height=90):
    nbytes=width*height*3
    r=_run(["ffmpeg","-v","error","-i",str(Path(path).resolve()),"-an","-vf",f"fps={fps},scale={width}:{height}:flags=area,format=rgb24","-f","rawvideo","-pix_fmt","rgb24","-"])
    if r.returncode:raise ValueError((r.stderr or b"rgb decode failed").decode(errors="replace")[-3000:])
    n=len(r.stdout)//nbytes
    return (np.arange(n)+.5)/fps,np.frombuffer(r.stdout[:n*nbytes],dtype=np.uint8).reshape(n,height,width,3)
def _feat(fr):
    f=fr.astype(np.float32)/255;mx=f.max(2);mn=f.min(2);sat=np.zeros_like(mx);np.divide(mx-mn,mx,out=sat,where=mx>1e-5)
    lum=.2126*f[:,:,0]+.7152*f[:,:,1]+.0722*f[:,:,2];edge=(np.abs(np.diff(lum,axis=1)).mean()+np.abs(np.diff(lum,axis=0)).mean())/2
    return {"luma":float(lum.mean()),"contrast":float(lum.std()),"saturation":float(sat.mean()),"edge_density":float(edge),"rgb":[float(x) for x in f.mean((0,1))]}
def visual_continuity(path,execution,fps=8.0,cut_window=.18,context_window=.55):
    times,frames=_rgb_samples(path,fps);features=[_feat(x) for x in frames];rows=[]
    def avg_features(idx):
        vals=[features[i] for i in idx]
        if not vals:return None
        return {"luma":float(np.mean([x["luma"] for x in vals])),
                "contrast":float(np.mean([x["contrast"] for x in vals])),
                "saturation":float(np.mean([x["saturation"] for x in vals])),
                "edge_density":float(np.mean([x["edge_density"] for x in vals])),
                "rgb":[float(x) for x in np.mean(np.array([v["rgb"] for v in vals]),0)]}
    def distance(a,b):
        rgb=float(np.linalg.norm(np.array(a["rgb"])-np.array(b["rgb"])))
        lu=abs(a["luma"]-b["luma"]);sa=abs(a["saturation"]-b["saturation"]);ed=abs(a["edge_density"]-b["edge_density"])
        dist=rgb*.45+lu*.25+sa*.20+min(ed*4,1)*.10
        return dist,rgb,lu,sa,ed
    for s in execution.get("shots",[]):
        idx=np.where((times>=float(s["start_seconds"]))&(times<float(s["end_seconds"])))[0];a=avg_features(idx)
        if not a:continue
        rows.append({"shot_id":s["id"],"luma":round(a["luma"],5),"contrast":round(a["contrast"],5),
                     "saturation":round(a["saturation"],5),"edge_density":round(a["edge_density"],5),
                     "rgb":[round(float(x),4) for x in a["rgb"]]})
    bounds=[];shots=execution.get("shots",[])
    for l,r in zip(shots,shots[1:]):
        at=float(l["end_seconds"])
        li=np.where((times>=at-cut_window)&(times<at))[0];ri=np.where((times>=at)&(times<at+cut_window))[0]
        lctx=np.where((times>=at-context_window)&(times<at-cut_window))[0]
        rctx=np.where((times>=at+cut_window)&(times<at+context_window))[0]
        a,b=avg_features(li),avg_features(ri);ca,cb=avg_features(lctx),avg_features(rctx)
        if not a or not b:continue
        dist,rgb,lu,sa,ed=distance(a,b)
        context_dist=distance(ca,cb)[0] if ca and cb else dist
        # Saturation is unstable and visually unimportant near black. Do not
        # call a dark dip discontinuous solely because hue math swings there.
        visible_saturation_jump=sa>.32 and max(a["luma"],b["luma"])>.20
        cut_warn=dist>.28 or lu>.24 or visible_saturation_jump
        style_shift=context_dist>.32
        bounds.append({"from":l["id"],"to":r["id"],"at_seconds":at,"cut_window_seconds":cut_window,
                       "context_window_seconds":context_window,"cut_distance":round(dist,4),
                       "context_style_distance":round(context_dist,4),"rgb_distance":round(rgb,4),
                       "luma_jump":round(lu,4),"saturation_jump":round(sa,4),"edge_jump":round(ed,5),
                       "cut_discontinuity_warning":cut_warn,"context_style_shift":style_shift})
    return {"sample_fps":fps,"cut_window_seconds":cut_window,"context_window_seconds":context_window,
            "shots":rows,"boundaries":bounds,
            "warning_boundaries":[{"from":x["from"],"to":x["to"],"cut_distance":x["cut_distance"]} for x in bounds if x["cut_discontinuity_warning"]],
            "style_shift_boundaries":[{"from":x["from"],"to":x["to"],"context_style_distance":x["context_style_distance"]} for x in bounds if x["context_style_shift"]]}

def audio_continuity(media_path,execution,stems_dir=None,sample_rate=16000):
    audio=_audio(media_path,sample_rate);n=len(audio);shots=execution.get("shots",[]);rows=[]
    for s in shots:
        a=max(0,int(float(s["start_seconds"])*sample_rate));b=min(n,int(float(s["end_seconds"])*sample_rate));x=audio[a:b]
        rows.append({"shot_id":s["id"],"rms_dbfs":round(_rms_db(x),2),"peak_dbfs":round(_peak_db(x),2)})
    bounds=[]
    for l,r in zip(shots,shots[1:]):
        at=float(l["end_seconds"]);i=int(at*sample_rate);h=int(.45*sample_rate);before=audio[max(0,i-h):i];after=audio[i:min(n,i+h)]
        bdb,adb=_rms_db(before),_rms_db(after);jump=abs(adb-bdb);local=audio[max(0,i-int(.03*sample_rate)):min(n,i+int(.03*sample_rate))]
        sj=float(np.max(np.abs(np.diff(local)))) if len(local)>2 else 0;lr=float(np.sqrt(np.mean(local.astype(np.float64)**2))) if len(local) else 0;click=sj>max(.12,lr*7)
        cb,ca=_centroid(before,sample_rate),_centroid(after,sample_rate);cr=max(cb,ca)/max(min(cb,ca),120.0) if cb and ca else 1.0;spectral=cr>2.8 and max(bdb,adb)>-45
        bounds.append({"from":l["id"],"to":r["id"],"at_seconds":at,"loudness_jump_db":round(jump,2),"spectral_centroid_before_hz":round(cb,1),
                       "spectral_centroid_after_hz":round(ca,1),"spectral_jump_ratio":round(cr,2),"sample_jump":round(sj,5),"click_risk":bool(click),
                       "spectral_jump_warning":bool(spectral),"audio_transition_warning":bool(jump>6.5 or click or spectral)})
    sr={"available":False,"shots":[],"warnings":[]}
    if stems_dir:
        sd=Path(stems_dir).resolve();stems={k:_audio(sd/f"{k}.wav",sample_rate) for k in ("narration","score","ambience","effects") if (sd/f"{k}.wav").is_file()}
        if "narration" in stems:
            sr["available"]=True;active=[]
            for s in shots:
                a=max(0,int(float(s["start_seconds"])*sample_rate));b=int(float(s["end_seconds"])*sample_rate);duration=float(s.get("duration_seconds",float(s["end_seconds"])-float(s["start_seconds"])))
                voice=stems["narration"][a:min(b,len(stems["narration"]))];beds=[stems[k][a:min(b,len(stems[k]))] for k in ("score","ambience","effects") if k in stems]
                bed=np.sum(np.vstack([x[:min(map(len,beds))] for x in beds]),0) if beds else np.zeros_like(voice);vr,br=_rms_db(voice),_rms_db(bed)
                block=max(1,int(.05*sample_rate));usable=(len(voice)//block)*block;env=np.array([_rms_db(x) for x in voice[:usable].reshape(-1,block)]) if usable else np.array([])
                ai=np.where(env>-45)[0] if env.size else np.array([],dtype=int);lead=float(ai[0])*.05 if len(ai) else duration;tail=duration-float(ai[-1]+1)*.05 if len(ai) else 0;occ=float(len(ai))/len(env) if len(env) else 0
                row={"shot_id":s["id"],"voice_rms_dbfs":round(vr,2),"bed_rms_dbfs":round(br,2),"voice_margin_db":round(vr-br,2),
                     "low_mid_ratio":round(_band(voice,sample_rate,300,700),4),"presence_ratio":round(_band(voice,sample_rate,2000,5000),4),
                     "masking_warning":bool(vr>-48 and vr-br<4),"lead_in_seconds":round(lead,2),"tail_out_seconds":round(max(0,tail),2),
                     "speech_occupancy":round(occ,3),"pacing_warning":bool(vr>-48 and (lead<.20 or tail<.20 or occ>.84))}
                sr["shots"].append(row)
                if vr>-48:active.append(row)
            if active:
                levels=np.array([x["voice_rms_dbfs"] for x in active]);lm=np.array([x["low_mid_ratio"] for x in active]);med=float(np.median(levels));lmmed=float(np.median(lm));mad=float(np.median(np.abs(lm-lmmed))) or .001
                for row in active:
                    row["voice_level_outlier"]=abs(row["voice_rms_dbfs"]-med)>4;row["low_mid_outlier"]=row["low_mid_ratio"]>lmmed+3*mad and row["low_mid_ratio"]>lmmed*1.25
                    if row["masking_warning"] or row["voice_level_outlier"] or row["low_mid_outlier"] or row["pacing_warning"]:
                        sr["warnings"].append({"shot_id":row["shot_id"],"masking":row["masking_warning"],"voice_level_outlier":row["voice_level_outlier"],
                                               "low_mid_outlier":row["low_mid_outlier"],"pacing_warning":row["pacing_warning"]})
    return {"sample_rate":sample_rate,"shots":rows,"boundaries":bounds,"warning_boundaries":[x for x in bounds if x["audio_transition_warning"]],"stems":sr}

def effect_sync_signal(timeline_path,stems_dir,sample_rate=16000,threshold=.0015):
    if not timeline_path or not stems_dir:return {"available":False,"events":[],"warnings":[]}
    tp=Path(timeline_path).resolve();fx=Path(stems_dir).resolve()/"effects.wav"
    if not tp.is_file() or not fx.is_file():return {"available":False,"events":[],"warnings":[]}
    timeline=json.loads(tp.read_text());audio=_audio(fx,sample_rate);events=[];warnings=[]
    for e in timeline.get("events",[]):
        if not str(e.get("asset_id") or "").startswith("audio.core-procedural:"):continue
        at=float(e.get("at_seconds") or 0);a=max(0,int((at-.12)*sample_rate));b=min(len(audio),int((at+.45)*sample_rate))
        x=np.abs(audio[a:b]);idx=np.where(x>=threshold)[0]
        onset=(a+int(idx[0]))/sample_rate if len(idx) else None
        offset=(onset-at) if onset is not None else None
        row={"event_id":e.get("id"),"at_seconds":at,"asset_id":e.get("asset_id"),
             "detected_onset_seconds":round(onset,5) if onset is not None else None,
             "onset_offset_ms":round(offset*1000,2) if offset is not None else None}
        row["sync_warning"]=onset is None or abs(offset)>.08
        events.append(row)
        if row["sync_warning"]:warnings.append(row)
    return {"available":True,"events":events,"warnings":warnings}

def _font(size):
    for f in ("/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf","/system/fonts/Roboto-Regular.ttf"):
        try:return ImageFont.truetype(f,size)
        except:pass
    return ImageFont.load_default()
def build_transition_evidence(media_path,execution,out_dir,max_width=240):
    media=Path(media_path).resolve();out=Path(out_dir).resolve();out.mkdir(parents=True,exist_ok=True);tmp=out/"_frames";tmp.mkdir(exist_ok=True);res=[];shots=execution.get("shots",[])
    for idx,(l,r) in enumerate(zip(shots,shots[1:]),1):
        at=float(l["end_seconds"]);times=[max(.01,at-.35),max(.01,at-.08),at+.08,at+.35];files=[]
        for j,t in enumerate(times):
            f=tmp/f"{idx:02d}-{j}.jpg";extract_frame(media,f,time_seconds=t,max_width=max_width);files.append(f)
        imgs=[Image.open(f).convert("RGB") for f in files];canvas=Image.new("RGB",(sum(x.width for x in imgs),max(x.height for x in imgs)+34),(5,8,12));x=0
        for im in imgs:canvas.paste(im,(x,34));x+=im.width
        ImageDraw.Draw(canvas).text((10,17),f"{l['id']} -> {r['id']} @ {at:.2f}s",font=_font(17),fill=(225,235,238),anchor="lm")
        strip=out/f"{idx:02d}-{l['id']}-to-{r['id']}.jpg";canvas.save(strip,quality=90)
        for im in imgs:im.close()
        clip=out/f"{idx:02d}-{l['id']}-to-{r['id']}.mp4";extract_review_clip(media,clip,center_seconds=at,duration_seconds=1.6,max_width=720)
        res.append({"from":l["id"],"to":r["id"],"at_seconds":at,"strip":strip.name,"strip_sha256":sha256_file(strip),"clip":clip.name,"clip_sha256":sha256_file(clip)})
    for f in tmp.glob("*"):f.unlink()
    try:tmp.rmdir()
    except OSError:pass
    return res
def build_sync_evidence(media_path,timeline_path,out_dir):
    if not timeline_path or not Path(timeline_path).is_file():return []
    timeline=json.loads(Path(timeline_path).read_text());out=Path(out_dir);out.mkdir(parents=True,exist_ok=True);res=[]
    for e in timeline.get("events",[]):
        targets=set(e.get("targets") or []);kind=str(e.get("kind") or "")
        if not {"audio","picture"}<=targets or kind in {"narration_start","shot_start","shot_end","review_point"}:continue
        at=float(e.get("at_seconds") or 0);clip=out/f"{len(res)+1:02d}-{e.get('id','event')}.mp4";extract_review_clip(media_path,clip,center_seconds=at,duration_seconds=2.2,max_width=720)
        res.append({"event_id":e.get("id"),"kind":kind,"at_seconds":at,"label":e.get("label"),"clip":clip.name,"clip_sha256":sha256_file(clip)})
    return res
def build_spectrogram(media_path,output_path):
    out=Path(output_path).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    r=_run(["ffmpeg","-y","-v","error","-i",str(Path(media_path).resolve()),"-lavfi","showspectrumpic=s=1200x500:legend=disabled:scale=log:color=channel","-frames:v","1",str(out)])
    if r.returncode or not out.is_file():raise ValueError((r.stderr or b"spectrogram failed").decode(errors="replace")[-3000:])
    return {"file":out.name,"sha256":sha256_file(out)}

def build_iteration_compare(old_media,new_media,execution,out_dir,max_clips=12):
    old,new=Path(old_media).resolve(),Path(new_media).resolve();out=Path(out_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    to,fo=_rgb_samples(old,8,120,68);tn,fn=_rgb_samples(new,8,120,68);ao,an=_audio(old,8000),_audio(new,8000);rows=[]
    for s in execution.get("shots",[]):
        a,b=float(s["start_seconds"]),float(s["end_seconds"]);io=np.where((to>=a)&(to<b))[0];inn=np.where((tn>=a)&(tn<b))[0];m=min(len(io),len(inn))
        if m:
            frame_delta=np.mean(np.abs(fo[io[:m]].astype(np.float32)-fn[inn[:m]].astype(np.float32)),axis=(1,2,3))/255
            vd=float(np.mean(frame_delta));vp95=float(np.percentile(frame_delta,95));vmax=float(np.max(frame_delta))
        else:vd=vp95=vmax=0
        ia,ib=int(a*8000),int(b*8000);m2=min(len(ao[ia:ib]),len(an[ia:ib]));ad=float(np.sqrt(np.mean((ao[ia:ia+m2].astype(np.float64)-an[ia:ia+m2].astype(np.float64))**2))) if m2 else 0
        changed_flag=(vd>.004 or vp95>.012 or vmax>.020 or ad>.004)
        rows.append({"shot_id":s["id"],"start_seconds":a,"duration_seconds":b-a,"visual_delta_mean":round(vd,5),
                     "visual_delta_p95":round(vp95,5),"visual_delta_max":round(vmax,5),"audio_delta_rms":round(ad,6),"changed":bool(changed_flag)})
    changed=sorted([x for x in rows if x["changed"]],key=lambda x:x["visual_delta_max"]+x["audio_delta_rms"],reverse=True)
    clips=[];audio_clips=[];font="/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf"
    for row in changed[:max_clips]:
        sid=row["shot_id"];a=row["start_seconds"];dur=row["duration_seconds"];dest=out/f"{sid}-ab.mp4"
        fc=(f"[0:v]scale=640:360,drawtext=fontfile={font}:text='BEFORE':fontcolor=white:fontsize=22:x=18:y=18[o];"
            f"[1:v]scale=640:360,drawtext=fontfile={font}:text='AFTER':fontcolor=white:fontsize=22:x=18:y=18[n];[o][n]hstack=inputs=2[v]")
        rr=_run(["ffmpeg","-y","-v","error","-ss",str(a),"-t",str(dur),"-i",str(old),"-ss",str(a),"-t",str(dur),"-i",str(new),
                 "-filter_complex",fc,"-map","[v]","-map","1:a?","-c:v","libx264","-preset","veryfast","-crf","21","-c:a","aac","-b:a","128k","-shortest",str(dest)])
        if rr.returncode:raise ValueError((rr.stderr or b"A/B render failed").decode(errors="replace")[-3000:])
        clips.append({"shot_id":sid,"file":dest.name,"sha256":sha256_file(dest),
                      "visual_delta_mean":row["visual_delta_mean"],"visual_delta_p95":row["visual_delta_p95"],
                      "visual_delta_max":row["visual_delta_max"],"audio_delta_rms":row["audio_delta_rms"]})
        if row["audio_delta_rms"]>.002:
            adest=out/f"{sid}-audio-ab.mp4"
            afc=(f"[1:v]scale=640:360,split=2[vb][va];"
                 f"[vb]drawtext=fontfile={font}:text='BEFORE AUDIO':fontcolor=white:fontsize=24:x=18:y=18[vb1];"
                 f"[va]drawtext=fontfile={font}:text='AFTER AUDIO':fontcolor=white:fontsize=24:x=18:y=18[va1];"
                 "[0:a]asetpts=PTS-STARTPTS[ab];[1:a]asetpts=PTS-STARTPTS[aa];"
                 "[vb1][ab][va1][aa]concat=n=2:v=1:a=1[vout][aout]")
            ar=_run(["ffmpeg","-y","-v","error","-ss",str(a),"-t",str(dur),"-i",str(old),"-ss",str(a),"-t",str(dur),"-i",str(new),
                     "-filter_complex",afc,"-map","[vout]","-map","[aout]","-c:v","libx264","-preset","veryfast","-crf","21",
                     "-c:a","aac","-b:a","160k",str(adest)])
            if ar.returncode:raise ValueError((ar.stderr or b"audio A/B render failed").decode(errors="replace")[-3000:])
            audio_clips.append({"shot_id":sid,"file":adest.name,"sha256":sha256_file(adest),"audio_delta_rms":row["audio_delta_rms"]})
    result={"schema_version":2,"before_sha256":sha256_file(old),"after_sha256":sha256_file(new),"shots":rows,"changed_shot_count":len(changed),
            "changed_shots":[x["shot_id"] for x in changed],"ab_clips":clips,"audio_ab_clips":audio_clips}
    (out/"iteration-compare.json").write_text(json.dumps(result,indent=2)+"\n");return result