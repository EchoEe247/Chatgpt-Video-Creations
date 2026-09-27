"""Local, renderer-independent shot iteration for a supervising ChatGPT session.

This module gathers evidence. A model inspects it and records its own judgment;
no image-quality score is invented by the runner.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import signal
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from src.core.media import sha256_file, validate_master

REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_source(spec_path, source):
    value = str(source).replace('{repo}', str(REPO_ROOT))
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = Path(spec_path).parent / candidate
    return candidate.resolve()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def load_spec(path):
    path = Path(path).resolve()
    spec = json.loads(path.read_text())
    if spec.get('schema_version') != 1:
        raise ValueError('schema_version must be 1')
    ids = set()
    for shot in spec['shots']:
        sid = shot['id']
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', sid) or sid in ids:
            raise ValueError('shot ids must be unique safe names')
        ids.add(sid)
        for name in ('fps', 'duration_seconds', 'width', 'height'):
            value = shot[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be finite and positive')
        if any(not isinstance(shot[n], int) or shot[n] % 2 for n in ('width', 'height')):
            raise ValueError('width and height must be even integers')
        count = shot['fps'] * shot['duration_seconds']
        if abs(count - round(count)) > 1e-6 or count < 2:
            raise ValueError('duration must contain a whole number of at least two frames')
        offset = shot.get('source_offset_seconds', 0)
        if not math.isfinite(offset) or offset < 0:
            raise ValueError('source_offset_seconds must be finite and nonnegative')
        if not shot.get('intent') or not shot.get('criteria') or len(set(shot['criteria'])) != len(shot['criteria']):
            raise ValueError('each shot needs intent and unique visual review criteria')
        modes = shot.get('visual_modes')
        if modes is not None:
            if not isinstance(modes, list) or not modes:
                raise ValueError('visual_modes must be a non-empty ordered list')
            mode_ids = set()
            for mode in modes:
                mid = mode.get('id')
                if not isinstance(mid, str) or not re.fullmatch(r'[a-zA-Z0-9_-]+', mid) or mid in mode_ids:
                    raise ValueError('visual mode ids must be unique safe names')
                mode_ids.add(mid)
                if not mode.get('sources') or not isinstance(mode.get('renderer'), list):
                    raise ValueError(f'visual mode {mid} needs sources and renderer argv')
                if '{request}' not in mode['renderer']:
                    raise ValueError(f'visual mode {mid} renderer must consume an exact {{request}} argv token')
        else:
            if not shot.get('sources') or not isinstance(shot.get('renderer'), list):
                raise ValueError('sources and renderer argv are required')
            if '{request}' not in shot['renderer']:
                raise ValueError('renderer must consume an exact {request} argv token')
            for source in shot['sources']:
                if not resolve_source(path, source).is_file():
                    raise ValueError(f'missing source: {source}')
    if not ids:
        raise ValueError('at least one shot is required')
    return path, spec


def resolve_visual_mode(path, shot):
    """Resolve the highest-priority locally usable visual source/renderer mode.

    visual_modes is an ordered degradation ladder. A mode is usable only when
    every declared source is already present locally. This lets a workflow prefer
    fresh generated art when available, then fall back to cached art or a local
    renderer without blocking the shot runner.
    """
    modes = shot.get('visual_modes')
    if not modes:
        return {'id': 'default', 'sources': shot['sources'], 'renderer': shot['renderer']}
    missing_by_mode = {}
    for mode in modes:
        missing = [source for source in mode['sources'] if not resolve_source(path, source).is_file()]
        if not missing:
            return {'id': mode['id'], 'sources': list(mode['sources']), 'renderer': list(mode['renderer'])}
        missing_by_mode[mode['id']] = missing
    details = '; '.join(f"{mid}: {', '.join(paths)}" for mid, paths in missing_by_mode.items())
    raise ValueError(f'no visual mode is currently available; missing sources by mode: {details}')


def context(path, sid):
    path, spec = load_spec(path)
    shot = next((s for s in spec['shots'] if s['id'] == sid), None)
    if shot is None:
        raise ValueError(f'unknown shot {sid}')
    mode = resolve_visual_mode(path, shot)
    shot = {**shot, 'sources': mode['sources'], 'renderer': mode['renderer'], 'selected_visual_mode': mode['id']}
    sources = [(str(resolve_source(path, p)), sha256_file(resolve_source(path, p))) for p in shot['sources']]
    # Runner revisions also invalidate evidence/cache. Adapter code belongs in sources.
    fingerprint = hashlib.sha256(json.dumps({'shot': shot, 'sources': sources,
        'runner': sha256_file(__file__)}, sort_keys=True).encode()).hexdigest()
    root = (path.parent / spec.get('work_dir', 'shot-work')).resolve()
    out = root / sid / fingerprint
    return path, spec, shot, fingerprint, out


def expected_frames(shot, stage):
    count = round(shot['fps'] * shot['duration_seconds'])
    if stage == 'preview':
        points = [0, count // 4, count // 2, 3 * count // 4, count - 1]
        points += [min(count - 1, max(0, round(t * shot['fps']))) for t in shot.get('review_seconds', [])]
        return sorted(set(points))
    return list(range(count))


def criteria_for(shot, stage):
    return list(dict.fromkeys(shot['criteria'] + (shot.get('motion_criteria', []) if stage == 'motion' else [])))


def valid_frame(path, record, width, height):
    if not record or not path.is_file() or sha256_file(path) != record.get('sha256'):
        return False
    try:
        from PIL import Image
        with Image.open(path) as img:
            size = img.size
            img.verify()
        return size == (width, height)
    except (OSError, ValueError):
        return False


@contextmanager
def device_lock(root):
    # One expensive render at a time, including independent shots / resumed sessions.
    import fcntl
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.render.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('another shot render is already running in this workspace') from exc
        yield


def execute(argv, cwd, log, timeout):
    with log.open('w') as stream:
        process = subprocess.Popen(argv, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise ValueError(f'render budget exhausted; completed frames preserved; see {log}')
    if rc:
        raise ValueError(f'renderer exited {rc}; see {log}')


def verify_bundle(path, stage):
    manifest = path / stage / 'evidence.json'
    if not manifest.is_file():
        raise ValueError(f'{stage} evidence has not been built')
    data = json.loads(manifest.read_text())
    for file, digest in data['files'].items():
        target = path / stage / file
        if not target.is_file() or sha256_file(target) != digest:
            raise ValueError(f'{stage} evidence changed or is missing: {file}')
    return data


def review_valid(out, stage):
    try:
        evidence = verify_bundle(out, stage)
        review = json.loads((out / stage / 'review.json').read_text())
        return review['evidence_sha256'] == sha256_file(out / stage / 'evidence.json') and review['pass'] is True
    except (OSError, KeyError, ValueError):
        return False


def render(path, sid, stage, timeout=300):
    path, spec, shot, fingerprint, out = context(path, sid)
    if stage not in ('preview', 'motion'):
        raise ValueError('stage must be preview or motion')
    if stage == 'motion' and not review_valid(out, 'preview'):
        raise ValueError('ChatGPT must inspect and review this version of the preview first')
    root = (path.parent / spec.get('work_dir', 'shot-work')).resolve()
    with device_lock(root):
        stage_dir = out / stage
        frame_dir = out / 'frames'
        stage_dir.mkdir(parents=True, exist_ok=True)
        frame_dir.mkdir(parents=True, exist_ok=True)
        cache_path = out / 'frames.json'
        cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
        frames = expected_frames(shot, stage)
        missing = [i for i in frames if not valid_frame(frame_dir / f'{i:06d}.png', cache.get(str(i)), shot['width'], shot['height'])]
        started = time.monotonic()
        request = {'schema_version': 1, 'shot': shot, 'frames': missing,
            'source_paths': [str(resolve_source(path, p)) for p in shot['sources']],
            'output_dir': str(frame_dir), 'spec_dir': str(path.parent), 'fingerprint': fingerprint,
            'selected_visual_mode': shot.get('selected_visual_mode', 'default')}
        write_json(stage_dir / 'request.json', request)
        error = None
        if missing:
            try:
                # Bound renderer lifetime on small devices: GL/renderer state can
                # accumulate even when the scene itself fits comfortably in RAM.
                batch_size = int(spec.get('batch_size', 8))
                if not 1 <= batch_size <= 32:
                    raise ValueError('batch_size must be between 1 and 32')
                attempt = time.time_ns()
                for offset in range(0, len(missing), batch_size):
                    remaining = timeout - (time.monotonic() - started)
                    if remaining <= 0:
                        raise ValueError('render budget exhausted; completed frames preserved')
                    batch = missing[offset:offset + batch_size]
                    batch_request = stage_dir / f'request-{attempt}-{offset}.json'
                    write_json(batch_request, {**request, 'frames': batch})
                    argv = [
                        str(batch_request) if a == '{request}'
                        else a.replace('{repo}', str(REPO_ROOT))
                        for a in shot['renderer']
                    ]
                    execute(argv, path.parent, stage_dir / f'render-{attempt}-{offset}.log', remaining)
                    # Some proot launchers return zero after a Blender signal 11.
                    # Verify artifacts rather than trusting the wrapper's status.
                    for i in batch:
                        f = frame_dir / f'{i:06d}.png'
                        record = {'sha256': sha256_file(f)} if f.is_file() else None
                        if not valid_frame(f, record, shot['width'], shot['height']):
                            raise ValueError(f'renderer omitted or corrupted frame {i}; completed frames preserved')
                        cache[str(i)] = record
                    write_json(cache_path, cache)
            except ValueError as exc:
                error = exc
            finally:
                # Valid frames survive timeout/crash; corrupt/incomplete files never enter cache.
                for i in missing:
                    f = frame_dir / f'{i:06d}.png'
                    if f.is_file():
                        record = {'sha256': sha256_file(f)}
                        if valid_frame(f, record, shot['width'], shot['height']):
                            cache[str(i)] = record
                write_json(cache_path, cache)
        if error:
            raise error
        if any(not valid_frame(frame_dir / f'{i:06d}.png', cache.get(str(i)), shot['width'], shot['height']) for i in frames):
            raise ValueError('renderer did not produce every requested frame at the required dimensions')
        if context(path, sid)[3] != fingerprint:
            raise ValueError('sources changed during render; rerun for the new version')
        from PIL import Image, ImageDraw
        cell_w = min(320, shot['width'])
        cell_h = round(cell_w * shot['height'] / shot['width'])
        sample = expected_frames(shot, 'preview')
        sheet = Image.new('RGB', (cell_w * min(3, len(sample)), (cell_h + 24) * math.ceil(len(sample) / 3)), '#10151d')
        draw = ImageDraw.Draw(sheet)
        for n, i in enumerate(sample):
            x, y = (n % 3) * cell_w, (n // 3) * (cell_h + 24)
            with Image.open(frame_dir / f'{i:06d}.png') as img:
                sheet.paste(img.resize((cell_w, cell_h)), (x, y))
            draw.text((x + 4, y + cell_h + 4), f'{i / shot["fps"]:.3f}s | frame {i}', fill='white')
        sheet.save(stage_dir / 'contact-sheet.png')
        files = {'contact-sheet.png': sha256_file(stage_dir / 'contact-sheet.png')}
        for i in frames:
            files[f'../frames/{i:06d}.png'] = cache[str(i)]['sha256']
        if stage == 'motion':
            video = stage_dir / 'candidate.mp4'
            execute(['ffmpeg', '-y', '-v', 'error', '-threads', '2', '-framerate', str(shot['fps']),
                '-i', str(frame_dir / '%06d.png'), '-frames:v', str(len(frames)), '-c:v', 'libx264',
                '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video)],
                path.parent, stage_dir / 'encode.log', 120)
            qa = validate_master(video, width=shot['width'], height=shot['height'], fps=shot['fps'],
                duration_seconds=shot['duration_seconds'], audio_required=False, video_codec='h264', pixel_format='yuv420p')
            write_json(stage_dir / 'technical-qa.json', qa)
            if not qa['pass']:
                raise ValueError('motion technical QA failed')
            files.update({n: sha256_file(stage_dir / n) for n in ('candidate.mp4', 'technical-qa.json')})
        elapsed = time.monotonic() - started
        evidence = {'fingerprint': fingerprint, 'stage': stage, 'intent': shot['intent'], 'criteria': criteria_for(shot, stage),
            'files': files, 'frames': frames, 'native_fps': shot['fps'], 'interpolation': False,
            'selected_visual_mode': shot.get('selected_visual_mode', 'default'),
            'rendered_frames': len(missing), 'reused_frames': len(frames) - len(missing), 'elapsed_seconds': round(elapsed, 3),
            'estimated_full_render_seconds': round(elapsed / len(missing) * round(shot['fps'] * shot['duration_seconds']), 1) if missing else None,
            'estimate_note': 'Measured preview throughput; full render timing can differ. Not a quality rating.'}
        prior_path = stage_dir / 'evidence.json'
        prior = json.loads(prior_path.read_text()) if prior_path.exists() else {}
        # A no-change cache check must not invalidate the previous visual judgment.
        if prior.get('files') != evidence['files'] or prior.get('fingerprint') != fingerprint:
            write_json(prior_path, evidence)
        write_json(stage_dir / 'last-run.json', evidence)
        template = {'observations': {c: {'pass': False, 'notes': '', 'evidence': []} for c in criteria_for(shot, stage)},
            'defects': [], 'next_change': ''}
        if not (stage_dir / 'review-template.json').exists():
            write_json(stage_dir / 'review-template.json', template)
        return {'output': str(stage_dir), **{k: v for k, v in evidence.items() if k != 'files'}}


def record_review(path, sid, stage, review_path):
    _, _, shot, fingerprint, out = context(path, sid)
    evidence = verify_bundle(out, stage)
    data = json.loads(Path(review_path).read_text())
    observations = data.get('observations', {})
    if set(observations) != set(criteria_for(shot, stage)):
        raise ValueError('review must cover every criterion exactly')
    for criterion, obs in observations.items():
        if not isinstance(obs.get('pass'), bool) or not str(obs.get('notes', '')).strip() or not obs.get('evidence'):
            raise ValueError(f'{criterion}: explicit judgment, notes and inspected evidence required')
        if any(p not in evidence['files'] for p in obs['evidence']):
            raise ValueError(f'{criterion}: evidence must reference this version')
    if (any(not o['pass'] for o in observations.values()) or data.get('defects')) and not data.get('next_change', '').strip():
        raise ValueError('failed review needs a concrete next_change')
    passed = all(o['pass'] for o in observations.values()) and not data.get('defects')
    result = {**data, 'pass': passed, 'fingerprint': fingerprint, 'stage': stage,
        'reviewer': 'assistant', 'evidence_sha256': sha256_file(out / stage / 'evidence.json')}
    review_file = out / stage / 'review.json'
    if review_file.exists():
        archive = out / stage / 'review-history'
        archive.mkdir(exist_ok=True)
        review_file.rename(archive / f'{time.time_ns()}.json')
    write_json(review_file, result)
    return result


def status(path):
    path, spec = load_spec(path)
    result = []
    for shot in spec['shots']:
        _, _, _, fingerprint, out = context(path, shot['id'])
        preview = review_valid(out, 'preview')
        motion = review_valid(out, 'motion')
        stage = 'motion' if preview else 'preview'
        try:
            verify_bundle(out, stage)
            action = f'inspect_{stage}'
        except (OSError, ValueError):
            action = f'render_{stage}'
        review_path = out / stage / 'review.json'
        review = json.loads(review_path.read_text()) if review_path.exists() else {}
        if review.get('pass') is False:
            action = 'repair_source'
        result.append({'shot': shot['id'], 'fingerprint': fingerprint, 'output': str(out),
            'next_action': 'productionctl_handoff' if motion else action,
            'next_change': review.get('next_change'), 'defects': review.get('defects', [])})
    return result
