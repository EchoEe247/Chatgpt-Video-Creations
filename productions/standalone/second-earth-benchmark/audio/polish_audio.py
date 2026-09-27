#!/usr/bin/env python3
from pathlib import Path
import shutil, subprocess

A=Path(__file__).resolve().parent
S=A/"polished-stems"
S.mkdir(exist_ok=True)
out=A/"master-polished.wav"

filters=(
    "[0:a]asplit=3[nmix][nsc1][nsc2];"
    "[1:a]volume=0.75[s];"
    "[2:a]volume=0.70[a];"
    "[s][a]amix=inputs=2:normalize=0:duration=longest[bed];"
    "[bed][nsc1]sidechaincompress=threshold=0.025:ratio=2.3:attack=40:release=300:knee=4:mix=0.58[bedduck0];"
    "[bedduck0]asplit=2[bedmix][bedstem];"
    "[3:a]volume=0.96[fx];"
    "[fx][nsc2]sidechaincompress=threshold=0.030:ratio=1.4:attack=14:release=180:knee=3:mix=0.42[fxduck0];"
    "[fxduck0]asplit=2[fxmix][fxstem];"
    "[nmix][bedmix][fxmix]amix=inputs=3:normalize=0:duration=longest,"
    "alimiter=limit=0.94:attack=5:release=80,"
    "loudnorm=I=-17:TP=-2:LRA=7[out]"
)
cmd=[
    "ffmpeg","-y","-v","error",
    "-i",str(A/"narration.wav"),
    "-i",str(A/"score.wav"),
    "-i",str(A/"ambience.wav"),
    "-i",str(A/"effects.wav"),
    "-filter_complex",filters,
    "-map","[out]","-t","150","-ar","48000","-ac","2","-c:a","pcm_s16le",str(out),
    "-map","[bedstem]","-t","150","-ar","48000","-ac","2","-c:a","pcm_s16le",str(S/"score.wav"),
    "-map","[fxstem]","-t","150","-ar","48000","-ac","2","-c:a","pcm_s16le",str(S/"effects.wav"),
]
subprocess.run(cmd,check=True)
shutil.copy2(A/"narration.wav",S/"narration.wav")
print("POLISHED_AUDIO_READY",out,flush=True)
print("POLISHED_STEMS_READY",S,flush=True)
