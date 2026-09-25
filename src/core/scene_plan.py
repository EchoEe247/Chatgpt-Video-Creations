from __future__ import annotations

from typing import Any, Mapping


def validate_scene_plan(data: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") not in {1, 2}:
        errors.append("schema_version must be 1 or 2")
    fps = data.get("fps")
    if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
        errors.append("fps must be positive")
    resolution = data.get("resolution")
    if not (
        isinstance(resolution, list)
        and len(resolution) == 2
        and all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in resolution)
    ):
        errors.append("resolution must be [positive_width, positive_height]")

    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes must be a non-empty array")
        return errors

    previous_end = 0.0
    ids: set[str] = set()
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, Mapping):
            errors.append(f"scene {index} must be an object")
            continue
        scene_id = str(scene.get("id") or scene.get("scene") or "")
        if not scene_id:
            errors.append(f"scene {index} requires id/scene")
        elif scene_id in ids:
            errors.append(f"duplicate scene id: {scene_id}")
        ids.add(scene_id)

        start = scene.get("start", scene.get("start_seconds"))
        duration = scene.get("duration", scene.get("duration_seconds"))
        if not isinstance(start, (int, float)) or isinstance(start, bool) or start < 0:
            errors.append(f"scene {index} start must be non-negative")
            continue
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
            errors.append(f"scene {index} duration must be positive")
            continue
        start = float(start)
        duration = float(duration)
        if start < previous_end - 1e-6:
            errors.append(f"scene {index} overlaps previous scene")
        previous_end = max(previous_end, start + duration)

        review_points = scene.get("review_points") or []
        if not isinstance(review_points, list):
            errors.append(f"scene {index} review_points must be an array")
            continue
        for point_index, point in enumerate(review_points, 1):
            value = point if isinstance(point, (int, float)) else (
                point.get("at_seconds") if isinstance(point, Mapping) else None
            )
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"scene {index} review point {point_index} needs numeric at_seconds")
            elif float(value) < 0 or float(value) > duration:
                errors.append(f"scene {index} review point {point_index} is outside scene duration")
            if isinstance(point, Mapping) and "clip_duration_seconds" in point:
                clip_duration = point.get("clip_duration_seconds")
                if (
                    not isinstance(clip_duration, (int, float))
                    or isinstance(clip_duration, bool)
                    or clip_duration <= 0
                    or clip_duration > 10
                ):
                    errors.append(
                        f"scene {index} review point {point_index} clip_duration_seconds "
                        "must be > 0 and <= 10"
                    )

    declared = data.get("duration_seconds")
    if declared is not None and isinstance(declared, (int, float)) and not isinstance(declared, bool):
        if abs(float(declared) - previous_end) > 1e-3:
            errors.append("duration_seconds does not match final scene end")
    return errors