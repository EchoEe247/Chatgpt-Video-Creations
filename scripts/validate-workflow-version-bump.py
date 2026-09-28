#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION_RE=re.compile(r"^\d+(?:\.\d+)+$")

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

def version_tuple(value: object) -> tuple[int, ...]:
    text=str(value or "")
    if not VERSION_RE.fullmatch(text):
        raise ValueError(f"workflow_version must be dot-separated integers, got {text!r}")
    return tuple(int(part) for part in text.split("."))

def evaluate_change(changed: set[str], old: dict, new: dict) -> tuple[list[str], list[str]]:
    canonical=contract_paths(old)|contract_paths(new)
    relevant=sorted(changed & canonical)
    errors=[]
    if relevant:
        old_version=version_tuple(old.get("workflow_version"))
        new_version=version_tuple(new.get("workflow_version"))
        if new_version <= old_version:
            relation="unchanged" if new_version == old_version else "downgraded"
            errors.append(
                f"canonical workflow files changed but workflow_version {relation}: "
                f"{old.get('workflow_version')} -> {new.get('workflow_version')}"
            )
    return errors, relevant

# Kept for callers/tests using the previous helper name.
def requires_version_bump(changed: set[str], old: dict, new: dict) -> tuple[bool, list[str]]:
    errors,relevant=evaluate_change(changed,old,new)
    return bool(errors), relevant

def resolve_base(candidate: str | None) -> tuple[str | None, str | None]:
    if candidate and set(candidate)!={"0"}:
        probe=subprocess.run(["git","cat-file","-e",f"{candidate}^{{commit}}"],cwd=ROOT,capture_output=True)
        if probe.returncode == 0:
            return candidate, None
        warning=f"provided base SHA {candidate} is unavailable; trying HEAD^"
    else:
        warning="no usable event base SHA was provided; trying HEAD^"

    probe=subprocess.run(["git","rev-parse","--verify","HEAD^"],cwd=ROOT,text=True,capture_output=True)
    if probe.returncode == 0:
        fallback=probe.stdout.strip()
        return fallback, warning+f"; using fallback {fallback}"
    return None, warning+"; no parent commit exists, so monotonic comparison cannot run"

def main() -> int:
    candidate=sys.argv[1] if len(sys.argv)>1 else None
    head=sys.argv[2] if len(sys.argv)>2 else "HEAD"
    base,warning=resolve_base(candidate)
    if warning:
        print(f"::warning::{warning}")
    if base is None:
        print("SKIP workflow version monotonic check: no comparable base commit")
        return 0

    try:
        old=json.loads(git("show",f"{base}:workflow/CURRENT.json"))
    except Exception as exc:
        print(f"::error::cannot read base workflow contract: {exc}")
        return 1

    new=json.loads((ROOT/"workflow/CURRENT.json").read_text(encoding="utf-8"))
    changed=set(git("diff","--name-only",base,head).splitlines())
    try:
        errors,relevant=evaluate_change(changed,old,new)
    except ValueError as exc:
        print(f"FAIL workflow version monotonic check: {exc}")
        return 1
    if errors:
        print("FAIL workflow version monotonic check")
        for error in errors: print("-",error)
        for path in relevant: print("-",path)
        return 1
    print("PASS workflow version monotonic check")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
