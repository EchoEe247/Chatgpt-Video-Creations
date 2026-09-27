import json,math,subprocess,wave,hashlib,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];A=P/"audio";F=P/"final";S=P/"source"
A.mkdir(exist_ok=True);F.mkdir(exist_ok=True)
sr=24000;dur=132;rng=np.random.default_rng(24)
SPEED_SEGMENTS=((0,12,.8),(12,36,4.5),(36,60,7.5),(60,84,4.8),(84,114,8.0),(114,132,5.8))
def route_y(t):
 y=6.0
 for a,b,v in SPEED_SEGMENTS:
  if t<=a: break
  y+=max(0.0,min(t,b)-a)*v
  if t<b: break
 return y
def time_for_y(target):
 y=6.0
 for a,b,v in SPEED_SEGMENTS:
  span=(b-a)*v
  if target<=y+span:return a+(target-y)/v
  y+=span
 return SPEED_SEGMENTS[-1][1]
landings=[time_for_y(y+10) for y in [167,315,474,576]]
events=[{"id":f"jump-{i+1}-landing","at_seconds":round(t,6),"duration_seconds":.5,"kind":"impact","label":"Landing pulse matches end of generated airborne route interval","targets":["picture","audio","qa"],"stem":"effects"} for i,t in enumerate(landings)]
(S/"av-events.json").write_text(json.dumps({"schema_version":1,"events":events},indent=2))
# Stream procedural acoustic bed in one-second blocks to keep phone memory stable.
with wave.open(str(A/"effects.wav"),"wb") as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr)
 for sec in range(dur):
  t=np.arange(sr)/sr+sec
  n=rng.standard_normal(sr+16);smooth=np.convolve(n,np.ones(17)/17,mode="valid")[:sr]
  tire=rng.standard_normal(sr)*(.025+.014*np.sin(t*17)**2)
  env=min(1,(sec+1)/12)*(1 if sec<125 else max(0,(132-sec)/7))
  attack=np.maximum(
   np.clip((t-36)/3,0,1)*np.clip((60-t)/3,0,1),
   np.clip((t-84)/3,0,1)*np.clip((114-t)/3,0,1)
  )
  # Wind and tire roar rise with the authored attack sections; score remains unchanged.
  wind=smooth*(.10+.20*attack)*env
  signal=(wind+tire*(.55+.85*attack))*env
  for at in landings:
   q=t-at;mask=(q>=0)&(q<.42)
   signal+=np.where(mask,.22*np.exp(-np.maximum(q,0)*14)*np.sin(2*np.pi*(72*q-24*q*q)),0)
   signal+=np.where(mask,.055*np.exp(-np.maximum(q,0)*10)*rng.standard_normal(sr),0)
  stereo=np.stack([signal,np.roll(signal,37)*.96],axis=1)
  w.writeframes(np.clip(stereo*32767,-32768,32767).astype("<i2").tobytes())
cmd=["ffmpeg","-y","-v","error","-i",str(P/"assets/score.mp3"),"-i",str(A/"effects.wav"),"-filter_complex","[0:a]atrim=0:132,asetpts=PTS-STARTPTS,volume=0.68,afade=t=in:d=5,afade=t=out:st=124:d=8[m];[1:a]highpass=f=65,lowpass=f=10000,volume=0.8[e];[m][e]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=10,aresample=48000[a]","-map","[a]","-c:a","pcm_s16le",str(A/"master.wav")]
subprocess.run(cmd,check=True)
font="/system/fonts/Roboto-Regular.ttf"
# Locate a font without downloading or using platform UI.
candidates=[font,"/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf"]
font=next((f for f in candidates if Path(f).exists()),None)
for name,large,small in [("opening","RIDGELINE","A   D E S C E N T"),("ending","FIND YOUR LINE.","")]:
 im=Image.new("RGBA",(960,540));d=ImageDraw.Draw(im)
 f=ImageFont.truetype(font,48) if font else ImageFont.load_default(size=48)
 f2=ImageFont.truetype(font,32) if font else ImageFont.load_default(size=32)
 d.text((480,245),large,font=f,anchor="mm",fill=(248,247,239,255),stroke_width=1,stroke_fill=(10,16,18,100))
 if small:d.text((480,290),small,font=f2,anchor="mm",fill=(240,230,210,255))
 im.save(A/(name+".png"))
print("AUDIO_READY",landings,flush=True)
