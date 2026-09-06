#!/usr/bin/env python3
"""Validate structural set-anchor geometry before rendering.

A PASS means the geometry is internally coherent. It is not a visual acceptance result.
"""
from __future__ import annotations
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.core.geometry import SetGeometry


def main(path: str) -> int:
    p = pathlib.Path(path)
    try:
        data = json.loads(p.read_text())
        geometry = SetGeometry.from_mapping(data)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("FAIL structural scene geometry")
        print("-", exc)
        return 1

    errors = []
    if data.get("schema_version") == 2 and geometry.canvas is None:
        errors.append("schema_version 2 requires canvas metadata")
    status = data.get("validation_status")
    if status is not None and status not in {"example_unvalidated", "candidate", "validated"}:
        errors.append("validation_status must be example_unvalidated, candidate, or validated")

    if errors:
        print("FAIL structural scene geometry")
        for error in errors:
            print("-", error)
        return 1

    print(f"PASS structural scene geometry: {geometry.name}")
    print("NOTE structural consistency does not establish visual correctness or a B-series baseline")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "templates/set-anchors.json"))
