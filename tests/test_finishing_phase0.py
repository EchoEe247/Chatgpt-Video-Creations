from scripts.finishing_phase0 import parse_channels, parse_stat_line, vector_nonzero

def test_parse_multilayer_channel_inventory():
    info = """image.exr : 1280 x 720, 3 channel, float openexr
    channel list: ViewLayer.Combined.R (half), ViewLayer.Vector.X (float), ViewLayer.Vector.Y (float)
"""
    assert parse_channels(info) == [
        "ViewLayer.Combined.R",
        "ViewLayer.Vector.X",
        "ViewLayer.Vector.Y",
    ]

def test_vector_nonzero_uses_pixel_stats():
    stats = """    Stats Min: -2.500000 0.000000 0.000000 0.000000 (float)
    Stats Max: 0.000000 1.250000 0.000000 0.000000 (float)
"""
    assert parse_stat_line(stats, "Min") == [-2.5, 0.0, 0.0, 0.0]
    assert vector_nonzero(stats)

def test_vector_zero_is_rejected():
    stats = """    Stats Min: 0.000000 0.000000 0.000000 0.000000 (float)
    Stats Max: 0.000000 0.000000 0.000000 0.000000 (float)
"""
    assert not vector_nonzero(stats)

def test_phase0_blender_fixture_is_tracked():
    from pathlib import Path
    assert Path("scripts/blender_phase0_fixture.py").is_file()
