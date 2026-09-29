import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("prepare_phase4",ROOT/"scripts/prepare_phase4_benchmark.py")
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def test_c2_changes_only_display_exposure():
    original={
        "recipe_id":"phase4-cinematic-deterministic",
        "recipe_version":1,
        "operations":[
            {"id":"depth","processor":"depth_atmosphere","params":{"density":0.014}},
            {"id":"display","processor":"display_transform","params":{"curve":"reinhard_srgb","exposure_stops":0.25}},
        ],
    }
    c2=MOD.make_c2_recipe(original)
    assert original["operations"][1]["params"]["exposure_stops"]==0.25
    assert c2["recipe_id"]=="phase4-cinematic-deterministic-c2"
    assert c2["recipe_version"]==2
    assert c2["operations"][0]==original["operations"][0]
    assert c2["operations"][1]["params"]=={"curve":"reinhard_srgb","exposure_stops":0.15}


def test_c2_requires_one_display_transform():
    import pytest
    with pytest.raises(ValueError,match="exactly one"):
        MOD.make_c2_recipe({"operations":[]})

def test_agx_recipe_replaces_only_display_processor():
    original={
        "recipe_id":"phase4-cinematic-deterministic",
        "recipe_version":1,
        "operations":[
            {"id":"depth","processor":"depth_atmosphere","params":{"density":0.014}},
            {"id":"display","processor":"display_transform","params":{"curve":"reinhard_srgb","exposure_stops":0.25}},
        ],
    }
    agx=MOD.make_agx_recipe(original,recipe_id="agx-c",recipe_version=2)
    assert original["operations"][1]["processor"]=="display_transform"
    assert agx["recipe_id"]=="agx-c"
    assert agx["recipe_version"]==2
    assert agx["operations"][0]==original["operations"][0]
    op=agx["operations"][1]
    assert op["processor"]=="agx_display_transform"
    assert op["params"]["exposure_stops"]==0.25
    assert op["params"]["display"]=="sRGB"
    assert op["params"]["view"]=="AgX"
    assert op["params"]["fromspace"]=="Linear Rec.709"
    assert op["params"]["config_sha256"]==MOD.BLENDER_OCIO_CONFIG_SHA256
    assert op["params"]["lut_sha256"]==MOD.BLENDER_AGX_SRGB_LUT_SHA256


def test_agx_recipe_requires_diagnostic_display_transform():
    import pytest
    with pytest.raises(ValueError,match="exactly one"):
        MOD.make_agx_recipe({"operations":[]},recipe_id="x",recipe_version=2)
