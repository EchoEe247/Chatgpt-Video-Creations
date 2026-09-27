import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from src.core.director_execution import ADAPTERS
from src.core.shot_workflow import resolve_source

ROOT=Path(__file__).resolve().parents[1]


def test_all_renderer_lanes_have_stable_entrypoints():
    expected={"python","canvas_handdrawn","threejs","blender","ffmpeg"}
    assert expected <= set(ADAPTERS)
    for lane in expected:
        assert "{request}" in ADAPTERS[lane]["entrypoint"]
        assert ADAPTERS[lane]["fallback_lanes"] is not None


def test_current_webgl_limitation_is_explicit_not_hidden():
    assert ADAPTERS["threejs"]["ready"] is False
    assert ADAPTERS["threejs"]["fallback_lanes"]==["blender","canvas_handdrawn"]
    assert "WebGL context" in ADAPTERS["threejs"]["runtime_note"]


def test_renderer_adapter_scripts_exist():
    for rel in (
        "scripts/python_shot_adapter.py",
        "scripts/browser_shot_adapter.py",
        "scripts/blender_termux_adapter.py",
        "scripts/blender_shot_adapter.py",
        "scripts/ffmpeg_shot_adapter.py",
        "scripts/rendererctl.py",
        "src/renderers/canvas_handdrawn/request-render.mjs",
    ):
        assert (ROOT/rel).is_file(), rel


def test_shot_template_uses_portable_repo_token():
    data=json.loads((ROOT/"templates/shot-workflow.json").read_text())
    argv=data["shots"][0]["renderer"]
    assert "{request}" in argv
    assert any("{repo}" in x for x in argv)
    assert not any("/data/data/com.termux/" in x for x in argv)
    assert any("{repo}" in x for x in data["shots"][0]["sources"])


def test_repo_token_resolves_portably(tmp_path):
    spec=tmp_path/"spec.json"
    assert resolve_source(spec,"{repo}/scripts/rendererctl.py")==ROOT/"scripts"/"rendererctl.py"


def test_generic_python_adapter_renders_requested_frames(tmp_path):
    source=tmp_path/"renderer.py"
    source.write_text(
        "from PIL import Image\n"
        "def render_frame(shot,frame_index,output_path,request):\n"
        "    Image.new('RGB',(shot['width'],shot['height']),(frame_index%255,10,20)).save(output_path)\n"
    )
    out=tmp_path/"out"
    req=tmp_path/"request.json"
    req.write_text(json.dumps({
        "schema_version":1,
        "shot":{"width":64,"height":48,"fps":24,"duration_seconds":1,"source_offset_seconds":0},
        "frames":[0,5],
        "source_paths":[str(source)],
        "output_dir":str(out)
    }))
    p=subprocess.run([sys.executable,str(ROOT/"scripts/python_shot_adapter.py"),str(req)],cwd=ROOT,text=True,capture_output=True)
    assert p.returncode==0,p.stderr
    for frame in (0,5):
        image=out/f"{frame:06d}.png"
        assert image.is_file()
        with Image.open(image) as im:
            assert im.size==(64,48)