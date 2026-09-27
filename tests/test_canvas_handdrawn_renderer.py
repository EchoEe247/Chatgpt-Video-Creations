import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "canvas_handdrawn_adapter.py"
ENGINE = ROOT / "src" / "renderers" / "canvas_handdrawn"


def test_canvas_renderer_vendor_surface_is_complete():
    required = [
        ENGINE / "LICENSE.upstream",
        ENGINE / "render.mjs",
        ENGINE / "package.json",
        ENGINE / "package-lock.json",
        ENGINE / "runtime" / "core.js",
        ENGINE / "runtime" / "studio.js",
        ENGINE / "runtime" / "cels.js",
        ENGINE / "runtime" / "materials.js",
    ]
    assert all(p.is_file() for p in required)


def test_canvas_adapter_cli_is_parseable():
    r = subprocess.run(
        [sys.executable, str(ADAPTER), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert r.returncode == 0, r.stderr
    assert "setup" in r.stdout
    assert "preview" in r.stdout
    assert "render" in r.stdout


def test_canvas_asset_catalog_points_at_integrated_runtime():
    catalog = json.loads((ROOT / "assets" / "catalog.json").read_text())
    asset = next(a for a in catalog["assets"] if a["asset_id"] == "code.alesha-hand-drawn-canvas")
    assert asset["source"]["commit"] == "b80438eb33823156c575cbedd282a8aa1b32de9f"
    assert asset["distribution"]["local_hint"] == "src/renderers/canvas_handdrawn"
    assert (ROOT / asset["distribution"]["local_hint"]).is_dir()


def test_original_canvas_smoke_film_exists():
    p = ROOT / "examples" / "canvas-handdrawn" / "signal-seed.html"
    text = p.read_text()
    assert "defineFilm" in text
    assert "signal-seed" not in text.lower() or "<title>Signal Seed" in text
    assert "src/renderers/canvas_handdrawn/runtime/core.js" in text
