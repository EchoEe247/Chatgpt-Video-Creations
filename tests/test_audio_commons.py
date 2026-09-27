import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_audio_commons_manifest_is_portable_and_complete():
    manifest=json.loads((ROOT/"assets"/"audio-commons.json").read_text())
    assert manifest["schema_version"]==1
    assert manifest["pack_id"]=="audio.core-procedural"
    assert manifest["generated_deterministically"] is True
    assert len(manifest["assets"])==6
    ids={a["id"] for a in manifest["assets"]}
    assert {"ui_tick","soft_impact","air_whoosh","riser_short","low_pulse","signal_chime"} <= ids
    for asset in manifest["assets"]:
        assert asset["sample_rate"]==48000
        assert asset["channels"]==2
        assert len(asset["sha256"])==64


def test_audio_commons_is_registered_as_integrated_core_asset():
    catalog=json.loads((ROOT/"assets"/"catalog.json").read_text())
    core=json.loads((ROOT/"assets"/"core-manifest.json").read_text())
    asset=next(a for a in catalog["assets"] if a["asset_id"]=="audio.core-procedural")
    assert asset["kind"]=="audio_pack"
    assert asset["distribution"]["local_hint"]=="assets/core/payload/audio-procedural"
    entry=next(e for e in core["entries"] if e["asset_id"]=="audio.core-procedural")
    assert entry["state"]=="integrated"


def test_freesound_catalog_entry_requires_per_file_license_filtering():
    catalog=json.loads((ROOT/"assets"/"catalog.json").read_text())
    asset=next(a for a in catalog["assets"] if a["asset_id"]=="provider.freesound-cc0")
    assert asset["distribution"]["mode"]=="catalog_only"
    assert "CC0" in asset["license"]["id"]
    assert asset["license"]["raw_redistribution"]=="unknown"
