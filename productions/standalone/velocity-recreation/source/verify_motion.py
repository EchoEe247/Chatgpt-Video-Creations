"""Numerical evidence; never a replacement for continuous viewing."""
from pathlib import Path
import json,math
import numpy as np
P=Path(__file__).resolve().parents[1]
profile=json.loads((P/'source/speed-profile.json').read_text())
dt=1/240;t=np.arange(0,120+dt,dt);v=np.ones_like(t)*30
for seg in profile['segments']:v[(t>=seg['start'])&(t<seg['end'])]=seg['speed_mps']
for i,seg in enumerate(profile['segments'][1:],1):
 c=seg['start'];m=(t>=c-4)&(t<=c+4);q=(t[m]-c+4)/8;q=q*q*(3-2*q);v[m]=profile['segments'][i-1]['speed_mps']+(seg['speed_mps']-profile['segments'][i-1]['speed_mps'])*q
y=np.concatenate(([0],np.cumsum((v[:-1]+v[1:])*.5*dt)))
traffic=json.loads((P/'source/motion-telemetry.json').read_text())['traffic']
collision=[];near=[];minhead=1e9
for i,a in enumerate(traffic):
 ya=a['base']+a['speed_mps']*t
 if a['lane']==0:
  gap=float(np.min(np.abs(ya-y)));minhead=min(minhead,gap)
  if gap<5:collision.append(['hero',i,gap])
 for j,b in enumerate(traffic[:i]):
  if a['lane']==b['lane']:
   gap=float(np.min(np.abs(ya-b['base']-b['speed_mps']*t)));minhead=min(minhead,gap)
   if gap<5:collision.append([i,j,gap])
cuts=[0,8,15,21,26,30,34,38,43,51,58,66,73,78,82,86,90,95,102,110,120]
setups=[(-12,4.8,3.4),(-8,-3.4,1.6),(-19,10,11),(0,7.1,1.45),(-7,2.8,1.2),(8,-2.5,1.55),(-10,-4.2,2.6),(.4,-2.7,.65),(-34,4,2.2),(-12,5,4),(0,-7.1,1.5),(-23,-11,13),(8,2.4,1.3),(1.15,0,1.52),(-7,-1.8,1.1),(1.25,1.9,.58),(-31,-4,2),(-10,4,2.8),(0,7.2,1.45),(-17,-6,6)]
for i,(along,side,z) in enumerate(setups):
 for j,a in enumerate(traffic):
  if abs(a['lane']*3.65-side)<1.05 and z<1.65:
   m=(t>=cuts[i])&(t<cuts[i+1]);d=a['base']+a['speed_mps']*t[m]-y[m]-along
   if np.any(abs(d)<2.6):near.append({'shot':i+1,'traffic':j,'time':float(t[m][np.argmin(abs(d))])})
report={"schema_version":1,"claim_type":"measured source trajectory","duration":120,"sample_hz":240,"distance_m":float(y[-1]),"speed_range_mps":[float(v.min()),float(v.max())],"maximum_acceleration_mps2":float(abs(np.diff(v)/dt).max()),"same_lane_minimum_center_gap_m":minhead,"traffic_collision_candidates":collision,"camera_intersection_candidates":near,"speed_windows":[{"time":q,"mps":float(np.interp(q,t,v))} for q in [0,25,29,33,43,47,66,70,74,95,99,119]],"limitations":["Source checks are not perceived motion or audiovisual sync.","Simplified lane-space bounding boxes; world road bends are small."]}
(P/'review/motion-qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
