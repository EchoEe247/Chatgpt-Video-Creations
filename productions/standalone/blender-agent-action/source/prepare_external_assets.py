#!/usr/bin/env python3
"""Prepare locally downloaded Quaternius CC0 packs for Blender imports.

The standard Modular Sci-Fi MegaKit glTF files reference shared textures as if
those PNGs live beside each model. The archive stores them once in /Textures.
Create relative symlinks so Blender can resolve the original glTF URIs without
copying texture payloads into every category.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACK = ROOT / "external-assets/quaternius/modular_scifi_megakitstandard/Modular SciFi MegaKit[Standard]"
TEXTURES = PACK / "Textures"
GLTF_ROOT = PACK / "glTF"


def main() -> None:
    linked = 0
    missing: set[str] = set()
    for gltf in GLTF_ROOT.rglob("*.gltf"):
        data = json.loads(gltf.read_text(encoding="utf-8"))
        for image_info in data.get("images", []):
            uri = image_info.get("uri")
            if not uri or uri.startswith("data:"):
                continue
            target = gltf.parent / uri
            if target.exists():
                continue
            source = TEXTURES / Path(uri).name
            if not source.exists():
                missing.add(Path(uri).name)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            rel = Path(os.path.relpath(source, target.parent))
            target.symlink_to(rel)
            linked += 1
    print(f"linked={linked} unresolved={len(missing)}")
    for name in sorted(missing):
        print("unresolved", name)
    if missing:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
