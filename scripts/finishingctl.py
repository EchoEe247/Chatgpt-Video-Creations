#!/usr/bin/env python3
"""Validate, fingerprint, and apply local Blender finishing contracts."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.finishing_contract import (
    canonical_json_sha256,
    validate_finishing_receipt,
    validate_finishing_recipe,
    validate_recipe_against_bundle,
    validate_render_bundle,
    verify_finishing_receipt_files,
    verify_render_bundle_files,
)
from src.core.shot_workflow import GLOBAL_DEVICE_LOCK_ROOT, device_lock


def load(path: str | Path) -> dict:
    return json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))


def emit(payload: dict, ok: bool) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok else 2


def validate_pair(bundle: dict, recipe: dict, bundle_root: Path, verify_files: bool) -> list[str]:
    errors = validate_render_bundle(bundle)
    errors += validate_finishing_recipe(recipe)
    if not errors:
        errors += validate_recipe_against_bundle(recipe, bundle)
    if verify_files and not errors:
        errors += verify_render_bundle_files(bundle, bundle_root)
    return errors


def guest_ready() -> tuple[bool, str]:
    if not shutil.which("proot-distro"):
        return False, "proot-distro missing"
    proc = subprocess.run(
        [
            "proot-distro",
            "login",
            "hermes-ubuntu",
            "--",
            "python3",
            "-c",
            "import OpenImageIO as oiio, numpy as np; print(oiio.VERSION_STRING, np.__version__)",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return proc.returncode == 0, (proc.stdout or proc.stderr or "guest probe failed").strip()


def apply(bundle_path: Path, recipe_path: Path, bundle_root: Path, output_dir: Path, timeout: int) -> int:
    bundle = load(bundle_path)
    recipe = load(recipe_path)
    errors = validate_pair(bundle, recipe, bundle_root, verify_files=True)
    if errors:
        return emit({"pass": False, "errors": errors}, False)

    ready, detail = guest_ready()
    if not ready:
        return emit({"pass": False, "errors": [f"finishing guest unavailable: {detail}"]}, False)

    worker = ROOT / "scripts" / "finishing_worker.py"
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "proot-distro",
        "login",
        "hermes-ubuntu",
        "--",
        "python3",
        str(worker),
        "--bundle",
        str(bundle_path),
        "--recipe",
        str(recipe_path),
        "--bundle-root",
        str(bundle_root),
        "--output-dir",
        str(output_dir),
    ]
    try:
        with device_lock(GLOBAL_DEVICE_LOCK_ROOT):
            proc = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
    except subprocess.TimeoutExpired:
        return emit({"pass": False, "errors": ["finishing worker timed out; completed outputs remain resumable"]}, False)
    except ValueError as exc:
        return emit({"pass": False, "errors": [str(exc)]}, False)

    receipt_path = output_dir / "finishing-receipt.json"
    if proc.returncode or not receipt_path.is_file():
        return emit(
            {
                "pass": False,
                "errors": [f"finishing worker exited {proc.returncode}"],
                "stdout_tail": (proc.stdout or "")[-4000:],
                "stderr_tail": (proc.stderr or "")[-4000:],
            },
            False,
        )
    receipt = load(receipt_path)
    errors = validate_finishing_receipt(receipt, bundle, recipe)
    errors += verify_finishing_receipt_files(receipt, output_dir)
    result = {
        "pass": not errors,
        "errors": errors,
        "bundle_sha256": canonical_json_sha256(bundle),
        "recipe_sha256": canonical_json_sha256(recipe),
        "receipt": str(receipt_path),
        "output_dir": str(output_dir),
        "guest": detail,
        "worker_stdout": (proc.stdout or "").strip().splitlines()[-12:],
    }
    return emit(result, not errors)


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

    dr = sp.add_parser("doctor")

    ap = sp.add_parser("apply")
    ap.add_argument("bundle")
    ap.add_argument("recipe")
    ap.add_argument("output_dir")
    ap.add_argument("--root", default="")
    ap.add_argument("--timeout", type=int, default=600)

    args = p.parse_args()
    try:
        if args.cmd == "fingerprint":
            data = load(args.json_file)
            return emit({"pass": True, "sha256": canonical_json_sha256(data)}, True)

        if args.cmd == "doctor":
            ready, detail = guest_ready()
            return emit({"pass": ready, "guest": "hermes-ubuntu", "detail": detail}, ready)

        if args.cmd == "validate-bundle":
            path = Path(args.bundle).expanduser().resolve()
            bundle = load(path)
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
        recipe_path = Path(args.recipe).expanduser().resolve()
        bundle_root = Path(args.root).expanduser().resolve() if args.root else bundle_path.parent

        if args.cmd == "apply":
            output_dir = Path(args.output_dir).expanduser().resolve()
            if not 1 <= args.timeout <= 86400:
                return emit({"pass": False, "errors": ["--timeout must be between 1 and 86400 seconds"]}, False)
            return apply(bundle_path, recipe_path, bundle_root, output_dir, args.timeout)

        bundle = load(bundle_path)
        recipe = load(recipe_path)
        errors = validate_pair(bundle, recipe, bundle_root, bool(args.verify_files))
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
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        return emit({"pass": False, "errors": [str(exc)]}, False)


if __name__ == "__main__":
    raise SystemExit(main())
