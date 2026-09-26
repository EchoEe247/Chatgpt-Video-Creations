#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
from pathlib import Path


def build_page(video_name: str, times: list[float], title: str) -> str:
    buttons = "".join(
        f'<button data-time="{t:.3f}">{t:.2f}s</button>' for t in times
    )
    src = html.escape(video_name, quote=True)
    safe_title = html.escape(title)
    return f"""<!doctype html>
<meta charset="utf-8">
<title>{safe_title}</title>
<style>
body{{margin:0;background:#111;color:#eee;font:17px system-ui;padding:14px}}
video{{display:block;width:min(960px,96vw);max-height:72vh;background:#000}}
.controls{{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0}}
button{{font:inherit;padding:8px 11px}}
#state{{white-space:pre-wrap;font:14px ui-monospace,monospace}}
</style>
<h1>{safe_title}</h1>
<video id="v" src="{src}" controls playsinline preload="auto"></video>
<div class="controls">
<button id="play">Play from start</button>
<button id="pause">Pause</button>
<button id="normal">1x</button>
<button id="half">0.5x</button>
{buttons}
</div>
<pre id="state"></pre>
<script>
const v=document.getElementById('v'), state=document.getElementById('state');
document.getElementById('play').onclick=()=>{{v.currentTime=0;v.play()}};
document.getElementById('pause').onclick=()=>v.pause();
document.getElementById('normal').onclick=()=>v.playbackRate=1;
document.getElementById('half').onclick=()=>v.playbackRate=.5;
document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{{v.pause();v.currentTime=Number(b.dataset.time)}});
let ended=0;v.addEventListener('ended',()=>ended++);
setInterval(()=>{{
  const q=v.getVideoPlaybackQuality?v.getVideoPlaybackQuality():{{totalVideoFrames:0,droppedVideoFrames:0}};
  const status=(v.ended?'ENDED':v.paused?'PAUSED':'PLAYING');
  state.textContent=v.currentTime.toFixed(3)+' / '+(v.duration||0).toFixed(3)+' s | '+v.playbackRate+'x | '+status+'\\\\ndecoded='+q.totalVideoFrames+' dropped='+q.droppedVideoFrames+' ended='+ended;
  document.title='{safe_title} | '+v.currentTime.toFixed(2)+'/'+(v.duration||0).toFixed(2)+' '+status+' d'+q.droppedVideoFrames;
}},100);
</script>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Create a local browser playback review page for a video.")
    ap.add_argument("video", help="video path")
    ap.add_argument("output", help="HTML output path")
    ap.add_argument("--times", default="", help="comma-separated review timestamps in seconds")
    ap.add_argument("--title", default="Browser playback review")
    args = ap.parse_args()

    video = Path(args.video).resolve()
    output = Path(args.output).resolve()
    if not video.is_file():
        raise SystemExit(f"missing video: {video}")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        rel = video.relative_to(output.parent)
        src = rel.as_posix()
    except ValueError:
        src = video.as_uri()
    times = [float(x) for x in args.times.split(",") if x.strip()]
    output.write_text(build_page(src, times, args.title))
    print(output)


if __name__ == "__main__":
    main()