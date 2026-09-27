import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"assetctl.py"

def run(*args):
    return subprocess.run([sys.executable,str(SCRIPT),*args],cwd=ROOT,text=True,capture_output=True)

def test_asset_catalog_validates():
    r=run("validate")
    assert r.returncode==0, r.stderr
    assert "PASS" in r.stdout

def test_asset_catalog_has_license_and_distribution_fields():
    data=json.loads((ROOT/"assets"/"catalog.json").read_text())
    ids=set()
    for a in data["assets"]:
        assert a["asset_id"] not in ids
        ids.add(a["asset_id"])
        assert a["license"]["id"]
        assert isinstance(a["license"]["commercial_use"],bool)
        assert a["license"]["raw_redistribution"] in {"allowed","prohibited","unknown"}
        assert a["distribution"]["mode"] in {"catalog_only","core_candidate","goal_pack","local_legacy"}

def test_asset_search_is_useful():
    r=run("search","animation")
    assert r.returncode==0
    assert "code.alesha-hand-drawn-canvas" in r.stdout

def test_core_manifest_references_catalog():
    cat=json.loads((ROOT/"assets"/"catalog.json").read_text())
    core=json.loads((ROOT/"assets"/"core-manifest.json").read_text())
    ids={a["asset_id"] for a in cat["assets"]}
    assert all(e["asset_id"] in ids for e in core["entries"])
