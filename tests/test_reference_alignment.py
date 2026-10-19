"""Tests for the real-reference alignment route in the intended film repository."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.core.reference_alignment import (
    ReferenceAlignmentError, make_lock, verify_lock, compare,
)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class ReferenceAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.source=self.dir/"source-phone.mp4"
        self.candidate=self.dir/"candidate.mp4"
        # Two visibly different scenes. The film is within black screen-recording chrome.
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
           "-f","lavfi","-i","testsrc=size=320x180:rate=12:duration=2",
           "-f","lavfi","-i","sine=frequency=440:sample_rate=48000:duration=2",
           "-vf","pad=320:240:0:30:black","-c:v","libx264","-pix_fmt","yuv420p",
           "-c:a","aac","-shortest","-y",str(self.source)],check=True)
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
           "-i",str(self.source),"-vf","crop=320:180:0:30",
           "-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",
           "-y",str(self.candidate)],check=True)
        self.shots=[
            {"id":"opening","source_start_seconds":0,"source_end_seconds":1,
             "target_start_frame":0,"target_end_frame":12,"complexity":"high",
             "visual_intent":"Moving test image enters the opening"},
            {"id":"ending","source_start_seconds":1,"source_end_seconds":2,
             "target_start_frame":12,"target_end_frame":24,"complexity":"normal",
             "visual_intent":"Moving image continues to final lockup"}]

    def lock(self,**kwargs):
        values={"width":320,"height":180,"fps":"12/1","duration_seconds":2,
                "crop_verified":True}
        values.update(kwargs)
        return make_lock(self.source,"320:180:0:30",self.shots,**values)

    def test_source_lock_source_drift_and_crop_verification(self):
        lock=self.lock()
        verify_lock(lock)
        with self.assertRaisesRegex(ReferenceAlignmentError,"verification"):
            self.lock(crop_verified=False)
        with self.assertRaisesRegex(ReferenceAlignmentError,"crop outside"):
            make_lock(self.source,"320:180:0:100",self.shots,**{
                "width":320,"height":180,"fps":"12/1","duration_seconds":2,
                "crop_verified":True})
        with self.source.open("ab") as f:
            f.write(b"nonvideo-mark")
        with self.assertRaisesRegex(ReferenceAlignmentError,"changed"):
            verify_lock(lock)

    def test_timing_and_aspect_fail_closed(self):
        with self.assertRaisesRegex(ReferenceAlignmentError,"aspect ratio"):
            self.lock(width=400,height=180)
        with self.assertRaisesRegex(ReferenceAlignmentError,"integer"):
            self.lock(duration_seconds=2.03)
        for changes in (
            {"target_start_frame":13},
            {"source_start_seconds":.5},
            {"target_end_frame":25},
        ):
            previous=self.shots[1].copy()
            self.shots[1].update(changes)
            with self.assertRaises(ReferenceAlignmentError):
                self.lock()
            self.shots[1]=previous

    def test_encoded_recreation_comparison_and_evidence_board(self):
        lock=self.lock()
        out=compare(lock,self.candidate,board=self.dir/"board.jpg")
        self.assertEqual(out["state"],"requires_real_moving_visual_review")
        self.assertTrue(out["technical_qa_passed"])
        self.assertEqual(len(out["per_shot_diagnostics"]),2)
        self.assertEqual(len(out["shot_boundaries"]),1)
        self.assertLess(max(x["luma_mae"] for x in out["per_shot_diagnostics"]),.075)
        self.assertTrue((self.dir/"board.jpg").is_file())
        self.assertEqual(len(out["candidate_sha256"]),64)

    def test_wrong_candidate_dimensions_and_audio_rejected(self):
        lock=self.lock()
        wrong=self.dir/"wrong.mp4"
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
                        "-f","lavfi","-i","color=c=black:s=400x180:r=12:d=2",
                        "-an","-c:v","libx264","-pix_fmt","yuv420p",
                        "-y",str(wrong)],check=True)
        with self.assertRaisesRegex(ReferenceAlignmentError,"geometry"):
            compare(lock,wrong)
        silent=self.dir/"silent.mp4"
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
                        "-i",str(self.candidate),"-an","-c:v","copy",
                        "-y",str(silent)],check=True)
        with self.assertRaisesRegex(ReferenceAlignmentError,"technical QA"):
            compare(lock,silent)


if __name__=="__main__":
    unittest.main(verbosity=2)
