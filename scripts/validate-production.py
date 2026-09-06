#!/usr/bin/env python3
"""Validate a business release production snapshot."""
import json, pathlib, sys

REQUIRED = ["schema_version", "production_type", "project", "release", "exact_tag", "exact_commit", "source_verified_at", "status"]

def main(path: str) -> int:
    data = json.loads(pathlib.Path(path).read_text())
    missing = [k for k in REQUIRED if not data.get(k)]
    if missing:
        print("FAIL missing:", ", ".join(missing))
        return 1
    if data["production_type"] != "release-marketing":
        print("FAIL production_type must be release-marketing")
        return 1
    if data["release"] != data["exact_tag"]:
        print("WARN release and exact_tag differ; verify intentionally")
    if len(str(data["exact_commit"])) < 7:
        print("FAIL exact_commit is not plausible")
        return 1
    print("PASS production snapshot")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "production.json"))
