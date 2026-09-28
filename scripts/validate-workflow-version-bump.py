#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def git(*args:str) -> str:
    p=subprocess.run(["git",*args],cwd=ROOT,text=True,capture_output=True,check=False)
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or f"git {' '.join(args)} failed")
    return p.stdout

def contract_paths(data: dict) -> set[str]:
    paths={"workflow/CURRENT.json"}
    paths.update(str(x) for x in data.get("core_docs") or [])
    for docs in (data.get("lane_docs") or {}).values():
        paths.update(str(x) for x in docs or [])
    brief=data.get("lane_briefs") or {}
    paths.update(str(x) for x in brief.values() if x)
    return paths

def requires_version_bump(changed: set[str], old: dict, new: dict) -> tuple[bool, list[str]]:
    canonical=contract_paths(old)|contract_paths(new)
    relevant=sorted(changed & canonical)
    return bool(relevant and old.get("workflow_version")==new.get("workflow_version")), relevant

def main() -> int:
    if len(sys.argv)<2 or not sys.argv[1] or set(sys.argv[1])=={"0"}:
        print("SKIP workflow version bump check: no usable base SHA")
        return 0
    base=sys.argv[1]
    head=sys.argv[2] if len(sys.argv)>2 else "HEAD"
    try:
        old=json.loads(git("show",f"{base}:workflow/CURRENT.json"))
    except Exception as exc:
        print(f"SKIP workflow version bump check: {exc}")
        return 0
    new=json.loads((ROOT/"workflow/CURRENT.json").read_text(encoding="utf-8"))
    changed=set(git("diff","--name-only",base,head).splitlines())
    required, relevant=requires_version_bump(changed,old,new)
    if required:
        print("FAIL canonical workflow files changed without workflow_version bump")
        for p in relevant: print("-",p)
        return 1
    print("PASS workflow version bump check")
    return 0

if __name__=="__main__":
    raise SystemExit(main())