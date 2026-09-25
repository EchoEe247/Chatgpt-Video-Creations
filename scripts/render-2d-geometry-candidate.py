from __future__ import annotations
import json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.core.geometry import Camera2D, Point, SetGeometry
from src.core.fonts import find_dejavu_sans
from src.animation_2d.layout import CharacterRigLayout, place_character, place_portal

W,H,FPS,DUR=1280,720,24,8.0
N=int(FPS*DUR)
OUT=Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'2d_geometry_candidate_001.mp4'
OUT.parent.mkdir(parents=True, exist_ok=True)
FONT=find_dejavu_sans()
FONT_B=find_dejavu_sans(bold=True)

def font(sz,b=False):
    try:return ImageFont.truetype(FONT_B if b else FONT,sz)
    except:return ImageFont.load_default()

with open(ROOT/'candidates/2d-geometry-001/set.json') as f:
    SET=SetGeometry.from_mapping(json.load(f))
assert SET.canvas and SET.canvas.width==W and SET.canvas.height==H
RIG=CharacterRigLayout(foot_anchor_px=Point(110,326))

def clamp01(x): return max(0.0,min(1.0,x))
def smooth(x):
    x=clamp01(x); return x*x*(3-2*x)
def lerp(a,b,t): return a+(b-a)*t

def camera_at(t):
    if t < 2.2:
        u=smooth(t/2.2); a=(0,0,1.0); b=(30,25,1.06)
    elif t < 4.6:
        u=smooth((t-2.2)/2.4); a=(30,25,1.06); b=(120,100,1.18)
    elif t < 6.2:
        u=smooth((t-4.6)/1.6); a=(120,100,1.18); b=(150,125,1.22)
    else:
        u=smooth((t-6.2)/1.8); a=(150,125,1.22); b=(0,0,1.0)
    return Camera2D(origin=Point(lerp(a[0],b[0],u),lerp(a[1],b[1],u)),scale=lerp(a[2],b[2],u))

def proj(cam,x,y):
    p=cam.point_to_screen(Point(x,y)); return (p.x,p.y)

def line_world(d,cam,pts,fill,width=1):
    d.line([proj(cam,*p) for p in pts],fill=fill,width=max(1,int(width*cam.scale)))

def rect_world(d,cam,box,fill,outline=None,width=1):
    x0,y0=proj(cam,box[0],box[1]); x1,y1=proj(cam,box[2],box[3])
    d.rectangle((x0,y0,x1,y1),fill=fill,outline=outline,width=max(1,int(width*cam.scale)))

def circle(d,cx,cy,r,fill=None,outline=None,width=1):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=fill,outline=outline,width=max(1,int(width)))

def make_character(kind,t):
    im=Image.new('RGBA',(220,340),(0,0,0,0)); d=ImageDraw.Draw(im)
    if kind=='vex':
        skin=(235,201,165,255); coat=(33,106,118,255); shirt=(187,68,126,255); hair=(147,76,187,255); pants=(70,66,82,255); phase=0.0
    else:
        skin=(241,171,107,255); coat=(177,65,48,255); shirt=(213,202,172,255); hair=(92,54,36,255); pants=(47,79,111,255); phase=.7
    d.polygon([(78,233),(104,233),(101,309),(73,309)],fill=pants,outline=(20,22,28,255))
    d.polygon([(116,233),(142,233),(147,309),(119,309)],fill=pants,outline=(20,22,28,255))
    d.rounded_rectangle((62,305,105,326),radius=7,fill=(237,239,237,255),outline=(18,20,23,255),width=2)
    d.rounded_rectangle((116,305,159,326),radius=7,fill=(237,239,237,255),outline=(18,20,23,255),width=2)
    d.rounded_rectangle((55,150,165,240),radius=22,fill=coat,outline=(23,23,29,255),width=3)
    d.rounded_rectangle((87,160,133,226),radius=7,fill=shirt,outline=(25,25,30,255),width=2)
    swing=math.sin(t*2.5+phase)*8
    if kind=='vex': swing+=6*math.sin(t*1.2)
    for side in (-1,1):
        shoulder=(58 if side<0 else 162,169); ex=shoulder[0]+side*(24+swing*side); ey=213+abs(swing)*0.4; hx=ex+side*17; hy=244
        d.line([shoulder,(ex,ey),(hx,hy)],fill=coat,width=17,joint='curve'); circle(d,hx,hy,7,fill=skin,outline=(25,25,30,255),width=2)
    bob=math.sin(t*3+phase)*2.5; head_y=105+bob
    circle(d,110,head_y,54,fill=skin,outline=(25,25,30,255),width=3)
    if kind=='vex':
        pts=[]
        for i in range(16):
            a=2*math.pi*i/16-math.pi/2; rr=68 if i%2==0 else 50; pts.append((110+math.cos(a)*rr,head_y+math.sin(a)*rr))
        d.polygon(pts,fill=hair,outline=(25,25,30,255)); circle(d,110,head_y,49,fill=skin,outline=(25,25,30,255),width=2)
    else:
        d.pieslice((48,39+bob,172,148+bob),180,360,fill=hair,outline=(25,25,30,255),width=2)
    eye_y=head_y-5
    for ex in (85,135):
        circle(d,ex,eye_y,14,fill=(248,248,242,255),outline=(24,24,30,255),width=2); circle(d,ex+4*math.sin(t*1.1+phase),eye_y,4.5,fill=(20,22,28,255))
    if (t+phase)%3.4 < .10:
        for ex in (85,135): d.line((ex-12,eye_y,ex+12,eye_y),fill=(20,22,28,255),width=3)
    if int(t*3+phase*4)%5 in (1,2): d.ellipse((94,head_y+24,126,head_y+41),fill=(61,28,31,255),outline=(20,20,25,255),width=2)
    else: d.line((94,head_y+30,126,head_y+30),fill=(30,30,34,255),width=3)
    return im

def draw_set(im,d,cam):
    im.paste((20,25,36),(0,0,W,H))
    for x in range(0,1401,120): line_world(d,cam,[(x,70),(x,525)],(52,60,73),1)
    line_world(d,cam,[(0,84),(1280,84)],(38,45,58),3)
    rect_world(d,cam,(70,326,760,350),(91,61,41)); rect_world(d,cam,(100,350,133,525),(77,82,91)); rect_world(d,cam,(210,292,345,332),(10,17,25),outline=(4,7,10),width=3); rect_world(d,cam,(227,304,328,321),(51,205,214))
    for box,title,lines in [((74,128,357,282),'LAB RULES',['1. One geometry source','2. Feet use contact anchors','3. Effects inherit sources']),((423,132,718,286),'CANDIDATE CHECK',['✓ shared floor anchors','✓ shared portal center','✓ shared camera transform'])]:
        x0,y0=proj(cam,box[0],box[1]); x1,y1=proj(cam,box[2],box[3]); d.rounded_rectangle((x0,y0,x1,y1),radius=max(8,int(14*cam.scale)),fill=(226,222,204),outline=(17,20,25),width=max(1,int(2*cam.scale))); d.text((x0+26*cam.scale,y0+20*cam.scale),title,font=font(max(12,int(26*cam.scale)),True),fill=(43,47,56)); fy=y0+68*cam.scale
        for ln in lines: d.text((x0+26*cam.scale,fy),ln,font=font(max(10,int(15*cam.scale))),fill=(53,56,64)); fy+=28*cam.scale
    fy=proj(cam,0,SET.floor_y)[1]; y0=proj(cam,0,520)[1]; d.rectangle((0,y0,W,H),fill=(83,68,55))
    for x in range(-200,1500,100): line_world(d,cam,[(640,520),(x,720)],(112,86,65),1)
    for y in range(555,721,45): line_world(d,cam,[(0,y),(1280,y)],(104,82,64),1)
    d.line((0,fy,W,fy),fill=(245,207,66),width=max(1,int(2*cam.scale)))

def draw_portal(d,cam,t):
    p=place_portal(set_geometry=SET,camera=cam); cx,cy=p.frame_outer.center.x,p.frame_outer.center.y; ro=p.frame_outer.radius; ri=p.frame_inner.radius
    circle(d,cx,cy,ro,fill=(21,27,36),outline=(6,10,15),width=max(2,int(8*cam.scale))); circle(d,cx,cy,ro*0.88,fill=(73,82,96),outline=(105,113,126),width=max(2,int(6*cam.scale)))
    for i in range(12):
        a=2*math.pi*i/12; br=ro*0.93; circle(d,cx+math.cos(a)*br,cy+math.sin(a)*br,max(4,6*cam.scale),fill=(112,120,132),outline=(10,13,18),width=1)
    circle(d,cx,cy,ri,fill=(20,50,38),outline=(21,168,67),width=max(2,int(7*cam.scale)))
    e=p.energy
    assert abs(e.center.x-cx)<1e-9 and abs(e.center.y-cy)<1e-9 and abs(e.radius-ri)<1e-9
    pulse=.96+.025*math.sin(t*5)
    for frac in (.92,.78,.64,.50,.36,.22): circle(d,e.center.x,e.center.y,e.radius*frac*pulse,outline=(78,255,130),width=max(2,int(4*cam.scale)))
    circle(d,e.center.x,e.center.y,max(8,12*cam.scale),fill=(207,244,79),outline=(82,255,130),width=max(1,int(2*cam.scale)))
    for i in range(14):
        a=0.9*i+t*(0.8+0.03*i); rr=e.radius*(.18+.7*((i*37)%100)/100); circle(d,e.center.x+math.cos(a)*rr,e.center.y+math.sin(a)*rr,max(1.5,2.4*cam.scale),fill=(194,255,186))
    return p

def draw_character_world(im,d,cam,t,kind,anchor_name,scale):
    pl=place_character(character=kind,set_geometry=SET,set_anchor=anchor_name,rig=RIG,camera=cam,sprite_scale=scale).placement; ax,ay=pl.anchor_screen.x,pl.anchor_screen.y; d.ellipse((ax-62*pl.scale,ay-10*pl.scale,ax+62*pl.scale,ay+8*pl.scale),fill=(25,24,24)); spr=make_character(kind,t); spr=spr.resize((max(1,int(round(spr.width*pl.scale))),max(1,int(round(spr.height*pl.scale)))),Image.Resampling.LANCZOS); im.alpha_composite(spr,(int(round(pl.top_left.x)),int(round(pl.top_left.y)))); return pl

def render_frame(i):
    t=i/FPS; cam=camera_at(t); im=Image.new('RGBA',(W,H),(20,25,36,255)); d=ImageDraw.Draw(im); draw_set(im,d,cam); portal=draw_portal(d,cam,t); vex=draw_character_world(im,d,cam,t,'vex','vex_start',0.92); milo=draw_character_world(im,d,cam,t,'milo','milo_start',0.92)
    d.rounded_rectangle((24,20,610,76),radius=14,fill=(9,14,22,235)); d.text((44,34),'2D GEOMETRY CANDIDATE 001 — NOT B1',font=font(22,True),fill=(242,245,247)); d.rounded_rectangle((24,640,655,698),radius=12,fill=(9,14,22,225)); d.text((42,657),f'camera origin=({cam.origin.x:.0f},{cam.origin.y:.0f})  scale={cam.scale:.2f}   floor/contact + portal share transform',font=font(15),fill=(207,218,228))
    if t<1.8 or t>7.3:
        for pl in (vex,milo): circle(d,pl.anchor_screen.x,pl.anchor_screen.y,6,fill=(255,220,45),outline=(20,20,20),width=1)
        pc=portal.energy.center; d.line((pc.x-15,pc.y,pc.x+15,pc.y),fill=(255,220,45),width=2); d.line((pc.x,pc.y-15,pc.x,pc.y+15),fill=(255,220,45),width=2)
    return im.convert('RGB')

cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(N): p.stdin.write(render_frame(i).tobytes())
p.stdin.close(); rc=p.wait()
if rc: raise SystemExit(rc)
print(OUT)