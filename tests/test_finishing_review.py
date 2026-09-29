from scripts.make_finishing_review import build_page


def test_finishing_review_has_shared_seek_and_native_controls():
    page=build_page("arm-b.mp4","arm-c.mp4",title="B vs C",fps=24)
    assert 'id="scrub"' in page
    assert 'controls playsinline' in page
    assert 'id="back"' in page and 'id="forward"' in page
    assert 'data-mode="split"' in page
    assert 'Open B MP4' in page and 'Open C MP4' in page
    assert '0.041666667' in page


def test_finishing_review_escapes_title_and_sources():
    page=build_page('b&x.mp4','c"x.mp4',title='<review>',fps=30)
    assert '&lt;review&gt;' in page
    assert 'b&amp;x.mp4' in page
    assert 'c&quot;x.mp4' in page
