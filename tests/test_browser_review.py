import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"scripts"/"make_browser_review.py"
spec=importlib.util.spec_from_file_location("make_browser_review",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def test_browser_review_page_has_playback_controls_and_times():
    page=m.build_page("clip.mp4",[0.5,1.25],"Review")
    assert 'src="clip.mp4"' in page
    assert 'data-time="0.500"' in page
    assert 'data-time="1.250"' in page
    assert 'getVideoPlaybackQuality' in page
    assert '0.5x' in page
    assert "\\\\ndecoded=" in page
