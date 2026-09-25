from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.media import artifact_receipt, build_contact_sheet, extract_frame, extract_review_clip


def _scene_start(scene: dict[str, Any]) -> float:
    value = scene.get("start_seconds", scene.get("start"))
    if value is None:
        raise ValueError("scene is missing start/start_seconds")
    return float(value)


def _scene_number(scene: dict[str, Any], fallback: int) -> int:
    value = scene.get("scene")
    if isinstance(value, int):
        return value
    scene_id = str(scene.get("id", ""))
    digits = "".join(ch for ch in scene_id if ch.isdigit())
    return int(digits) if digits else fallback


def build_review_pack(
    video_path: str | Path,
    output_dir: str | Path,
    *,
    scene_plan: str | Path | None = None,
    count: int = 16,
    columns: int = 4,
    cell_width: int = 320,
    frame_width: int = 960,
    boundary_offset: float = 0.15,
    review_clip_duration: float = 2.0,
    silence_threshold_db: float = -55.0,
    silence_min_duration: float = 0.5,
    receipt_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    video = Path(video_path).expanduser().resolve()
    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    receipt_path = out_dir / "artifact-receipt.json"
    sheet_path = out_dir / "contact-sheet.png"
    if receipt_data is None:
        receipt_data = artifact_receipt(
            video,
            silence_threshold_db=silence_threshold_db,
            silence_min_duration=silence_min_duration,
        )
    receipt_path.write_text(json.dumps(receipt_data, indent=2, sort_keys=True) + "\n")
    build_contact_sheet(
        video,
        sheet_path,
        count=count,
        columns=columns,
        cell_width=cell_width,
    )

    boundary_records: list[dict[str, Any]] = []
    review_point_records: list[dict[str, Any]] = []
    scene_plan_path: Path | None = None

    if scene_plan:
        scene_plan_path = Path(scene_plan).expanduser().resolve()
        plan = json.loads(scene_plan_path.read_text(encoding="utf-8"))
        scenes = plan.get("scenes") or []
        boundary_dir = out_dir / "boundaries"
        review_dir = out_dir / "review-points"
        boundary_dir.mkdir(exist_ok=True)
        review_dir.mkdir(exist_ok=True)

        for index, scene in enumerate(scenes, 1):
            scene_number = _scene_number(scene, index)
            start = _scene_start(scene)

            if index > 1:
                before_at = max(0.0, start - boundary_offset)
                after_at = start + boundary_offset
                before = boundary_dir / f"scene_{scene_number:02d}_before.png"
                after = boundary_dir / f"scene_{scene_number:02d}_after.png"
                extract_frame(video, before, time_seconds=before_at, max_width=frame_width)
                extract_frame(video, after, time_seconds=after_at, max_width=frame_width)
                boundary_records.append(
                    {
                        "scene": scene_number,
                        "boundary_seconds": start,
                        "before_seconds": before_at,
                        "before": str(before.relative_to(out_dir)),
                        "after_seconds": after_at,
                        "after": str(after.relative_to(out_dir)),
                    }
                )

            for point_index, point in enumerate(scene.get("review_points") or [], 1):
                if isinstance(point, (int, float)):
                    relative_at = float(point)
                    label = f"point-{point_index}"
                elif isinstance(point, dict):
                    relative_at = float(point.get("at_seconds", 0.0))
                    label = str(point.get("label") or f"point-{point_index}")
                else:
                    continue
                at = max(0.0, start + relative_at)
                safe_label = "".join(
                    ch if ch.isalnum() or ch in "-_" else "-"
                    for ch in label.lower()
                ).strip("-") or f"point-{point_index}"
                output = review_dir / f"scene_{scene_number:02d}_{safe_label}.png"
                clip_output = review_dir / f"scene_{scene_number:02d}_{safe_label}.mp4"
                clip_duration = (
                    float(point.get("clip_duration_seconds", review_clip_duration))
                    if isinstance(point, dict)
                    else float(review_clip_duration)
                )
                extract_frame(video, output, time_seconds=at, max_width=frame_width)
                extract_review_clip(
                    video,
                    clip_output,
                    center_seconds=at,
                    duration_seconds=clip_duration,
                    max_width=frame_width,
                )
                review_point_records.append(
                    {
                        "scene": scene_number,
                        "label": label,
                        "time_seconds": at,
                        "frame": str(output.relative_to(out_dir)),
                        "clip": str(clip_output.relative_to(out_dir)),
                        "clip_duration_seconds": clip_duration,
                    }
                )

    manifest = {
        "video": str(video),
        "candidate_sha256": receipt_data.get("sha256"),
        "receipt": receipt_path.name,
        "contact_sheet": sheet_path.name,
        "scene_plan": str(scene_plan_path) if scene_plan_path else None,
        "boundaries": boundary_records,
        "review_points": review_point_records,
    }
    manifest_path = out_dir / "review-pack.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return {
        "manifest_path": str(manifest_path),
        "receipt_path": str(receipt_path),
        "contact_sheet": str(sheet_path),
        **manifest,
    }