#!/usr/bin/env python3
"""Create a mobile-friendly synchronized B/C video review page."""
from __future__ import annotations

import argparse
import html
from pathlib import Path


def relative_media(path: Path, output: Path) -> str:
    try:
        return path.relative_to(output.parent).as_posix()
    except ValueError as exc:
        raise ValueError("review videos must live under the review page directory") from exc


def build_page(b_src: str, c_src: str, *, title: str, fps: float, b_label: str = "B · Conventional post", c_label: str = "C · Pass-aware finishing") -> str:
    safe_title=html.escape(title)
    safe_b_label=html.escape(b_label)
    safe_c_label=html.escape(c_label)
    b=html.escape(b_src,quote=True)
    c=html.escape(c_src,quote=True)
    frame=1.0/fps
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{safe_title}</title>
<style>
:root{{color-scheme:dark;--bg:#070a10;--card:#111722;--line:#2a3444;--text:#edf3fb;--muted:#9fb0c5;--accent:#79b7ff}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font:16px system-ui,-apple-system,sans-serif}}
main{{max-width:1200px;margin:auto;padding:12px}}
h1{{font-size:22px;margin:4px 0 2px}} .sub{{color:var(--muted);margin:0 0 12px}}
.toolbar{{position:sticky;top:0;z-index:10;background:rgba(7,10,16,.96);padding:8px 0;border-bottom:1px solid var(--line)}}
.controls{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
button,a.btn{{border:1px solid #41516a;background:#182232;color:var(--text);border-radius:9px;padding:10px 12px;font:inherit;text-decoration:none}}
button.active{{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}}
.timeline{{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;margin-top:9px}}
input[type=range]{{width:100%;height:34px}} #clock{{font:14px ui-monospace,monospace;min-width:94px;text-align:right}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px;min-width:0}}
.card h2{{font-size:15px;margin:0 0 7px}} video{{display:block;width:100%;background:#000;border-radius:8px;max-height:72vh}}
body.mode-b #cardC{{display:none}} body.mode-b .grid{{grid-template-columns:1fr}}
body.mode-c #cardB{{display:none}} body.mode-c .grid{{grid-template-columns:1fr}}
.note{{color:var(--muted);font-size:14px;line-height:1.45;margin-top:12px}}
.links{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}}
#state{{white-space:pre-wrap;font:13px ui-monospace,monospace;color:#b8c8dc;margin:10px 0 0}}
@media(max-width:760px){{
  main{{padding:8px}} .grid{{grid-template-columns:1fr}} .card{{padding:6px}}
  .controls button,.controls a{{flex:1 1 auto}} video{{max-height:55vh}}
}}
</style>
</head>
<body class="mode-c">
<main>
<h1>{safe_title}</h1>
<p class="sub"><strong>{safe_b_label}</strong> · <strong>{safe_c_label}</strong> · {fps:g} fps</p>
<div class="toolbar">
  <div class="controls">
    <button id="play">▶ Play synced</button>
    <button id="pause">Pause</button>
    <button id="back">−1 frame</button>
    <button id="forward">+1 frame</button>
    <button id="half">0.5×</button>
    <button id="normal" class="active">1×</button>
    <button data-mode="b">B only</button>
    <button data-mode="c" class="active">C only</button>
    <button data-mode="split">Split</button>
  </div>
  <div class="timeline">
    <input id="scrub" type="range" min="0" max="0" step="0.001" value="0" aria-label="Shared timeline">
    <span id="clock">0.000 / 0.000</span>
  </div>
</div>
<div class="grid">
  <section class="card" id="cardB"><h2>{safe_b_label}</h2><video id="b" src="{b}" controls playsinline preload="metadata"></video></section>
  <section class="card" id="cardC"><h2>{safe_c_label}</h2><video id="c" src="{c}" controls playsinline preload="metadata"></video></section>
</div>
<div class="links">
  <a class="btn" href="{b}" target="_blank">Open B MP4</a>
  <a class="btn" href="{c}" target="_blank">Open C MP4</a>
</div>
<p class="note">Use the shared scrubber to jump anywhere without replaying from the start. Native player controls remain enabled. Tapping or scrubbing either video makes it the timing master and keeps the other synchronized.</p>
<pre id="state"></pre>
</main>
<script>
const B=document.getElementById('b'), C=document.getElementById('c');
const scrub=document.getElementById('scrub'), clock=document.getElementById('clock'), state=document.getElementById('state');
const videos=[B,C], frame={frame:.9f};
let master=C, syncing=false, userScrub=false, rate=1;
function duration(){{ return Math.min(...videos.map(v=>Number.isFinite(v.duration)?v.duration:Infinity)); }}
function setBothTime(t, source=null){{
  const d=duration(); if(!Number.isFinite(d)) return;
  t=Math.max(0,Math.min(d,t)); syncing=true;
  videos.forEach(v=>{{ if(v!==source || Math.abs(v.currentTime-t)>.002) v.currentTime=t; }});
  requestAnimationFrame(()=>syncing=false);
}}
function update(){{
  const d=duration(); if(Number.isFinite(d)){{ scrub.max=d.toFixed(3); if(!userScrub) scrub.value=master.currentTime; }}
  clock.textContent=master.currentTime.toFixed(3)+' / '+(Number.isFinite(d)?d:0).toFixed(3);
  const q=master.getVideoPlaybackQuality?master.getVideoPlaybackQuality():{{totalVideoFrames:0,droppedVideoFrames:0}};
  state.textContent='master='+(master===B?'B':'C')+'  rate='+rate+'x  '+(master.paused?'PAUSED':'PLAYING')+'\nframe≈'+Math.round(master.currentTime/{frame:.9f})+'  decoded='+q.totalVideoFrames+'  dropped='+q.droppedVideoFrames;
  if(!master.paused && !syncing){{
    const other=master===B?C:B;
    if(Math.abs(other.currentTime-master.currentTime)>{max(frame*0.65,0.025) if False else '0.025'}) other.currentTime=master.currentTime;
  }}
  requestAnimationFrame(update);
}}
videos.forEach(v=>{{
  v.playbackRate=rate;
  v.addEventListener('pointerdown',()=>master=v);
  v.addEventListener('seeking',()=>{{ if(!syncing){{master=v;setBothTime(v.currentTime,v)}} }});
  v.addEventListener('play',()=>{{master=v; videos.forEach(x=>{{x.playbackRate=rate;if(x!==v)x.play().catch(()=>{{}})}})}}); 
  v.addEventListener('pause',()=>{{if(!syncing)videos.forEach(x=>{{if(x!==v&&!x.paused)x.pause()}})}}); 
  v.addEventListener('loadedmetadata',()=>{{const d=duration();if(Number.isFinite(d))scrub.max=d.toFixed(3)}});
}});
scrub.addEventListener('pointerdown',()=>userScrub=true);
scrub.addEventListener('input',()=>{{userScrub=true; videos.forEach(v=>v.pause()); setBothTime(Number(scrub.value)); clock.textContent=Number(scrub.value).toFixed(3)+' / '+duration().toFixed(3)}});
scrub.addEventListener('change',()=>userScrub=false);
scrub.addEventListener('pointerup',()=>userScrub=false);
document.getElementById('play').onclick=()=>{{setBothTime(master.currentTime);videos.forEach(v=>{{v.playbackRate=rate;v.play().catch(()=>{{}})}})}};
document.getElementById('pause').onclick=()=>videos.forEach(v=>v.pause());
document.getElementById('back').onclick=()=>{{videos.forEach(v=>v.pause());setBothTime(master.currentTime-frame)}};
document.getElementById('forward').onclick=()=>{{videos.forEach(v=>v.pause());setBothTime(master.currentTime+frame)}};
document.getElementById('half').onclick=()=>{{rate=.5;videos.forEach(v=>v.playbackRate=rate);document.getElementById('half').classList.add('active');document.getElementById('normal').classList.remove('active')}};
document.getElementById('normal').onclick=()=>{{rate=1;videos.forEach(v=>v.playbackRate=rate);document.getElementById('normal').classList.add('active');document.getElementById('half').classList.remove('active')}};
document.querySelectorAll('[data-mode]').forEach(btn=>btn.onclick=()=>{{
  document.body.className='mode-'+btn.dataset.mode;
  document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===btn));
  if(btn.dataset.mode==='b')master=B; if(btn.dataset.mode==='c')master=C;
}});
requestAnimationFrame(update);
</script>
</body></html>
""".replace(">{max(frame*0.65,0.025) if False else '0.025'}",">0.025")


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("b_video")
    ap.add_argument("c_video")
    ap.add_argument("output")
    ap.add_argument("--title",default="Finishing review · B vs C")
    ap.add_argument("--fps",type=float,default=24)
    ap.add_argument("--b-label",default="B · Conventional post")
    ap.add_argument("--c-label",default="C · Pass-aware finishing")
    args=ap.parse_args()
    b=Path(args.b_video).resolve(); c=Path(args.c_video).resolve(); out=Path(args.output).resolve()
    if args.fps<=0: raise SystemExit("--fps must be positive")
    for label,p in (("B",b),("C",c)):
        if not p.is_file(): raise SystemExit(f"missing {label} video: {p}")
    out.parent.mkdir(parents=True,exist_ok=True)
    page=build_page(relative_media(b,out),relative_media(c,out),title=args.title,fps=args.fps,b_label=args.b_label,c_label=args.c_label)
    out.write_text(page,encoding="utf-8")
    print(out)


if __name__=="__main__":
    main()