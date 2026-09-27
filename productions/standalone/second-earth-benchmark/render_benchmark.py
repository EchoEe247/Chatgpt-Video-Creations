#!/usr/bin/env python3
"""SECOND EARTH restartable local production orchestrator.

All animation/rendering is local. The only network-dependent step is narration TTS,
which is cached per shot after the first successful build.
"""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys

P=Path(__file__).resolve().parent
ROOT=P.parents[2]
R=P/"renders"
F=P/"final"
A=P/"audio"
R.mkdir(exist_ok=True);F.mkdir(exist_ok=True);A.mkdir(exist_ok=True)
plan=json.loads((P/"source/execution-plan.json").read_text())
python_ids={"shot-01","shot-04","shot-08","shot-14","shot-15","shot-17","shot-19"}

def probe_duration(path):
    q=subprocess.run(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(path)],
        capture_output=True,text=True
    )
    if q.returncode:
        return None
    try:return float(q.stdout.strip())
    except:return None

def valid(path,duration,tol=.08):
    d=probe_duration(path)
    return d is not None and abs(d-duration)<=tol

def run(cmd,cwd=None,env=None):
    subprocess.run(cmd,cwd=cwd or P,env=env,check=True)

def render_python():
    spec=importlib.util.spec_from_file_location("second_earth_python",P/"renderers/python_frames.py")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    from PIL import Image
    temp=P/".runtime-frame.jpg"
    for shot in [s for s in plan["shots"] if s["id"] in python_ids]:
        out=R/f"{shot['id']}.mp4"
        if valid(out,shot["duration_seconds"]):
            continue
        proc=subprocess.Popen([
            "ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24",
            "-s","1280x720","-r","24","-i","-","-an","-c:v","libx264",
            "-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(out)
        ],stdin=subprocess.PIPE)
        for index in range(round(shot["duration_seconds"]*24)):
            mod.render_frame({**shot,"width":1280,"height":720,"fps":24},index,temp,{"shot":shot})
            with Image.open(temp) as im:
                proc.stdin.write(im.convert("RGB").tobytes())
        proc.stdin.close()
        if proc.wait()!=0:
            raise RuntimeError(f"Python shot render failed: {shot['id']}")
        if temp.exists():temp.unlink()
        print("PY_DONE",shot["id"],flush=True)

def render_canvas():
    needed=["shot-03","shot-05","shot-06","shot-09","shot-13","shot-18"]
    shot_map={s["id"]:s for s in plan["shots"]}
    if all(valid(R/f"{sid}.mp4",shot_map[sid]["duration_seconds"]) for sid in needed):
        return
    run(["node",str(P/"renderers/render_canvas_shots.mjs")])

def ensure_blender_reel(frame_dir_name,builder,reel_name,expected_frames,duration,source_fps=6):
    frame_dir=R/frame_dir_name;frame_dir.mkdir(exist_ok=True)
    reel=R/reel_name
    if valid(reel,duration):
        return reel
    if reel.exists():reel.unlink()
    env={**os.environ,"LIBGL_ALWAYS_SOFTWARE":"1","GALLIUM_DRIVER":"llvmpipe"}
    for attempt in range(1,7):
        count=len(list(frame_dir.glob("frame_*.png")))
        if count>=expected_frames:break
        print("BLENDER_RESUME",frame_dir_name,"attempt",attempt,"have",count,"need",expected_frames,flush=True)
        subprocess.run([
            "proot-distro","login","hermes-ubuntu","--","blender","--background",
            "--python-exit-code","1","--python",str(P/"renderers"/builder)
        ],cwd=P,env=env,check=False)
    count=len(list(frame_dir.glob("frame_*.png")))
    if count<expected_frames:
        raise RuntimeError(f"{frame_dir_name} incomplete: {count}/{expected_frames}")
    run([
        "ffmpeg","-y","-v","error","-framerate",str(source_fps),"-pattern_type","glob",
        "-i",str(frame_dir/"frame_*.png"),"-frames:v",str(expected_frames),
        "-an","-c:v","libx264","-preset","veryfast",
        "-crf","18","-r",str(source_fps),"-pix_fmt","yuv420p",str(reel)
    ])
    if not valid(reel,duration):
        raise RuntimeError(f"invalid Blender reel: {reel}")
    print("BLENDER_REEL_READY",reel_name,count,flush=True)
    return reel

def split_blender_reels():
    groups=[
        (R/"blender-physical-reel.mp4",[("shot-02",0,7),("shot-07",7,8),("shot-16",15,7)]),
        (R/"blender-probe-v2-reel.mp4",[("shot-10",0,7),("shot-11",7,8),("shot-20",15,7)]),
    ]
    for reel,segments in groups:
        physical=(reel.name=="blender-physical-reel.mp4")
        for sid,start,duration in segments:
            out=R/f"{sid}.mp4"
            if valid(out,duration):
                continue
            exposure="eq=brightness=0.045:contrast=1.07:gamma=1.18:saturation=1.08," if physical else ""
            vf=(
                "scale=1280:720:flags=lanczos,"
                +exposure+
                "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1,"
                f"tpad=stop_mode=clone:stop_duration=0.35,trim=duration={duration},setpts=PTS-STARTPTS"
            )
            run([
                "ffmpeg","-y","-v","error","-ss",str(start),"-i",str(reel),
                "-t",str(duration),"-an","-vf",vf,"-c:v","libx264","-preset","veryfast",
                "-crf","19","-r","24","-pix_fmt","yuv420p",str(out)
            ])
            if not valid(out,duration):
                current=probe_duration(out)
                if current is not None and current < duration and duration-current < 0.6:
                    fixed=R/f"{sid}.duration-fix.mp4"
                    run([
                        "ffmpeg","-y","-v","error","-i",str(out),
                        "-vf",f"tpad=stop_mode=clone:stop_duration=0.6,trim=duration={duration},setpts=PTS-STARTPTS",
                        "-an","-c:v","libx264","-preset","veryfast","-crf","19",
                        "-r","24","-pix_fmt","yuv420p",str(fixed)
                    ])
                    fixed.replace(out)
                if not valid(out,duration):
                    raise RuntimeError(f"invalid split Blender shot: {sid} ({probe_duration(out)})")

def render_editorial():
    out=R/"shot-12.mp4"
    if not valid(out,6):
        if out.exists():out.unlink()
        src=R/"shot-11.mp4"
        filt=(
          "[0:v]trim=duration=6,setpts=PTS-STARTPTS,"
          "eq=brightness=-0.025:saturation=0.90,scale=1280:720[base];"
          "color=c=0xB8F6FF:s=8x720:r=24:d=6[bar];"
          "[base][bar]overlay=x='180+900*t/6':y=0:shortest=1,"
          "fade=t=out:st=5.55:d=0.45[v]"
        )
        run([
            "ffmpeg","-y","-v","error","-i",str(src),"-filter_complex",filt,
            "-map","[v]","-t","6","-an","-c:v","libx264","-preset","veryfast",
            "-crf","19","-r","24","-pix_fmt","yuv420p",str(out)
        ])
    out=R/"shot-21.mp4"
    if not valid(out,5):
        if out.exists():out.unlink()
        font="/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf"
        src=R/"shot-20.mp4"
        vf=(
          "trim=start=2:end=7,setpts=PTS-STARTPTS,scale=1280:720:flags=lanczos,"
          "eq=brightness='-0.10*min(t/0.85,1)':saturation='1-0.28*min(t/0.85,1)':eval=frame,"
          f"drawtext=fontfile={font}:text='BUILD FAST. DISCOVER WHAT IS POSSIBLE.':"
          "fontcolor=0xE6EDEB:fontsize=40:x=(w-text_w)/2:y=h*0.39:enable='between(t,0.9,4.45)',"
          f"drawtext=fontfile={font}:text='KEEP ENOUGH FREEDOM TO BE WRONG.':"
          "fontcolor=0xE7B975:fontsize=40:x=(w-text_w)/2:y=h*0.52:enable='between(t,1.25,4.45)',"
          "fade=t=out:st=4.2:d=0.8"
        )
        run([
            "ffmpeg","-y","-v","error","-i",str(src),"-vf",vf,"-t","5","-an",
            "-c:v","libx264","-preset","veryfast","-crf","18","-r","24",
            "-pix_fmt","yuv420p",str(out)
        ])

def verify_shots():
    errors=[]
    for shot in plan["shots"]:
        path=R/f"{shot['id']}.mp4"
        duration=probe_duration(path)
        if duration is None or abs(duration-shot["duration_seconds"])>.08:
            errors.append({"shot":shot["id"],"expected":shot["duration_seconds"],"actual":duration})
    if errors:
        raise RuntimeError("shot duration failures: "+json.dumps(errors))
    print("SHOTS_READY",len(plan["shots"]),flush=True)

def build_audio():
    master=A/"master.wav"
    if not valid(master,150,.10):
        run([sys.executable,str(A/"build_audio.py")])
    if not valid(master,150,.10):
        raise RuntimeError("invalid audio master")
    polished=A/"master-polished.wav"
    # Cheap post-master polish may contain authored envelopes; always refresh it.
    run([sys.executable,str(A/"polish_audio.py")])
    if not valid(polished,150,.10):
        raise RuntimeError("invalid polished audio master")
    return polished

def finish_transitions():
    run([sys.executable,str(P/"finish_transitions.py")])

def assemble():
    order=R/"ordered.txt"
    finished=R/"finished"
    def shot_path(sid):
        candidate=finished/f"{sid}.mp4"
        return candidate if candidate.is_file() else R/f"{sid}.mp4"
    order.write_text("\n".join("file '"+str(shot_path(s["id"]))+"'"
                               for s in plan["shots"])+"\n")
    silent=F/"second-earth-silent.mp4"
    run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(order),
         "-c:v","copy","-an",str(silent)])
    if not valid(silent,150,.12):
        raise RuntimeError(f"silent master duration invalid: {probe_duration(silent)}")
    master=F/"second-earth.mp4"
    audio_master=A/"master-polished.wav"
    run(["ffmpeg","-y","-v","error","-i",str(silent),"-i",str(audio_master),
         "-map","0:v:0","-map","1:a:0","-c:v","copy","-af","atrim=end=149.2,asetpts=PTS-STARTPTS,apad=pad_dur=0.8","-c:a","aac","-b:a","192k",
         "-t","150","-movflags","+faststart",str(master)])
    if not valid(master,150,.12):
        raise RuntimeError(f"final master duration invalid: {probe_duration(master)}")
    print("FINAL_READY",master,flush=True)

def main():
    render_python()
    render_canvas()
    ensure_blender_reel("physical-frames","build_blender_physical.py","blender-physical-reel.mp4",132,22)
    ensure_blender_reel("probe-v2-frames","build_blender_probe.py","blender-probe-v2-reel.mp4",88,22,source_fps=4)
    split_blender_reels()
    render_editorial()
    verify_shots()
    build_audio()
    finish_transitions()
    assemble()

if __name__=="__main__":
    main()