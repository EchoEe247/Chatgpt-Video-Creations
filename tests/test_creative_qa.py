import json
from copy import deepcopy
from pathlib import Path

from src.core.creative_qa import camera_family,camera_repetition,layout_checks,segment_motion,validate_assistant_review

ROOT=Path(__file__).resolve().parents[1]


def test_camera_family_normalization():
    assert camera_family("Slow push toward the core.")=="push"
    assert camera_family("Visible camera translation plus orbital travel.")=="orbit"
    assert camera_family("Controlled final hold.")=="hold"


def test_camera_repetition_flags_consecutive_family():
    plan={"shots":[
        {"id":"a","motion":{"camera":"Slow spatial drift."}},
        {"id":"b","motion":{"camera":"Perspective drift around structure."}},
        {"id":"c","motion":{"camera":"Orbit around subject."}},
    ]}
    out=camera_repetition(plan)
    assert out["consecutive_repeats"]==[{"shots":["a","b"],"family":"drift"}]


def test_layout_checks_safe_area_and_phone_font():
    layout={"safe_margin_ratio":0.04,"text_items":[
        {"id":"good","bbox_norm":[.1,.1,.5,.1],"font_px":48},
        {"id":"bad","bbox_norm":[.01,.1,.5,.1],"font_px":20},
    ]}
    out=layout_checks(layout,master_width=1280,master_height=720,phone_width=360,min_phone_font_px=11)
    codes={(x["id"],x["code"]) for x in out["violations"]}
    assert ("bad","safe_area") in codes
    assert ("bad","phone_font") in codes
    assert not any(x["id"]=="good" for x in out["violations"])


def test_layout_without_metadata_does_not_fake_text_pass():
    out=layout_checks(None,master_width=1280,master_height=720)
    assert out["manual_text_review_required"] is True
    assert out["metadata_present"] is False


def test_segment_motion_flags_only_weak_shot():
    signal={"series":[
      {"time_seconds":.25,"mean_delta":.001,"changed_ratio":.002},
      {"time_seconds":.5,"mean_delta":.002,"changed_ratio":.003},
      {"time_seconds":1.25,"mean_delta":.02,"changed_ratio":.25},
      {"time_seconds":1.5,"mean_delta":.03,"changed_ratio":.30},
    ]}
    plan={"shots":[
      {"id":"a","start_seconds":0,"end_seconds":1,"motion":{}},
      {"id":"b","start_seconds":1,"end_seconds":2,"motion":{}},
    ]}
    out=segment_motion(signal,plan)
    assert out[0]["weak_motion_signal"] is True
    assert out[1]["weak_motion_signal"] is False


def test_assistant_review_must_be_hash_bound_and_use_generated_evidence(tmp_path):
    report=tmp_path/"creative-qa.json"
    report.write_text(json.dumps({
      "media_sha256":"a"*64,
      "evidence":{"contact_sheet":"contact-sheet.jpg","review_points":[{"phone_frame":"phone/a.jpg","normal_speed_clip":"normal/a.mp4"}]}
    }))
    import hashlib
    digest=hashlib.sha256(report.read_bytes()).hexdigest()
    review={
      "candidate_sha256":"a"*64,"creative_qa_sha256":digest,
      "criteria":{
        k:{"pass":True,"notes":"reviewed","evidence":["contact-sheet.jpg"]}
        for k in ("composition","phone_scale_readability","visible_motion","camera_variety","normal_speed_story_read")
      },
      "defects":[],"next_change":""
    }
    rp=tmp_path/"review.json"; rp.write_text(json.dumps(review))
    assert validate_assistant_review(report,rp)["pass"] is True
    review["criteria"]["visible_motion"]["evidence"]=["invented.mp4"]
    rp.write_text(json.dumps(review))
    out=validate_assistant_review(report,rp)
    assert out["valid"] is False
    assert any("generated creative-QA artifacts" in e for e in out["errors"])
