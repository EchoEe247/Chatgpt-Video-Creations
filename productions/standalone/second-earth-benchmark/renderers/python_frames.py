#!/usr/bin/env python3
from __future__ import annotations
import math, random
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
import numpy as np

W,H=1280,720
FONT_REG="/system/fonts/Roboto-Regular.ttf"
FONT_BOLD="/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
def font(n,b=False):
    try:return ImageFont.truetype(FONT_BOLD if b else FONT_REG,n)
    except:return ImageFont.load_default()

def clamp(x,a=0,b=1): return max(a,min(b,x))
def ease(x): x=clamp(x); return x*x*(3-2*x)
def lerp(a,b,t): return a+(b-a)*t
def mix(c1,c2,t): return tuple(int(lerp(c1[i],c2[i],t)) for i in range(3))
def text(draw,xy,s,size=32,fill=(235,242,244),anchor="mm",bold=False):
    draw.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def glow_dot(im,xy,r,col,blur=16):
    g=Image.new("RGBA",im.size,(0,0,0,0)); d=ImageDraw.Draw(g)
    x,y=xy
    d.ellipse((x-r,y-r,x+r,y+r),fill=(*col,190))
    g=g.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(g)
def gradient(top,bottom):
    arr=np.zeros((H,W,3),dtype=np.uint8)
    for y in range(H):
        t=y/(H-1); arr[y,:,:]=[int(lerp(top[i],bottom[i],t)) for i in range(3)]
    return Image.fromarray(arr,"RGB").convert("RGBA")
def stars(im,t,count=180,seed=7):
    rng=random.Random(seed);d=ImageDraw.Draw(im)
    for i in range(count):
        x=(rng.random()*W+t*(1+(i%5))*.9)%W; y=40+rng.random()*(H-80)
        b=90+int(120*(.5+.5*math.sin(t*.7+i)))
        d.point((x,y),fill=(b,b,min(255,b+30),190))
def bar(draw,x,y,w,h,fill):
    draw.rounded_rectangle((x,y,x+w,y+h),radius=min(h/2,8),fill=fill)

def shot01(im,t,dur):
    d=ImageDraw.Draw(im); u=ease(t/dur)
    cx,cy=W/2,H/2+20; R=lerp(40,250,ease(min(1,t/3.0)))
    for k in range(180):
        a=k*2.399963+t*.18; rr=R*math.sqrt((k+.5)/180)
        x=cx+rr*math.cos(a);y=cy+rr*.62*math.sin(a)
        b=int(100+130*(k%7)/6);d.ellipse((x-1.5,y-1.5,x+1.5,y+1.5),fill=(70,b,220,210))
    for k in range(18):
        a=k*math.pi/9+t*.35;r=R*.88
        x=cx+r*math.cos(a); y=cy+r*.48*math.sin(a)
        d.line((cx,cy,x,y),fill=(35,110,140,90),width=1)
    # city-grid message grows from the geometry rather than a plain title.
    p=ease(clamp((t-2.6)/2.4))
    if p>0:
        phrase="ARE YOU THERE?"
        tw=d.textbbox((0,0),phrase,font=font(74,True))[2]
        x0=(W-tw)/2
        for i,ch in enumerate(phrase):
            frac=clamp(p*len(phrase)-i)
            if frac<=0: continue
            x=x0+i*(tw/max(1,len(phrase)-1))
            d.line((cx,cy,x,H*.48),fill=(45,132,160,int(100*frac)),width=1)
        text(d,(W/2,H*.48),phrase,74,(225,246,248,int(255*p)) if im.mode=="RGBA" else (225,246,248),"mm",True)
    glow_dot(im,(cx,cy),18,(244,174,91),18)

def shot04(im,t,dur):
    d=ImageDraw.Draw(im);stars(im,t,120,17);cx,cy=W/2,H/2
    u=t/dur
    for ring in range(6):
        r=95+ring*33+10*math.sin(t*.9+ring)
        col=mix((62,157,199),(230,172,90),ring/5)
        d.ellipse((cx-r,cy-r*.55,cx+r,cy+r*.55),outline=(*col,180),width=2)
        for k in range(10):
            a=t*(1.2+ring*.15)+k*math.tau/10
            x=cx+r*math.cos(a);y=cy+r*.55*math.sin(a)
            d.ellipse((x-3,y-3,x+3,y+3),fill=(*col,220))
    for y in range(-4,5):
        yy=cy+y*22
        d.line((cx-110,yy,cx+110,yy),fill=(40,120,145,110),width=1)
    for x in range(-5,6):
        xx=cx+x*20
        d.line((xx,cy-95,xx,cy+95),fill=(40,120,145,110),width=1)
    # morphology change: vertical towers grow around core
    for k in range(14):
        a=k*math.tau/14+t*.25; r=150+22*math.sin(k)
        x=cx+r*math.cos(a); base=cy+r*.35*math.sin(a)
        h=20+70*(.5+.5*math.sin(t*1.6+k))
        d.rectangle((x-5,base-h,x+5,base),fill=(35,74,92,220))
        d.rectangle((x-3,base-h+5,x+3,base-h+8),fill=(237,183,101,220))
    text(d,(86,92),f"ERA  {int(1+t*220):04d}",26,(181,204,214),"la",True)

def molecule_panel(d,x0,y0,w,h,t,mode):
    d.rounded_rectangle((x0,y0,x0+w,y0+h),radius=18,fill=(12,22,34,220),outline=(62,102,125,180),width=2)
    if mode==0:
        pts=[]
        for i in range(10):
            a=i*2.2+t*.6;r=40+18*(i%3); pts.append((x0+w/2+r*math.cos(a),y0+h/2+r*.55*math.sin(a)))
        for i,p in enumerate(pts):
            q=pts[(i*3+2)%len(pts)];d.line((p,q),fill=(71,120,150,150),width=2)
        for i,(x,y) in enumerate(pts): d.ellipse((x-8,y-8,x+8,y+8),fill=(104,210,232) if i<6 else (218,148,220))
    elif mode==1:
        for k in range(16):
            a=k*math.tau/16+t*.15;r=65+16*math.sin(k*2+t)
            x=x0+w/2+r*math.cos(a);y=y0+h/2+r*.6*math.sin(a)
            d.arc((x-35,y-18,x+35,y+18),0,220,fill=(84,202,213),width=2)
        d.ellipse((x0+w*.42,y0+h*.36,x0+w*.58,y0+h*.58),outline=(170,232,235),width=4)
    else:
        for yy in range(5):
            for xx in range(8):
                x=x0+45+xx*34+(yy%2)*17;y=y0+45+yy*30
                s=6+2*math.sin(t*2+xx+yy)
                d.ellipse((x-s,y-s,x+s,y+s),fill=(235,184,91) if (xx+yy)%3==0 else (95,157,188))
                if xx<7:d.line((x+6,y,x+34,y),fill=(73,98,118),width=1)

def shot08(im,t,dur):
    d=ImageDraw.Draw(im)
    seg=min(2,int(t/(dur/3)))
    labels=["PROTEIN LOCKED","STORM PATH SHIFTED","LATTICE STABILIZED"]
    for i in range(3):
        x=80+i*400
        a=1 if i<seg else ease((t-i*dur/3)/(dur/3)) if i==seg else 0
        molecule_panel(d,x,170,330,330,t,i)
        col=(240,194,100) if a>.3 else (105,135,150)
        text(d,(x+165,545),labels[i],28,col,"mm",True)
        if a>.4:
            d.line((x+60,570,x+270,570),fill=col,width=3)

def shot14(im,t,dur):
    d=ImageDraw.Draw(im);stars(im,t*.2,150,31)
    # Deliberate lateral reveal after shot-13's push: the map travels across frame
    # while the scan discovers repeated pulse bands on the newly exposed side.
    u=ease(t/dur)
    cx,cy=lerp(W*.68,W*.45,u),H/2+10
    for r in range(60,300,36):
        d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(40,79,106,130),width=1)
    for k in range(28):
        a=k*.73; r=30+(k*23)%280; val=.5+.5*math.sin(k*2.7)
        col=mix((60,110,170),(210,90,70),val)
        x=cx+r*math.cos(a); y=cy+r*math.sin(a)
        d.rectangle((x-5,y-5,x+5,y+5),fill=(*col,180))
    scan=(t/dur)*math.tau
    x=cx+270*math.cos(scan);y=cy+270*math.sin(scan)
    d.line((cx,cy,x,y),fill=(220,235,240,190),width=2)
    p=ease(clamp((t-3.6)/2.1))
    for k in range(7):
        a=-1.0+k*.32; r=215
        x=cx+r*math.cos(a);y=cy+r*math.sin(a)
        d.ellipse((x-6*p,y-6*p,x+6*p,y+6*p),fill=(245,216,145,220))
    reveal=ease(clamp((t-2.2)/3.0))
    for k in range(5):
        y=220+k*64
        x0=900+55*math.sin(k*.8+t*.4)
        d.line((x0,y,x0+150*reveal,y),fill=(240,203,130,190),width=3)
    text(d,(88,92),"COSMIC BACKGROUND / CORRELATION",30,(178,200,214),"la",True)

def shot15(im,t,dur):
    d=ImageDraw.Draw(im);stars(im,t*.15,220,51)
    u=ease(t/dur);cx,cy=W/2,H/2
    scales=[(58,(87,197,229)),(120,(88,112,185)),(220,(147,91,188)),(360,(225,171,95))]
    for idx,(base,col) in enumerate(scales):
        r=base*(.45+1.2*u)+idx*14
        d.ellipse((cx-r,cy-r*.62,cx+r,cy+r*.62),outline=(*col,180),width=max(1,4-idx))
        for k in range(6+idx*3):
            a=k*math.tau/(6+idx*3)+t*.08*(idx+1)
            x=cx+r*math.cos(a);y=cy+r*.62*math.sin(a)
            d.ellipse((x-2,y-2,x+2,y+2),fill=(*col,180))
    # foreground shells cross frame to make pull-back spatial
    for k in range(5):
        x=(W+260)-((t*95+k*310)%(W+620))
        d.arc((x-180,-100,x+250,H+140),70,290,fill=(53,74,110,90),width=5)
    text(d,(W/2,620),"THE OBSERVER MAY ALSO BE OBSERVED",30,(196,208,220),"mm",True)

def shot17(im,t,dur):
    d=ImageDraw.Draw(im);cx=190;cy=H/2
    d.line((cx,cy,W-110,cy),fill=(120,140,155,170),width=3)
    split=430
    d.ellipse((split-9,cy-9,split+9,cy+9),fill=(240,239,224))
    # left collapse
    p=ease(t/dur)
    d.line((split,cy,690,210),fill=(110,130,145,170),width=3)
    d.line((split,cy,690,510),fill=(197,144,87,180),width=3)
    for i in range(7):
        x=690+i*68*p
        d.line((x,510-i*22,x+55,455-i*10),fill=(188,126,210,140),width=2)
        d.line((x,510-i*22,x+55,555+i*7),fill=(210,166,95,140),width=2)
    black=clamp((t-2.3)/3.3)
    d.rectangle((700,120,1180,330),fill=(5,8,13,int(240*black)))
    text(d,(W/2,96),"TWO CERTAINTIES.  BOTH UNPROVEN.",26,(226,230,230),"mm",True)

def shot19(im,t,dur):
    d=ImageDraw.Draw(im);cx=W/2
    d.line((cx,90,cx,630),fill=(84,190,208,210),width=4)
    for side in [-1,1]:
        for k in range(9):
            phase=(t*.9+k*.37)%1
            x=cx+side*(55+420*phase); y=150+(k*53)%430
            col=(94,210,224) if side<0 else (238,186,95)
            d.ellipse((x-5,y-5,x+5,y+5),fill=(*col,220))
            d.line((x,y,cx,y),fill=(*col,70),width=1)
    # molecule left
    molecule_panel(d,85,175,360,300,t,0)
    # telescope right
    d.ellipse((850,230,1090,470),outline=(236,188,105,200),width=5)
    d.line((970,350,1150,220),fill=(236,188,105,170),width=5)
    p=ease(clamp((t-4.0)/2.7))
    if p>0:
        d.arc((500,260,780,540),180,180+180*p,fill=(245,240,220),width=6)
        text(d,(W/2,575),"PROOF COMPLETES ONLY WHEN BOTH HALVES CONNECT",28,(205,218,222),"mm",True)

def render_frame(shot, frame_index, output_path, request):
    sid=shot["id"];fps=float(shot["fps"]);dur=float(shot["duration_seconds"]);t=frame_index/fps
    palettes={
      "shot-01":((3,7,13),(9,24,40)),"shot-04":((8,10,24),(34,15,48)),"shot-08":((7,15,25),(11,27,36)),
      "shot-14":((4,6,14),(11,20,36)),"shot-15":((3,4,11),(20,9,31)),"shot-17":((7,10,18),(22,18,28)),"shot-19":((4,9,16),(11,26,33))
    }
    im=gradient(*palettes.get(sid,((5,8,13),(14,25,38))))
    if sid in {"shot-01","shot-04","shot-14","shot-15"}: stars(im,t,120,hash(sid)&0xffff)
    globals()[sid.replace("-","")](im,t,dur) if sid.replace("-","") in globals() else {
      "shot-01":shot01,"shot-04":shot04,"shot-08":shot08,"shot-14":shot14,
      "shot-15":shot15,"shot-17":shot17,"shot-19":shot19
    }[sid](im,t,dur)
    d=ImageDraw.Draw(im)
    # fade only at hard boundaries
    f=min(1,t/.25,(dur-t)/.25)
    if f<1:
        black=Image.new("RGBA",im.size,(0,0,0,255))
        im=Image.blend(black,im,max(0,f))
    Path(output_path).parent.mkdir(parents=True,exist_ok=True)
    im.convert("RGB").save(output_path,quality=95)