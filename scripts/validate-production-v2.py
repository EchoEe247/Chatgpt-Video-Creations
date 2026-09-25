#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.production_manifest import validate_production_v2


def main(path: str) -> int:
    p = pathlib.Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("FAIL production v2")
        print("-", exc)
        return 1

    errors = validate_production_v2(data)
    if errors:
        print("FAIL production v2")
        for error in errors:
            print("-", error)
        return 1

    print(f"PASS production v2: {data['production_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(sys.argv[1] if len(sys.argv) > 1 else "templates/production-v2.json")
    )
