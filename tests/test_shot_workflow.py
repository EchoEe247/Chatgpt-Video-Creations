import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from src.core.shot_workflow import context, load_spec, record_review, render, status, write_json


class ShotWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.adapter = self.root / 'adapter.py'
        self.adapter.write_text('''import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
r=json.loads(Path(sys.argv[1]).read_text())
for i in r['frames']:
 im=Image.new('RGB',(64,48),'#26324a')
 ImageDraw.Draw(im).rectangle((i*3,12,i*3+10,30),fill='orange')
 im.save(Path(r['output_dir'])/f'{i:06d}.png')
''')
        self.spec = self.root / 'shots.json'
        self.data = {'schema_version': 1, 'shots': [{'id': 'test', 'sources': ['adapter.py'],
            'renderer': [sys.executable, str(self.adapter), '{request}'], 'width': 64, 'height': 48,
            'fps': 24, 'duration_seconds': .5, 'intent': 'moving rectangle', 'criteria': ['framing', 'motion']}]}
        write_json(self.spec, self.data)

    def review(self, stage, passed=True):
        out = context(self.spec, 'test')[4]
        evidence = 'candidate.mp4' if stage == 'motion' else 'contact-sheet.png'
        doc = {'observations': {c: {'pass': passed, 'notes': 'test fixture judgment',
            'evidence': [evidence]} for c in ['framing', 'motion']},
            'defects': [] if passed else ['cropped subject'], 'next_change': '' if passed else 'widen camera'}
        p = self.root / 'review.json'
        write_json(p, doc)
        return record_review(self.spec, 'test', stage, p)

    def test_full_local_flow_and_frame_reuse(self):
        first = render(self.spec, 'test', 'preview')
        self.assertEqual(first['rendered_frames'], 5)
        self.review('preview')
        motion = render(self.spec, 'test', 'motion')
        self.assertEqual(motion['reused_frames'], 5)
        self.assertEqual(motion['rendered_frames'], 7)
        self.assertFalse(motion['interpolation'])
        self.review('motion')
        self.assertEqual(status(self.spec)[0]['next_action'], 'productionctl_handoff')
        # Corrupt the exact inspected video: prior review no longer authorizes handoff.
        (Path(motion['output']) / 'candidate.mp4').write_bytes(b'corrupt')
        self.assertNotEqual(status(self.spec)[0]['next_action'], 'productionctl_handoff')

    def test_source_change_invalidates_review_and_cache(self):
        render(self.spec, 'test', 'preview')
        self.review('preview')
        before = context(self.spec, 'test')[3]
        self.adapter.write_text(self.adapter.read_text() + '\n# changed renderer\n')
        self.assertNotEqual(before, context(self.spec, 'test')[3])
        self.assertEqual(status(self.spec)[0]['next_action'], 'render_preview')
        with self.assertRaisesRegex(ValueError, 'inspect and review'):
            render(self.spec, 'test', 'motion')

    def test_failed_preview_keeps_specific_repair(self):
        render(self.spec, 'test', 'preview')
        self.review('preview', False)
        self.assertEqual(status(self.spec)[0]['next_change'], 'widen camera')
        self.assertEqual(status(self.spec)[0]['next_action'], 'repair_source')
        with self.assertRaises(ValueError):
            render(self.spec, 'test', 'motion')

    def test_corrupt_cached_frame_is_rerendered(self):
        first = render(self.spec, 'test', 'preview')
        frame = Path(first['output']).parent / 'frames/000000.png'
        frame.write_bytes(b'bad PNG')
        second = render(self.spec, 'test', 'preview')
        self.assertEqual(second['rendered_frames'], 1)
        with Image.open(frame) as image:
            self.assertEqual(image.size, (64, 48))

    def test_review_rejects_foreign_evidence(self):
        render(self.spec, 'test', 'preview')
        doc = {'observations': {c: {'pass': True, 'notes': 'yes', 'evidence': ['other.png']} for c in ['framing', 'motion']}}
        p = self.root / 'bad-review.json'
        write_json(p, doc)
        with self.assertRaisesRegex(ValueError, 'this version'):
            record_review(self.spec, 'test', 'preview', p)

    def test_partial_failed_job_resumes_completed_frames(self):
        self.adapter.write_text(self.adapter.read_text() + "\nif len(r['frames'])>1: sys.exit(3)\n")
        with self.assertRaisesRegex(ValueError, 'exited 3'):
            render(self.spec, 'test', 'preview')
        result = render(self.spec, 'test', 'preview')
        self.assertEqual(result['rendered_frames'], 0)
        self.assertEqual(result['reused_frames'], 5)

    def test_invalid_timing_rejected(self):
        self.data['shots'][0]['fps'] = float('nan')
        self.spec.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, 'finite'):
            load_spec(self.spec)

    def test_motion_criteria_are_not_cleared_by_stills(self):
        self.data['shots'][0]['motion_criteria'] = ['cadence']
        write_json(self.spec, self.data)
        render(self.spec, 'test', 'preview')
        self.review('preview')
        render(self.spec, 'test', 'motion')
        with self.assertRaisesRegex(ValueError, 'every criterion'):
            self.review('motion')

    def test_no_change_preview_preserves_prior_review(self):
        render(self.spec, 'test', 'preview')
        self.review('preview')
        out = context(self.spec, 'test')[4]
        before = (out / 'preview/evidence.json').read_bytes()
        result = render(self.spec, 'test', 'preview')
        self.assertEqual(result['rendered_frames'], 0)
        self.assertEqual(before, (out / 'preview/evidence.json').read_bytes())
        self.assertEqual(status(self.spec)[0]['next_action'], 'render_motion')

    def test_zero_exit_with_missing_frames_is_not_success(self):
        self.adapter.write_text(self.adapter.read_text().replace("r['frames']:", "r['frames'][:1]:"))
        with self.assertRaisesRegex(ValueError, 'omitted or corrupted'):
            render(self.spec, 'test', 'preview')
        out = context(self.spec, 'test')[4]
        self.assertFalse((out / 'preview/evidence.json').exists())
        self.assertEqual(len(json.loads((out / 'frames.json').read_text())), 1)

    def test_renderer_lifetime_is_bounded_by_batches(self):
        self.adapter.write_text(self.adapter.read_text().replace("for i in r['frames']:",
            "assert len(r['frames']) <= 2\nfor i in r['frames']:"))
        self.data['batch_size'] = 2
        write_json(self.spec, self.data)
        render(self.spec, 'test', 'preview')
        self.review('preview')
        result = render(self.spec, 'test', 'motion')
        self.assertEqual(result['rendered_frames'], 7)

    def test_visual_mode_falls_back_then_promotes_when_primary_arrives(self):
        generated = self.root / 'generated-keyframe.png'
        fallback = self.root / 'cached-keyframe.png'
        fallback.write_bytes(b'cached')
        shot = self.data['shots'][0]
        shot.pop('sources')
        shot.pop('renderer')
        shot['visual_modes'] = [
            {'id': 'generated', 'sources': ['generated-keyframe.png', 'adapter.py'],
             'renderer': [sys.executable, str(self.adapter), '{request}']},
            {'id': 'cached', 'sources': ['cached-keyframe.png', 'adapter.py'],
             'renderer': [sys.executable, str(self.adapter), '{request}']},
            {'id': 'local-blockout', 'sources': ['adapter.py'],
             'renderer': [sys.executable, str(self.adapter), '{request}']},
        ]
        write_json(self.spec, self.data)

        _, _, effective, before, _ = context(self.spec, 'test')
        self.assertEqual(effective['selected_visual_mode'], 'cached')
        first = render(self.spec, 'test', 'preview')
        self.assertEqual(first['selected_visual_mode'], 'cached')

        generated.write_bytes(b'generated')
        _, _, effective, after, _ = context(self.spec, 'test')
        self.assertEqual(effective['selected_visual_mode'], 'generated')
        self.assertNotEqual(before, after)

    def test_visual_mode_uses_local_blockout_when_art_is_unavailable(self):
        shot = self.data['shots'][0]
        shot.pop('sources')
        shot.pop('renderer')
        shot['visual_modes'] = [
            {'id': 'generated', 'sources': ['missing-generated.png', 'adapter.py'],
             'renderer': [sys.executable, str(self.adapter), '{request}']},
            {'id': 'cached', 'sources': ['missing-cache.png', 'adapter.py'],
             'renderer': [sys.executable, str(self.adapter), '{request}']},
            {'id': 'local-blockout', 'sources': ['adapter.py'],
             'renderer': [sys.executable, str(self.adapter), '{request}']},
        ]
        write_json(self.spec, self.data)
        _, _, effective, _, _ = context(self.spec, 'test')
        self.assertEqual(effective['selected_visual_mode'], 'local-blockout')


if __name__ == '__main__':
    unittest.main()
