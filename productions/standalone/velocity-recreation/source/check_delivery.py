from pathlib import Path
import struct,json,subprocess,hashlib
P=Path(__file__).resolve().parents[1];M=P/'final/velocity.mp4'
atoms=[]
with M.open('rb') as f:
 while True:
  at=f.tell();b=f.read(8)
  if len(b)<8:break
  size,typ=struct.unpack('>I4s',b)
  if size==1:size=struct.unpack('>Q',f.read(8))[0]
  if size==0:size=M.stat().st_size-at
  atoms.append({'type':typ.decode('ascii','replace'),'offset':at,'size':size})
  if size<8:raise ValueError('bad atom')
  f.seek(at+size)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(M)]))
v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
order=[x['type'] for x in atoms]
checks={'duration_120':abs(float(probe['format']['duration'])-120)<.01,'frames_2880':int(v['nb_frames'])==2880,'resolution':(v['width'],v['height'])==(960,540),'fps_24':v['r_frame_rate']=='24/1','h264':v['codec_name']=='h264','yuv420p':v['pix_fmt']=='yuv420p','aac_stereo_48k':a['codec_name']=='aac' and a['channels']==2 and int(a['sample_rate'])==48000,'faststart':order.index('moov')<order.index('mdat')}
d={'candidate_sha256':hashlib.sha256(M.read_bytes()).hexdigest(),'checks':checks,'pass':all(checks.values()),'mp4_atoms':atoms}
(P/'review/delivery-qa.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
if not d['pass']:raise SystemExit(1)
