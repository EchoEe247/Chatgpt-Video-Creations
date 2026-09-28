#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"respectful","below_respectful_salvageable","medium_bad","failed"}
SHA = re.compile(r"^[0-9a-f]{64}$")

def validate(path: Path) -> list[str]:
    data=json.loads(path.read_text(encoding="utf-8"))
    errors=[]
    tracked=set(subprocess.run(["git","ls-files"],cwd=ROOT,text=True,capture_output=True,check=True).stdout.splitlines())
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    items=data.get("productions")
    if not isinstance(items,list) or not items:
        return errors+["productions must be a non-empty array"]
    seen=set()
    for i,item in enumerate(items):
        p=f"productions[{i}]"
        pid=item.get("production_id")
        if not isinstance(pid,str) or not pid:
            errors.append(f"{p}.production_id required")
        elif pid in seen:
            errors.append(f"{p}.production_id duplicate: {pid}")
        seen.add(pid)
        if not isinstance(item.get("title"),str) or not item.get("title"):
            errors.append(f"{p}.title required")
        if item.get("user_quality_status") not in STATUSES:
            errors.append(f"{p}.user_quality_status invalid")
        if item.get("lane") not in {"cinematic", "animation", "business"}:
            errors.append(f"{p}.lane must be cinematic, animation, or business")
        for key in ("current","keep_working","potentially_releasable","baseline_promoted"):
            if not isinstance(item.get(key),bool):
                errors.append(f"{p}.{key} must be boolean")
        if item.get("user_quality_status") == "respectful" and item.get("baseline_promoted"):
            errors.append(f"{p}: respectful does not imply baseline promotion")
        digest=item.get("candidate_sha256")
        if digest is not None and (not isinstance(digest,str) or not SHA.fullmatch(digest)):
            errors.append(f"{p}.candidate_sha256 must be null or lowercase SHA-256")
        repo_path=item.get("repo_path")
        if repo_path is not None and not isinstance(repo_path,str):
            errors.append(f"{p}.repo_path must be string or null")
        if isinstance(repo_path,str):
            production=ROOT/repo_path/"production.json"
            rel_manifest=f"{repo_path}/production.json"
            if production.is_file() and rel_manifest in tracked:
                pdata=json.loads(production.read_text(encoding="utf-8"))
                manifest_sha=(pdata.get("artifacts") or {}).get("candidate_sha256")
                if digest and manifest_sha and digest != manifest_sha:
                    errors.append(f"{p}.candidate_sha256 disagrees with tracked {rel_manifest}")
    return errors

def main() -> int:
    path=ROOT/"productions"/"quality-status.json"
    errors=validate(path)
    if errors:
        print("FAIL production quality status")
        for e in errors: print("-",e)
        return 1
    print("PASS production quality status")
    return 0

if __name__=="__main__":
    raise SystemExit(main())