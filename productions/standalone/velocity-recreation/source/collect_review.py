"""Collect candidate-bound review evidence. Does not grant perceptual approval."""
from pathlib import Path
import json,subprocess,hashlib,time
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];Q=P/'review';M=P/'final/velocity.mp4'
def run(args):subprocess.run(args,cwd=ROOT,check=True)
# Caller starts this only after assembly completes.
sha=hashlib.sha256(M.read_bytes()).hexdigest()
run(['python','scripts/creativeqactl.py','analyze',str(M),str(P/'source/execution-plan.json'),str(Q/'experience'),'--layout',str(P/'source/layout-qa.json'),'--timeline',str(P/'source/av-timeline.json'),'--stems-dir',str(P/'audio')])
run(['python','scripts/creativeqactl.py','validate-bundle',str(Q/'experience/creative-qa.json')])
frames=sorted((Q/'experience/phone-frames').glob('*.jpg'))
for page in range((len(frames)+19)//20):
 im=Image.new('RGB',(1280,1000),(8,12,19));dr=ImageDraw.Draw(im)
 for k,f in enumerate(frames[page*20:(page+1)*20]):
  im.paste(Image.open(f).resize((320,180)),((k%4)*320,(k//4)*200));dr.text(((k%4)*320+5,(k//4)*200+181),f.stem,fill='white')
 im.save(Q/f'authored-page-{page+1}.jpg',quality=92)
# Full timeline at 1-second intervals, and exact adjacent frames at each cut.
review=Q/'screening';review.mkdir(exist_ok=True)
run(['ffmpeg','-v','error','-i',str(M),'-vf',r'select=not(mod(n\,24)),scale=320:180','-fps_mode','vfr','-q:v','3',str(review/'sample-%03d.jpg')])
for page in range(6):
 im=Image.new('RGB',(1280,1000),(8,12,19));dr=ImageDraw.Draw(im)
 for k in range(20):
  i=page*20+k;f=review/f'sample-{i+1:03}.jpg'
  im.paste(Image.open(f),((k%4)*320,(k//4)*200));dr.text(((k%4)*320+8,(k//4)*200+181),f'{i:03d}.000s / frame {i*24}',fill='white')
 im.save(review/f'page-{page+1}.jpg',quality=90)
cuts=[8,15,21,26,30,34,38,43,51,58,66,73,78,82,86,90,95,102,110]
for page in range(4):
 cs=cuts[page*5:(page+1)*5];im=Image.new('RGB',(960,len(cs)*290),(8,12,19));dr=ImageDraw.Draw(im)
 for k,c in enumerate(cs):
  for j,t in enumerate([c-1/24,c]):
   f=review/f'cut-{c}-{j}.jpg'
   run(['ffmpeg','-v','error','-ss',str(t),'-i',str(M),'-frames:v','1','-vf','scale=480:270','-y',str(f)])
   im.paste(Image.open(f),(j*480,k*290));dr.text((j*480+8,k*290+270),f'{t:.5f}s',fill='white')
 im.save(review/f'cuts-{page+1}.jpg',quality=90)
(Q/'evidence-index.json').write_text(json.dumps({'candidate_sha256':sha,'sampled_screening_pages':6,'cuts':cuts,'continuous_video':'UNVERIFIED','auditory':'UNAVAILABLE','synchronized_av':'UNVERIFIED','note':'Still and sampled images do not constitute end-to-end viewing.'},indent=2))
print('EVIDENCE_READY',sha,flush=True)
