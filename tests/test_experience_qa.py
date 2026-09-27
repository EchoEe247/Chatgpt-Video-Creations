import json, wave
from pathlib import Path

import numpy as np

from src.core.experience_qa import motion_smoothness, audio_continuity, effect_sync_signal
from src.core.creative_qa import validate_assistant_review


def test_motion_smoothness_flags_spiky_cadence():
    signal={"series":[]}
    vals=[.010,.011,.009,.010,.11,.009,.010,.011]
    for i,v in enumerate(vals,1):
        signal["series"].append({"time_seconds":i*.25,"mean_delta":v,"changed_ratio":.08})
    plan={"shots":[{"id":"a","start_seconds":0,"end_seconds":2.1}]}
    out=motion_smoothness(signal,plan)
    assert out["shots"][0]["cadence_warning"] is True
    assert "isolated_motion_spikes" in out["shots"][0]["reasons"]


def test_motion_smoothness_accepts_consistent_motion():
    signal={"series":[
        {"time_seconds":i*.25,"mean_delta":.018+(i%2)*.001,"changed_ratio":.10}
        for i in range(1,9)
    ]}
    plan={"shots":[{"id":"a","start_seconds":0,"end_seconds":2.1}]}
    out=motion_smoothness(signal,plan)
    assert out["warning_shots"]==[]


def _write_wav(path: Path, values: np.ndarray, sr=16000):
    pcm=(np.clip(values,-1,1)*32767).astype("<i2")
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())


def test_audio_continuity_finds_large_cut_jump_and_voice_mask(tmp_path):
    sr=16000
    a=np.full(sr,.008,dtype=np.float32)
    b=np.full(sr,.25,dtype=np.float32)
    master=np.concatenate([a,b])
    master_wav=tmp_path/"master.wav";_write_wav(master_wav,master,sr)
    stems=tmp_path/"stems";stems.mkdir()
    voice=np.concatenate([
        .035*np.sin(2*np.pi*220*np.arange(sr)/sr),
        .035*np.sin(2*np.pi*220*np.arange(sr)/sr)
    ]).astype(np.float32)
    bed=np.full(sr*2,.05,dtype=np.float32)
    _write_wav(stems/"narration.wav",voice,sr)
    _write_wav(stems/"score.wav",bed,sr)
    _write_wav(stems/"ambience.wav",np.zeros(sr*2,dtype=np.float32),sr)
    _write_wav(stems/"effects.wav",np.zeros(sr*2,dtype=np.float32),sr)
    plan={"shots":[
        {"id":"a","start_seconds":0,"end_seconds":1},
        {"id":"b","start_seconds":1,"end_seconds":2},
    ]}
    out=audio_continuity(master_wav,plan,stems_dir=stems,sample_rate=sr)
    assert out["warning_boundaries"]
    assert out["stems"]["available"] is True
    assert any(x["masking"] for x in out["stems"]["warnings"])


def test_schema2_review_requires_experience_criteria(tmp_path):
    report=tmp_path/"creative-qa.json"
    report.write_text(json.dumps({
        "schema_version":2,
        "media_sha256":"b"*64,
        "evidence":{"contact_sheet":"contact.jpg","review_points":[],"transitions":[],"sync_events":[]}
    }))
    import hashlib
    digest=hashlib.sha256(report.read_bytes()).hexdigest()
    old=("composition","phone_scale_readability","visible_motion","camera_variety","normal_speed_story_read")
    review={
        "candidate_sha256":"b"*64,
        "creative_qa_sha256":digest,
        "criteria":{k:{"pass":True,"notes":"reviewed","evidence":["contact.jpg"]} for k in old},
        "defects":[],"next_change":""
    }
    rp=tmp_path/"review.json";rp.write_text(json.dumps(review))
    out=validate_assistant_review(report,rp)
    assert out["valid"] is False
    assert "review criteria set is incomplete" in out["errors"]

def test_schema2_warnings_cannot_be_silently_ignored(tmp_path):
    report=tmp_path/"creative-qa.json"
    report.write_text(json.dumps({
        "schema_version":2,
        "media_sha256":"c"*64,
        "warnings":[{"code":"visual_transition_review","detail":["a->b"]}],
        "evidence":{
            "contact_sheet":"contact.jpg",
            "review_points":[],
            "transitions":[{"strip":"transitions/a-b.jpg","clip":"transitions/a-b.mp4"}],
            "sync_events":[]
        }
    }))
    import hashlib
    digest=hashlib.sha256(report.read_bytes()).hexdigest()
    keys=(
        "composition","phone_scale_readability","visible_motion","camera_variety",
        "normal_speed_story_read","motion_smoothness","transition_coherence",
        "visual_style_continuity","audio_continuity","narration_clarity","av_sync"
    )
    review={
        "candidate_sha256":"c"*64,
        "creative_qa_sha256":digest,
        "criteria":{k:{"pass":True,"notes":"reviewed","evidence":["contact.jpg"]} for k in keys},
        "warning_dispositions":[],
        "defects":[],
        "next_change":""
    }
    rp=tmp_path/"review.json";rp.write_text(json.dumps(review))
    out=validate_assistant_review(report,rp)
    assert out["valid"] is False
    assert "warning_dispositions must cover every report warning exactly once" in out["errors"]

    review["warning_dispositions"]=[{
        "code":"visual_transition_review",
        "status":"repair_required",
        "notes":"transition visibly breaks the visual language",
        "evidence":["transitions/a-b.jpg"]
    }]
    review["next_change"]="repair the transition"
    rp.write_text(json.dumps(review))
    out=validate_assistant_review(report,rp)
    assert out["valid"] is True
    assert out["pass"] is False
    assert out["repair_warnings"]==["visual_transition_review"]

def test_effect_sync_signal_detects_authored_onset(tmp_path):
    sr=16000
    stems=tmp_path/"stems";stems.mkdir()
    x=np.zeros(sr*2,dtype=np.float32)
    x[int(.5*sr):int(.55*sr)]=.1
    _write_wav(stems/"effects.wav",x,sr)
    timeline=tmp_path/"timeline.json"
    timeline.write_text(json.dumps({"events":[{
        "id":"hit","at_seconds":.5,
        "asset_id":"audio.core-procedural:soft_impact"
    }]}))
    out=effect_sync_signal(timeline,stems,sample_rate=sr)
    assert out["available"] is True
    assert out["warnings"]==[]
    assert abs(out["events"][0]["onset_offset_ms"])<5
