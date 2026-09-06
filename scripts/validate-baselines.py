#!/usr/bin/env python3
"""Validate the formal B-series baseline registry."""
from __future__ import annotations
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.core.baseline_registry import validate_registry

def main(path: str) -> int:
    data = json.loads(pathlib.Path(path).read_text())
    errors = validate_registry(data)
    if errors:
        print("FAIL baseline registry")
        for error in errors:
            print("-", error)
        return 1
    count = len(data["validated_baselines"])
    print(f"PASS baseline registry ({count} validated baseline{'s' if count != 1 else ''})")
    if count == 0:
        print("NOTE no B-series baseline is promoted yet; this is valid and intentional")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "baselines/registry.json"))
