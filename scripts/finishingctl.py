#!/usr/bin/env python3
"""Validate and fingerprint local Blender finishing contracts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.finishing_contract import (
    canonical_json_sha256,
    validate_finishing_recipe,
    validate_recipe_against_bundle,
    validate_render_bundle,
    verify_render_bundle_files,
)


def load(path: str) -> dict:
    return json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))


def emit(payload: dict, ok: bool) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok else 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)

    vb = sp.add_parser("validate-bundle")
    vb.add_argument("bundle")
    vb.add_argument("--verify-files", action="store_true")
    vb.add_argument("--root", default="")

    vr = sp.add_parser("validate-recipe")
    vr.add_argument("recipe")

    vp = sp.add_parser("validate-pair")
    vp.add_argument("bundle")
    vp.add_argument("recipe")
    vp.add_argument("--verify-files", action="store_true")
    vp.add_argument("--root", default="")

    fp = sp.add_parser("fingerprint")
    fp.add_argument("json_file")

    args = p.parse_args()
    try:
        if args.cmd == "fingerprint":
            data = load(args.json_file)
            return emit({"pass": True, "sha256": canonical_json_sha256(data)}, True)

        if args.cmd == "validate-bundle":
            path = Path(args.bundle).expanduser().resolve()
            bundle = load(str(path))
            errors = validate_render_bundle(bundle)
            if args.verify_files and not errors:
                root = Path(args.root).expanduser().resolve() if args.root else path.parent
                errors += verify_render_bundle_files(bundle, root)
            return emit(
                {
                    "pass": not errors,
                    "errors": errors,
                    "bundle_sha256": canonical_json_sha256(bundle),
                    "files_verified": bool(args.verify_files),
                },
                not errors,
            )

        if args.cmd == "validate-recipe":
            recipe = load(args.recipe)
            errors = validate_finishing_recipe(recipe)
            return emit(
                {
                    "pass": not errors,
                    "errors": errors,
                    "recipe_sha256": canonical_json_sha256(recipe),
                },
                not errors,
            )

        bundle_path = Path(args.bundle).expanduser().resolve()
        bundle = load(str(bundle_path))
        recipe = load(args.recipe)
        errors = validate_render_bundle(bundle)
        errors += validate_finishing_recipe(recipe)
        if not errors:
            errors += validate_recipe_against_bundle(recipe, bundle)
        if args.verify_files and not errors:
            root = Path(args.root).expanduser().resolve() if args.root else bundle_path.parent
            errors += verify_render_bundle_files(bundle, root)
        return emit(
            {
                "pass": not errors,
                "errors": errors,
                "bundle_sha256": canonical_json_sha256(bundle),
                "recipe_sha256": canonical_json_sha256(recipe),
                "files_verified": bool(args.verify_files),
            },
            not errors,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return emit({"pass": False, "errors": [str(exc)]}, False)


if __name__ == "__main__":
    raise SystemExit(main())
