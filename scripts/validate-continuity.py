#!/usr/bin/env python3
"""Validate episode completion state before canon advancement."""
import json, pathlib, sys

VALID = {"PLANNED", "IN_PRODUCTION", "ASSISTANT_REVIEW", "USER_REVIEW", "REFINEMENT_REQUIRED", "DONE"}

def main(path: str) -> int:
    data = json.loads(pathlib.Path(path).read_text())
    status = data.get("status")
    if status not in VALID:
        print("FAIL invalid status")
        return 1
    if status == "DONE":
        if data.get("assistant_review") != "PASS":
            print("FAIL DONE requires assistant_review=PASS")
            return 1
        if data.get("user_review") != "PASS":
            print("FAIL DONE requires user_review=PASS")
            return 1
        if data.get("continuity_updated") is not True:
            print("FAIL DONE requires continuity_updated=true")
            return 1
        if not data.get("final_mp4"):
            print("FAIL DONE requires final_mp4")
            return 1
    print("PASS episode state")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "status.json"))
