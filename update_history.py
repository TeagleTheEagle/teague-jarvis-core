"""Local source history. Hashes prove file identity, never runtime correctness."""
import hashlib
import json
import threading
import time
import uuid
from pathlib import Path

LOCK = threading.RLock()


def snapshot(root):
    root = Path(root)
    files = {}
    for folder, extensions in [('', {'.py', '.txt', '.json'}), ('static', {'.js', '.css', '.html', '.svg', '.png', '.jpg', '.webp'}), ('desktop', {'.cjs', '.js', '.html', '.css'})]:
        for p in sorted((root / folder).glob('*')):
            if not p.is_file() or p.is_symlink() or p.suffix not in extensions or p.name.startswith('test_'):
                continue
            if not folder and p.suffix != '.py' and p.name not in ('requirements.txt', 'personality.txt', 'release-notes.json'):
                continue
            files[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    revision = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16]
    return {'revision': revision, 'files': files}


def observe(root, data_root):
    current = snapshot(root)
    folder = Path(data_root) / 'update-history'
    with LOCK:
        folder.mkdir(parents=True, exist_ok=True)
        records = []
        for p in folder.glob('*.json'):
            try:
                records.append(json.loads(p.read_text(encoding='utf-8')))
            except (OSError, ValueError):
                continue
        previous = max(records, key=lambda r: r['observed_at'], default=None)
        if previous is None or previous['revision'] != current['revision']:
            old = previous['files'] if previous else {}
            changed = sorted(k for k in set(old) | set(current['files']) if old.get(k) != current['files'].get(k))
            record = {**current, 'observed_at': time.time(), 'changed_files': changed,
                      'kind': 'source_change' if previous else 'initial_baseline',
                      'verification': 'Files recorded; no tests or runtime success inferred.'}
            if previous and record['observed_at'] <= previous['observed_at']:
                import math
                record['observed_at'] = math.nextafter(previous['observed_at'], float('inf'))
            target = folder / (str(time.time_ns()) + '-' + uuid.uuid4().hex + '.json')
            with target.open('x', encoding='utf-8') as f:
                json.dump(record, f, indent=2)
            records.append(record)
    return current, sorted(records, key=lambda r: r['observed_at'], reverse=True)[:100]


def history(root, data_root, backend_revision):
    current, records = observe(root, data_root)
    notes_path = Path(root) / 'release-notes.json'
    try:
        notes = json.loads(notes_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        notes = []
    return {'source_revision': current['revision'], 'backend_start_revision': backend_revision,
            'frontend_files': {k:v for k,v in current['files'].items() if k in ('static/app.js','static/assistant-controls.js')},
            'source_changed_since_backend_start': current['revision'] != backend_revision,
            'limitations': 'Backend-start revision is not proof of which frontend scripts are loaded. Automatic entries record observed file changes, not authorship, tests, or every edit between observations.',
            'releases': notes, 'observations': records}
