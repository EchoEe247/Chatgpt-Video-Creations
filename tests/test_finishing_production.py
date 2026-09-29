import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from src.core.finishing_contract import canonical_json_sha256
from src.core.production_manifest import validate_production_v2

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=json.loads((ROOT/"templates/production-v2.json").read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_ctl(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python","scripts/productionctl.py",*map(str,args)],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )


def build_finishing_evidence(root: Path):
    bundle_root=root/"bundle"; bundle_root.mkdir(parents=True)
    source_frame=bundle_root/"frame-0001.exr"; source_frame.write_bytes(b"source-exr")
    bundle={
        "schema_version":1,"kind":"blender-render-bundle",
        "production_id":"finishing-binding","shot_id":"shot-01",
        "source":{"scene_path":"scene.blend","scene_sha256":"0"*64,"execution_plan_sha256":"1"*64},
        "render":{"engine":"CYCLES","width":2,"height":2,"native_fps":24,"frame_start":1,"frame_end":1,"color_space":"scene_linear","view_transform":"AgX"},
        "pass_map":{"beauty":["ViewLayer.Combined.R"]},
        "frames":[{"frame":1,"path":"frame-0001.exr","sha256":sha(source_frame),"bytes":source_frame.stat().st_size,"readback_status":"verified"}],
        "protections":[],
        "approved_facts":{},
        "policy":{"allowed_processor_classes":["P"],"prohibited_transforms":[]},
        "runtime":{"blender_version":"4.0.2","readback_tool":"test","platform":"test"},
    }
    recipe={
        "schema_version":1,"kind":"finishing-recipe","recipe_id":"test-finish","recipe_version":1,
        "operations":[{"id":"display","processor":"display_transform","risk_class":"P","color_stage":"display_referred","inputs":["beauty"],"masks":[],"params":{},"deterministic":True,"uses_randomness":False,"seed":None}],
        "output":{"lossless_format":"OPEN_EXR","delivery_color_stage":"display_referred"},
    }
    bundle_path=bundle_root/"render-bundle.json"; bundle_path.write_text(json.dumps(bundle,indent=2)+"\n")
    recipe_path=bundle_root/"recipe.json"; recipe_path.write_text(json.dumps(recipe,indent=2)+"\n")

    finished=root/"finished"; finished.mkdir()
    exr=finished/"frame-0001.exr"; exr.write_bytes(b"finished-exr")
    png=finished/"frame-0001.png"; png.write_bytes(b"preview")
    receipt={
        "schema_version":1,"kind":"finishing-receipt",
        "bundle_sha256":canonical_json_sha256(bundle),
        "recipe_sha256":canonical_json_sha256(recipe),
        "frames":[{
            "frame":1,"source_sha256":sha(source_frame),
            "path":exr.name,"sha256":sha(exr),"bytes":exr.stat().st_size,
            "preview_path":png.name,"preview_sha256":sha(png),
            "color_stage":"display_referred","skipped_existing":False,
        }],
    }
    receipt_path=finished/"finishing-receipt.json"; receipt_path.write_text(json.dumps(receipt,indent=2)+"\n")
    return bundle_path,recipe_path,receipt_path


def test_candidate_finishing_provenance_is_immutable_and_repair_counted():
    with tempfile.TemporaryDirectory() as td:
        package=Path(td)/"production"; package.mkdir()
        data=copy.deepcopy(TEMPLATE)
        data["production_id"]="finishing-binding"
        data["workflow"]["bootstrap_required"]=False
        data["workflow"]["quality_floor_required"]=False
        data["workflow"]["studio_review_required"]=False
        data["workflow"]["creative_qa_required"]=False
        data["source"]["show"]="test-show"
        data["delivery"]["expected_duration_seconds"]=1.0
        manifest=package/"production.json"
        manifest.write_text(json.dumps(data,indent=2)+"\n")
        assert validate_production_v2(data)==[]

        candidate=Path(td)/"candidate.mp4"; candidate.write_bytes(b"candidate-one")
        bundle,recipe,receipt=build_finishing_evidence(Path(td)/"evidence")
        result=run_ctl(
            "candidate",manifest,candidate,
            "--finishing-bundle",bundle,
            "--finishing-recipe",recipe,
            "--finishing-receipt",receipt,
        )
        assert result.returncode==0, result.stderr+result.stdout
        current=json.loads(manifest.read_text())
        provenance=current["artifacts"]["finishing_provenance"]
        assert provenance["candidate_sha256"]==current["artifacts"]["candidate_sha256"]
        assert provenance["bundle_sha256"]
        assert provenance["recipe_sha256"]
        assert provenance["receipt_sha256"]
        assert provenance["finished_frame_manifest_sha256"]
        for key in ("bundle","recipe","receipt","provenance"):
            assert (package/provenance[key]).is_file()

        repair=run_ctl("repair-start",manifest,"--reason","finishing-only repair")
        assert repair.returncode==0, repair.stderr+repair.stdout
        after=json.loads(manifest.read_text())
        assert after["workflow"]["repair_cycle"]==1
        assert after["artifacts"]["finishing_provenance"] is None
        archived=after["history"][-1]["artifacts"]["finishing_provenance"]
        assert archived==provenance


def test_candidate_requires_complete_finishing_triplet():
    with tempfile.TemporaryDirectory() as td:
        package=Path(td)/"production"; package.mkdir()
        data=copy.deepcopy(TEMPLATE)
        data["production_id"]="finishing-incomplete"
        data["workflow"]["bootstrap_required"]=False
        data["workflow"]["quality_floor_required"]=False
        data["workflow"]["studio_review_required"]=False
        data["workflow"]["creative_qa_required"]=False
        data["source"]["show"]="test-show"
        manifest=package/"production.json"; manifest.write_text(json.dumps(data,indent=2)+"\n")
        candidate=Path(td)/"candidate.mp4"; candidate.write_bytes(b"candidate")
        bundle,_,_=build_finishing_evidence(Path(td)/"evidence")
        result=run_ctl("candidate",manifest,candidate,"--finishing-bundle",bundle)
        assert result.returncode==2
        assert "must be provided together" in result.stderr