"""Package the completed candidate and report; never grant assistant acceptance."""
from pathlib import Path
import json,hashlib,zipfile,datetime
P=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
master=P/'final/velocity.mp4';candidate=sha(master)
for name in ['technical-qa.json','cinematic-qa.json','motion-qa.json']:
 p=P/'review'/name;d=json.loads(p.read_text());d['candidate_sha256']=candidate;p.write_text(json.dumps(d,indent=2))
prov=P/'source/provenance.json';d=json.loads(prov.read_text());d['vendored_asset_hashes']={str(p.relative_to(P)):sha(p) for p in sorted((P/'assets').glob('*')) if p.is_file()};d['production_source_hashes']={str(p.relative_to(P)):sha(p) for p in sorted((P/'source').glob('*.py'))};prov.write_text(json.dumps(d,indent=2))
technical=json.loads((P/'review/technical-qa.json').read_text());cinematic=json.loads((P/'review/cinematic-qa.json').read_text())
manifest=json.loads((P/'production.json').read_text())
manifest['status']='REFINEMENT_REQUIRED' if not cinematic['pass'] else 'VERIFICATION_REQUIRED'
manifest['artifacts'].update(candidate_master=str(master),candidate_sha256=candidate,creative_qa=str(P/'review/experience/creative-qa.json'),studio_review=str(P/'review/final-screening.json'),review_pack=str(P/'review'))
manifest['gates']['technical'].update(status='PASS' if technical['pass'] else 'FAIL',candidate_sha256=candidate,evidence=str(P/'review/technical-qa.json'))
manifest['gates']['cinematic']={'status':'PASS' if cinematic['pass'] else 'FAIL','candidate_sha256':candidate,'evidence':str(P/'review/cinematic-qa.json')}
manifest['gates']['assistant'].update(status='PENDING',candidate_sha256=candidate,notes='No assistant perceptual PASS: continuous video, auditory and synchronized A/V remain unavailable on this route; see the cinematic gate for measured image status.')
manifest['studio_review'].update(candidate_sha256=candidate,notes='See candidate-bound review/final-review.md and final-screening.json; no end-to-end screening claimed.')
manifest['workflow'].update(last_action='Master and evidence delivered; explicit perceptual verification gaps retained',escalation_reason='This route cannot hear audio or perceive continuous video; assistant perceptual approval remains pending.')
(P/'production.json').write_text(json.dumps(manifest,indent=2))
files=[]
for folder in ['source','assets']:
 files += [p for p in (P/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
files += [P/x for x in ['README.md','index.html','serve.py','production.json','final/sha256.txt','review/final-review.md','review/final-review.html','review/final-screening.json','review/technical-qa.json','review/delivery-qa.json','review/cinematic-qa.json','review/motion-qa.json','review/evidence-index.json','review/perception-capabilities.json'] if (P/x).exists()]
with zipfile.ZipFile(P/'source-package.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,'velocity-recreation/'+str(p.relative_to(P)))
(P/'delivery-receipt.json').write_text(json.dumps({'candidate_sha256':candidate,'master_bytes':master.stat().st_size,'source_package_bytes':(P/'source-package.zip').stat().st_size,'state':manifest['status'],'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
print(json.dumps({'candidate_sha256':candidate,'master_bytes':master.stat().st_size,'state':manifest['status']},indent=2))