from pathlib import Path
import json,os,re,requests,subprocess,wave,numpy as np
P=Path(__file__).resolve().parent
scenes=json.loads((P/'story.json').read_text())
(P/'audio').mkdir(exist_ok=True)
key=os.environ.get('DEEPGRAM_API_KEY','')
if not key:
    s=(Path.home()/'.deepgram_env').read_text()
    m=re.search(r'(?:export\s+)?DEEPGRAM_API_KEY\s*=\s*["\x27]?([^\s"\x27]+)',s)
    key=m.group(1) if m else ''
assert key,'Narration credential not configured'
for i,sc in enumerate(scenes):
    out=P/'audio'/f'voice_{i:02}.wav'
    if out.exists(): continue
    r=requests.post('https://api.deepgram.com/v1/speak?model=aura-2-thalia-en&encoding=linear16&sample_rate=24000',headers={'Authorization':'Token '+key,'Content-Type':'application/json'},json={'text':sc['text']},timeout=50)
    r.raise_for_status()
    raw=P/'audio'/f'raw_{i:02}.wav'; raw.write_bytes(r.content)
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(raw)]))
    tempo=max(1,dur/12.7)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'atempo={tempo},highpass=f=95,equalizer=f=470:t=q:w=1:g=-2,loudnorm=I=-20:TP=-4:LRA=6','-ar','32000','-ac','1',str(out)],check=True)
    print('VOICE',i,round(dur,2),'tempo',round(tempo,3),flush=True)
SR=32000; DUR=180
# Compose in short blocks to keep RAM stable.
with wave.open(str(P/'audio'/'score.wav'),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    rng=np.random.default_rng(41)
    for sec in range(DUR):
        t=sec+np.arange(SR)/SR
        part=sec//15
        roots=[110,130.8128,146.8324,110,103.826,110,130.8128,82.4069,110,146.8324,164.8138,146.8324]
        root=roots[part]
        local=t%15; env=np.minimum(1,local/1.5)*np.minimum(1,(15-local)/1.5)
        music=np.zeros(SR)
        # Soft moving harmonic texture, no harsh broadband drone.
        for ratio,amp in [(1,.016),(1.5,.012),(2,.008),(2.5,.005)]:
            music+=amp*np.sin(2*np.pi*root*ratio*t+0.22*np.sin(t*.4))
        beat=(t*1.6)%1
        if part in [2,3,4,6,8,9,10]:
            music+=.025*np.exp(-beat*12)*np.sin(2*np.pi*(root*2)*t)
        bellphase=(t*0.4)%1
        music+=.014*np.exp(-bellphase*5)*np.sin(2*np.pi*root*4*t)
        # Quiet transition swells; blackout has near-silence, not a blast.
        swell=np.exp(-((local-14.3)/.45)**2)*rng.normal(0,.003,SR)
        music=(music+swell)*env
        if part==7: music*=.25
        if sec<3: music*=np.minimum(1,t/3)
        if sec>176: music*=np.clip((180-t)/3,0,1)
        stereo=np.stack([music, music*.98+.002*np.sin(2*np.pi*root*3*t)*env],axis=1)
        w.writeframes((np.clip(stereo,-.3,.3)*32767).astype('<i2').tobytes())
# Narration timeline; exact subtitle cues track the trimmed voice clips.
cmd=['ffmpeg','-v','error','-y','-i',str(P/'audio'/'score.wav')]
for i in range(12): cmd+=['-i',str(P/'audio'/f'voice_{i:02}.wav')]
filters=[]; ins=['[0:a]']
cues=[]
for i,sc in enumerate(scenes):
    delay=int((i*15+1.15)*1000)
    filters.append(f'[{i+1}:a]adelay={delay}:all=1[v{i}]');ins.append(f'[v{i}]')
    d=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(P/'audio'/f'voice_{i:02}.wav')]))
    words=sc['text'].split(); groups=[words[j:j+9] for j in range(0,len(words),9)]
    k=0
    for g in groups:
        a=sc['start']+1.15+d*k/len(words); k+=len(g); b=sc['start']+1.15+d*k/len(words)
        cues.append((a,b,' '.join(g)))
filters.append(''.join(ins)+f'amix=inputs=13:normalize=0:duration=first,alimiter=limit=0.79:level=false[a]')
cmd+=['-filter_complex',';'.join(filters),'-map','[a]','-ar','48000','-ac','2','-c:a','pcm_s16le',str(P/'audio'/'master.wav')]
subprocess.run(cmd,check=True)
def stamp(s):
    return f'{int(s//3600):02}:{int(s//60)%60:02}:{s%60:06.3f}'
(P/'subtitles.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f'{stamp(a)} --> {stamp(b)}\n{x}' for a,b,x in cues)+'\n')
print('AUDIO_READY',flush=True)
