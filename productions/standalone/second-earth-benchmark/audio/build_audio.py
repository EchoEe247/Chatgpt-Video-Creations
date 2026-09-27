#!/usr/bin/env python3
from pathlib import Path
import json,os,re,requests,subprocess,wave,math
import numpy as np

P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
A=P/'audio';A.mkdir(exist_ok=True);SR=48000;DUR=150
plan=json.loads((P/'source/execution-plan.json').read_text())
timeline=json.loads((P/'source/av-timeline.json').read_text())
key=os.environ.get('DEEPGRAM_API_KEY','')
if not key:
    env=Path.home()/'.deepgram_env'
    if env.exists():
        m=re.search(r'(?:export\s+)?DEEPGRAM_API_KEY\s*=\s*["\x27]?([^\s"\x27]+)',env.read_text())
        key=m.group(1) if m else ''

def probe(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)]))
def tempo_chain(v):
    parts=[]
    while v>2:parts.append(2);v/=2
    while v<.5:parts.append(.5);v/=.5
    parts.append(v)
    return ','.join('atempo='+f'{x:.6f}' for x in parts)

# Narration clips: exact shot audio cues, one independently repairable file per shot.
if key:
  for shot in plan['shots']:
    sid=shot['id'];out=A/f'{sid}-voice.wav'
    if out.exists():continue
    raw=A/f'{sid}-raw.wav'
    rr=requests.post('https://api.deepgram.com/v1/speak?model=aura-2-thalia-en&encoding=linear16&sample_rate=24000',
      headers={'Authorization':'Token '+key,'Content-Type':'application/json'},
      json={'text':shot['audio']['cue']},timeout=45)
    rr.raise_for_status();raw.write_bytes(rr.content)
    rawdur=probe(raw);target=max(2.0,shot['duration_seconds']-.95);tempo=max(1.0,rawdur/target)
    filt=tempo_chain(tempo)+',highpass=f=95,equalizer=f=470:t=q:w=1:g=-2,loudnorm=I=-20:TP=-4:LRA=6'
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(raw),'-af',filt,'-ar',str(SR),'-ac','1',str(out)],check=True)
    print('VOICE',sid,round(rawdur,2),'tempo',round(tempo,3),flush=True)
else:
  raise SystemExit('Deepgram narration credential unavailable')

# score.wav — deterministic evolving harmonic bed
score=A/'score.wav'
if not score.exists():
  roots=[55,65.4,73.4,82.4,61.7,55,69.3,73.4,49,55,65.4]
  with wave.open(str(score),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
    for sec in range(DUR):
      tt=sec+np.arange(SR)/SR;root=roots[min(len(roots)-1,int(sec/(DUR/len(roots))))]
      amp=.020
      if 35<=sec<=43 or 82<=sec<=86:amp=.006
      if sec>=147:amp*=np.clip((149.3-tt)/2.0,0,1)
      m=np.zeros(SR)
      for ratio,gain in [(1,.55),(1.5,.38),(2,.26),(2.5,.16)]:
        m+=amp*gain*np.sin(2*np.pi*root*ratio*tt+.18*np.sin(tt*.27+ratio))
      pulse=np.exp(-((tt*1.35)%1)*9)*np.sin(2*np.pi*root*2*tt)*(.008 if sec<110 else .012)
      m+=pulse
      l=m;r=m*.97+.002*np.sin(2*np.pi*root*3*tt)
      st=np.stack([l,r],axis=1)
      w.writeframes((np.clip(st,-.3,.3)*32767).astype('<i2').tobytes())

# ambience.wav — quiet physical/digital bed that changes by shot family
amb=A/'ambience.wav'
if not amb.exists():
  rng=np.random.default_rng(992)
  with wave.open(str(amb),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
    low=0.0
    for sec in range(DUR):
      tt=sec+np.arange(SR)/SR
      noise=rng.normal(0,1,SR);smooth=np.convolve(noise,np.ones(64)/64,mode='same')
      hum=.004*np.sin(2*np.pi*58*tt)+.002*np.sin(2*np.pi*116*tt)
      a=hum+smooth*.004
      if 65<=sec<88 or 142<=sec:a*=.38
      if 82<=sec<86:a*=.08
      st=np.stack([a,a*.96],axis=1);w.writeframes((np.clip(st,-.2,.2)*32767).astype('<i2').tobytes())

# narration stem
nar=A/'narration.wav'
if not nar.exists():
  cmd=['ffmpeg','-y','-v','error','-f','lavfi','-i',f'anullsrc=r={SR}:cl=stereo:d={DUR}']
  voices=[];filters=[];mix=['[0:a]']
  for idx,shot in enumerate(plan['shots'],1):
    f=A/f"{shot['id']}-voice.wav";cmd+=['-i',str(f)]
    start=shot['start_seconds']+min(.7,max(.35,shot['duration_seconds']*.08))
    filters.append(f'[{idx}:a]adelay={int(start*1000)}:all=1[v{idx}]');mix.append(f'[v{idx}]')
  filters.append(''.join(mix)+f'amix=inputs={len(mix)}:normalize=0:duration=first[n]')
  cmd+=['-filter_complex',';'.join(filters),'-map','[n]','-t',str(DUR),'-ar',str(SR),'-ac','2','-c:a','pcm_s16le',str(nar)]
  subprocess.run(cmd,check=True)

# effects stem from local Core Commons
fx=A/'effects.wav'
if not fx.exists():
  ev=[e for e in timeline['events'] if e.get('asset_id','').startswith('audio.core-procedural:')]
  cmd=['ffmpeg','-y','-v','error','-f','lavfi','-i',f'anullsrc=r={SR}:cl=stereo:d={DUR}'];filters=[];mix=['[0:a]']
  manifest=json.loads((ROOT/'assets/audio-commons.json').read_text());idxmap={a['id']:ROOT/a['file'] for a in manifest['assets']}
  for j,e in enumerate(ev,1):
    aid=e['asset_id'].split(':',1)[1];cmd+=['-i',str(idxmap[aid])]
    gain=float(e.get('gain_db',-8));delay=int(float(e['at_seconds'])*1000)
    filters.append(f'[{j}:a]volume={gain}dB,adelay={delay}:all=1[f{j}]');mix.append(f'[f{j}]')
  filters.append(''.join(mix)+f'amix=inputs={len(mix)}:normalize=0:duration=first[f]')
  cmd+=['-filter_complex',';'.join(filters),'-map','[f]','-t',str(DUR),'-ar',str(SR),'-ac','2','-c:a','pcm_s16le',str(fx)]
  subprocess.run(cmd,check=True)

master=A/'master.wav'
subprocess.run(['ffmpeg','-y','-v','error','-i',str(nar),'-i',str(score),'-i',str(amb),'-i',str(fx),
 '-filter_complex','[0:a]volume=1.0[n];[1:a]volume=.75[s];[2:a]volume=.7[m];[3:a]volume=1.0[f];[n][s][m][f]amix=inputs=4:normalize=0:duration=longest,loudnorm=I=-17:TP=-2:LRA=6[a]',
 '-map','[a]','-t',str(DUR),'-ar',str(SR),'-ac','2','-c:a','pcm_s16le',str(master)],check=True)
print('AUDIO_READY',master)
