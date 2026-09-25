import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.core.media import (
    analyze_audio,
    artifact_receipt,
    build_contact_sheet,
    compare_video,
    decode_check,
    extract_frame,
    probe_media,
    validate_master,
)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class MediaRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.video = cls.root / "sample.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=320x180:rate=12:duration=2",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=2",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(cls.video),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            capture_output=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_probe_and_decode(self):
        data = probe_media(self.video)
        self.assertEqual(data["video_streams"], 1)
        self.assertEqual(data["audio_streams"], 1)
        video = next(x for x in data["streams"] if x["codec_type"] == "video")
        self.assertEqual(video["width"], 320)
        self.assertEqual(video["height"], 180)
        self.assertAlmostEqual(video["frame_rate"], 12.0)
        self.assertTrue(decode_check(self.video)["success"])

    def test_audio_analysis(self):
        data = analyze_audio(self.video)
        self.assertIsNotNone(data["integrated_lufs"])
        self.assertIsNotNone(data["true_peak_dbfs"])
        self.assertEqual(data["silence_segment_count"], 0)

    def test_frame_and_contact_sheet(self):
        frame = extract_frame(self.video, self.root / "frame.png", time_seconds=0.75)
        sheet = build_contact_sheet(
            self.video,
            self.root / "sheet.png",
            count=6,
            columns=3,
            cell_width=160,
        )
        self.assertTrue(frame.is_file())
        self.assertTrue(sheet.is_file())
        self.assertTrue(frame.read_bytes().startswith(b"\x89PNG"))
        self.assertTrue(sheet.read_bytes().startswith(b"\x89PNG"))

    def test_compare_identical_video(self):
        result = compare_video(
            self.video,
            self.video,
            sample_fps=4,
            max_duration_seconds=2,
        )
        self.assertTrue(result["comparable"])
        self.assertAlmostEqual(result["ssim_all"], 1.0, places=6)

    def test_master_qa_and_receipt(self):
        qa = validate_master(
            self.video,
            width=320,
            height=180,
            fps=12,
            duration_seconds=2.0,
            duration_tolerance=0.1,
            audio_required=True,
            max_silence_seconds=0.5,
        )
        self.assertTrue(qa["pass"], json.dumps(qa, indent=2))

        receipt = artifact_receipt(self.video)
        self.assertEqual(len(receipt["sha256"]), 64)
        self.assertTrue(receipt["decode"]["success"])
        self.assertIsNotNone(receipt["audio"])


if __name__ == "__main__":
    unittest.main()