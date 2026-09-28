#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.production_manifest import validate_production_v2
from src.core.production_runtime import apply_runtime_defaults


def validate_data(data: dict[str, Any], *, strict: bool) -> list[str]:
    candidate = data if strict else json.loads(json.dumps(data))
    if not strict:
        apply_runtime_defaults(candidate)
    return validate_production_v2(candidate)


def validate_path(path: pathlib.Path, *, strict: bool) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [str(exc)]
    return data, validate_data(data, strict=strict)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a production-v2 manifest. Default mode accepts legacy values via runtime defaults; --strict validates committed data exactly as stored."
    )
    parser.add_argument("path", nargs="?", default="templates/production-v2.json")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Validate raw committed data without applying compatibility/runtime defaults.",
    )
    args = parser.parse_args(argv)

    path = pathlib.Path(args.path)
    data, errors = validate_path(path, strict=args.strict)
    if errors:
        print("FAIL production v2" + (" (strict)" if args.strict else ""))
        for error in errors:
            print("-", error)
        return 1

    assert data is not None
    print(
        f"PASS production v2{' (strict)' if args.strict else ''}: "
        f"{data['production_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
