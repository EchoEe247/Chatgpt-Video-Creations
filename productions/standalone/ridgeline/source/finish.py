import json,subprocess,time,hashlib,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];R=P/"renders";F=P/"final";A=P/"audio";Q=P/"review";Q.mkdir(exist_ok=True)
def run(cmd):print("RUN",cmd[0:3],flush=True);subprocess.run(cmd,cwd=ROOT,check=True)
deadline=time.time()+900
while not all((R/f"shot-{i:02}.mp4").exists() for i in range(1,23)) or not (A/"ending.png").exists():
 if time.time()>deadline:raise RuntimeError("render wait exceeded")
 time.sleep(3)
run(["python","scripts/timelinectl.py","compile",str(P/"source/execution-plan.json"),str(P/"source/av-timeline.json"),"--events",str(P/"source/av-events.json")])
(R/"concat.txt").write_text("".join("file '"+str(R/f"shot-{i:02}.mp4")+"'\n" for i in range(1,23)))
run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(R/"concat.txt"),"-c","copy",str(R/"picture.mp4")])
filters="[0:v]eq=contrast=1.06:brightness=0.018:saturation=1.10[v];[v][2:v]overlay=enable='between(t,1,5)'[v1];[v1][3:v]overlay=enable='between(t,126,130.8)',fade=t=in:st=0:d=1,fade=t=out:st=130.7:d=1.3[out];[1:a]volume=-1.5dB,afade=t=out:st=128:d=2[aout]"
run(["ffmpeg","-y","-v","error","-threads","2","-i",str(R/"picture.mp4"),"-i",str(A/"master.wav"),"-i",str(A/"opening.png"),"-i",str(A/"ending.png"),"-filter_complex_threads","1","-filter_complex",filters,"-map","[out]","-map","[aout]","-t","132","-c:v","libx264","-threads","2","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart",str(F/"ridgeline.mp4")])
h=hashlib.sha256((F/"ridgeline.mp4").read_bytes()).hexdigest();(F/"sha256.txt").write_text(h+"  ridgeline.mp4\n")
print("MASTER_READY",h,flush=True)
run(["python","scripts/videoctl.py","qa",str(F/"ridgeline.mp4"),"--width","960","--height","540","--fps","24","--duration","132","--intentional-silence","130:132","--output",str(Q/"technical-qa.json")])
run(["python","scripts/videoctl.py","contact-sheet",str(F/"ridgeline.mp4"),str(Q/"contact-sheet.jpg"),"--count","22","--columns","4"])
print("TECHNICAL_READY",flush=True)
run(["python","scripts/creativeqactl.py","analyze",str(F/"ridgeline.mp4"),str(P/"source/execution-plan.json"),str(Q/"experience"),"--timeline",str(P/"source/av-timeline.json"),"--layout",str(P/"source/layout-qa.json")])
print("ALL_QA_READY",flush=True)
