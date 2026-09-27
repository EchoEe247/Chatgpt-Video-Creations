#!/usr/bin/env python3
"""Cinematic/physical QA gates for locally rendered driving films.

Complements creativeqactl's signal checks with continuity, exposure, periodicity,
stereo-spatialization, and shared picture/audio motion-model checks.
"""
from __future__ import annotations
import argparse, json, math, subprocess, hashlib
from pathlib import Path
import numpy as np

def smooth01(x):
    x=np.clip(x,0.0,1.0)
    return x*x*(3-2*x)

def profile_speed(profile,t):
    tt=np.asarray(t,dtype=np.float64)
    seg=profile["segments"]; ramp=float(profile.get("ramp_half_seconds",0))
    out=np.full(tt.shape,float(seg[-1]["speed_mps"]),dtype=np.float64)
    for s in seg:
        m=(tt>=float(s["start"]))&(tt<float(s["end"]))
        out[m]=float(s["speed_mps"])
    if ramp>0:
        for i in range(1,len(seg)):
            c=float(seg[i]["start"]);lo=c-ramp;hi=c+ramp;m=(tt>=lo)&(tt<=hi)
            if np.any(m):
                x=smooth01((tt[m]-lo)/(hi-lo))
                out[m]=float(seg[i-1]["speed_mps"])+(float(seg[i]["speed_mps"])-float(seg[i-1]["speed_mps"]))*x
    return out

def check_speed(profile):
    fps=24.0; dur=float(profile["duration_seconds"])
    t=np.arange(0,dur,1/fps)
    v=profile_speed(profile,t)
    dv=np.abs(np.diff(v))
    accel=np.abs(np.diff(v))*fps
    return {
        "pass": bool(dv.max(initial=0)<=0.35 and accel.max(initial=0)<=7.0),
        "max_frame_speed_step_mps": float(dv.max(initial=0)),
        "max_accel_mps2": float(accel.max(initial=0)),
        "limits":{"frame_step_mps":0.35,"accel_mps2":7.0}
    }

def check_traffic(telemetry):
    worst=0.0
    offenders=[]
    for i,d in enumerate(telemetry.get("traffic",[])):
        lane=float(d["lane"]);target=float(d["target"]);a=float(d["change_start"]);b=float(d["change_end"])
        t=np.arange(0,120,1/24)
        x=np.full_like(t,lane,dtype=float)
        if target!=lane:
            mid=(t>a)&(t<b); x[t>=b]=target
            q=(t[mid]-a)/(b-a); x[mid]=lane+(target-lane)*smooth01(q)
        step=float(np.max(np.abs(np.diff(x)),initial=0))
        worst=max(worst,step)
        if step>.03: offenders.append({"traffic_index":i,"max_lane_step":step})
    return {"pass":not offenders,"max_lane_step_per_frame":worst,"limit":0.03,"offenders":offenders[:8]}

def check_camera_periodicity(plan):
    cams=[s.get("motion",{}).get("camera","") for s in plan.get("shots",[])]
    best={"lag":None,"match_ratio":0.0}
    for lag in range(2,min(9,len(cams))):
        n=len(cams)-lag
        if n<=0: continue
        ratio=sum(cams[i]==cams[i+lag] for i in range(n))/n
        if ratio>best["match_ratio"]: best={"lag":lag,"match_ratio":ratio}
    counts={c:cams.count(c) for c in sorted(set(cams))}
    dominant=max(counts.values(),default=0)/max(len(cams),1)
    ok=best["match_ratio"]<.55 and dominant<=.25
    return {"pass":ok,"best_periodic_lag":best["lag"],"best_match_ratio":best["match_ratio"],"dominant_family_ratio":dominant,"counts":counts,"limits":{"periodic_match_ratio":.55,"dominant_family_ratio":.25}}

def decode_frames(media,fps=1/3,w=320,h=180):
    cmd=["ffmpeg","-v","error","-i",str(media),"-vf",f"fps={fps},scale={w}:{h}","-f","rawvideo","-pix_fmt","rgb24","-"]
    data=subprocess.check_output(cmd)
    n=w*h*3
    if len(data)%n: raise RuntimeError("raw frame byte count mismatch")
    arr=np.frombuffer(data,dtype=np.uint8).reshape(-1,h,w,3).astype(np.float32)/255.0
    return arr

def check_exposure_detail(media):
    frames=decode_frames(media)
    lum=.2126*frames[:,:,:,0]+.7152*frames[:,:,:,1]+.0722*frames[:,:,:,2]
    avg=lum.mean(axis=(1,2))
    # late-film floor is where the original candidate failed.
    times=np.arange(len(frames))*3.0
    late=avg[times>=84] if np.any(times>=84) else avg
    gx=np.abs(np.diff(lum,axis=2)).mean(axis=(1,2))
    gy=np.abs(np.diff(lum,axis=1)).mean(axis=(1,2))
    detail=(gx+gy)*.5
    late_detail=detail[times>=84] if np.any(times>=84) else detail
    min_late=float(late.min(initial=1))
    p10_late=float(np.percentile(late,10)) if late.size else 0
    p10_detail=float(np.percentile(late_detail,10)) if late_detail.size else 0
    return {
      "pass":bool(min_late>=.055 and p10_late>=.065 and p10_detail>=.020),
      "late_min_luma":min_late,"late_p10_luma":p10_late,"late_p10_detail_energy":p10_detail,
      "limits":{"late_min_luma":.055,"late_p10_luma":.065,"late_p10_detail_energy":.020}
    }

def check_stereo(media):
    cmd=["ffmpeg","-v","error","-i",str(media),"-map","0:a:0","-ac","2","-ar","12000","-f","f32le","-"]
    raw=subprocess.check_output(cmd)
    a=np.frombuffer(raw,dtype="<f4")
    if len(a)<4:return {"pass":False,"error":"no stereo samples"}
    a=a[:len(a)//2*2].reshape(-1,2)
    # ignore near-silence ends
    mask=np.max(np.abs(a),axis=1)>1e-4
    a=a[mask]
    corr=float(np.corrcoef(a[:,0],a[:,1])[0,1]) if len(a)>10 else 1.0
    side_rms=float(np.sqrt(np.mean(((a[:,0]-a[:,1])*.5)**2)))
    mid_rms=float(np.sqrt(np.mean(((a[:,0]+a[:,1])*.5)**2)))
    ratio=side_rms/max(mid_rms,1e-9)
    return {"pass":bool(abs(corr)<=.985 and ratio>=.08),"lr_correlation":corr,"side_to_mid_rms":ratio,"limits":{"abs_correlation":.985,"side_to_mid_rms":.08}}

def check_model_sync(root,telemetry):
    sp=root/"source/speed-profile.json"
    expected=hashlib.sha256(sp.read_bytes()).hexdigest()
    render_sha=(root/"renders-v2/speed-profile.sha256").read_text().strip() if (root/"renders-v2/speed-profile.sha256").exists() else ""
    audio_sha=(root/"audio/speed-profile.sha256").read_text().strip() if (root/"audio/speed-profile.sha256").exists() else ""
    tele_sha=telemetry.get("speed_profile_sha256","")
    return {"pass":expected==render_sha==audio_sha==tele_sha,"expected_sha256":expected,"renderer_sha256":render_sha,"audio_sha256":audio_sha,"telemetry_sha256":tele_sha}

def check_plan_hygiene(plan,root):
    raw=json.dumps(plan).lower()
    stale=[x for x in ["moving rider","mountain backgrounds","poly haven ground","connected trail"] if x in raw]
    closing=(root/"audio/closing.png").exists()
    varying=len(set(round(float(s["duration_seconds"]),3) for s in plan.get("shots",[])))>1
    return {"pass":not stale and closing and varying,"stale_terms":stale,"ending_credit_asset":closing,"variable_shot_durations":varying}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("media");ap.add_argument("plan");ap.add_argument("output");ap.add_argument("--telemetry")
    args=ap.parse_args()
    media=Path(args.media);plan_path=Path(args.plan);root=plan_path.parent.parent
    plan=json.loads(plan_path.read_text())
    tele_path=Path(args.telemetry) if args.telemetry else root/"source/motion-telemetry.json"
    telemetry=json.loads(tele_path.read_text())
    profile=json.loads((root/"source/speed-profile.json").read_text())
    checks={
      "speed_continuity":check_speed(profile),
      "traffic_trajectory_continuity":check_traffic(telemetry),
      "camera_periodicity":check_camera_periodicity(plan),
      "exposure_and_detail":check_exposure_detail(media),
      "stereo_spatialization":check_stereo(media),
      "picture_audio_motion_model_sync":check_model_sync(root,telemetry),
      "plan_hygiene":check_plan_hygiene(plan,root)
    }
    result={"schema_version":1,"pass":all(x.get("pass",False) for x in checks.values()),"checks":checks}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0 if result["pass"] else 2
if __name__=="__main__": raise SystemExit(main())
