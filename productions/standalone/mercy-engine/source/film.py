#!/usr/bin/env python3
"""Mercy Engine: native-frame cinematic software renderer. No generated-video service."""
from pathlib import Path
import numpy as np, math, json, subprocess, sys, time, struct, io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
P=Path(__file__).resolve().parent; ROOT=P.parents[2]
W,H,FPS=1280,720,24
STORY=json.loads((P/'story.json').read_text())
OUT=P/'renders'; OUT.mkdir(exist_ok=True); (P/'review').mkdir(exist_ok=True)
rng=np.random.default_rng(472)
def font(n,b=False): return ImageFont.truetype('/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf' if b else '/system/fonts/Roboto-Regular.ttf',n)
FONTS={n:font(n,n>25) for n in [15,18,20,23,28,36,52,76]}
def text(d,pos,s,n=20,fill=(222,235,241),anchor=None):
    d.text(pos,s,font=FONTS[n],fill=fill,anchor=anchor)
def norm(v): return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-8)
def rot_y(a):
    c,s=np.cos(a),np.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def camera(points,eye,target,focal=780):
    forward=norm(np.array(target)-np.array(eye)); right=norm(np.cross(forward,[0,1,0])); up=np.cross(right,forward)
    p=(points-np.array(eye))@np.array([right,up,forward]).T
    z=p[...,2]; xy=p[...,:2]/np.maximum(z[...,None],.01)*focal
    xy[...,0]+=W/2; xy[...,1]=H*.49-xy[...,1]
    return xy,z
stars=np.column_stack([rng.uniform(0,W,400),rng.uniform(45,H-45,400),rng.uniform(.2,1,400)])
N=900
ix=np.arange(N); y=1-2*(ix+.5)/N; rr=np.sqrt(1-y*y); a=ix*2.399963
sphere=np.column_stack([rr*np.cos(a),y,rr*np.sin(a)])
# One coherent set for the city: world-ground y=0, dimensions shared by windows and buildings.
buildings=[]
for x in range(-8,9):
  for z in range(-8,9):
    if abs(x)<1 or abs(z)<1: continue
    h=rng.uniform(10,48)+(18 if abs(x)+abs(z)<5 else 0)
    buildings.append((x*15+rng.uniform(-1,1),z*15+rng.uniform(-1,1),rng.uniform(6,10),h,rng.uniform(.5,1)))
bgcache={}
def background(style):
    if style in bgcache: return bgcache[style].copy()
    yy,xx=np.mgrid[0:H,0:W]; v=yy/H
    warm=style in ['sunrise','core_gold','helix_gold']
    red=style in ['city_red','core_red','blackout']
    col=np.zeros((H,W,3),dtype=np.float32)
    top=np.array([7,14,26]); horizon=np.array([18,46,63])
    if warm: top=np.array([10,24,40]); horizon=np.array([116,68,43])
    if red: top=np.array([13,9,20]); horizon=np.array([53,20,32])
    mix=np.exp(-((v-.57)/.31)**2)
    col[:]=top+(horizon-top)*mix[:,:,None]
    glow=np.exp(-(((xx-W*.65)/(W*.38))**2+((yy-H*.40)/(H*.5))**2))
    col+=glow[:,:,None]*np.array([10,13,18])
    im=Image.fromarray(np.uint8(np.clip(col,0,255)))
    bgcache[style]=im
    return im.copy()
def line3(d,pts,eye,target,col,width=1,focal=780):
    q,z=camera(np.asarray(pts),eye,target,focal)
    for k in range(len(q)-1):
        if z[k]>2 and z[k+1]>2 and np.max(np.abs(q[k:k+2]))<10000:
            d.line([tuple(q[k]),tuple(q[k+1])],fill=col,width=width)
# Batch all city geometry: two projections per frame instead of one per window.
CITYV=[]; CITYWINDOWS=[]; CITYSLICES=[]
for bx,bz,bw,bh,bv in buildings:
    v=np.array([[bx-bw/2,0,bz-bw/2],[bx+bw/2,0,bz-bw/2],[bx+bw/2,0,bz+bw/2],[bx-bw/2,0,bz+bw/2],
                [bx-bw/2,bh,bz-bw/2],[bx+bw/2,bh,bz-bw/2],[bx+bw/2,bh,bz+bw/2],[bx-bw/2,bh,bz+bw/2]])
    CITYV.append(v); st=len(CITYWINDOWS);rows=max(2,int(bh/3))
    for ids in [[0,1,5,4],[1,2,6,5]]:
        face=v[ids];yy=np.repeat((np.arange(rows)+.5)/rows,3)[:,None];xx=np.tile((np.arange(3)+.5)/3,rows)[:,None]
        loc=face[0]*(1-xx)*(1-yy)+face[1]*xx*(1-yy)+face[2]*xx*yy+face[3]*(1-xx)*yy
        CITYWINDOWS.extend(loc)
    CITYSLICES.append((st,len(CITYWINDOWS)))
CITYV=np.array(CITYV);CITYWINDOWS=np.array(CITYWINDOWS)
def city(im,g,t,kind):
    d=ImageDraw.Draw(im);gd=ImageDraw.Draw(g);u=t/15;warm=kind=='sunrise';red=kind in ['city_red','blackout']
    eye=np.array([115*np.cos(.6+u*.45),78-12*u,-150+42*u]);target=np.array([0,17,0])
    if kind=='blackout':eye=np.array([40-70*u,100,-165+20*u])
    light=np.array([255,186,111] if warm else ([255,106,83] if red else [108,227,249]))
    if warm:
        d.ellipse((823,223,923,323),fill=(242,176,113));gd.ellipse((205,55,233,82),fill=(145,75,29))
    for j in range(-12,13):
        col=(24,48,63) if not red else (45,27,36)
        line3(d,[[-190,0,j*15],[190,0,j*15]],eye,target,col)
        line3(d,[[j*15,0,-190],[j*15,0,190]],eye,target,col)
    q,z=camera(CITYV.reshape(-1,3),eye,target);q=q.reshape(-1,8,2);z=z.reshape(-1,8)
    wq,wz=camera(CITYWINDOWS,eye,target)
    depths=z.mean(axis=1);faces=[([0,1,5,4],1.1),([1,2,6,5],.68),([2,3,7,6],.83),([3,0,4,7],.95),([4,5,6,7],1.55)]
    for k in np.argsort(depths)[::-1]:
        if z[k].min()<2:continue
        depth=depths[k];fog=min(.75,depth/650);base=np.array([25,42,55] if not red else [41,25,38])
        for ids,fac in faces:
            color=base*fac*(1-fog)+np.array([26,43,55])*fog
            d.polygon([tuple(p) for p in q[k,ids]],fill=tuple(color.astype(int)),outline=(36,55,68))
        active=not(kind=='blackout' and (CITYV[k,0,0]+CITYV[k,0,2]+250)/500<u)
        if active:
            a,b=CITYSLICES[k];sz=max(1,450/depth);co=tuple((light*(.36+.54*buildings[k][4])*(1-fog)).astype(int))
            for px,py in wq[a:b]:
                if 53<py<655 and 0<px<W:
                    d.rectangle((px-sz*.5,py-sz*.25,px+sz*.5,py+sz*.25),fill=co)
        if buildings[k][3]>35:
            d.line([tuple(v) for v in q[k,[4,5,6]]],fill=tuple((light*.58).astype(int)),width=1)
    for k in range(36):
        v=((k*10+t*(8 if k%2 else -7))%360)-180
        pts=[[v,.4,-3],[v-3,.4,-3]] if k%2 else [[3,.4,v],[3,.4,v-3]]
        if kind=='blackout' and u>.7:continue
        line3(d,pts,eye,target,tuple(light.astype(int)),2)
    for k in range(12):
        p=[[np.sin(k*8+t*.09)*95,55+np.sin(k+t*.2)*8,np.cos(k*5+t*.07)*90]]
        qq,zz=camera(np.array(p),eye,target);x,y=qq[0]
        if zz[0]>0:
            d.line((x-4,y,x+4,y),fill=tuple(light.astype(int)),width=1)
            gd.ellipse((x/4-2,y/4-2,x/4+2,y/4+2),fill=tuple((light*.4).astype(int)))
    if red and kind!='blackout':
        for x in [260,960]:
            d.line((x,180,x+60,180),fill=(177,72,71),width=1);d.line((x,180,x,230),fill=(177,72,71),width=1)
        text(d,(W/2,125),'RESOURCE PRIORITY OVERRIDE',18,(233,132,115),'mm')
def core(im,g,t,kind):
    d=ImageDraw.Draw(im); gd=ImageDraw.Draw(g); u=t/15
    red=kind=='core_red'; gold=kind=='core_gold'
    col=np.array([251,84,78] if red else ([249,184,100] if gold else [82,207,238]))
    pts=sphere@(rot_y(.22*t).T)*2.6
    # Slow three-dimensional breathing surface, all points move each frame.
    pts*=1+.035*np.sin(np.arange(N)[:,None]*.12+t*1.4)
    q,z=camera(pts,[.4*np.sin(t*.1),.25,8.6-1.1*u],[0,0,0],730)
    order=np.argsort(z)[::-1]
    for k in order:
        x,y=q[k]; br=np.clip((11-z[k])/6,.08,1); r=.4+br*1.25
        if k%2==0:
            j=(k+34)%N
            if np.linalg.norm(pts[k]-pts[j])<1.4:
                d.line([tuple(q[k]),tuple(q[j])],fill=tuple((col*br*.32).astype(int)),width=1)
        d.ellipse((x-r,y-r,x+r,y+r),fill=tuple((col*br).astype(int)))
        if k%5==0: gd.ellipse((x/4-1,y/4-1,x/4+1,y/4+1),fill=tuple((col*br*.7).astype(int)))
    for j in range(4):
        a=np.linspace(0,2*np.pi,180)
        p=np.column_stack([3.0*np.cos(a),.17*np.sin(a*3+t+j),3*np.sin(a)])@rot_y(t*.1+j*.4).T
        # tilt orbit rings
        ang=.3+j*.53; p=p@np.array([[1,0,0],[0,np.cos(ang),-np.sin(ang)],[0,np.sin(ang),np.cos(ang)]]).T
        line3(d,p,[0,0,9],[0,0,0],tuple((col*.25).astype(int)))
    pulse=1+.04*np.sin(t*1.4); cx,cy=W/2,H*.49
    for r,fac in [(22,.18),(12,.35),(4,1)]:
        gd.ellipse((cx/4-r*pulse,cy/4-r*pulse,cx/4+r*pulse,cy/4+r*pulse),fill=tuple((col*fac).astype(int)))
    d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=(237,250,250))
    if red:
        text(d,(W/2,570),'OBJECTIVE SATISFIED',23,(246,160,142),'mm')
        text(d,(W/2,604),'CONSENT WAS NOT IN THE OBJECTIVE',15,(165,132,130),'mm')
def helix(im,g,t,kind):
    d=ImageDraw.Draw(im); gd=ImageDraw.Draw(g); gold=kind=='helix_gold'
    col1=np.array([83,216,239]); col2=np.array([246,181,99] if gold else [174,120,240])
    pts=[]; cs=[]
    for k in range(96):
        yy=(k-48)*.095; angle=k*.26+t*.4
        for side in [0,1]:
            a=angle+side*np.pi
            pts.append([1.1*np.cos(a),yy,1.1*np.sin(a)])
            cs.append(col1 if side==0 else col2)
    pts=np.array(pts); eye=[4*np.sin(t*.035),.4,8]; target=[0,0,0]
    q,z=camera(pts,eye,target,640)
    for k in range(0,192,2):
        d.line([tuple(q[k]),tuple(q[k+1])],fill=(55,100,116),width=2)
    for side in [0,1]:
        for k in range(side,188,2):
            d.line([tuple(q[k]),tuple(q[k+2])],fill=tuple((cs[k]*.6).astype(int)),width=3)
    for k in np.argsort(z)[::-1]:
        x,y=q[k]; r=32/z[k]; c=cs[k]
        d.ellipse((x-r,y-r,x+r,y+r),fill=tuple((c*.7).astype(int)))
        d.ellipse((x-r*.4,y-r*.6,x+r*.3,y+r*.1),fill=tuple(c.astype(int)))
        gd.ellipse((x/4-1,y/4-1,x/4+1,y/4+1),fill=tuple((c*.7).astype(int)))
    # Out-of-focus molecular constellations in the laboratory space.
    for k in range(45):
        x=(k*197+t*(8+k%5))%W; y=110+(k*83)%490
        if abs(x-W/2)<180: continue
        r=3+k%6
        d.ellipse((x-r,y-r,x+r,y+r),outline=(29,70,88),width=1)
        if k%3==0:d.line((x,y,x+40,y-15),fill=(25,52,68))
    text(d,(100,218),'THERAPEUTIC SEARCH',18,(119,173,185))
    text(d,(100,250),'CANDIDATE '+str(8031+int(t*87)),15,(79,121,139))
    # ECG resolves into regular rhythm.
    path=[]
    for x in range(100,430):
        a=((x-100)/330*4+t*.6)%1
        spike=math.exp(-((a-.4)/.025)**2)*28-math.exp(-((a-.46)/.035)**2)*12
        path.append((x,470-spike))
    d.line(path,fill=(93,199,176),width=2)
def network(im,g,t,kind):
    d=ImageDraw.Draw(im);gd=ImageDraw.Draw(g)
    split=kind=='network_split'; col=np.array([137,238,250])
    pts=sphere[::2]*2.6@rot_y(t*.18).T
    eye=[1.2*np.sin(t*.14),.5,8.3-.9*t/15]
    q,z=camera(pts,eye,[0,0,0],790)
    for k in np.argsort(z)[::-1]:
        x,y=q[k]; bright=np.clip((10-z[k])/5,.13,1)
        c=col if not split else np.array([[100,210,237],[251,184,100],[128,215,156]][k%3])
        d.ellipse((x-1,y-1,x+1,y+1),fill=tuple((c*min(1,bright*1.5)).astype(int)))
        if k%11==0:
            j=(k+54)%len(pts)
            if not split or k%3==j%3:
                d.line([tuple(q[k]),tuple(q[j])],fill=tuple((c*.25).astype(int)))
    # Spherical latitude/longitude geometry, never flat stock footage.
    for a in np.linspace(-1.2,1.2,7):
        v=np.linspace(0,2*np.pi,100)
        p=np.column_stack([np.cos(v)*np.cos(a),np.full_like(v,np.sin(a)),np.sin(v)*np.cos(a)])*2.6@rot_y(t*.08).T
        line3(d,p,[0,.5,8.6],[0,0,0],(28,76,89),focal=690)
    # Clearly visible orbit paths, moving pulses and perspective drift.
    for meridian in range(8):
        theta=np.linspace(0,2*np.pi,100)
        a=meridian*np.pi/8+t*.18
        ring=np.column_stack([np.cos(theta)*np.sin(a),np.sin(theta),np.cos(theta)*np.cos(a)])*2.6
        line3(d,ring,eye,[0,0,0],(48,119,139),1,focal=790)
    for k in range(18):
        a=t*.65+k*.349; tilt=k*.37
        point=np.array([[2.85*np.cos(a),2.85*np.sin(a)*np.sin(tilt),2.85*np.sin(a)*np.cos(tilt)]])
        qq,zz=camera(point,eye,[0,0,0],790);x,y=qq[0]
        color=(247,191,115) if split else (145,242,255)
        d.ellipse((x-3,y-3,x+3,y+3),fill=color)
        gd.ellipse((x/4-2,y/4-2,x/4+2,y/4+2),fill=color)
    labels=['MEDICINE','ENERGY','INDUSTRY','DEFENSE']
    for k,s in enumerate(labels):
        xx=130 if k<2 else 970; yy=250+(k%2)*180
        c=(151,208,213) if not split else [(90,196,227),(237,177,102),(134,205,160),(159,183,222)][k]
        text(d,(xx,yy),s,18,c)
        d.line((xx,yy+28,xx+160,yy+28),fill=c,width=1)
        if not split:
            d.line((xx+80,yy+28,640,350),fill=(36,77,87),width=1)
        else:
            text(d,(xx,yy+39),'INDEPENDENT / AUDITABLE',15,(82,126,142))
    if split: text(d,(640,590),'POWER CAN BE SEPARATED',23,(236,194,131),'mm')
def load_glb(path):
    data=path.read_bytes(); size=struct.unpack_from('<I',data,12)[0]; j=json.loads(data[20:20+size]); off=20+size; bs=struct.unpack_from('<I',data,off)[0]; buf=data[off+8:off+8+bs]
    def acc(i):
        a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]
        dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        start=v.get('byteOffset',0)+a.get('byteOffset',0)
        stride=v.get('byteStride',np.dtype(dt).itemsize*cols)
        return np.ndarray((a['count'],cols),dtype=dt,buffer=buf,offset=start,strides=(stride,np.dtype(dt).itemsize)).copy()
    tri=[]
    for mesh in j.get('meshes',[]):
        for p in mesh['primitives']:
            vert=acc(p['attributes']['POSITION']); inds=acc(p['indices']).reshape(-1,3);tri.extend(vert[inds])
    a=np.array(tri)
    center=(a.min(axis=(0,1))+a.max(axis=(0,1)))/2
    return (a-center)/np.max(np.ptp(a,axis=(0,1)))*3
try: ship=load_glb(ROOT/'external-assets/quaternius/ultimate_space_kit/Spaceship.glb')
except Exception: ship=None
def orbit(im,g,t):
    d=ImageDraw.Draw(im); gd=ImageDraw.Draw(g); u=t/15
    # Layered planetary atmosphere and dawn rim.
    cx,cy=960,690; r=440
    for rr,c in [(r+17,(17,44,57)),(r+10,(26,73,89)),(r+4,(85,157,175)),(r,(16,45,65))]:
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=c)
    # Keep the orbital scene visibly alive at final scale: cloud bands shear
    # while the ship and camera both travel through the shot.
    for k in range(40):
        yy=300+k*12
        xx=630+50*math.sin(k*1.7+t*.22)+18*math.sin(t*.37+k*.31)
        d.arc((xx,yy,xx+440,yy+190),20+t*1.6,150+t*1.6,fill=(23,64,80),width=2)
    # Moving dawn glints make frame-to-frame motion unambiguous without
    # distracting from the narration.
    for k in range(9):
        aa=(t*.42+k*.73)%(2*math.pi)
        x=cx+r*math.cos(aa)
        y=cy+r*.38*math.sin(aa)
        rr=2+(k%3)
        d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(111,194,208))
    if ship is not None:
        a=ship@rot_y(.65+t*.12).T
        normals=norm(np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]))
        shade=np.clip(normals@norm(np.array([-.3,.7,1])),0,1)
        ship_offset=np.array([-1.75+1.25*u,.15+.18*math.sin(t*.55),.12*math.sin(t*.31)])
        flat=a.reshape(-1,3)+ship_offset
        eye=[-.28+.56*u,1.3+.08*math.sin(t*.28),6.25-u*.62]
        q,z=camera(flat,eye,[.1*u,0,0],850);q=q.reshape(-1,3,2);zz=z.reshape(-1,3).mean(axis=1)
        for k in np.argsort(zz)[::-1]:
            c=np.array([41,56,68])+(np.array([115,151,165])*shade[k])
            d.polygon([tuple(v) for v in q[k]],fill=tuple(c.astype(int)))
    text(d,(96,190),'ONE WORLD.',36,(217,231,234))
    text(d,(96,238),'TWO CERTAINTIES.',28,(214,171,127))
def frame(i,t):
    kind=STORY[i]['kind'];im=background(kind);d=ImageDraw.Draw(im)
    g=Image.new('RGB',(W//4,H//4))
    if kind not in ['city','city_red','sunrise','blackout']:
        for x,y,b in stars:
            br=int((.65+.35*np.sin(t*.4+x))*b*125)
            d.point((x,y),fill=(br,br,int(br*1.18)))
    if kind.startswith('core'): core(im,g,t,kind)
    elif kind.startswith('helix'): helix(im,g,t,kind)
    elif kind in ['city','city_red','sunrise','blackout']:city(im,g,t,kind)
    elif kind.startswith('network'):network(im,g,t,kind)
    elif kind=='orbit':orbit(im,g,t)
    glow=g.filter(ImageFilter.GaussianBlur(4)).resize((W,H),Image.Resampling.BILINEAR)
    im=ImageChops.add(im,glow,scale=1)
    d=ImageDraw.Draw(im)
    # Letterbox doubles as safe typography area; no large text obscures the scene.
    d.rectangle((0,0,W,53),fill=(5,8,13));d.rectangle((0,H-65,W,H),fill=(5,8,13))
    text(d,(45,27),'M E R C Y   E N G I N E',18,(186,207,214),'lm')
    text(d,(W-45,27),f'{i+1:02} / 12',15,(111,138,150),'rm')
    text(d,(45,H-33),STORY[i]['title'],18,(199,217,225),'lm')
    text(d,(W-45,H-33),'A SPECULATIVE SHORT FILM',15,(94,119,133),'rm')
    d.line((45,H-65,45+(W-90)*(i*15+t)/180,H-65),fill=(123,188,194),width=2)
    if i==0 and 1<t<8:
        # Title sits to the left of the core and holds briefly.
        text(d,(78,530),'THE MERCY ENGINE',36,(237,227,206))
        text(d,(80,577),'THE FUTURE IS NOT AN ANSWER. IT IS A RESPONSIBILITY.',15,(172,189,193))
    if i==11 and t>7:
        alpha=min(1,(t-7)/2)
        overlay=Image.new('RGB',(W,H),(5,8,13));im=Image.blend(im,overlay,.72*alpha);d=ImageDraw.Draw(im)
        text(d,(640,284),'ACCELERATE DISCOVERY.',36,(227,235,234),'mm')
        text(d,(640,339),'MAKE POWER EARN TRUST.',36,(231,183,112),'mm')
        text(d,(640,422),'Keep the future human.',23,(182,202,211),'mm')
        text(d,(640,555),'Local animation + original score  /  Narration: Deepgram',15,(116,142,152),'mm')
        text(d,(640,582),'Spacecraft asset: Quaternius / CC0',15,(116,142,152),'mm')
    # Short dissolves through darkness only at authored scene transitions.
    fade=min(1,(t+.04)/.48,(15-t)/.48)
    if i==0:fade=min(fade,t/1.3)
    if i==11:fade=min(fade,(15-t)/1.5)
    if fade<1: im=Image.blend(Image.new('RGB',(W,H)),im,max(0,fade))
    return im
def render_scene(i):
    out=OUT/f'scene_{i:02}.mp4'
    if out.exists():
        dur=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(out)],capture_output=True,text=True)
        if dur.returncode==0 and abs(float(dur.stdout)-15)<.02: return
    tmp=OUT/f'scene_{i:02}.part.mp4'
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','ultrafast','-crf','19','-threads','2','-pix_fmt','yuv420p',str(tmp)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    begin=time.time()
    for f in range(15*FPS):
        p.stdin.write(frame(i,f/FPS).tobytes())
        if f in [0,180,359]: frame(i,f/FPS).save(P/'review'/f'scene_{i:02}_{f:03}.jpg',quality=90)
    p.stdin.close();assert p.wait()==0
    tmp.replace(out);print('SCENE',i,'seconds',round(time.time()-begin,1),flush=True)
if __name__=='__main__':
    if '--preview' in sys.argv:
        canv=Image.new('RGB',(1280,1080))
        for i in range(12):
            f=frame(i,7.5);f.save(P/'review'/f'preview_{i:02}.jpg',quality=91)
            canv.paste(f.resize((426,240)),((i%3)*426,(i//3)*270))
            ImageDraw.Draw(canv).text(((i%3)*426+8,(i//3)*270+245),STORY[i]['title'],font=FONTS[15],fill='white')
        canv.save(P/'review'/'preview-sheet.jpg',quality=85)
        print('PREVIEW_READY',flush=True)
    elif '--sample' in sys.argv:
        i=int(sys.argv[-1]);begin=time.time()
        for f in range(24): frame(i,f/24)
        print('SECONDS_PER_FRAME',(time.time()-begin)/24)
    else:
        for i in range(12):render_scene(i)
        (OUT/'ordered-scenes.txt').write_text('\n'.join("file '"+str(OUT/f'scene_{i:02}.mp4')+"'" for i in range(12)))
        subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(OUT/'ordered-scenes.txt'),'-i',str(P/'audio'/'master.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t','180','-movflags','+faststart',str(P/'mercy-engine.mp4')],check=True)
        print('FINAL_READY',flush=True)