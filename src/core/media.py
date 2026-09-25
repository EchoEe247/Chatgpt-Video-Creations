from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


class MediaToolError(RuntimeError):
    pass


def _binary(name: str) -> str:
    value = shutil.which(name)
    if not value:
        raise MediaToolError(f"{name} is not installed")
    return value


def _run(argv: list[str], *, timeout: float = 120.0, binary: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        argv,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=not binary,
        timeout=timeout,
        check=False,
    )


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ratio(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        if "/" in value:
            left, right = value.split("/", 1)
            denominator = float(right)
            return float(left) / denominator if denominator else None
        return float(value)
    except ValueError:
        return None


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    digest = hashlib.sha256()
    with p.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_media(path: str | Path) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(str(p))
    proc = _run(
        [
            _binary("ffprobe"),
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(p),
        ],
        timeout=45,
    )
    if proc.returncode != 0:
        raise MediaToolError((proc.stderr or proc.stdout or "ffprobe failed").strip())
    raw = json.loads(proc.stdout)
    fmt = raw.get("format") or {}
    streams: list[dict[str, Any]] = []
    for item in raw.get("streams") or []:
        stream: dict[str, Any] = {
            "index": _int(item.get("index")),
            "codec_type": item.get("codec_type"),
            "codec_name": item.get("codec_name"),
            "codec_long_name": item.get("codec_long_name"),
            "duration_seconds": _float(item.get("duration")),
            "bit_rate": _int(item.get("bit_rate")),
        }
        if item.get("codec_type") == "video":
            stream.update(
                {
                    "width": _int(item.get("width")),
                    "height": _int(item.get("height")),
                    "pixel_format": item.get("pix_fmt"),
                    "frame_rate": _ratio(item.get("avg_frame_rate"))
                    or _ratio(item.get("r_frame_rate")),
                    "frame_count": _int(item.get("nb_frames")),
                }
            )
        elif item.get("codec_type") == "audio":
            stream.update(
                {
                    "sample_rate": _int(item.get("sample_rate")),
                    "channels": _int(item.get("channels")),
                    "channel_layout": item.get("channel_layout"),
                    "sample_format": item.get("sample_fmt"),
                }
            )
        streams.append(stream)

    return {
        "path": str(p),
        "format_name": fmt.get("format_name"),
        "format_long_name": fmt.get("format_long_name"),
        "duration_seconds": _float(fmt.get("duration")),
        "size_bytes": _int(fmt.get("size")) or p.stat().st_size,
        "bit_rate": _int(fmt.get("bit_rate")),
        "streams": streams,
        "video_streams": sum(1 for x in streams if x.get("codec_type") == "video"),
        "audio_streams": sum(1 for x in streams if x.get("codec_type") == "audio"),
    }


def decode_check(path: str | Path) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    proc = _run(
        [
            _binary("ffmpeg"),
            "-v",
            "error",
            "-i",
            str(p),
            "-map",
            "0:v?",
            "-map",
            "0:a?",
            "-f",
            "null",
            "-",
        ],
        timeout=180,
    )
    errors = (proc.stderr or "").strip()[-16000:]
    return {
        "path": str(p),
        "success": proc.returncode == 0 and not errors,
        "exit_code": proc.returncode,
        "errors": errors,
    }


def _loudnorm_json(stderr: str) -> dict[str, Any]:
    matches = re.findall(r"\{\s*\"input_i\".*?\}", stderr, flags=re.S)
    if not matches:
        return {}
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return {}
    return {
        "integrated_lufs": _float(data.get("input_i")),
        "true_peak_dbfs": _float(data.get("input_tp")),
        "loudness_range_lu": _float(data.get("input_lra")),
        "threshold_lufs": _float(data.get("input_thresh")),
    }


def analyze_audio(
    path: str | Path,
    *,
    silence_threshold_db: float = -55.0,
    silence_min_duration: float = 0.5,
) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    info = probe_media(p)
    if not info["audio_streams"]:
        raise MediaToolError("media has no audio stream")

    threshold = max(-120.0, min(float(silence_threshold_db), 0.0))
    minimum = max(0.05, min(float(silence_min_duration), 60.0))

    loud = _run(
        [
            _binary("ffmpeg"),
            "-nostats",
            "-v",
            "info",
            "-i",
            str(p),
            "-map",
            "0:a:0",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        timeout=180,
    )
    if loud.returncode != 0:
        raise MediaToolError(
            (loud.stderr or loud.stdout or "loudness analysis failed").strip()
        )
    result = _loudnorm_json(loud.stderr or "")
    if result.get("integrated_lufs") is None or result.get("true_peak_dbfs") is None:
        raise MediaToolError("loudness analysis produced no valid measurements")

    silence = _run(
        [
            _binary("ffmpeg"),
            "-nostats",
            "-v",
            "info",
            "-i",
            str(p),
            "-map",
            "0:a:0",
            "-af",
            f"silencedetect=noise={threshold}dB:d={minimum}",
            "-f",
            "null",
            "-",
        ],
        timeout=180,
    )
    if silence.returncode != 0:
        raise MediaToolError(
            (silence.stderr or silence.stdout or "silence analysis failed").strip()
        )

    segments: list[dict[str, float]] = []
    active_start: float | None = None
    for line in (silence.stderr or "").splitlines():
        found = re.search(r"silence_start:\s*([-+0-9.eE]+)", line)
        if found:
            active_start = float(found.group(1))
        found = re.search(
            r"silence_end:\s*([-+0-9.eE]+)\s*\|\s*silence_duration:\s*([-+0-9.eE]+)",
            line,
        )
        if found:
            end = float(found.group(1))
            duration = float(found.group(2))
            start = active_start if active_start is not None else max(0.0, end - duration)
            segments.append(
                {
                    "start_seconds": round(start, 6),
                    "end_seconds": round(end, 6),
                    "duration_seconds": round(duration, 6),
                }
            )
            active_start = None

    total = sum(x["duration_seconds"] for x in segments)
    duration = float(info.get("duration_seconds") or 0.0)
    result.update(
        {
            "path": str(p),
            "duration_seconds": duration,
            "silence_threshold_db": threshold,
            "silence_min_duration": minimum,
            "silence_segments": segments,
            "silence_segment_count": len(segments),
            "total_silence_seconds": round(total, 6),
            "silence_ratio": round(total / duration, 6) if duration > 0 else None,
            "longest_silence_seconds": max(
                (x["duration_seconds"] for x in segments), default=0.0
            ),
        }
    )
    return result


def extract_frame(
    path: str | Path,
    output: str | Path,
    *,
    time_seconds: float = 0.0,
    max_width: int = 1280,
) -> Path:
    p = Path(path).expanduser().resolve()
    out = Path(output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    width = max(160, min(int(max_width), 3840))
    proc = _run(
        [
            _binary("ffmpeg"),
            "-y",
            "-v",
            "error",
            "-ss",
            f"{max(0.0, float(time_seconds)):.6f}",
            "-i",
            str(p),
            "-frames:v",
            "1",
            "-vf",
            f"scale='min({width},iw)':-2",
            str(out),
        ],
        timeout=60,
    )
    if proc.returncode != 0 or not out.is_file():
        raise MediaToolError((proc.stderr or proc.stdout or "frame extraction failed").strip())
    return out


def extract_review_clip(
    path: str | Path,
    output: str | Path,
    *,
    center_seconds: float,
    duration_seconds: float = 2.0,
    max_width: int = 960,
) -> Path:
    """Create a short H.264/AAC review clip centered on an important beat."""
    p = Path(path).expanduser().resolve()
    out = Path(output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.5, min(float(duration_seconds), 10.0))
    start = max(0.0, float(center_seconds) - duration / 2.0)
    width = max(160, min(int(max_width), 1920))
    proc = _run(
        [
            _binary("ffmpeg"),
            "-y",
            "-v",
            "error",
            "-ss",
            f"{start:.6f}",
            "-i",
            str(p),
            "-t",
            f"{duration:.6f}",
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-vf",
            f"scale='min({width},iw)':-2",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "24",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(out),
        ],
        timeout=120,
    )
    if proc.returncode != 0 or not out.is_file():
        raise MediaToolError(
            (proc.stderr or proc.stdout or "review clip extraction failed").strip()
        )
    decoded = decode_check(out)
    if not decoded["success"]:
        out.unlink(missing_ok=True)
        raise MediaToolError(
            f"review clip decode failed: {decoded['errors'] or 'unknown decode error'}"
        )
    return out


def build_contact_sheet(
    path: str | Path,
    output: str | Path,
    *,
    count: int = 12,
    columns: int = 4,
    cell_width: int = 320,
) -> Path:
    p = Path(path).expanduser().resolve()
    out = Path(output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    info = probe_media(p)
    duration = float(info.get("duration_seconds") or 0.0)
    if duration <= 0:
        raise MediaToolError("media duration is unavailable or non-positive")

    count = max(2, min(int(count), 40))
    columns = max(1, min(int(columns), count))
    rows = int(math.ceil(count / columns))
    cell_width = max(160, min(int(cell_width), 960))
    interval = duration / count
    fps = 1.0 / interval
    vf = (
        f"fps={fps:.10f},"
        f"scale='min({cell_width},iw)':-2,"
        f"drawtext=text='%{{pts\\:hms}}':x=8:y=8:"
        "fontsize=18:fontcolor=white:box=1:boxcolor=black@0.65,"
        f"tile={columns}x{rows}:nb_frames={count}:padding=4:margin=4"
    )
    proc = _run(
        [
            _binary("ffmpeg"),
            "-y",
            "-v",
            "error",
            "-ss",
            f"{interval / 2:.6f}",
            "-i",
            str(p),
            "-frames:v",
            "1",
            "-vf",
            vf,
            str(out),
        ],
        timeout=120,
    )
    if proc.returncode != 0 or not out.is_file():
        raise MediaToolError((proc.stderr or proc.stdout or "contact sheet failed").strip())
    return out


def validate_master(
    path: str | Path,
    *,
    width: int | None = None,
    height: int | None = None,
    fps: float | None = None,
    duration_seconds: float | None = None,
    duration_tolerance: float = 0.15,
    audio_required: bool = True,
    video_codec: str | None = None,
    pixel_format: str | None = None,
    audio_codec: str | None = None,
    silence_threshold_db: float = -55.0,
    silence_min_duration: float = 0.5,
    max_silence_seconds: float | None = None,
    intentional_silence_intervals: list[list[float]] | None = None,
) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    probe = probe_media(p)
    decode = decode_check(p)
    video = next((x for x in probe["streams"] if x.get("codec_type") == "video"), None)
    audio_stream = next((x for x in probe["streams"] if x.get("codec_type") == "audio"), None)

    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, actual: Any, expected: Any = None) -> None:
        checks.append(
            {
                "name": name,
                "pass": bool(passed),
                "actual": actual,
                "expected": expected,
            }
        )

    add("decode", bool(decode["success"]), decode["errors"], "no decode errors")
    add("video_stream", video is not None, probe["video_streams"], ">=1")

    if video is not None:
        if width is not None:
            add("width", video.get("width") == width, video.get("width"), width)
        if height is not None:
            add("height", video.get("height") == height, video.get("height"), height)
        if fps is not None:
            actual_fps = _float(video.get("frame_rate"))
            add(
                "fps",
                actual_fps is not None and abs(actual_fps - fps) <= 0.01,
                actual_fps,
                fps,
            )
        if video_codec is not None:
            add("video_codec", video.get("codec_name") == video_codec, video.get("codec_name"), video_codec)
        if pixel_format is not None:
            add("pixel_format", video.get("pixel_format") == pixel_format, video.get("pixel_format"), pixel_format)

    if duration_seconds is not None:
        actual_duration = _float(probe.get("duration_seconds"))
        add(
            "duration",
            actual_duration is not None
            and abs(actual_duration - duration_seconds) <= duration_tolerance,
            actual_duration,
            f"{duration_seconds} ± {duration_tolerance}",
        )

    audio: dict[str, Any] | None = None
    if audio_required:
        add("audio_stream", probe["audio_streams"] > 0, probe["audio_streams"], ">=1")
    if audio_stream is not None and audio_codec is not None:
        add("audio_codec", audio_stream.get("codec_name") == audio_codec, audio_stream.get("codec_name"), audio_codec)
    if probe["audio_streams"]:
        try:
            audio = analyze_audio(
                p,
                silence_threshold_db=silence_threshold_db,
                silence_min_duration=silence_min_duration,
            )
            add("audio_analysis", True, "valid measurements", "valid measurements")
        except MediaToolError as exc:
            audio = {"path": str(p), "analysis_error": str(exc)}
            add("audio_analysis", False, str(exc), "valid measurements")
        if max_silence_seconds is not None and "silence_segments" in audio:
            allowed = intentional_silence_intervals or []

            def uncovered_duration(segment: dict[str, Any]) -> float:
                remaining = [(float(segment["start_seconds"]), float(segment["end_seconds"]))]
                for interval in allowed:
                    if not isinstance(interval, (list, tuple)) or len(interval) != 2:
                        continue
                    left, right = float(interval[0]), float(interval[1])
                    next_remaining: list[tuple[float, float]] = []
                    for start, end in remaining:
                        if right <= start or left >= end:
                            next_remaining.append((start, end))
                            continue
                        if left > start:
                            next_remaining.append((start, min(left, end)))
                        if right < end:
                            next_remaining.append((max(right, start), end))
                    remaining = next_remaining
                return max((end - start for start, end in remaining), default=0.0)

            longest_unintended = max(
                (uncovered_duration(segment) for segment in audio["silence_segments"]),
                default=0.0,
            )
            audio["longest_unintended_silence_seconds"] = round(longest_unintended, 6)
            audio["intentional_silence_intervals"] = allowed
            add(
                "max_unintended_silence",
                longest_unintended <= max_silence_seconds,
                round(longest_unintended, 6),
                f"<= {max_silence_seconds}",
            )

    return {
        "path": str(p),
        "pass": all(x["pass"] for x in checks),
        "checks": checks,
        "probe": probe,
        "decode": decode,
        "audio": audio,
    }


def artifact_receipt(
    path: str | Path,
    *,
    include_audio: bool = True,
    silence_threshold_db: float = -55.0,
    silence_min_duration: float = 0.5,
) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    probe = probe_media(p)
    receipt: dict[str, Any] = {
        "artifact": str(p),
        "sha256": sha256_file(p),
        "probe": probe,
        "decode": decode_check(p),
    }
    if include_audio and probe["audio_streams"]:
        receipt["audio"] = analyze_audio(
            p,
            silence_threshold_db=silence_threshold_db,
            silence_min_duration=silence_min_duration,
        )
    else:
        receipt["audio"] = None
    return receipt


def compare_video(
    reference_path: str | Path,
    candidate_path: str | Path,
    *,
    sample_fps: float = 6.0,
    max_duration_seconds: float | None = None,
) -> dict[str, Any]:
    """Return a bounded sampled SSIM regression signal for same-geometry videos."""
    reference = Path(reference_path).expanduser().resolve()
    candidate = Path(candidate_path).expanduser().resolve()
    ref_info = probe_media(reference)
    cand_info = probe_media(candidate)
    ref_video = next((x for x in ref_info["streams"] if x.get("codec_type") == "video"), None)
    cand_video = next((x for x in cand_info["streams"] if x.get("codec_type") == "video"), None)
    if ref_video is None or cand_video is None:
        raise MediaToolError("both media files must contain video")

    structural = {
        "width_match": ref_video.get("width") == cand_video.get("width"),
        "height_match": ref_video.get("height") == cand_video.get("height"),
        "fps_delta": abs(
            float(ref_video.get("frame_rate") or 0.0)
            - float(cand_video.get("frame_rate") or 0.0)
        ),
        "duration_delta_seconds": abs(
            float(ref_info.get("duration_seconds") or 0.0)
            - float(cand_info.get("duration_seconds") or 0.0)
        ),
    }
    if not structural["width_match"] or not structural["height_match"]:
        return {
            "reference": str(reference),
            "candidate": str(candidate),
            "comparable": False,
            "reason": "video dimensions differ",
            "structural": structural,
            "ssim_all": None,
        }

    fps = max(0.5, min(float(sample_fps), 30.0))
    common_duration = min(
        float(ref_info.get("duration_seconds") or 0.0),
        float(cand_info.get("duration_seconds") or 0.0),
    )
    requested_limit = common_duration if max_duration_seconds is None else float(max_duration_seconds)
    limit = max(1.0, min(requested_limit, common_duration if common_duration > 0 else requested_limit))
    width = min(640, int(ref_video.get("width") or 640))
    if width % 2:
        width -= 1
    graph = (
        f"[0:v]fps={fps:.6f},scale={width}:-2[ref];"
        f"[1:v]fps={fps:.6f},scale={width}:-2[cand];"
        "[ref][cand]ssim"
    )
    proc = _run(
        [
            _binary("ffmpeg"),
            "-nostats",
            "-v",
            "info",
            "-i",
            str(reference),
            "-i",
            str(candidate),
            "-filter_complex",
            graph,
            "-t",
            f"{limit:.6f}",
            "-f",
            "null",
            "-",
        ],
        timeout=120,
    )
    text = proc.stderr or ""
    matches = re.findall(r"SSIM .*?All:([0-9.]+)", text)
    if proc.returncode != 0 or not matches:
        raise MediaToolError((text[-16000:] or "SSIM comparison failed").strip())
    return {
        "reference": str(reference),
        "candidate": str(candidate),
        "comparable": True,
        "sample_fps": fps,
        "max_duration_seconds": limit,
        "structural": structural,
        "ssim_all": float(matches[-1]),
    }