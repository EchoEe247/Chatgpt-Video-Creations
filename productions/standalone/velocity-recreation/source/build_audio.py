#!/usr/bin/env python3
import math,wave,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

P=Path(__file__).resolve().parents[1]
A=P/"audio";A.mkdir(parents=True,exist_ok=True)
SR=48000;D=120.0
t=np.arange(int(SR*D),dtype=np.float32)/SR
profile_path=P/"source/speed-profile.json"
profile=json.loads(profile_path.read_text())
import hashlib
(A/"speed-profile.sha256").write_text(hashlib.sha256(profile_path.read_bytes()).hexdigest()+chr(10))
SPEED=tuple((x["start"],x["end"],x["speed_mps"]) for x in profile["segments"])
RAMP=float(profile["ramp_half_seconds"])

def speed_curve(tt):
 out=np.full_like(tt,SPEED[-1][2],dtype=np.float32)
 for a,b,v in SPEED:
  out[(tt>=a)&(tt<b)]=v
 for i in range(1,len(SPEED)):
  c=SPEED[i][0];lo=c-RAMP;hi=c+RAMP;m=(tt>=lo)&(tt<=hi)
  if m.any():
   x=(tt[m]-lo)/(hi-lo);x=x*x*(3-2*x)
   out[m]=SPEED[i-1][2]+(SPEED[i][2]-SPEED[i-1][2])*x
 return out

spd=speed_curve(t)
attack=np.clip((spd-28)/20,0,1)
rng=np.random.default_rng(21)
noise_c=rng.standard_normal(len(t)).astype(np.float32)
noise_l=rng.standard_normal(len(t)).astype(np.float32)
noise_r=rng.standard_normal(len(t)).astype(np.float32)
kernel=np.ones(32,dtype=np.float32)/32
wind_l=np.convolve(noise_l,kernel,mode="same")*(.045+.18*(spd/47)**2)
wind_r=np.convolve(noise_r,kernel,mode="same")*(.045+.18*(spd/47)**2)
road_l=np.convolve(noise_l,np.array([.04,.10,.18,.26,.18,.10,.04],dtype=np.float32),mode="same")*(.04+.08*(spd/47))
road_r=np.convolve(noise_r,np.array([.04,.10,.18,.26,.18,.10,.04],dtype=np.float32),mode="same")*(.04+.08*(spd/47))

# Engine phase is derived from exactly the same continuous speed curve as picture.
rpm=1450+spd*88
for c in [31.5,37.5,72.5,80.5,88.5]:
 rpm-=760*np.exp(-((t-c)/.25)**2)
freq=rpm/60*2.0
phase=2*np.pi*np.cumsum(freq)/SR
engine=(.12*np.sin(phase)+.085*np.sin(2*phase+.3)+.045*np.sin(3*phase+.7))*(.54+.46*attack)

distance=np.cumsum(spd)/SR
joints=np.zeros_like(t)
for spacing in [22.0,37.0]:
 ph=np.mod(distance,spacing);joints+=np.exp(-(ph/.17)**2)*.010

# Passing cars cross the stereo field instead of using a nearly mono shared noise source.
who_l=np.zeros_like(t);who_r=np.zeros_like(t)
passes=[]
motion=json.loads((P/'source/motion-telemetry.json').read_text())
ts=np.arange(0,120.001,.025);vs=speed_curve(ts);ys=np.concatenate(([0],np.cumsum((vs[:-1]+vs[1:])*.5*np.diff(ts))))
for car in motion['traffic']:
 if car['lane']==0:continue
 delta=car['base']+car['speed_mps']*ts-ys
 for k in np.where(delta[:-1]*delta[1:]<0)[0]:
  c=float(ts[k]-delta[k]*(ts[k+1]-ts[k])/(delta[k+1]-delta[k]))
  if 1<c<119:passes.append((c,.12,car['lane']))
passes.sort()
for c,amp,direction in passes:
 q=(t-c)/.78;env=np.exp(-q*q*2.0)
 pan=direction*(.5+.28*np.exp(-q*q))
 src=np.convolve(rng.standard_normal(len(t)).astype(np.float32),np.ones(12,dtype=np.float32)/12,mode="same")
 tone=np.sin(2*np.pi*(190*(t-c)-25*np.log(np.cosh(np.clip(q,-10,10)))))*.08
 sig=(src*.65+tone)*env*amp
 who_l+=sig*np.sqrt((1-pan)*.5);who_r+=sig*np.sqrt((1+pan)*.5)

score_l=np.zeros_like(t);score_r=np.zeros_like(t)
chords=[(0,[110,164.8,220]),(25,[116.5,174.6,233]),(43,[110,164.8,220]),(66,[146.8,220,293.6]),(95,[116.5,174.6,233])]
for i,(start,notes) in enumerate(chords):
 end=chords[i+1][0] if i+1<len(chords) else 120;m=(t>=start)&(t<end);local=t[m]-start
 left=np.zeros(m.sum(),dtype=np.float32);right=np.zeros(m.sum(),dtype=np.float32)
 for k,f in enumerate(notes):
  left+=np.sin(2*np.pi*f*local+f*.013+k*.17)+.28*np.sin(2*np.pi*f*2*local)
  right+=np.sin(2*np.pi*f*local+f*.019-k*.15)+.28*np.sin(2*np.pi*f*2*local+.12)
 left/=len(notes)*1.4;right/=len(notes)*1.4
 fade=np.minimum(np.clip(local/2,0,1),np.clip((end-start-local)/2,0,1))
 beat=np.maximum(0,np.sin(2*np.pi*(1.45 if start<78 else 1.65)*local))**7
 pulse=beat*np.sin(2*np.pi*(55 if start<78 else 65.4)*local)*(.022+.032*attack[m])
 score_l[m]+=(left*.050+pulse)*fade;score_r[m]+=(right*.050+pulse)*fade

def save_stem(name,l,r):
 data=np.clip(np.stack([l,r],axis=1)*32767,-32768,32767).astype('<i2')
 with wave.open(str(A/(name+'.wav')),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(data.tobytes())
save_stem('engine',engine,engine)
save_stem('score',score_l,score_r)
save_stem('ambience',wind_l+road_l,wind_r+road_r)
save_stem('effects',engine+joints+who_l,engine+joints+who_r)
left=engine+score_l+joints+wind_l+road_l+who_l
right=engine+score_r+joints+wind_r+road_r+who_r
fade=np.ones_like(t);fade[:SR*2]=np.linspace(0,1,SR*2);fade[-SR*2:]=np.linspace(1,0,SR*2)
left*=fade;right*=fade
st=np.stack([left,right],axis=1);peak=np.max(np.abs(st));st*=.82/max(peak,1e-6)
pcm=np.clip(st*32767,-32768,32767).astype("<i2")
with wave.open(str(A/"master.wav"),"wb") as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())

font="/system/fonts/Roboto-Regular.ttf"
def text_img(title,sub,y1,y2):
 im=Image.new("RGBA",(960,540),(0,0,0,0));d=ImageDraw.Draw(im)
 try:f1=ImageFont.truetype(font,54);f2=ImageFont.truetype(font,34)
 except:f1=ImageFont.load_default();f2=ImageFont.load_default()
 for txt,f,y,alpha in [(title,f1,y1,232),(sub,f2,y2,220)]:
  bb=d.textbbox((0,0),txt,font=f);x=(960-(bb[2]-bb[0]))//2;d.text((x,y),txt,font=f,fill=(242,242,236,alpha))
 return im
text_img("VELOCITY","A HIGHWAY STUDY",62,132).save(A/"opening.png")
text_img("VELOCITY","LOCAL / ORIGINAL PRODUCTION",350,414).save(A/"closing.png")

events=[]
for i,(c,amp,direction) in enumerate(passes):
 events.append({"id":f"traffic-pass-{i+1}","at_seconds":c,"duration_seconds":1.6,"kind":"whoosh","label":"Stereo moving vehicle pass-by","targets":["picture","audio","qa"],"stem":"effects"})
for i,c in enumerate([25.0,66.0]):
 events.append({"id":f"accel-{i+1}","at_seconds":c,"duration_seconds":8.0,"kind":"acceleration","label":"Continuous hero acceleration ramp begins in shared speed profile","targets":["picture","audio","qa"],"stem":"effects"})
(P/"source/av-events.json").write_text(json.dumps({"schema_version":1,"events":events},indent=2)+"\n")
print("AUDIO_V2_READY",len(events),flush=True)
