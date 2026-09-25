import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.core.media import probe_media

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class AssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.scene = cls.root / "scene.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=320x180:rate=12:duration=1",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(cls.scene),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            capture_output=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_explicit_manifest_ignores_stale_mp4s(self):
        work = self.root / "explicit"
        work.mkdir(exist_ok=True)
        scene1 = work / "scene-01.mp4"
        scene2 = work / "scene-02.mp4"
        stale = work / "stale-master.mp4"
        shutil.copy2(self.scene, scene1)
        shutil.copy2(self.scene, scene2)
        shutil.copy2(self.scene, stale)

        manifest = work / "assembly.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "scenes": [
                        {"id": "scene-01", "path": "scene-01.mp4", "expected_duration_seconds": 1.0},
                        {"id": "scene-02", "path": "scene-02.mp4", "expected_duration_seconds": 1.0},
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        output = work / "master.mp4"
        proc = subprocess.run(
            ["python", "scripts/assemble-scenes.py", str(manifest), str(output)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        info = probe_media(output)
        self.assertAlmostEqual(float(info["duration_seconds"]), 2.0, delta=0.2)

    def test_output_cannot_be_an_input(self):
        work = self.root / "collision"
        work.mkdir(exist_ok=True)
        scene = work / "scene.mp4"
        shutil.copy2(self.scene, scene)
        manifest = work / "assembly.json"
        manifest.write_text(
            json.dumps({"schema_version": 1, "scenes": [{"id": "scene-01", "path": "scene.mp4"}]}) + "\n",
            encoding="utf-8",
        )
        proc = subprocess.run(
            ["python", "scripts/assemble-scenes.py", str(manifest), str(scene)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("output path must not be one of the scene inputs", proc.stdout)


if __name__ == "__main__":
    unittest.main()
