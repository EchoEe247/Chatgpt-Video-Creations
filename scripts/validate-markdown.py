#!/usr/bin/env python3
from __future__ import annotations
import re, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LINK=re.compile(r"\[[^\]]*\]\(([^)]+)\)")

def tracked_markdown() -> list[Path]:
    out=subprocess.run(["git","ls-files","*.md"],cwd=ROOT,text=True,capture_output=True,check=True).stdout
    return [ROOT/p for p in out.splitlines() if p]

def main() -> int:
    errors=[]
    files=tracked_markdown()
    for path in files:
        text=path.read_text(encoding="utf-8")
        if "\\n-" in text:
            errors.append(f"{path.relative_to(ROOT)}: contains literal \\n- sequence")
        for target in LINK.findall(text):
            target=target.strip()
            if not target or target.startswith(("#","http://","https://","mailto:")):
                continue
            target=target.split("#",1)[0]
            if not target: continue
            resolved=(path.parent/target).resolve()
            try: resolved.relative_to(ROOT)
            except ValueError:
                continue
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
    if errors:
        print("FAIL markdown hygiene")
        for e in errors: print("-",e)
        return 1
    print(f"PASS markdown hygiene ({len(files)} tracked markdown files)")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
