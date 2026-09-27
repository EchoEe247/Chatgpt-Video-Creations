#!/usr/bin/env python3
"""Small dependency-free asset catalog CLI for local video production."""
from __future__ import annotations
import argparse, hashlib, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets" / "catalog.json"
CORE = ROOT / "assets" / "core-manifest.json"
LOCAL = ROOT / "assets" / "local-state.json"

REQUIRED = {"asset_id","name","kind","source","license","distribution","compatibility","tags"}
MODES = {"catalog_only","core_candidate","goal_pack","local_legacy"}
REDIST = {"allowed","prohibited","unknown"}

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def validate_catalog(data):
    errors=[]
    if data.get("schema_version") != 1: errors.append("catalog schema_version must be 1")
    assets=data.get("assets")
    if not isinstance(assets,list): return errors+["assets must be a list"]
    seen=set()
    for i,a in enumerate(assets):
        p=f"assets[{i}]"
        missing=REQUIRED-set(a)
        if missing: errors.append(f"{p}: missing {sorted(missing)}"); continue
        aid=a["asset_id"]
        if aid in seen: errors.append(f"{p}: duplicate asset_id {aid}")
        seen.add(aid)
        lic=a["license"]
        for k in ("id","commercial_use","modification_allowed","attribution_required","raw_redistribution","verified_on"):
            if k not in lic: errors.append(f"{p}.license: missing {k}")
        if lic.get("raw_redistribution") not in REDIST: errors.append(f"{p}.license.raw_redistribution invalid")
        if a["distribution"].get("mode") not in MODES: errors.append(f"{p}.distribution.mode invalid")
        if not isinstance(a["compatibility"].get("renderers"),list): errors.append(f"{p}.compatibility.renderers must be list")
        if not isinstance(a["tags"],list): errors.append(f"{p}.tags must be list")
    return errors

def catalog_assets():
    data=load(CATALOG)
    errors=validate_catalog(data)
    if errors:
        raise SystemExit("INVALID CATALOG\n" + "\n".join(errors))
    return data["assets"]

def local_state():
    if not LOCAL.exists(): return {"schema_version":1,"installed":{}}
    return load(LOCAL)

def matches(a,args):
    if args.kind and a["kind"] != args.kind: return False
    if args.tag and args.tag.lower() not in {t.lower() for t in a["tags"]}: return False
    if args.renderer and args.renderer.lower() not in {r.lower() for r in a["compatibility"]["renderers"]}: return False
    if getattr(args,"core",False) and a["distribution"]["mode"] != "core_candidate": return False
    return True

def print_asset(a, installed=None):
    mark=""
    if installed is not None: mark=" installed=yes" if installed else " installed=no"
    print(f'{a["asset_id"]}\t{a["kind"]}\t{a["distribution"]["mode"]}\t{a["license"]["id"]}{mark}\t{a["name"]}')

def cmd_validate(_):
    errors=validate_catalog(load(CATALOG))
    core=load(CORE)
    ids={a["asset_id"] for a in load(CATALOG)["assets"]}
    for i,e in enumerate(core.get("entries",[])):
        if e.get("asset_id") not in ids: errors.append(f'core.entries[{i}]: unknown asset_id {e.get("asset_id")}')
    if errors:
        print("\n".join(errors),file=sys.stderr); return 1
    print(f"PASS catalog={len(ids)} core_entries={len(core.get('entries',[]))}")
    return 0

def cmd_list(args):
    state=local_state().get("installed",{})
    for a in catalog_assets():
        if matches(a,args): print_asset(a,a["asset_id"] in state)
    return 0

def cmd_search(args):
    q=args.query.lower()
    state=local_state().get("installed",{})
    for a in catalog_assets():
        hay=" ".join([a["asset_id"],a["name"],a["kind"],*a["tags"],a.get("notes") or ""]).lower()
        if q in hay and matches(a,args): print_asset(a,a["asset_id"] in state)
    return 0

def cmd_scan(_):
    installed={}
    for a in catalog_assets():
        hint=a["distribution"].get("local_hint")
        if not hint: continue
        p=(ROOT / hint).resolve()
        if not p.exists(): continue
        item={"path":str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),"type":"directory" if p.is_dir() else "file"}
        if p.is_file():
            item["bytes"]=p.stat().st_size
            h=hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
            item["sha256"]=h.hexdigest()
        installed[a["asset_id"]]=item
    LOCAL.write_text(json.dumps({"schema_version":1,"installed":installed},indent=2)+"\n",encoding="utf-8")
    print(f"WROTE {LOCAL.relative_to(ROOT)} installed={len(installed)}")
    return 0

def cmd_status(_):
    assets=catalog_assets(); state=local_state().get("installed",{})
    by_mode={}
    for a in assets: by_mode[a["distribution"]["mode"]]=by_mode.get(a["distribution"]["mode"],0)+1
    print(f"catalog={len(assets)} installed={len(state)} core_candidates={by_mode.get('core_candidate',0)} goal_pack={by_mode.get('goal_pack',0)} catalog_only={by_mode.get('catalog_only',0)} local_legacy={by_mode.get('local_legacy',0)}")
    return 0

def parser():
    p=argparse.ArgumentParser()
    sp=p.add_subparsers(dest="cmd",required=True)
    sp.add_parser("validate")
    sp.add_parser("scan-local")
    sp.add_parser("status")
    for name in ("list","search"):
        x=sp.add_parser(name)
        if name=="search": x.add_argument("query")
        x.add_argument("--kind"); x.add_argument("--tag"); x.add_argument("--renderer"); x.add_argument("--core",action="store_true")
    return p

def main():
    args=parser().parse_args()
    return {"validate":cmd_validate,"scan-local":cmd_scan,"status":cmd_status,"list":cmd_list,"search":cmd_search}[args.cmd](args)

if __name__=="__main__":
    raise SystemExit(main())
