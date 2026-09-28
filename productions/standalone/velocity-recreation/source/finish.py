#!/usr/bin/env python3
import subprocess,time,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];R=P/"renders-v3";A=P/"audio";F=P/"final";Q=P/"review"
F.mkdir(exist_ok=True);Q.mkdir(exist_ok=True)
def run(cmd):print("RUN",cmd[:4],flush=True);subprocess.run(cmd,cwd=ROOT,check=True)
deadline=time.time()+1200
while not all((R/f"shot-{i:02}.mp4").exists() for i in range(1,21)) or not (A/"master.wav").exists():
 if time.time()>deadline:raise RuntimeError("render wait exceeded")
 time.sleep(3)
run(["python","scripts/timelinectl.py","compile",str(P/"source/execution-plan.json"),str(P/"source/av-timeline.json"),"--events",str(P/"source/av-events.json")])
(R/"concat.txt").write_text("".join("file '"+str(R/f"shot-{i:02}.mp4")+"'\n" for i in range(1,21)))
run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(R/"concat.txt"),"-c","copy",str(R/"picture.mp4")])
flt="[0:v]eq=contrast=1.07:brightness=0.012:saturation=1.05,unsharp=5:5:0.7:5:5:0.0[v0];[v0][2:v]overlay=enable='between(t,1,5)'[v1];[v1][3:v]overlay=enable='between(t,116,120)'[v2];[v2]fade=t=out:st=118.4:d=1.6[out];[1:a]volume=-1.2dB,afade=t=out:st=118.2:d=1.8[aout]"
run(["ffmpeg","-y","-v","error","-threads","2","-i",str(R/"picture.mp4"),"-i",str(A/"master.wav"),"-i",str(A/"opening.png"),"-i",str(A/"closing.png"),"-filter_complex_threads","1","-filter_complex",flt,"-map","[out]","-map","[aout]","-t","120","-c:v","libx264","-threads","2","-preset","veryfast","-tune","grain","-crf","15","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart",str(F/"velocity.mp4")])
sha=hashlib.sha256((F/"velocity.mp4").read_bytes()).hexdigest();(F/"sha256.txt").write_text(sha+"  velocity.mp4\n");print("MASTER_READY",sha,flush=True)
run(["python","scripts/videoctl.py","qa",str(F/"velocity.mp4"),"--width","960","--height","540","--fps","24","--duration","120","--output",str(Q/"technical-qa.json")])
run(["python","scripts/videoctl.py","contact-sheet",str(F/"velocity.mp4"),str(Q/"contact-sheet.jpg"),"--count","20","--columns","4"])
run(["python",str(P/"source/cinematic_qa.py"),str(F/"velocity.mp4"),str(P/"source/execution-plan.json"),str(Q/"cinematic-qa.json"),"--telemetry",str(P/"source/motion-telemetry.json")])
print("REVIEW_CANDIDATE_READY",flush=True)