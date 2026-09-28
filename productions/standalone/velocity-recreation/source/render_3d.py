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
R=P/"renders-v3";R.mkdir(parents=True,exist_ok=True)
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
 return max(pulse(25,43),pulse(66,95))
def center_x(y):return 5.2*math.sin(y*.0037)+1.8*math.sin(y*.0107)
def road_z(y):return .24*math.sin(y*.0045)+.10*math.sin(y*.013)
def road_pose(y):
 x=center_x(y);dy=.35
 p0=np.array([center_x(y-dy),y-dy,road_z(y-dy)],dtype="f4")
 p1=np.array([center_x(y+dy),y+dy,road_z(y+dy)],dtype="f4")
 f=norm(p1-p0);r=norm(np.cross(f,[0,0,1]));u=norm(np.cross(r,f))
 return np.array([x,y,road_z(y)],dtype="f4"),f,r,u

def hero_lane(t): return 0.0
def hero_state(t):
 y=route_y(t);p,f,r,u=road_pose(y);p=p+r*(hero_lane(t)*LANE);p[2]+=.0
 yaw=math.atan2(f[1],f[0])-math.pi/2
 return y,p,f,r,u,yaw

ctx=moderngl.create_standalone_context(backend="egl")
print("RENDERER",ctx.info["GL_RENDERER"],flush=True)
prog=ctx.program(vertex_shader="""#version 330
in vec3 in_pos; in vec3 in_norm; in vec3 in_color;
uniform mat4 mvp;uniform vec3 eye;uniform float phase;
in mat4 instance_model;in vec3 instance_tint;in float instance_kind;
out vec3 wp;out vec3 normal;out vec3 vc;flat out int kind;
void main(){vec4 w=instance_model*vec4(in_pos,1);wp=w.xyz;normal=transpose(inverse(mat3(instance_model)))*in_norm;vc=in_color*instance_tint;kind=int(instance_kind);gl_Position=mvp*w;}
""",fragment_shader="""#version 330
in vec3 wp;in vec3 normal;in vec3 vc;uniform vec3 eye;uniform float phase;uniform vec3 heroP;uniform vec3 heroF;flat in int kind;out vec4 frag;
float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
void main(){
 vec3 n=normalize(normal);vec3 sun=normalize(vec3(-.45,-.32,.84));
 float nd=max(dot(n,sun),0.0);vec3 c=vc;
 float grain=hash(floor(wp*24.0));
 if(kind==1){
  // Keep asphalt/terrain readable after the 960->320 review downsample.
  // The previous 24-cycles/m noise was sub-pixel and averaged away.
  float coarse=hash(floor(vec3(wp.x*1.15,wp.y*.72,wp.z*2.0)+vec3(13.0,29.0,7.0)));
  float aggregate=hash(floor(vec3(wp.x*3.1,wp.y*2.0,wp.z*4.0)+vec3(41.0,3.0,19.0)));
  c*=.62+.48*coarse+.22*aggregate;
 }
 if(kind==1 && n.z>.8){
  float joint=step(.11,mod(wp.y,37.0));
  c*=.77+.23*joint;
 }
 
 float dusk=smoothstep(.32,.92,phase);
 vec3 amb=mix(vec3(.31,.34,.36),vec3(.09,.14,.23),dusk);
 vec3 key=mix(vec3(.92,.70,.46),vec3(.16,.21,.33),dusk);
 float sp=pow(max(dot(reflect(-sun,n),normalize(eye-wp)),0.0),58.0);
 if(kind==4){c*=2.7;sp=0.;}
 else { float fres=pow(1.0-max(dot(normalize(eye-wp),n),0.0),3.0); c=c*(amb+key*nd)+((kind==3)?sp*.55:sp*.10); if(kind==3){ float flake=hash(floor(wp*vec3(5.2,3.1,7.3)+vec3(23.0,11.0,31.0))); float refl=.5+.5*sin(wp.y*2.2+wp.x*6.3+wp.z*4.1); c*=.88+.20*flake; c+=mix(vec3(.025,.035,.05),vec3(.055,.075,.105),dusk)*refl + mix(vec3(.08,.12,.18),vec3(.04,.075,.13),dusk)*fres; } }
 vec3 rel=wp-heroP;float ahead=dot(rel,heroF);
 float lateral=length(rel-heroF*ahead);
 float beams=exp(-pow(lateral/(.8+max(ahead,0.)*.08),2.0))*smoothstep(0.,3.,ahead)*(1.-smoothstep(8.,48.,ahead));
 if(kind==1)c+=vec3(.26,.28,.25)*beams*dusk*max(n.z,0.);
 float lampY=round((wp.y+260.0)/72.0)*72.0-260.0;
 float pool=exp(-pow((wp.y-lampY)/8.0,2.0))*dusk;
 float roadx=5.2*sin(wp.y*.0037)+1.8*sin(wp.y*.0107); float edge=min(abs(wp.x-roadx),abs(wp.x-roadx+17.5)); pool*=exp(-pow(edge/9.0,4.0)); if(kind!=4)c+=vec3(.25,.20,.12)*pool*max(n.z,0.);
 if(kind==5){
  float facade=hash(floor(vec3(wp.x*.58,wp.y*.58,wp.z*.72)+vec3(9.0,17.0,5.0)));
  c*=mix(1.0,.86+.25*facade,dusk);
  float wx=step(.35,fract(wp.x*.45))*step(.35,fract(wp.y*.45));
  float wz=step(.70,fract(wp.z*.34));
  c+=vec3(.32,.25,.13)*wx*wz*(.2+.8*dusk);
 }
 if(kind==7)c=vec3(.012,.014,.019); float dist=length(eye-wp);float fog=1.0-exp(-dist*(mix(.0018,.0030,dusk)));
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
 // Use review-scale star cells so real night-sky structure survives downsample.
 float star=step(.988,fract(sin(dot(floor(uv*vec2(320,180)),vec2(12.9898,78.233)))*43758.5453))*d*.16;
 float cloud=(.5+.5*sin(uv.x*52.0+sin(uv.y*18.0)*2.0))*(.5+.5*sin(uv.y*31.0+uv.x*7.0));
 c*=1.0+(cloud-.5)*.18*d;
 c+=star;
 frag=vec4(c,1);
}
""")
skyvao=ctx.vertex_array(sky,[])
fbo=ctx.simple_framebuffer((W,H),components=3);fbo.use()
instance_buffer=ctx.buffer(reserve=1024*1024)
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
  v=[p[i] for i in reversed(q)];tri(out,*v[:3],(1,1,1));tri(out,v[0],v[2],v[3],(1,1,1))
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
  tri(out,v[0],v[2],v[1],(.115,.12,.125));tri(out,v[0],v[3],v[2],(.115,.12,.125))
 return mesh(out)
road_bins=[]
for y0 in range(-360,5700,120):road_bins.append((y0+60,road_mesh_bin(y0,y0+120)))

# Lane stripes, shoulder lines, reflectors, guard rails, lamp posts.
static=[]
for y in np.arange(-300,5700,12):
 p,f,r,u=road_pose(y)
 for off in [-LANE/2,LANE/2]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.018
  static.append((y,box,root@mat((0,0,0),(.055,2.1,.012)),(.88,.88,.78),4))
for y in np.arange(-300,5700,8):
 p,f,r,u=road_pose(y)
 for off in [-ROAD_HALF+.18,ROAD_HALF-.18]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.025
  static.append((y,box,root@mat((0,0,0),(.06,3.9,.014)),(.92,.91,.83),4))
for y in np.arange(-280,5700,24):
 p,f,r,u=road_pose(y)
 for off in [-ROAD_HALF+.55,ROAD_HALF-.55]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.04
  static.append((y,ball,root@mat((0,0,0),(.035,.12,.025)),(.95,.72,.26),4))
# road wear / repaired asphalt strips
for y in np.arange(-280,5700,34):
 p,f,r,u=road_pose(y)
 off=((int(y/34)%5)-2)*.55
 root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.006
 static.append((y,box,root@mat((0,0,0),(.20,4.2,.006)),(.075,.078,.080),1))
# roadside delineator posts
for y in np.arange(-260,5700,40):
 p,f,r,u=road_pose(y)
 for off in [-ROAD_HALF-1.35,ROAD_HALF+1.35]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off
  static.append((y,box,root@mat((0,0,.42),(.055,.055,.42)),(.58,.59,.58),3))
  static.append((y,ball,root@mat((0,0,.74),(.08,.05,.045)),(.95,.70,.25),4))
# barriers
for y in np.arange(-300,5700,8):
 p,f,r,u=road_pose(y)
 for off in [-ROAD_HALF-1.0,ROAD_HALF+1.0]:
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*.48
  static.append((y,box,root@mat((0,0,0),(.10,4.0,.08)),(.42,.44,.45),3))
  root2=root.copy();root2[:3,3]=p+r*off+u*.23
  static.append((y,tube,root2@mat((0,0,0),(.055,.055,.48)),(.33,.34,.34),3))
# lamps every 72m
for y in np.arange(-260,5700,72):
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
for y in range(-200,5700,55):
 p,f,r,u=road_pose(y)
 side=-1 if (y//55)%2 else 1
 for k in range(2):
  off=side*(28+k*15+rng.uniform(-4,4));h=rng.uniform(7,28);w=rng.uniform(5,12);dep=rng.uniform(5,14)
  root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+r*off+u*(h*.5-.2)
  col=(.21+rng.random()*.08,.22+rng.random()*.07,.24+rng.random()*.08)
  static.append((y,box,root@mat((0,0,0),(w*.5,dep*.5,h*.5)),col,5))
  # a few window bands
  if h>13:
   for zz in np.arange(-h*.34,h*.34,3.2):
    static.append((y,box,root@mat((-side*w*.51,0,zz),(.03,dep*.40,.13)),(.72,.55,.30),4))

def car_root(y,lane):
 p,f,r,u=road_pose(y);p=p+r*(lane*LANE);root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p
 return root,f,r,u

# CC0 Kenney GLB importer: sample the palette texture to vertex colors.
import struct,io
def load_car(name):
 raw=(P/'assets'/f'{name}.glb').read_bytes(); ln=struct.unpack_from('<I',raw,12)[0]
 doc=json.loads(raw[20:20+ln]); binary=raw[28+ln:]
 palette=Image.open(P/'assets/colormap.png').convert('RGB'); pw,ph=palette.size
 def acc(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
  typ={5121:'u1',5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']]
  n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
  return np.frombuffer(binary,dtype=typ,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
 pieces=[]; allpos=[]
 def node(i,parent):
  n=doc['nodes'][i];tr=parent+np.array(n.get('translation',[0,0,0]))
  if 'mesh' in n:
   for prim in doc['meshes'][n['mesh']]['primitives']:
    at=prim['attributes'];pos=acc(at['POSITION']);ns=acc(at['NORMAL']);uv=acc(at['TEXCOORD_0']);ix=acc(prim['indices']).ravel()
    cols=[]
    for u,v in uv:
     c=np.array(palette.getpixel((min(pw-1,max(0,int(u*pw))),min(ph-1,max(0,int(v*ph))))),dtype='f4')/255
     if c[0]>.55 and c[0]>c[1]*1.3: c=np.array([.12,.27,.49],dtype='f4')
     if n.get('name')=='body' and min(c)>.68: c=np.array([.15,.22,.29],dtype='f4')
     c=c**2.2
     cols.append(c)
    # GLTF +Z forward,+Y up -> renderer +Y forward,+Z up.
    pos=pos[:,[0,2,1]]; ns=ns[:,[0,2,1]]; tr2=tr[[0,2,1]]
    pieces.append((n.get('name',''),pos,ns,np.array(cols),ix,tr2));allpos.extend(pos+tr2)
  for child in n.get('children',[]):node(child,tr)
 children={c for n in doc['nodes'] for c in n.get('children',[])}
 for i in range(len(doc['nodes'])):
  if i not in children:node(i,np.zeros(3))
 allpos=np.array(allpos); sc=4.65/(allpos[:,1].max()-allpos[:,1].min()); bottom=allpos[:,2].min()*sc
 result=[]
 for name,pos,ns,col,ix,tr in pieces:
  pos=pos*sc;tr=tr*sc;tr[2]-=bottom
  def along(y):
   return np.interp(y,[-2.4,-1.78,-1.2,-.64,0,.64,1.2,1.78,2.4],[-2.4,-1.73,-1.36,-.99,0,.99,1.36,1.73,2.4])
  if name.startswith('wheel'):
   pos[:,0]*=.80;pos[:,1:]*=.62
   tr[0]*=.80;tr[1]=along(tr[1]);tr[2]*=.62
  else:
   pos+=tr;tr=np.zeros(3)
   pos[:,0]*=.80;pos[:,1]=along(pos[:,1]);pos[:,2]*=.67
  data=np.concatenate([pos,ns,col],axis=1)[ix]
  va=mesh(data)
  result.append((name,va,tr))
 return result
CARS={k:load_car(n) for k,n in [('coupe','sedan-sports'),('sedan','sedan'),('suv','suv-luxury')]}
def rotx(a):
 c,z=math.cos(a),math.sin(a);m=np.eye(4,dtype='f4');m[1:3,1:3]=[[c,-z],[z,c]];return m
def car(root,color,hero=False,kind='sedan',wheel_spin=0,phase=0):
 for name,obj,tr in CARS[kind]:
  M=root@mat(tr)
  if name.startswith('wheel'): M=M@rotx(wheel_spin)
  draw(obj,M,(1,1,1) if hero else color,3)
  if hero and name.startswith('wheel'):
   side=1 if tr[0]>0 else -1
   for k in range(5):
    spoke=M@rotx(k*math.tau/5)@mat((side*.43,0,.11),(.014,.024,.11))
    draw(box,spoke,(.42,.46,.52),3)
 # Lamps sit on the front and rear planes without body rescaling.
 for x in [-.64,.64]:
  cube((x,2.29,.48),(.19,.035,.045),(1,.88,.65),root,4)
  cube((x,-2.26,.48),(.23,.035,.04),(.85,.025,.012),root,4)

# Persistent lane traffic with same-lane headway guaranteed for the entire film.
# Hero has a reserved center lane; each adjacent lane has an independent flow.
TRAFFIC=[]
colors=[(.82,.82,.84),(.52,.60,.68),(.85,.73,.58),(.64,.72,.67)]
for lane,velocity,offset in [(-1,33,-380),(1,26,-330)]:
 for i in range(18):
  TRAFFIC.append(dict(lane=lane,target=lane,base=offset+i*95,v=velocity,
   color=colors[i%4],kind=['sedan','suv','coupe'][i%3],change_start=200))
# A faster center-lane car begins ahead and continues to pull away.
TRAFFIC.append(dict(lane=0,target=0,base=65,v=51,color=(.7,.7,.73),kind='sedan',change_start=200))
TRAFFIC=[d for d in TRAFFIC if not any(
 d['lane']==side and any(abs(d['base']+d['v']*tt-route_y(tt))<14 for tt in np.arange(lo,hi,.25))
 for lo,hi,side in [(21,26,1),(58,66,-1),(102,110,1)])]
_profile_sha=hashlib.sha256((P/"source/speed-profile.json").read_bytes()).hexdigest()
(P/"renders-v3").mkdir(parents=True,exist_ok=True)
(P/"renders-v3/speed-profile.sha256").write_text(_profile_sha+"\n")
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
 q=shot_q(t,idx); a=attack(t)
 setups=[
 (-12,4.8,3.4,1.0,49),(-8,-3.4,1.6,.8,48),(-19,10,11,7,47),
 (0,7.1,1.45,0,48),(-7,2.8,1.2,.8,49),(8,-2.5,1.55,0,50),
 (-10,-4.2,2.6,2,47),(.4,-2.7,.65,.7,48),(-34,4,2.2,2,27),
 (-12,5,4,4,48),(0,-7.1,1.5,0,48),(-23,-11,13,10,47),
 (8,2.4,1.3,0,50),(1.15,0,1.52,40,73),(-7,-1.8,1.1,1,51),
 (1.25,1.9,.58,1.2,60),(-31,-4,2,2,29),(-10,4,2.8,2,47),
 (0,7.2,1.45,0,48),(-17-10*q,-6,6+3*q,4,46)]
 along,side,height,aim,fov=setups[idx]
 eye=p+f*along+r*side+u*height
 target=p+f*aim+u*(.40 if idx in [7,15] else .72)
 if idx==13: target=p+f*48+u*.7
 if idx in [7,15]: target=p+r*(.85 if side>0 else -.85)+f*aim+u*.38
 eye+=r*.008*math.sin(t*4.1)+u*(.006+.004*a)*math.sin(t*6.3)
 return eye,target,fov

def render(t):
 idx=shot_index(t);y,p,f,r,u,yaw=hero_state(t);phase=t/DURATION
 eye,target,fov=camera(t,idx,p,f,r,u)
 ctx.clear(.10,.14,.20,1,depth=1);ctx.disable(moderngl.DEPTH_TEST);sky["phase"].value=phase;skyvao.render(vertices=3);ctx.enable(moderngl.DEPTH_TEST)
 prog["mvp"].write((persp(math.radians(fov),W/H)@view(eye,target)).T.tobytes());prog["eye"].value=tuple(eye);prog["phase"].value=phase;prog["heroP"].value=tuple(p);prog["heroF"].value=tuple(f)
 # Static ground below highway (no sky beneath road).
 cube((0,2400,-1.2),(1800,3600,.35),(.045,.057,.056),I,1)
 # road chunks
 for cy,obj in road_bins:
  if abs(cy-y)<500:
   draw(obj,kind=1);draw(obj,mat((-17.5,0,0)),kind=1)
 # static roadside details
 for cy,obj,M,col,k in static:
  if abs(cy-y)<430:
   draw(obj,M,col,k)
   if abs(M[0,3]-center_x(cy))<10: draw(obj,mat((-17.5,0,0))@M,col,k)
 # Opposing carriageway traffic with persistent world coordinates.
 for j in range(35):
  oy=-400+j*175-27*t
  if abs(oy-y)<430:
   tr,tf,rr,uu=car_root(oy,(-1,0,1)[j%3]);tr[0,3]-=17.5
   tr=tr@rotz(math.pi)
   car(tr,(.64,.67,.72),False,'sedan',wheel_spin=oy/.34,phase=phase)
 # hero car
 root=np.eye(4,dtype="f4");root[:3,0]=r;root[:3,1]=f;root[:3,2]=u;root[:3,3]=p+u*.005
 hero_col=(.065,.16,.29)
 car(root,hero_col,True,"coupe",wheel_spin=-y/.34,phase=phase)
 # contact shadow
 ell((0,0,.015),(1.05,2.25,.018),(.025,.025,.028),root,7)
 dusk=smooth01((phase-.42)/.45)
 # traffic
 for d in TRAFFIC:
  ty,lane=traffic_state(d,t,y)
  if abs(ty-y)>240:continue
  tr,tf,rr,uu=car_root(ty,lane);tr[:3,3]+=uu*.005
  
  car(tr,d["color"],False,d["kind"],wheel_spin=-ty/.34,phase=phase)
  ell((0,0,.012),(1.02,2.15,.015),(.03,.03,.032),tr,7)
 for obj,instances in queue.items():
  instance_buffer.write(np.asarray(instances,dtype="f4").tobytes());obj.render(instances=len(instances))
 queue.clear()
 data=fbo.read(components=3,alignment=1)
 im=Image.frombytes("RGB",(W,H),data).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 # Intentional fine cinematic grain: low at sunset, stronger at blue-hour/night.
 # It is deterministic per source frame and generated at review-resolvable scale
 # so the night image retains texture rather than collapsing into flat gradients.
 grain_mix=smooth01((phase-.45)/.25)
 grain_amp=.008+.022*grain_mix
 arr=np.asarray(im,dtype=np.float32)/255.0
 grng=np.random.default_rng(9000+int(round(float(t)*FPS)))
 small=grng.uniform(-grain_amp,grain_amp,(math.ceil(H/3),math.ceil(W/3),1)).astype(np.float32)
 grain=np.repeat(np.repeat(small,3,axis=0),3,axis=1)[:H,:W]
 arr=np.clip(arr+grain,0.0,1.0)
 return Image.fromarray((arr*255.0+.5).astype(np.uint8),"RGB")

def render_frame(shot,frame_index,output_path,request):
 render(float(shot.get('timeline_start_seconds',0))+frame_index/FPS).save(output_path)

if __name__=="__main__":
 if "--preview" in sys.argv:
  ts=sorted(set([3,11,18,23,28,32,36,40,47,54,62,69,75,80,84,88,92,98,106,116]+list(range(84,118,3))));st=time.time()
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