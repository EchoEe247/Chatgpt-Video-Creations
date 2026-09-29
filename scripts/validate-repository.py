#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.core.workflow_contract import bootstrap

def tracked(pattern:str) -> list[Path]:
    out=subprocess.run(["git","ls-files",pattern],cwd=ROOT,text=True,capture_output=True,check=True).stdout
    return [ROOT/p for p in out.splitlines() if p]

def main() -> int:
    errors=[]
    manifests=sorted(set(tracked("productions/**/production.json")+tracked("shows/**/production-v2.json")))
    for path in manifests:
        cmd=[sys.executable, "scripts/validate-production-v2.py", "--strict", str(path.relative_to(ROOT))]
        result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        if result.returncode:
            errors.append("$ "+" ".join(cmd)+"\n"+result.stdout+result.stderr)

    for lane in ("cinematic","animation","business"):
        result=bootstrap(repo=ROOT,lane=lane,refresh_remote=False,allow_unverified_remote=True)
        for blocker in result.get("blockers") or []:
            if str(blocker).startswith("workflow_file_dirty:"):
                continue
            errors.append(f"workflow {lane}: {blocker}")

    checks=[
        [sys.executable,"scripts/validate-production.py","templates/business-release/production.json"],
        [sys.executable,"scripts/validate-scene-alignment.py","templates/set-anchors.json"],
        [sys.executable,"scripts/validate-continuity.py","templates/new-episode/status.json"],
        [sys.executable,"scripts/validate-production-v2.py","--strict","templates/production-v2.json"],
        [sys.executable,"scripts/validate-scene-plan.py","templates/new-episode/scene-plan.json"],
        [sys.executable,"scripts/validate-baselines.py","baselines/registry.json"],
        [sys.executable,"scripts/validate-quality-status.py"],
        [sys.executable,"scripts/finishingctl.py","validate-pair","templates/finishing/render-bundle-v1.json","templates/finishing/recipe-v1.json"],
        [sys.executable,"scripts/generate-lane-brief.py","--lane","cinematic","--check"],
        [sys.executable,"scripts/validate-markdown.py"],
    ]
    for cmd in checks:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        if p.returncode:
            errors.append("$ "+" ".join(cmd)+"\n"+p.stdout+p.stderr)

    pyfiles=[str(p.relative_to(ROOT)) for p in sorted((ROOT/"scripts").glob("*.py"))]
    pyfiles += [str(p.relative_to(ROOT)) for p in sorted((ROOT/"src").glob("**/*.py"))]
    p=subprocess.run([sys.executable,"-m","py_compile",*pyfiles],cwd=ROOT,text=True,capture_output=True)
    if p.returncode:
        errors.append("py_compile failed\n"+p.stdout+p.stderr)

    if errors:
        print("FAIL repository validation")
        for e in errors: print("-",e)
        return 1
    print(f"PASS repository validation ({len(manifests)} tracked production manifests)")
    return 0

if __name__=="__main__":
    raise SystemExit(main())