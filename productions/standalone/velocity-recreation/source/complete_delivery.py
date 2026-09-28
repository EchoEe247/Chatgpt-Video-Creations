from pathlib import Path
import time,json,subprocess
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
deadline=time.time()+1200
while not all((P/'renders-v3'/f'shot-{i:02}.mp4').exists() for i in range(1,21)):
 if time.time()>deadline:raise RuntimeError('Render not completed within bound')
 time.sleep(4)
r=subprocess.run(['python',str(P/'source/finish.py')],cwd=ROOT)
print('FINISH_EXIT',r.returncode,flush=True)
# Preserve and report a cinematic gate failure; it must not suppress evidence collection.
technical=json.loads((P/'review/technical-qa.json').read_text())
if not technical['pass']:raise RuntimeError('Technical QA failed; stop evidence delivery')
subprocess.run(['python',str(P/'source/collect_review.py')],cwd=ROOT,check=True)
print('DELIVERY_EVIDENCE_READY',flush=True)
