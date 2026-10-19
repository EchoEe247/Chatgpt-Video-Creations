"""Tests for the optional native Earshot provider on the canonical AV timeline."""
from __future__ import annotations
import copy
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np
from src.core.native_earshot import compile_effects,write_wav


class FakeBank:
    VERSION="stub-0.3"
    def __init__(self):
        self.calls=0
    def render(self,sound_id,**kwargs):
        self.calls+=1
        audio=np.full((9600,2),.3,dtype=np.float32)
        return audio,{"seed":kwargs.get("seed",1),"onset_s":.01,"peak_s":.06,
                      "end_s":.19,"checks":{"ok":True,"warnings":[]}}


def timeline():
    return {"schema_version":1,"fps":24,"sample_rate":48000,"runtime_seconds":2.,
            "events":[{"id":"hit","at_seconds":.5,"frame":12,"sample":24000,
                       "kind":"audio_cue","label":"Impact","stem":"effects",
                       "targets":["audio"],"duration_seconds":0},
                      {"id":"hit2","at_seconds":1.,"frame":24,"sample":48000,
                       "kind":"audio_cue","label":"Second hit","stem":"effects",
                       "targets":["audio"],"duration_seconds":0}]}


class EarshotIntegrationTests(unittest.TestCase):
    def test_sample_alignment_reusable_sound_and_wav(self):
        bank=FakeBank()
        cues=[{"event_id":"hit","sound_id":"whoosh_fast/crisp","align":"peak","seed":13},
              {"event_id":"hit2","sound_id":"whoosh_fast/crisp","align":"peak","seed":13}]
        audio,receipt=compile_effects(timeline(),cues,bank=bank)
        self.assertEqual(audio.shape,(96000,2))
        self.assertEqual(receipt["cues"][0]["render_start_sample"],21120)
        self.assertEqual(bank.calls,1)
        self.assertEqual(receipt["source"],"native_earshot.forge.bank.render")
        with tempfile.TemporaryDirectory() as td:
            out=write_wav(Path(td)/"effects.wav",audio)
            with wave.open(str(out),"rb") as file:
                self.assertEqual(file.getframerate(),48000)
                self.assertEqual(file.getnframes(),96000)
                self.assertEqual(file.getnchannels(),2)

    def test_invalid_event_and_malformed_clock(self):
        bank=FakeBank()
        with self.assertRaisesRegex(ValueError,"event must exist"):
            compile_effects(timeline(),[{"event_id":"bad","sound_id":"whoosh_fast/crisp"}],bank=bank)
        changed=timeline()
        changed["events"][0]["sample"]=24200
        with self.assertRaisesRegex(ValueError,"invalid AV timeline"):
            compile_effects(changed,[{"event_id":"hit","sound_id":"whoosh_fast/crisp"}],bank=bank)
        with self.assertRaisesRegex(ValueError,"effects stem"):
            compile_effects(timeline(),[{"event_id":"hit","sound_id":"whoosh_fast/crisp",
                                       "stem":"narration"}],bank=bank)

    def test_native_earshot_when_installed(self):
        try:
            from earshot.forge import bank
        except ImportError:
            self.skipTest("native Earshot is optional in CI runtime")
        audio,receipt=compile_effects(timeline(),[
            {"event_id":"hit","sound_id":"whoosh_fast/crisp","align":"peak",
             "seed":11,"gain_db":-14}],bank=bank)
        self.assertEqual(receipt["bank_version"],bank.VERSION)
        self.assertGreater(float(np.max(np.abs(audio))),0.005)


if __name__=="__main__":
    unittest.main()
