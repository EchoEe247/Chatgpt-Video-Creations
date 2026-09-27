#!/usr/bin/env python3
"""RIDGELINE: deterministic, locally rendered 3D MTB film. No riding footage."""
import os,sys,math,json,time,subprocess,random
os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE","1")
os.environ.setdefault("LP_NUM_THREADS","3")
from pathlib import Path
import numpy as np
import moderngl
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1]
W,H,FPS,DURATION=960,540,24,132
R=P/"renders"; R.mkdir(exist_ok=True)
rng=random.Random(43)
def norm(a):
 a=np.array(a,dtype="f4"); return a/max(np.linalg.norm(a),1e-8)
def view(eye,target):
 f=norm(np.array(target)-eye); s=norm(np.cross(f,[0,0,1])); u=np.cross(s,f)
 m=np.eye(4,dtype="f4"); m[0,:3]=s;m[1,:3]=u;m[2,:3]=-f;m[:3,3]=-m[:3,:3]@eye
 return m
def persp(fov,aspect,near=.06,far=650):
 f=1/math.tan(fov/2); m=np.zeros((4,4),dtype="f4");m[0,0]=f/aspect;m[1,1]=f;m[2,2]=(far+near)/(near-far);m[2,3]=2*far*near/(near-far);m[3,2]=-1;return m
def mat(pos=(0,0,0),scale=(1,1,1)):
 m=np.eye(4,dtype="f4");m[:3,3]=pos;m[0,0],m[1,1],m[2,2]=scale;return m
JUMPS=(167,315,474,576)
def trailx(y): return 11*np.sin(y*.019)+5*np.sin(y*.047)
def base(y): return 42-.055*y+1.3*np.sin(y*.031)+.65*np.sin(y*.079)
def jump_feature(y):
 # Visible dirt kicker/drop: the rider only leaves the ground at an authored trail feature.
 yy=np.asarray(y,dtype="f4"); out=np.zeros_like(yy)
 for jy in JUMPS:
  d=yy-jy
  up=np.where((d>=-7)&(d<0),1.65*(1-np.cos((d+7)/7*math.pi))*.5,0)
  down=np.where((d>=0)&(d<1.8),1.65*(1-d/1.8),0)
  out=np.maximum(out,np.maximum(up,down))
 return float(out) if out.ndim==0 else out
def height(x,y):
 d=x-trailx(y); a=np.abs(d)
 edge=np.maximum(a-2.0,0)
 hills=7*np.sin(x*.045+y*.013)+4*np.sin(y*.027-x*.061)
 terrain=base(y)+np.minimum(edge/18,1)*(hills+edge*.32)
 # Kicker is localized to the trail corridor instead of lifting the whole mountain.
 terrain+=jump_feature(y)*np.exp(-(a/4.0)**4)
 rough=(np.sin(x*1.43+y*.71)*np.sin(y*1.71-x*.27)*.29+np.sin(x*3.1+y*2.7)*.065)*np.minimum(edge/2,1)
 return terrain+rough
def path(y): return np.array([trailx(y),y,base(y)+jump_feature(y)],dtype="f4")

SPEED_SEGMENTS=((0,12,.8),(12,36,4.5),(36,60,7.5),(60,84,4.8),(84,114,8.0),(114,132,5.8))
def route_y(t):
 y=6.0
 for a,b,v in SPEED_SEGMENTS:
  if t<=a: break
  y+=max(0.0,min(t,b)-a)*v
  if t<b: break
 return y
def speed_intensity(t):
 # Calm/flow sections remain, but two attack windows ramp into a high-focus descent.
 def pulse(a,b,edge=3.0):
  return min(max((t-a)/edge,0.0),1.0)*min(max((b-t)/edge,0.0),1.0)
 return max(pulse(36,60),pulse(84,114))
ctx=moderngl.create_standalone_context(backend="egl")
print("RENDERER",ctx.info["GL_RENDERER"],flush=True)
prog=ctx.program(vertex_shader="""#version 330
in vec3 in_pos; in vec3 in_norm; in vec3 in_color;
uniform mat4 mvp; in mat4 instance_model; in vec3 instance_tint; in float instance_kind;
out vec3 wp; out vec3 normal; out vec3 vc; flat out int kind;
void main(){vec4 w=instance_model*vec4(in_pos,1);wp=w.xyz;normal=mat3(instance_model)*in_norm;vc=in_color*instance_tint;kind=int(instance_kind);gl_Position=mvp*w;}
""",fragment_shader="""#version 330
in vec3 wp; in vec3 normal; in vec3 vc;
uniform vec3 eye; flat in int kind; uniform sampler2D rock; uniform sampler2D forest;
out vec4 frag;
float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
void main(){
 vec3 n=normalize(normal); vec3 sun=normalize(vec3(-.55,-.35,.8));
 float diffuse=max(dot(n,sun),0.0);
 vec3 c=vc;
 if(kind==1){vec3 tex=texture(rock,wp.xy*.24).rgb;if(vc.g>vc.r){tex=texture(forest,wp.xy*.35).rgb;c=mix(c,tex*vec3(.50,.68,.43),.8);}else{c=mix(c,tex*vec3(.82,.72,.56),.85);}}
 float grain=hash(floor(wp*50.0));
 if(kind==1||kind==2)c*=.92+.15*grain;
 vec3 light=vec3(.24,.29,.32)+diffuse*vec3(.93,.78,.56);
 float spec=pow(max(dot(reflect(-sun,n),normalize(eye-wp)),0.0),48.0);
 c=c*light+((kind==3)?spec*.43:spec*.015);
 float dist=length(eye-wp);float fog=1.0-exp(-dist*.0032);
 c=mix(c,vec3(.48,.60,.66),fog);
 c=c/(c+vec3(.42)); c=pow(c,vec3(.85));
 frag=vec4(c,1);
}
""")
sky=ctx.program(vertex_shader="""#version 330
out vec2 uv;void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);uv=p;gl_Position=vec4(p*2.-1.,.9999,1);}
""",fragment_shader="""#version 330
in vec2 uv;out vec4 frag;
void main(){vec3 c=mix(vec3(.70,.74,.71),vec3(.16,.34,.49),smoothstep(0.,1.,uv.y));
float sun=exp(-length((uv-vec2(.23,.76))*vec2(1.6,1.))*20.);c+=vec3(.55,.37,.15)*sun;frag=vec4(c,1);}
""")
skyvao=ctx.vertex_array(sky,[])
fbo=ctx.simple_framebuffer((W,H),components=3); fbo.use()
texim=Image.open(P/"assets/rock.jpg").convert("RGB"); tex=ctx.texture(texim.size,3,texim.tobytes());tex.build_mipmaps();tex.use(0);prog["rock"]=0
im2=Image.open(P/"assets/forest.jpg").convert("RGB");tx2=ctx.texture(im2.size,3,im2.tobytes());tx2.build_mipmaps();tx2.use(1);prog["forest"]=1
instance_buffer=ctx.buffer(reserve=1024*80)
queue={}
def mesh(verts):
 a=np.asarray(verts,dtype="f4").reshape(-1,9); b=ctx.buffer(a.tobytes());return ctx.vertex_array(prog,[(b,"3f 3f 3f","in_pos","in_norm","in_color"),(instance_buffer,"16f 3f 1f /i","instance_model","instance_tint","instance_kind")])
def tri(out,a,b,c,col,ns=None):
 n=norm(np.cross(np.array(b)-a,np.array(c)-a))
 for i,v in enumerate([a,b,c]):out.append([*v,*(ns[i] if ns else n),*col])
def sphere(slices=16,rings=10):
 out=[]
 for j in range(rings):
  a0=-math.pi/2+j*math.pi/rings;a1=a0+math.pi/rings
  for i in range(slices):
   b0=i*2*math.pi/slices;b1=b0+2*math.pi/slices
   vs=[(math.cos(a)*math.cos(b),math.cos(a)*math.sin(b),math.sin(a)) for a,b in [(a0,b0),(a0,b1),(a1,b1),(a1,b0)]]
   tri(out,*vs[:3],(1,1,1),vs[:3]);tri(out,vs[0],vs[2],vs[3],(1,1,1),[vs[0],vs[2],vs[3]])
 return mesh(out)
def cylinder(n=12):
 out=[]
 for i in range(n):
  a=i*math.tau/n;b=(i+1)*math.tau/n
  v=[(math.cos(a),math.sin(a),0),(math.cos(b),math.sin(b),0),(math.cos(b),math.sin(b),1),(math.cos(a),math.sin(a),1)]
  ns=[(x,y,0) for x,y,z in v]
  tri(out,*v[:3],(1,1,1),ns[:3]);tri(out,v[0],v[2],v[3],(1,1,1),[ns[0],ns[2],ns[3]])
 return mesh(out)
def torus(major=1,minor=.08,n=48,k=8):
 out=[]
 for i in range(n):
  for j in range(k):
   vs=[];ns=[]
   for ii,jj in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]:
    a=ii*math.tau/n;b=jj*math.tau/k
    vs.append(((major+minor*math.cos(b))*math.cos(a),(major+minor*math.cos(b))*math.sin(a),minor*math.sin(b)))
    ns.append((math.cos(b)*math.cos(a),math.cos(b)*math.sin(a),math.sin(b)))
   tri(out,*vs[:3],(1,1,1),ns[:3]);tri(out,vs[0],vs[2],vs[3],(1,1,1),[ns[0],ns[2],ns[3]])
 return mesh(out)
ball=sphere();tube=cylinder();tire=torus(1,.11);rim=torus(1,.032)
# Terrain: a connected mountain slope with a continuous explicit singletrack.
out=[]
ys=np.arange(-80,880,2.5); ds=np.concatenate([np.arange(-150,-14,6),np.arange(-14,14.1,1.4),np.arange(20,151,6)])
for j in range(len(ys)-1):
 for i in range(len(ds)-1):
  v=[]
  for jj,ii in [(j,i),(j,i+1),(j+1,i+1),(j+1,i)]:
   y=ys[jj];x=trailx(y)+ds[ii];v.append((x,y,float(height(x,y))))
  d=(ds[i]+ds[i+1])/2
  ym=(ys[j]+ys[j+1])*.5
  if jump_feature(ym)>.08 and abs(d)<4.2:col=(.60,.40,.22)
  elif abs(d)<2.2:col=(.49,.36,.22)
  elif abs(d)<4:col=(.27,.29,.16)
  elif abs(d)>40:col=(.32,.34,.28)
  else:col=(.24,.29,.15)
  col=tuple(c*rng.uniform(.88,1.1) for c in col)
  tri(out,*v[:3],col);tri(out,v[0],v[2],v[3],col)
def splitmesh(vertices):
 a=np.asarray(vertices,dtype="f4").reshape(-1,3,9);bins=np.floor(a[:,:,1].mean(axis=1)/50).astype(int)
 return [(k*50+25,mesh(a[bins==k])) for k in sorted(set(bins))]
terrain=splitmesh(out); print("TERRAIN",len(out),flush=True)
# Trees: irregular multi-tier firs, trunks and sloping crowns, baked geometry.
out=[]
for k in range(950):
 y=rng.uniform(-35,815); d=rng.choice([-1,1])*rng.uniform(5,90);x=trailx(y)+d
 # expose the middle rocky ridge and keep camera corridors open
 if 235<y<370 and abs(d)<45:continue
 z=float(height(x,y)); h=rng.uniform(5,13);rad=h*.19
 for tier in range(7):
  zz=z+h*(.17+tier*.115);rr=rad*(1-tier*.115);hh=h*.32
  n=23
  for i in range(n):
   a=i*math.tau/n; b=(i+1)*math.tau/n
   rr=rad*(1-tier*.115)*rng.uniform(.72,1.12)
   c=(.075+rng.random()*.025,.16+rng.random()*.055,.095+rng.random()*.015)
   tri(out,(x+rr*math.cos(a),y+rr*math.sin(a),zz+rng.uniform(-.35,.2)),(x+rr*math.cos(b),y+rr*math.sin(b),zz+rng.uniform(-.45,.1)),(x+.1,y,zz+hh),c)
 for i in range(6):
  a=i*math.tau/6;b=(i+1)*math.tau/6;r=.12
  v=[(x+r*math.cos(a),y+r*math.sin(a),z),(x+r*math.cos(b),y+r*math.sin(b),z),(x+r*.5*math.cos(b),y+r*.5*math.sin(b),z+h*.8),(x+r*.5*math.cos(a),y+r*.5*math.sin(a),z+h*.8)]
  tri(out,*v[:3],(.20,.12,.065));tri(out,v[0],v[2],v[3],(.20,.12,.065))
trees=splitmesh(out)
# Stones and grass at trail margins, small geometry supports speed/parallax.
out=[]
for k in range(3600):
 y=rng.uniform(-30,790);d=rng.choice([-1,1])*rng.uniform(2.25,13);x=trailx(y)+d;z=float(height(x,y));r=rng.uniform(.05,.37)
 a=(x-r,y-r,z);b=(x+r,y-r*.7,z+.03);c=(x+r*.5,y+r,z);d1=(x-r*.8,y+r*.7,z);top=(x,y,z+r*.9)
 for v in [(a,b,top),(b,c,top),(c,d1,top),(d1,a,top)]:tri(out,*v,(.40,.39,.33))
rocks=splitmesh(out)
# Distant irregular mountains, not a backdrop image.
out=[]
for side in [-1,1]:
 for y in range(-150,1200,90):
  x=side*rng.uniform(170,250);z=base(y)+rng.uniform(50,120);w=rng.uniform(65,130)
  col=(.29,.37,.38)
  tri(out,(x-w,y-100,base(y)-25),(x+w,y-100,base(y)-25),(x,y,z),col)
  tri(out,(x+w,y-100,base(y)-25),(x,y+110,base(y)-25),(x,y,z),(.22,.29,.31))
mountains=mesh(out)
I=np.eye(4,dtype="f4")
def draw(obj,M=I,color=(1,1,1),kind=0):
 queue.setdefault(obj,[]).append([*np.asarray(M,dtype="f4").T.ravel(),*color,float(kind)])
def seg(a,b,r,color,root=I,kind=0,r2=None):
 a=np.array(a,dtype="f4"); b=np.array(b,dtype="f4");v=b-a;length=np.linalg.norm(v);z=norm(v);x=norm(np.cross(z,[0,1,0] if abs(z[1])<.9 else [1,0,0]));y=np.cross(z,x)
 M=np.eye(4,dtype="f4");M[:3,0]=x*r;M[:3,1]=y*r;M[:3,2]=z*length;M[:3,3]=a;draw(tube,root@M,color,kind)
def ell(pos,scale,color,root=I):draw(ball,root@mat(pos,scale),color)
# Route speed, authored trail features and airborne motion remain deterministic.
def riding(t):
 y=route_y(t)
 p=path(y); tangent=norm(path(y+.1)-path(y-.1));right=norm(np.cross(tangent,[0,0,1]));up=norm(np.cross(right,tangent))
 turn=(trailx(y+1)-2*trailx(y)+trailx(y-1));lean=np.clip(-turn*(7+5*speed_intensity(t)),-.45,.45)
 hop=0.;pitch=0.
 for jy in JUMPS:
  q=(y-jy)/10
  if 0<q<1:hop+=2.15*4*q*(1-q);pitch+=.22*(1-2*q)
 bump=.017*math.sin(y*5)+.013*math.sin(y*9)
 p[2]+=hop+bump
 U=up*math.cos(lean)+right*math.sin(lean);Rr=right*math.cos(lean)-up*math.sin(lean)
 F=tangent*math.cos(pitch)+U*math.sin(pitch);U=U*math.cos(pitch)-tangent*math.sin(pitch)
 root=np.eye(4,dtype="f4");root[:3,0]=Rr;root[:3,1]=F;root[:3,2]=U;root[:3,3]=p
 return y,p,tangent,right,root,hop
def bike(root,t,y,hop):
 black=(.025,.030,.031);rubber=(.018,.019,.018);red=(.63,.085,.035);metal=(.46,.49,.46);gold=(.53,.32,.08)
 # 29-inch wheels, spinning spoke field, tread blocks and brake rotors.
 for wy in [-.57,.65]:
  C=np.array([0,wy,.365]); rot=np.eye(4,dtype="f4");rot[:3,:3]=np.array([[0,0,1],[1,0,0],[0,1,0]])
  M=mat(C,(.35,.35,.35))@rot
  draw(tire,root@M,rubber);draw(rim,root@(mat(C,(.307,.307,.307))@rot),metal,3)
  ang=-y/.35
  for j in range(20):
   a=ang+j*math.tau/20
   seg((-.028,wy,.365),(.0,wy+math.sin(a)*.305,.365+math.cos(a)*.305),.0035,metal,root,3)
  for j in range(26):
   a=ang+j*math.tau/26
   ell((0,wy+math.sin(a)*.386,.365+math.cos(a)*.386),(.045,.018,.014),black,root)
  draw(rim,root@(mat((-.054,wy,.365),(.105,.105,.105))@rot),metal,3)
  seg((-.08,wy,.365),(.08,wy,.365),.035,metal,root,3)
 A=(0,-.57,.365);B=(0,-.05,.32);C=(0,-.22,.87);D=(0,.45,.94);E=(0,.65,.365)
 for a,b,r in [(A,B,.024),(A,C,.022),(B,C,.042),(B,D,.048),(C,D,.038)]:seg(a,b,r,red,root,3)
 for x in [-.075,.075]:
  seg((x,.45,.92),(x,.65,.365),.026,black,root,3)
  seg((x,.45,.83),(x,.57,.57),.022,gold,root,3)
  seg((x,-.56,.37),(x,-.18,.71),.019,black,root)
 seg((0,-.2,.8),(0,-.22,1.0),.024,metal,root,3)
 ell((0,-.25,1.02),(.105,.18,.034),black,root)
 seg((0,.45,.91),(0,.43,1.13),.025,black,root)
 seg((-.37,.41,1.14),(.37,.41,1.14),.019,black,root,3)
 for x in [-.34,.34]:seg((x-.052,.41,1.14),(x+.052,.41,1.14),.027,black,root)
 seg((-.07,-.54,.365),(-.07,-.05,.32),.012,metal,root)
 seg((-.07,-.54,.365),(-.07,-.05,.39),.010,metal,root)
 # coasting posture for technical terrain, alternating pedal phase in the early acceleration.
 phase=t*6 if t<39 else .35+math.sin(t*.5)*.12
 feet=[]
 for side in [-1,1]:
  a=phase+(math.pi if side<0 else 0)
  foot=(side*.17,-.05+math.sin(a)*.155,.36+math.cos(a)*.155)
  feet.append(foot);seg((side*.08,-.05,.36),foot,.014,metal,root,3)
  ell(foot,(.105,.16,.052),black,root)
 # More human silhouette: speed-dependent attack stance, separated clothing masses,
 # anatomical joint placement, exposed lower face/neck, gloves, knee pads and a layered helmet.
 attack=speed_intensity(t)
 crouch=.035*math.sin(y*2.7)-.11*min(hop,1)-.10*attack
 hip=np.array([0,-.31,1.23+crouch])
 should=np.array([0,.10+.08*attack,1.64+crouch-.05*attack])
 head=np.array([0,.285+.09*attack,1.86+crouch-.07*attack])
 v=should-hip; ang=-math.atan2(v[1],v[2]);rot=np.eye(4,dtype="f4");rot[1:3,1:3]=[[math.cos(ang),-math.sin(ang)],[math.sin(ang),math.cos(ang)]]
 # Jersey chest + abdomen, with a darker waist and shorts to break the mannequin silhouette.
 draw(ball,root@mat((hip+should)/2)@rot@mat(scale=(.225,.145,.30)),(.66,.105,.040))
 ell(should+np.array([0,-.015,-.05]),(.245,.16,.16),(.72,.14,.055),root)
 ell(hip,(.205,.19,.15),(.035,.043,.045),root)
 ell(hip+np.array([0,-.03,-.08]),(.23,.18,.14),(.025,.03,.032),root)
 for idx,side in enumerate([-1,1]):
  h=hip+np.array([side*.145,0,0]);k=np.array([side*.225,-.07-.055*attack,.88+crouch*.4]);f=np.array(feet[idx])
  mid=(h+k)/2
  ell(mid,(.105,.13,.25),(.035,.043,.045),root)
  seg(h,k,.080,(.035,.043,.045),root)
  ell(k,(.105,.09,.12),(.065,.073,.072),root)
  calf=(k+f)/2
  ell(calf,(.074,.085,.23),(.10,.115,.11),root)
  seg(k,f,.055,(.10,.115,.11),root)
  shoulder=should+np.array([side*.205,0,0])
  elbow=np.array([side*.34,.13+.04*attack,1.38+crouch*.7])
  hand=np.array([side*.32,.41,1.15])
  ell((shoulder+elbow)/2,(.074,.085,.20),(.60,.095,.037),root)
  seg(shoulder,elbow,.057,(.60,.095,.037),root)
  ell((elbow+hand)/2,(.060,.070,.18),(.10,.115,.115),root)
  seg(elbow,hand,.047,(.10,.115,.115),root)
  ell(hand,(.058,.067,.053),(.025,.03,.03),root)
 # Neck + visible lower face prevent the old floating-helmet/mannequin read.
 neck=should+np.array([0,.035,.17])
 seg(neck,head-np.array([0,.02,.13]),.055,(.52,.30,.20),root)
 ell(head-np.array([0,-.015,.035]),(.135,.17,.145),(.53,.31,.21),root)
 # Full-face helmet shell, chin bar, goggles and visor.
 ell(head+np.array([0,.015,.035]),(.165,.205,.165),(.055,.065,.07),root)
 ell(head+np.array([0,.055,.055]),(.154,.186,.125),(.68,.12,.045),root)
 ell(head+np.array([0,.178,.018]),(.132,.034,.060),(.055,.14,.17),root)
 ell(head+np.array([0,.17,.105]),(.19,.145,.018),(.018,.022,.024),root)
 seg(head+np.array([-.12,.125,-.105]),head+np.array([.12,.125,-.105]),.026,(.025,.03,.03),root)
def speed_cues(root,t,y):
 intensity=speed_intensity(t)
 if intensity<.05:return
 # Wind itself is invisible: use small wind-tossed dust/needles close to the trail,
 # not screen-space speed lines.
 for i in range(28):
  ph=i*1.731+t*(3.4+i*.09)
  side=((i%9)-4)*.34+.10*math.sin(ph)
  z=.08+(i%5)*.12
  fy=.5+(i%7)*.72+((ph*1.7)%1.0)*1.2
  col=(.43+.025*(i%3),.40+.02*(i%2),.28)
  ell((side,fy,z),(.018,.075+.05*intensity,.012),col,root)
 # Rear-wheel dust hugs the actual trail instead of floating with the airborne bike.
 gr=root.copy();gr[:3,3]=path(y)
 for i in range(16):
  ph=t*7.0+i*2.17
  side=.22*math.sin(ph)+(i%3-1)*.14
  back=-.72-(i%7)*.19
  zz=.045+(i%4)*.045
  ell((side,back,zz),(.04+.012*(i%3),.085+.018*(i%2),.025+.009*(i%2)),(.42,.35,.24),gr)

def camera(t,idx,p,f,r):
 mode=[0,1,2,3,4,5,2,6,3,7,2,4,1,5,3,6,7,2,4,3,1,0][idx]
 intensity=speed_intensity(t)
 z=np.array([0,0,1],dtype="f4");u=(t%6)/6
 if mode==0:
  eye=p-f*(18-4*u)+r*(12-5*u)+z*(12-3*u);target=p+f*8;fov=52
 elif mode==1:eye=p-f*7+r*(3+math.sin(t*.3))+z*3.0;target=p+z*.9+f*2;fov=50
 elif mode==2:eye=p+r*4.3-f*.8+z*1.25;target=p+z*1.0;fov=48
 elif mode==3:eye=p-f*3.1+r*.6+z*1.55;target=p+f*4+z*.65;fov=72
 elif mode==4:eye=p+f*4+r*2+z*.85;target=p+z*.95;fov=57
 elif mode==5:eye=p-r*1.5-f*.4+z*.55;target=p+f*.25+z*.5;fov=64
 elif mode==6:eye=p-f*5+r*7+z*5;target=p+z*.8;fov=53
 else:eye=p+f*.95+z*1.75;target=p+f*15+z*.65;fov=83
 # Around a kicker, deliberately show the lip and then the airborne trajectory.
 yy=route_y(t)
 near_jump=None
 for jy in JUMPS:
  if -8 < yy-jy < 10:
   near_jump=yy-jy;break
 if near_jump is not None:
  if near_jump<0:
   eye=p-f*4.2+r*3.8+z*1.20;target=p+f*3.6+z*.55;fov=62
  else:
   eye=p-r*4.6-f*.8+z*1.35;target=p+f*1.8+z*.75;fov=66
 # High-speed windows widen the lens, look farther down-trail and gain controlled inertial shake.
 fov+=9*intensity
 target+=f*(3.3*intensity)
 eye[2]=max(eye[2],height(eye[0],eye[1])+.28)
 eye+=r*((.014+.038*intensity)*math.sin(t*21))+z*((.009+.020*intensity)*math.sin(t*32))
 return eye,target,fov
def render(t):
 idx=min(21,int(t/6));y,p,f,r,root,hop=riding(t);eye,target,fov=camera(t,idx,p,f,r)
 fbo.use();ctx.disable(moderngl.DEPTH_TEST);skyvao.render(vertices=3)
 ctx.enable(moderngl.DEPTH_TEST);ctx.depth_func="<";fbo.clear(depth=1.0,viewport=(0,0,0,0))
 # clear depth alone without touching sky using depth_mask and GL clear? framebuffer.clear viewport zero leaves depth stale.
 ctx.clear(0.40,.55,.64,1,depth=1)
 ctx.disable(moderngl.DEPTH_TEST);skyvao.render(vertices=3);ctx.enable(moderngl.DEPTH_TEST)
 prog["mvp"].write((persp(math.radians(fov),W/H)@view(eye,target)).T.tobytes());prog["eye"].value=tuple(eye)
 draw(mountains)
 for cy,obj in terrain:
  if abs(cy-y)<250:draw(obj,kind=1)
 for cy,obj in trees:
  if abs(cy-y)<145:draw(obj,kind=2)
 for cy,obj in rocks:
  if abs(cy-y)<90:draw(obj,kind=1)
 # contact shadow follows the road, remaining on ground during a jump.
 sh=root.copy();sh[:3,3]=path(y);ell((0,0,.012),(.45,.98,.016),(.10,.09,.065),sh)
 bike(root,t,y,hop)
 speed_cues(root,t,y)
 for obj,instances in queue.items():
  instance_buffer.write(np.asarray(instances,dtype="f4").tobytes());obj.render(instances=len(instances))
 queue.clear()
 data=fbo.read(components=3,alignment=1)
 return Image.frombytes("RGB",(W,H),data).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
def render_frame(shot,frame_index,output_path,request):
 t=shot.get("source_offset_seconds",0)+frame_index/shot.get("fps",FPS);render(t).save(output_path)
if __name__=="__main__":
 if "--preview" in sys.argv:
  ts=[3,15,27,45,57,69,81,99,117,129];start=time.time()
  for t in ts:render(t).save(R/f"preview-{t:03}.jpg",quality=88)
  print("PREVIEW_SECONDS",time.time()-start,flush=True)
 else:
  start=time.time()
  for idx in range(22):
   out=R/f"shot-{idx+1:02}.mp4"
   if out.exists() and out.stat().st_size>15000:continue
   tmp=R/f"shot-{idx+1:02}.partial.mp4"
   cmd=["ffmpeg","-y","-v","error","-threads","2","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-threads","2","-preset","ultrafast","-crf","19","-pix_fmt","yuv420p",str(tmp)]
   proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
   for fr in range(144):
    im=render(idx*6+fr/FPS);proc.stdin.write(im.tobytes())
   proc.stdin.close()
   if proc.wait()!=0:raise RuntimeError("encoder failed")
   tmp.replace(out);print("SHOT_DONE",idx+1,"elapsed",round(time.time()-start,1),flush=True)
