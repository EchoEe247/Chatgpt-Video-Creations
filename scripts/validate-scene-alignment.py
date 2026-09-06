#!/usr/bin/env python3
"""Validate canonical set-anchor geometry before rendering."""
import json, pathlib, sys

def main(path: str) -> int:
    data = json.loads(pathlib.Path(path).read_text())
    floor = data.get("floor_y")
    portal = data.get("portal", {})
    errors = []
    if not isinstance(floor, (int, float)):
        errors.append("floor_y missing/non-numeric")
    center = portal.get("center")
    if not (isinstance(center, list) and len(center) == 2 and all(isinstance(v, (int, float)) for v in center)):
        errors.append("portal.center must be [x,y]")
    for k in ("outer_radius", "inner_radius"):
        if not isinstance(portal.get(k), (int, float)) or portal.get(k, 0) <= 0:
            errors.append(f"portal.{k} must be positive")
    if portal.get("inner_radius", 0) >= portal.get("outer_radius", float("inf")):
        errors.append("portal.inner_radius must be smaller than outer_radius")
    for name, anchor in data.get("anchors", {}).items():
        if "floor_y" in anchor and anchor["floor_y"] != floor:
            errors.append(f"anchor {name} floor_y drifts from set floor_y")
    if errors:
        print("FAIL")
        for e in errors: print("-", e)
        return 1
    print("PASS set anchors")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "set-anchors.json"))
