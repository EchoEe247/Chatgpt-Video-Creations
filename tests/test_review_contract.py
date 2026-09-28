import hashlib
import json
import numpy as np
from src.core.review_contract import (
    review_anchors, transition_windows, silence_measure,
    active_speech_windows, validate_perceptual_review,
)
from src.core.creative_qa import validate_assistant_review

def plan():
    return {"shots":[{"id":"a","start_seconds":0,"end_seconds":8,
        "intent":{"visible_event":"Late message"},
        "review_points":[{"absolute_seconds":1},{"absolute_seconds":7}]},
        {"id":"b","start_seconds":8,"end_seconds":12}]}

def test_all_points_text_and_unannotated_shot_are_preserved():
    result=review_anchors(plan(),{"text_items":[{"id":"late","start_seconds":6,"end_seconds":7.9}]})
    assert [x["at_seconds"] for x in result]==[1,7,10,6.95]
    assert len({x["id"] for x in result})==4

def test_invalid_point_and_text_interval_fail():
    import pytest
    p=plan();p["shots"][0]["review_points"][0]["absolute_seconds"]=9
    with pytest.raises(ValueError):review_anchors(p)
    with pytest.raises(ValueError):
        review_anchors(plan(),{"text_items":[{"id":"cross-cut","start_seconds":7,"end_seconds":10}]})

def test_transition_samples_cover_real_shoulders():
    out=transition_windows(plan(),{"transitions":[{"from":"a","to":"b","duration_seconds":.55,"color":"black"}]})
    w=out["boundaries"][0]
    assert min(w["sample_times"])<8-.55
    assert max(w["sample_times"])>8+.55
    assert out["color_fade_count"]==1
    assert out["color_fade_ratio"]==1

def test_short_collision_hidden_by_average_is_detected():
    sr=1000;voice=np.ones(10*sr)*.05;bed=np.ones(10*sr)*.0001
    bed[4000:4200]=.08
    # Whole-shot voice/bed margin still exceeds 10 dB.
    assert 20*np.log10(np.sqrt(np.mean(voice**2))/np.sqrt(np.mean(bed**2)))>10
    out=active_speech_windows(voice,bed,sr)
    assert out["risk_windows"][0]["start_seconds"]==4
    assert out["risk_windows"][0]["end_seconds"]==4.2

def test_silence_checks_interior_pulses_and_absent_samples():
    x=np.zeros(2000);x[1500:1510]=.2
    assert silence_measure(x,1000,1,1)["warning"]
    assert not silence_measure(np.zeros(2000),1000,1,1)["warning"]
    assert not silence_measure(x,1000,1,2)["measurable"]

def test_v3_rejects_stills_as_audio_or_motion_and_missing_points():
    report={"review_coverage":{"required_points":[{"id":"a"}],"missing_point_ids":["a"]}}
    review={"criteria":{"motion_smoothness":{"pass":True,"method":"still_inspection","evidence":["a.jpg"]},
                        "narration_clarity":{"pass":True,"method":"measurements","evidence":["a.png"]}}}
    errors=validate_perceptual_review(report,review)
    assert any("narration_clarity" in e for e in errors)
    assert any("motion_smoothness" in e for e in errors)
    assert any("omits" in e for e in errors)
    assert any("every required point" in e for e in errors)

def test_observation_cannot_borrow_another_shots_evidence():
    report={"review_coverage":{"required_points":[{"id":"a"}]},
            "evidence":{"review_points":[{"id":"a","phone_frame":"a.jpg","normal_speed_clip":"a.mp4"}]}}
    review={"criteria":{"composition":{"pass":False}},
            "observations":[{"point_id":"a","observed":"city","intent_match":True,"evidence":["b.jpg"]}]}
    assert any("own point" in e for e in validate_perceptual_review(report,review))

def test_duplicate_warning_dispositions_rejected(tmp_path):
    keys=("composition","phone_scale_readability","visible_motion","camera_variety",
          "normal_speed_story_read","motion_smoothness","transition_coherence",
          "visual_style_continuity","audio_continuity","narration_clarity","av_sync")
    report={"schema_version":2,"media_sha256":"a"*64,"warnings":[{"code":"w"}],
            "evidence":{"contact_sheet":"a.jpg"}}
    rp=tmp_path/"report.json";rp.write_text(json.dumps(report))
    item={"code":"w","status":"accepted_intentional","notes":"reviewed","evidence":["a.jpg"]}
    review={"candidate_sha256":"a"*64,"creative_qa_sha256":hashlib.sha256(rp.read_bytes()).hexdigest(),
            "criteria":{k:{"pass":True,"notes":"observed","evidence":["a.jpg"]} for k in keys},
            "warning_dispositions":[item,item],"defects":[],"next_change":""}
    vp=tmp_path/"review.json";vp.write_text(json.dumps(review))
    assert not validate_assistant_review(rp,vp)["valid"]

def test_contact_sheet_samples_and_labels_source_time(tmp_path,monkeypatch):
    from PIL import Image
    from src.core import media
    calls=[]
    monkeypatch.setattr(media,"probe_media",lambda p:{"duration_seconds":8})
    def frame(p,dest,*,time_seconds,max_width):
        calls.append(time_seconds)
        Image.new("RGB",(160,90),("red" if time_seconds<4 else "blue")).save(dest)
    monkeypatch.setattr(media,"extract_frame",frame)
    out=media.build_contact_sheet(tmp_path/"video.mp4",tmp_path/"sheet.png",count=4,columns=2,cell_width=160)
    assert calls==[1,3,5,7]
    with Image.open(out) as im:
        assert im.getpixel((80,60))[0]>200
        assert im.getpixel((80,174))[2]>200
def test_opposite_phase_channels_are_not_false_silence():
    x=np.column_stack([np.ones(1000)*.1,-np.ones(1000)*.1])
    assert silence_measure(x,1000,0,1)["warning"]

def test_v3_complete_direct_review_can_pass_contract():
    report={"media_sha256":"a"*64,
            "review_coverage":{"required_points":[{"id":"a"}],"missing_point_ids":[]},
            "evidence":{"review_points":[{"id":"a","phone_frame":"a.jpg","normal_speed_clip":"a.mp4"}]}}
    review={"criteria":{"narration_clarity":{"pass":True,"method":"audio_listening","evidence":["a.mp4"]}},
            "perception_receipt":{"route_id":"route","bridge_fingerprint":"bridge","capability_receipt_sha256":"b"*64,
                                  "capabilities":{"auditory":{"state":"AVAILABLE"},"continuous_video":{"state":"AVAILABLE"},"synchronized_av":{"state":"AVAILABLE"}}},
            "observations":[{"point_id":"a","observed":"The message resolves fully.","intent_match":True,"evidence":["a.jpg"]}],
            "full_film_review":{"candidate_sha256":"a"*64,"method":"audiovisual_playback","completed":True,"observed":"Read and heard the full sequence."}}
    assert validate_perceptual_review(report,review)==[]


def test_audio_listening_pass_requires_route_bound_perception_receipt():
    report={"review_coverage":{"required_points":[],"missing_point_ids":[]},"evidence":{"review_points":[]}}
    review={"criteria":{"narration_clarity":{"pass":True,"method":"audio_listening","evidence":["a.wav"]}},
            "observations":[]}
    errors=validate_perceptual_review(report,review)
    assert any("auditory perception receipt" in e for e in errors)