#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.scene_plan import validate_scene_plan


def main(path: str) -> int:
    p = pathlib.Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("FAIL scene plan")
        print("-", exc)
        return 1
    errors = validate_scene_plan(data)
    if errors:
        print("FAIL scene plan")
        for error in errors:
            print("-", error)
        return 1
    print(f"PASS scene plan: {data.get('episode', p.name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "templates/new-episode/scene-plan.json"))
