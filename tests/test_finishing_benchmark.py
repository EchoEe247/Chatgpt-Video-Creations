import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("finishing_benchmark_script",ROOT/"scripts/finishing_benchmark.py")
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def recipe():
    return {
        "schema_version":1,
        "kind":"finishing-recipe",
        "recipe_id":"x",
        "recipe_version":1,
        "operations":[
            {"id":"depth","processor":"depth_atmosphere","risk_class":"S","color_stage":"scene_linear","inputs":["beauty","depth"],"masks":[],"params":{},"deterministic":True,"uses_randomness":False,"seed":None},
            {"id":"display","processor":"display_transform","risk_class":"P","color_stage":"display_referred","inputs":["beauty"],"masks":[],"params":{},"deterministic":True,"uses_randomness":False,"seed":None},
        ],
        "output":{"lossless_format":"OPEN_EXR","delivery_color_stage":"display_referred"},
    }


def test_baseline_recipe_keeps_only_shared_display_transform():
    baseline=MOD.baseline_recipe(recipe())
    assert baseline["recipe_id"]=="x-beauty-baseline"
    assert len(baseline["operations"])==1
    assert baseline["operations"][0]["processor"]=="display_transform"
    assert baseline["operations"][0]["id"]=="baseline-display"


def test_baseline_recipe_requires_exactly_one_display_transform():
    data=recipe()
    data["operations"]=data["operations"][:1]
    try:
        MOD.baseline_recipe(data)
    except ValueError as exc:
        assert "exactly one display_transform" in str(exc)
    else:
        raise AssertionError("missing display transform should fail")


def test_png_delta_reports_descriptive_pixel_distance(tmp_path):
    a=np.zeros((4,4,3),dtype=np.uint8)
    b=np.full((4,4,3),64,dtype=np.uint8)
    pa=tmp_path/"a.png"; pb=tmp_path/"b.png"
    Image.fromarray(a).save(pa); Image.fromarray(b).save(pb)
    delta=MOD.png_delta(pa,pb)
    expected=round(64/255,6)
    assert delta=={"mean":expected,"p95":expected,"max":expected}
