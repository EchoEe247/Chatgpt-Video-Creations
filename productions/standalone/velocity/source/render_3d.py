#!/usr/bin/env python3
"""VELOCITY: deterministic local 3D highway film. No driving footage."""
import os,sys,math,time,subprocess,random,json,hashlib
os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE","1")
os.environ.setdefault("LP_NUM_THREADS","3")
from pathlib import Path
import numpy as np
import moderngl
from PIL import Image

P=Path(__file__).resolve().parents[1]
W,H,FPS,DURATION=960,540,24,120
R=P/"renders-v2";R.mkdir(parents=True,exist_ok=True)
rng=random.Random(121)

def norm(a):
 a=np.array(a,dtype="f4");return a/max(np.linalg.norm(a),1e-8)
def view(eye,target):
 f=norm(np.array(target)-eye);s=norm(np.cross(f,[0,0,1]));u=np.cross(s,f)
 m=np.eye(4,dtype="f4");m[0,:3]=s;m[1,:3]=u;m[2,:3]=-f;m[:3,3]=-m[:3,:3]@eye;return m
def persp(fov,aspect,near=.06,far=1200):
 f=1/math.tan(fov/2);m=np.zeros((4,4),dtype="f4");m[0,0]=f/aspect;m[1,1]=f;m[2,2]=(far+near)/(near-far);m[2,3]=2*far*near/(near-far);m[3,2]=-1;return m
def mat(pos=(0,0,0),scale=(1,1,1)):
 m=np.eye(4,dtype="f4");m[:3,3]=pos;m[0,0],m[1,1],m[2,2]=scale;return m
def rotz(a):
 c,s=math.cos(a),math.sin(a);m=np.eye(4,dtype="f4");m[:2,:2]=[[c,-s],[s,c]];return m
def roty(a):
 c,s=math.cos(a),math.sin(a);m=np.eye(4,dtype="f4");m[[0,0,2,2],[0,2,0,2]]=[c,s,-s,c];return m

LANE=3.65
ROAD_HALF=6.2
_PROFILE=json.loads((P/"source/speed-profile.json").read_text())
SPEED=tuple((x["start"],x["end"],x["speed_mps"]) for x in _PROFILE["segments"])
RAMP_HALF=float(_PROFILE["ramp_half_seconds"])
SHOT_DURS=(8,7,6,5,4,4,4,5,8,7,8,7,5,4,4,4,5,7,8,10)
CUTS=np.concatenate(([0.0],np.cumsum(SHOT_DURS,dtype="f4")))
def smooth01(x): x=max(0,min(1,x));return x*x*(3-2*x)
def speed(t):
 t=float(t)
 base=SPEED[-1][2]
 for a,b,v in SPEED:
  if a<=t<b: base=v;break
 for i in range(1,len(SPEED)):
  c=SPEED[i][0];lo=c-RAMP_HALF;hi=c+RAMP_HALF
  if lo<=t<=hi:
   x=smooth01((t-lo)/(hi-lo));return SPEED[i-1][2]+(SPEED[i][2]-SPEED[i-1][2])*x
 return base
_SPEED_T=np.linspace(0,DURATION,int(DURATION*240)+1,dtype="f4")
_SPEED_V=np.array([speed(x) for x in _SPEED_T],dtype="f4")
_ROUTE_Y=np.concatenate(([0.0],np.cumsum((_SPEED_V[:-1]+_SPEED_V[1:])*.5*np.diff(_SPEED_T))))
def route_y(t): return float(np.interp(float(t),_SPEED_T,_ROUTE_Y))
def shot_index(t): return min(len(SHOT_DURS)-1,max(0,int(np.searchsorted(CUTS,float(t),side="right")-1)))
def shot_q(t,idx): return max(0.0,min(1.0,(float(t)-float(CUTS[idx]))/float(SHOT_DURS[idx])))
def attack(t):
 def pulse(a,b,e=3.0):return min(max((t-a)/e,0),1)*min(max((b-t)/e,0),1)
 return max(pulse(42,60),pulse(78,102))
def center_x(y):return 5.2*math.sin(y*.0037)+1.8*math.sin(y*.0107)
def road_z(y):return .24*math.sin(y*.0045)+.10*math.sin(y*.013)
def road_pose(y):
 x=center_x(y);dy=.35
 p0=np.array([center_x(y-dy),y-dy,road_z(y-dy)],dtype="f4")
 p1=np.array([center_x(y+dy),y+dy,road_z(y+dy)],dtype="f4")
 f=norm(p1-p0);r=norm(np.cross(f,[0,0,1]));u=norm(np.cross(r,f))
 return np.array([x,y,road_z(y)],dtype="f4"),f,r,u

def hero_lane(t):
 if t<26:return 0.
 if t<34:return -smooth01((t-26)/8)
 if t<52:return -1.
 if t<60:return -1+smooth01((t-52)/8)
 if t<78:return 0.
 if t<86:return -smooth01((t-78)/8)
 if t<104:return -1.
 if t<112:return -1+smooth01((t-104)/8)
 return 0.
def hero_state(t):
 y=route_y(t);p,f,r,u=road_pose(y);p=p+r*(hero_lane(t)*LANE);p[2]+=.03
 yaw=math.atan2(f[1],f[0])-math.pi/2
 return y,p,f,r,u,yaw

ctx=moderngl.create_standalone_context(backend="egl")
print("RENDERER",ctx.info["GL_RENDERER"],flush=True)
prog=ctx.program(vertex_shader="""#version 330
in vec3 in_pos; in vec3 in_norm; in vec3 in_color;
uniform mat4 mvp;uniform vec3 eye;uniform float phase;
in mat4 instance_model;in vec3 instance_tint;in float instance_kind;
out vec3 wp;out vec3 normal;out vec3 vc;flat out int kind;
void main(){vec4 w=instance_model*vec4(in_pos,1);wp=w.xyz;normal=mat3(instance_model)*in_norm;vc=in_color*instance_tint;kind=int(instance_kind);gl_Position=mvp*w;}
""",fragment_shader="""#version 330
in vec3 wp;in vec3 normal;in vec3 vc;uniform vec3 eye;uniform float phase;flat in int kind;out vec4 frag;
float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
void main(){
 vec3 n=normalize(normal);vec3 sun=normalize(vec3(-.45,-.32,.84));
 float nd=max(dot(n,sun),0.0);vec3 c=vc;
 float grain=hash(floor(wp*24.0));
 if(kind==1)c*=.94+.09*grain;
 float dusk=smoothstep(.32,.92,phase);
 vec3 amb=mix(vec3(.31,.34,.36),vec3(.20,.23,.30),dusk);
 vec3 key=mix(vec3(.92,.70,.46),vec3(.68,.70,.78),dusk);
 float sp=pow(max(dot(reflect(-sun,n),normalize(eye-wp)),0.0),58.0);
 if(kind==4){c*=2.7;sp=0.;}
 else { float fres=pow(1.0-max(dot(normalize(eye-wp),n),0.0),3.0); c=c*(amb+key*nd)+((kind==3)?sp*1.05:sp*.10); if(kind==3)c+=mix(vec3(.035,.05,.075),vec3(.10,.13,.18),dusk)*fres; }
 float dist=length(eye-wp);float fog=1.0-exp(-dist*(mix(.0018,.0030,dusk)));
 vec3 fogc=mix(vec3(.62,.56,.49),vec3(.10,.15,.23),dusk);
 c=mix(c,fogc,fog);c=c/(c+vec3(.38));c=pow(c,vec3(.88));
 frag=vec4(c,1);
}
""")
sky=ctx.program(vertex_shader="""#version 330
out vec2 uv;void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);uv=p;gl_Position=vec4(p*2.-1.,.9999,1);}
""",fragment_shader="""#version 330
in vec2 uv;uniform float phase;out vec4 frag;
void main(){
 float d=smoothstep(.30,.92,phase);
 vec3 lo=mix(vec3(.72,.42,.24),vec3(.08,.12,.21),d);
 vec3 hi=mix(vec3(.18,.31,.48),vec3(.015,.035,.085),d);
 vec3 c=mix(lo,hi,smoothstep(0.,1.,uv.y));
 float sun=exp(-length((uv-vec2(.22,.50))*vec2(1.2,1.))*22.0)*(1.0-d);
 c+=vec3(.9,.45,.16)*sun*.7;
 float star=step(.996,fract(sin(dot(floor(uv*vec2(900,500)),vec2(12.9898,78.233)))*43758.5453))*d*.28;
 c+=star;
 frag=vec4(c,1);
}
""")
skyvao=ctx.vertex_array(sky,[])
fbo=ctx.simple_framebuffer((W,H),components=3);fbo.use()
instance_buffer=ctx.buffer(reserve=1024*160)
queue={}
def tri(out,a,b,c,col,ns=None):
 n=norm(np.cross(np.array(b)-a,np.array(c)-a))
 for i,v in enumerate([a,b,c]):out.append([*v,*(ns[i] if ns else n),*col])
def mesh(verts):
 a=np.asarray(verts,dtype="f4").reshape(-1,9);b=ctx.buffer(a.tobytes())
 return ctx.vertex_array(prog,[(b,"3f 3f 3f","in_pos","in_norm","in_color"),(instance_buffer,"16f 3f 1f /i","instance_model","instance_tint","instance_kind")])
def sphere(slices=16,rings=10):
 out=[]
 for j in range(rings):
  a0=-math.pi/2+j*math.pi/rings;a1=a0+math.pi/rings
  for i in range(slices):
   b0=i*2*math.pi/slices;b1=b0+2*math.pi/slices
   vs=[(math.cos(a)*math.cos(b),math.cos(a)*math.sin(b),math.sin(a)) for a,b in [(a0,b0),(a0,b1),(a1,b1),(a1,b0)]]
   tri(out,*vs[:3],(1,1,1),vs[:3]);tri(out,vs[0],vs[2],vs[3],(1,1,1),[vs[0],vs[2],vs[3]])
 return mesh(out)
def cylinder(n=14):
 out=[]
 for i in range(n):
  a=i*math.tau/n;b=(i+1)*math.tau/n
  v=[(math.cos(a),math.sin(a),0),(math.cos(b),math.sin(b),0),(math.cos(b),math.sin(b),1),(math.cos(a),math.sin(a),1)]
  ns=[(x,y,0) for x,y,z in v]
  tri(out,*v[:3],(1,1,1),ns[:3]);tri(out,v[0],v[2],v[3],(1,1,1),[ns[0],ns[2],ns[3]])
 return mesh(out)
def torus(major=1,minor=.10,n=30,k=8):
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
def boxmesh():
 out=[]
 p=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
 for q in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:
  v=[p[i] for i in q];tri(out,*v[:3],(1,1,1));tri(out,v[0],v[2],v[3],(1,1,1))
 return mesh(out)
def hullmesh():
 # sports-sedan proportions: 4.65m x 1.88m x 1.30m, wheelbase 2.78m
 sections=[(-2.32,.76,.18,.54),(-1.78,.92,.16,.64),(-1.20,.94,.15,.82),(-.62,.93,.14,1.20),(.45,.91,.14,1.25),(1.05,.88,.14,.89),(1.82,.86,.14,.64),(2.33,.68,.17,.54)]
 out=[]
 for i in range(len(sections)-1):
  y0,w0,z0,t0=sections[i];y1,w1,z1,t1=sections[i+1]
  # top, bottom and sides
  a=[(-w0,y0,t0),(w0,y0,t0),(w1,y1,t1),(-w1,y1,t1)]
  b=[(-w0,y0,z0),(-w1,y1,z1),(w1,y1,z1),(w0,y0,z0)]
  l=[(-w0,y0,z0),(-w0,y0,t0),(-w1,y1,t1),(-w1,y1,z1)]
  rr=[(w0,y0,z0),(w1,y1,z1),(w1,y1,t1),(w0,y0,t0)]
  for v in [a,b,l,rr]:
   tri(out,*v[:3],(1,1,1));tri(out,v[0],v[2],v[3],(1,1,1))
 # front/rear caps
 for y,w,z,t,rev in [sections[0]+(False,),sections[-1]+(True,)]:
  v=[(-w,y,z),(w,y,z),(w,y,t),(-w,y,t)]
  if rev:v=list(reversed(v))
  tri(out,*v[:3],(1,1,1));tri(out,v[0],v[2],v[3],(1,1,1))
 return mesh(out)

ball=sphere();tube=cylinder();tire=torus();box=boxmesh();hull=hullmesh()
I=np.eye(4,dtype="f4")
def draw(obj,M=I,color=(1,1,1),kind=0):queue.setdefault(obj,[]).append([*np.asarray(M,dtype="f4").T.ravel(),*color,float(kind)])
def ell(pos,scale,color,root=I,kind=0):draw(ball,root@mat(pos,scale),color,kind)
def cube(pos,scale,color,root=I,kind=0):draw(box,root@mat(pos,scale),color,kind)
def seg(a,b,r,color,root=I,kind=0):
 a=np.array(a,dtype="f4");b=np.array(b,dtype="f4");v=b-a;ln=np.linalg.norm(v);z=norm(v);x=norm(np.cross(z,[0,1,0] if abs(z[1])<.9 else [1,0,0]));y=np.cross(z,x)
 M=np.eye(4,dtype="f4");M[:3,0]=x*r;M[:3,1]=y*r;M[:3,2]=z*ln;M[:3,3]=a;draw(tube,root@M,color,kind)

# Static highway geometry split into 120m bins.
def road_mesh_bin(y0,y1):
 out=[];step=8.;ys=np.arange(y0,y1+step,step)
 for i in range(len(ys)-1):
  ya,yb=ys[i],ys[i+1];pa,fa,ra,ua=road_pose(ya);pb,fb,rb,ub=road_pose(yb)
  v=[pa-ra*ROAD_HALF,pb-rb*ROAD_HALF,pb+rb*ROAD_HALF,pa+ra*ROAD_HALF]
  v=[tuple(x+np.array([0,0,-.01],dtype="f4")) for x in v]
  tri(out,v[0],v[1],v[2],(.115,.12,.125));tri(out,v[0],v[2],v[3],(.115,.12,.125))
 return mesh(out)
road_bins=[]
for y0 in range(-360,4300,120):road_bins.append((y0+60,road_mesh_bin(y0,y0+120)))

# Lane stripes, shoulder lines, reflectors, guard rails, lamp posts.
static=[]
for y in np.arange(-300,4300,12):
 p,f,r,u=road_pose(y)
 for off in [-LANE/2,LANE/2]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.018
  static.append((y,box,root@mat((0,0,0),(.055,2.1,.012)),(.88,.88,.78),4))
for y in np.arange(-300,4300,8):
 p,f,r,u=road_pose(y)
 for off in [-ROAD_HALF+.18,ROAD_HALF-.18]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.025
  static.append((y,box,root@mat((0,0,0),(.06,3.9,.014)),(.92,.91,.83),4))
for y in np.arange(-280,4300,24):
 p,f,r,u=road_pose(y)
 for off in [-ROAD_HALF+.55,ROAD_HALF-.55]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.04
  static.append((y,ball,root@mat((0,0,0),(.035,.12,.025)),(.95,.72,.26),4))
# road wear / repaired asphalt strips
for y in np.arange(-280,4300,34):
 p,f,r,u=road_pose(y)
 off=((int(y/34)%5)-2)*.55
 root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.006
 static.append((y,box,root@mat((0,0,0),(.20,4.2,.006)),(.075,.078,.080),1))
# roadside delineator posts
for y in np.arange(-260,4300,40):
 p,f,r,u=road_pose(y)
 for off in [-ROAD_HALF-1.35,ROAD_HALF+1.35]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off
  static.append((y,box,root@mat((0,0,.42),(.055,.055,.42)),(.58,.59,.58),3))
  static.append((y,ball,root@mat((0,0,.74),(.08,.05,.045)),(.95,.70,.25),4))
# barriers
for y in np.arange(-300,4300,8):
 p,f,r,u=road_pose(y)
 for off in [-ROAD_HALF-1.0,ROAD_HALF+1.0]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.48
  static.append((y,box,root@mat((0,0,0),(.10,4.0,.08)),(.42,.44,.45),3))
  root2=root.copy();root2[:3,3]=p+r*off+u*.23
  static.append((y,tube,root2@mat((0,0,0),(.055,.055,.48)),(.33,.34,.34),3))
# lamps every 72m
for y in np.arange(-260,4300,72):
 p,f,r,u=road_pose(y)
 side=-1 if int(y/72)%2 else 1
 base=p+r*(side*(ROAD_HALF+2.2))
 root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=base
 static.append((y,tube,root@mat((0,0,0),(.055,.055,6.4)),(.23,.25,.27),3))
 static.append((y,box,root@mat((-.55*side,0,6.3),(.65,.08,.06)),(.23,.25,.27),3))
 static.append((y,ball,root@mat((-1.1*side,0,6.15),(.14,.18,.10)),(1.0,.78,.42),4))
# overpasses + signs
for y in [880,1780,2870,3720]:
 p,f,r,u=road_pose(y);root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+u*5.3
 static.append((y,box,root@mat((0,0,0),(10,.55,.28)),(.28,.29,.30),3))
 for off in [-8.2,8.2]:static.append((y,box,root@mat((off,0,-2.55),(.30,.35,2.7)),(.32,.33,.34),3))
for y in [520,2450,3450]:
 p,f,r,u=road_pose(y);root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+u*5.8
 static.append((y,box,root@mat((0,0,0),(5.6,.10,1.15)),(.055,.19,.16),3))
 static.append((y,box,root@mat((-5.0,0,-2.4),(.14,.12,2.5)),(.35,.36,.36),3))
 static.append((y,box,root@mat((5.0,0,-2.4),(.14,.12,2.5)),(.35,.36,.36),3))

# skyline / sound walls
for y in range(-200,4300,55):
 p,f,r,u=road_pose(y)
 side=-1 if (y//55)%2 else 1
 for k in range(2):
  off=side*(28+k*15+rng.uniform(-4,4));h=rng.uniform(7,28);w=rng.uniform(5,12);dep=rng.uniform(5,14)
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*(h*.5-.2)
  col=(.21+rng.random()*.08,.22+rng.random()*.07,.24+rng.random()*.08)
  static.append((y,box,root@mat((0,0,0),(w*.5,dep*.5,h*.5)),col,1))
  # a few window bands
  if h>13:
   for zz in np.arange(-h*.34,h*.34,3.2):
    static.append((y,box,root@mat((-side*w*.51,0,zz),(.03,dep*.40,.13)),(.72,.55,.30),4))

def car_root(y,lane):
 p,f,r,u=road_pose(y);p=p+r*(lane*LANE);root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p
 return root,f,r,u

wheelrot=np.eye(4,dtype="f4");wheelrot[:3,:3]=np.array([[0,0,1],[1,0,0],[0,1,0]],dtype="f4")
def car(root,color,hero=False,kind="sedan",wheel_spin=0,phase=.0):
 # coherent real-world dimensions, with traffic variants.
 if kind=="suv":
  sx,sy,sz=1.02,1.06,1.18
 elif kind=="coupe":
  sx,sy,sz=.98,1.01,.92
 else:sx,sy,sz=1,1,1
 draw(hull,root@mat((0,0,.02),(sx,sy,sz)),color,3)
 # glass canopy and black lower grille/rocker
 ell((0,-.10,.88*sz),(.76*sx,1.02*sy,.33*sz),(.055,.085,.11),root,3)
 cube((0,1.94*sy,.46*sz),(.56*sx,.055,.12*sz),(.025,.03,.035),root,3)
 cube((0,-2.03*sy,.42*sz),(.62*sx,.05,.09*sz),(.03,.03,.033),root,3)
 # lights
 light=(.95,.93,.76);tail=(.95,.07,.025)
 for x in [-.58*sx,.58*sx]:
  cube((x,2.18*sy,.55*sz),(.18,.035,.07),light,root,4)
  cube((x,-2.19*sy,.55*sz),(.20,.035,.065),tail,root,4)
 # side mirrors and trim
 for x in [-.99*sx,.99*sx]:
  ell((x,.52*sy,.82*sz),(.13,.16,.08),color,root,3)
 cube((0,0,.22),(.92*sx,2.15*sy,.055),(.025,.027,.03),root,3)
 # wheels
 for x in [-.86*sx,.86*sx]:
  for yy in [-1.36*sy,1.36*sy]:
   M=mat((x,yy,.34*sz),(.34*sz,.34*sz,.34*sz))@wheelrot@rotz(wheel_spin)
   draw(tire,root@M,(.018,.019,.020),3)
   draw(tire,root@(mat((x,yy,.34*sz),(.22*sz,.22*sz,.22*sz))@wheelrot),(.40,.42,.44),3)
 # hero details: splitter, spoiler, bright rim center
 if hero:
  cube((0,2.27,.29),(.87,.08,.035),(.025,.03,.035),root,3)
  cube((0,-2.20,.80),(.78,.08,.035),(.035,.04,.045),root,3)
  # hood / roof / trunk panel breaks and sill trim improve scale reads.
  cube((0,.98,1.02),(.69,.52,.025),(.050,.125,.235),root,3)
  cube((0,-.26,1.22),(.66,.48,.028),(.040,.090,.155),root,3)
  cube((0,-1.50,.74),(.72,.40,.022),(.052,.125,.225),root,3)
  for x in [-.91,.91]: cube((x,0,.43),(.028,1.62,.035),(.30,.32,.34),root,3)
  for x in [-.86,.86]:
   for yy in [-1.36,1.36]:
    ell((x,yy,.34),(.075,.04,.075),(.72,.72,.68),root,4)
    ell((x,yy,.34),(.035,.025,.035),(.08,.08,.085),root,3)

TRAFFIC=[]
colors=[(.55,.56,.59),(.15,.18,.22),(.62,.12,.08),(.12,.22,.38),(.74,.70,.60),(.24,.29,.27),(.44,.11,.14),(.71,.72,.74)]
for i in range(42):
 lane=rng.choice([-1,0,1]);can_change=(i%7==0)
 target=lane
 if can_change:
  opts=[x for x in [-1,0,1] if x!=lane and abs(x-lane)==1];target=rng.choice(opts)
 TRAFFIC.append(dict(lane=lane,target=target,base=rng.uniform(-650,1250),v=rng.uniform(23.5,38.5),
  color=colors[i%len(colors)],kind=rng.choice(["sedan","sedan","suv","coupe"]),change_start=28+rng.random()*66))
_profile_sha=hashlib.sha256((P/"source/speed-profile.json").read_bytes()).hexdigest()
(P/"renders-v2").mkdir(parents=True,exist_ok=True)
(P/"renders-v2/speed-profile.sha256").write_text(_profile_sha+"\n")
(P/"source/motion-telemetry.json").write_text(json.dumps({
 "schema_version":1,
 "speed_profile_sha256":_profile_sha,
 "shot_durations":list(SHOT_DURS),
 "cut_times":[float(x) for x in CUTS],
 "traffic":[{"lane":d["lane"],"target":d["target"],"base":d["base"],"speed_mps":d["v"],"change_start":d["change_start"],"change_end":d["change_start"]+7.0} for d in TRAFFIC]
},indent=2)+"\n")
def traffic_lane(d,t):
 start=d["change_start"];end=start+7.0
 if d["target"]==d["lane"]: return float(d["lane"])
 if t<=start:return float(d["lane"])
 if t>=end:return float(d["target"])
 return d["lane"]+(d["target"]-d["lane"])*smooth01((t-start)/(end-start))
def traffic_state(d,t,hero_y):
 y=d["base"]+d["v"]*t
 return y,traffic_lane(d,t)

def camera(t,idx,p,f,r,u):
 a=attack(t);mode=[0,1,6,3,4,2,1,5,7,0,3,6,2,4,1,5,7,0,3,2][idx];q=shot_q(t,idx)
 if mode==0:eye=p-f*(12-3*q)+r*(5.8-2*q)+u*(3.4-1*q);target=p+f*10+u*.65;fov=52
 elif mode==1:eye=p-f*6.8+r*3.2+u*1.15;target=p+f*7+u*.50;fov=58
 elif mode==2:eye=p+f*8-r*2.8+u*1.35;target=p+u*.55;fov=60
 elif mode==3:
  side=1 if q<.5 else -1
  drift=(q*2 if q<.5 else (q-.5)*2)
  eye=p+r*(side*5.6)-f*(1.0-2.0*drift)+u*1.35;target=p+f*2.5+u*.50;fov=55
 elif mode==4:eye=p+u*1.43+f*.30;target=p+f*48+u*.38;fov=76
 elif mode==5:
  eye=p-r*2.75+f*.60+u*.72;target=p-r*.78+f*.82+u*.38;fov=54
 elif mode==6:eye=p-f*16+r*10+u*12;target=p+f*14;fov=48
 else:eye=p-f*30+r*7+u*2.1;target=p+f*14+u*.45;fov=44
 # speed feels faster through lens and low-amplitude road vibration, not fake jumps
 fov+=8*a
 eye+=r*((.010+.022*a)*math.sin(t*20.3))+u*((.006+.016*a)*math.sin(t*31.7))
 return eye,target,fov

def render(t):
 idx=shot_index(t);y,p,f,r,u,yaw=hero_state(t);phase=t/DURATION
 eye,target,fov=camera(t,idx,p,f,r,u)
 ctx.clear(.10,.14,.20,1,depth=1);ctx.disable(moderngl.DEPTH_TEST);sky["phase"].value=phase;skyvao.render(vertices=3);ctx.enable(moderngl.DEPTH_TEST)
 prog["mvp"].write((persp(math.radians(fov),W/H)@view(eye,target)).T.tobytes());prog["eye"].value=tuple(eye);prog["phase"].value=phase
 # road chunks
 for cy,obj in road_bins:
  if abs(cy-y)<420:draw(obj,kind=1)
 # static roadside details
 for cy,obj,M,col,k in static:
  if abs(cy-y)<260:draw(obj,M,col,k)
 # hero car
 root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+u*.02
 hero_col=(.065,.16,.29)
 car(root,hero_col,True,"coupe",wheel_spin=-y/.34,phase=phase)
 # contact shadow
 ell((0,0,.015),(1.05,2.25,.018),(.025,.025,.028),root,1)
 dusk=smooth01((phase-.42)/.45)
 # traffic
 for d in TRAFFIC:
  ty,lane=traffic_state(d,t,y)
  if abs(ty-y)>240:continue
  tr,tf,rr,uu=car_root(ty,lane);tr[:3,3]+=uu*.02
  if np.linalg.norm(tr[:3,3]-eye)<5.2:continue
  car(tr,d["color"],False,d["kind"],wheel_spin=-ty/.34,phase=phase)
  ell((0,0,.012),(1.02,2.15,.015),(.03,.03,.032),tr,1)
  if dusk>.48:
   ell((0,2.7,.018),(.34,2.2,.010),(.10*dusk,.095*dusk,.065*dusk),tr,1)
 # subtle headlight pools after blue hour, and fast roadside reflector glints
 if dusk>.35:
  for lx in [-.52,.52]:
   ell((lx,3.3,.025),(.28,2.5,.008),(.16*dusk,.145*dusk,.085*dusk),root,1)
 if attack(t)>.1:
  for i in range(12):
   yy=y-8-i*6.5;pp,ff,rr,uu=road_pose(yy);side=-1 if i%2 else 1
   ell(tuple(pp+rr*(side*(ROAD_HALF-.45))+uu*.05),(.045,.16,.025),(.95,.66,.22),I,4)
 for obj,instances in queue.items():
  instance_buffer.write(np.asarray(instances,dtype="f4").tobytes());obj.render(instances=len(instances))
 queue.clear()
 data=fbo.read(components=3,alignment=1)
 return Image.frombytes("RGB",(W,H),data).transpose(Image.Transpose.FLIP_TOP_BOTTOM)

if __name__=="__main__":
 if "--preview" in sys.argv:
  ts=[3,15,27,45,51,63,81,93,105,117];st=time.time()
  for t in ts:render(t).save(R/f"preview-{t:03}.jpg",quality=90)
  print("PREVIEW_SECONDS",round(time.time()-st,2),flush=True)
 else:
  st=time.time()
  for idx,dur in enumerate(SHOT_DURS):
   out=R/f"shot-{idx+1:02}.mp4"
   if out.exists() and out.stat().st_size>15000:continue
   tmp=R/f"shot-{idx+1:02}.partial.mp4"
   cmd=["ffmpeg","-y","-v","error","-threads","2","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-threads","2","-preset","ultrafast","-crf","18","-pix_fmt","yuv420p",str(tmp)]
   pr=subprocess.Popen(cmd,stdin=subprocess.PIPE)
   start=float(CUTS[idx]);frames=int(round(float(dur)*FPS))
   for fr in range(frames):pr.stdin.write(render(start+fr/FPS).tobytes())
   pr.stdin.close()
   if pr.wait()!=0:raise RuntimeError("encoder failed")
   tmp.replace(out);print("SHOT_DONE",idx+1,"duration",dur,"elapsed",round(time.time()-st,1),flush=True)
