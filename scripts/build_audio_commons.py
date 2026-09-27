#!/usr/bin/env python3
"""Build a tiny deterministic procedural Core Audio Commons pack."""
from __future__ import annotations
import hashlib,json,math,random,struct,wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"core"/"payload"/"audio-procedural"
MANIFEST=ROOT/"assets"/"audio-commons.json"
SR=48000

SPECS=[
    ("ui_tick",0.12,"ui,click,interface","Short bright interface confirmation"),
    ("soft_impact",0.55,"impact,transition,hit","Low-mid restrained impact"),
    ("air_whoosh",0.70,"whoosh,transition,motion","Broadband motion whoosh"),
    ("riser_short",1.20,"riser,transition,tension","Short tonal/noise rise"),
    ("low_pulse",0.80,"pulse,technology,tension","Low cinematic pulse"),
    ("signal_chime",0.65,"chime,signal,technology","Two-tone signal/chime")
]

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def env(t,d,attack=.02,release=.12):
    a=min(1.0,t/max(attack,1e-6))
    r=min(1.0,max(0.0,(d-t))/max(release,1e-6))
    return a*r

def sample(name,t,d,rng):
    if name=="ui_tick":
        return .30*math.sin(2*math.pi*1250*t)*math.exp(-28*t)+.10*math.sin(2*math.pi*2500*t)*math.exp(-38*t)
    if name=="soft_impact":
        return (.30*math.sin(2*math.pi*(78+18*math.exp(-10*t))*t)+.055*rng.uniform(-1,1))*math.exp(-6.3*t)
    if name=="air_whoosh":
        x=t/d; band=math.sin(math.pi*x)**1.4
        return .18*rng.uniform(-1,1)*band+.035*math.sin(2*math.pi*(180+850*x)*t)*band
    if name=="riser_short":
        x=t/d; tone=160+1100*x*x
        return (.12*math.sin(2*math.pi*tone*t)+.055*rng.uniform(-1,1))*x*env(t,d,.05,.08)
    if name=="low_pulse":
        return .30*math.sin(2*math.pi*(62-9*t/d)*t)*math.exp(-4.2*t)+.055*math.sin(2*math.pi*124*t)*math.exp(-6*t)
    if name=="signal_chime":
        return (.20*math.sin(2*math.pi*660*t)+.13*math.sin(2*math.pi*990*t))*math.exp(-4.8*t)
    return 0.0

def render(name,duration,path):
    rng=random.Random("video-commons-"+name)
    frames=bytearray()
    total=round(duration*SR)
    for i in range(total):
        t=i/SR
        v=max(-.88,min(.88,sample(name,t,duration,rng)))
        l=v
        r=max(-.88,min(.88,v*.96+.004*math.sin(2*math.pi*.7*t)*env(t,duration)))
        frames += struct.pack("<hh",int(l*32767),int(r*32767))
    with wave.open(str(path),"wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(frames)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assets=[]
    for name,dur,tags,desc in SPECS:
        p=OUT/f"{name}.wav"; render(name,dur,p)
        assets.append({"id":name,"file":str(p.relative_to(ROOT)),"duration_seconds":dur,"sample_rate":SR,"channels":2,"tags":tags.split(","),"description":desc,"sha256":sha(p)})
    manifest={
        "schema_version":1,
        "pack_id":"audio.core-procedural",
        "name":"Core Procedural Audio Primitives",
        "source":"scripts/build_audio_commons.py",
        "license":"PROJECT-ORIGINAL",
        "generated_deterministically":True,
        "assets":assets
    }
    MANIFEST.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"pass":True,"output":str(OUT),"assets":len(assets),"manifest":str(MANIFEST)},indent=2))

if __name__=="__main__": main()
