"""Select nonsecret campaign records; never copy TEST runtime directories wholesale."""
import difflib
import hashlib
import json
import pathlib
import re
import shutil
from datetime import datetime, timezone

OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BASE = OUT.parent
BUNDLE = OUT / 'selected-records'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put_json(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def main():
    # Regenerate only the documentary matrix. Existing syntax/runtime results stay intact.
    matrix_script = OUT / 'build_matrix.py'
    prefix = matrix_script.read_text(encoding='utf-8').split("files=['stage4_runtime.py'")[0]
    exec(compile(prefix, str(matrix_script), 'exec'), {'__file__': str(matrix_script)})
    rows = json.loads((OUT / 'requirement-to-evidence.json').read_text(encoding='utf-8'))
    selected = set()

    def add(path):
        path = pathlib.Path(path).resolve(strict=True)
        path.relative_to(ROOT)
        if path.is_symlink() or not path.is_file():
            raise ValueError('not a plain selected file')
        if path.suffix.lower() not in {'.py', '.txt', '.md', '.json', '.csv', '.log', '.cjs', '.js', '.html', '.png', '.patch', '.ps1'}:
            raise ValueError('unapproved evidence extension: ' + path.name)
        if any(part in {'.env', 'node_modules', '.venv'} for part in path.parts):
            raise ValueError('runtime or credentials excluded')
        selected.add(path)

    for name in ['CORE-COMPLETION-CHECKLIST.md', 'POST-CORE-BACKLOG.md', 'STAGE4-HUMAN-LIFECYCLE-CHECK.md',
                 'STAGE4-REMAINING-REQUIREMENTS-20260915.md', 'CANONICAL-CORE-STAGE-4.md']:
        add(ROOT / 'docs' / name)
    for directory in [OUT, BASE / 'restart-transaction-20260915', BASE / 'client-state-media-20260915']:
        candidates = directory.iterdir() if directory == OUT else directory.rglob('*')
        for path in candidates:
            if path.is_file() and path.name not in {'package-manifest.json', 'archive-verification.json', 'source-diff-manifest.json'}:
                add(path)
    for path in json.loads((OUT / 'reconciliation-summary.json').read_text())['selected_reports']:
        add(path)
    # Every file named by the requirement table resolves from lifecycle-stage4-evidence.
    for row in rows:
        for reference in row['evidence'].split('; '):
            if reference.endswith(('.json', '.log', '.md')):
                add(BASE / reference)
    add(BASE / 'response-commit-final-validation-20260915' / 'REVIEW.md')
    add(BASE / 'response-commit-final-validation-20260915' / 'validation-summary.json')

    source_hashes = json.loads((OUT / 'final-source-hashes.json').read_text())
    scoped = []
    for record in source_hashes:
        path = ROOT / record['path']
        if digest(path) != record['sha256']:
            raise ValueError('validated source changed: ' + record['path'])
        if 'node_modules' in path.parts or path.suffix in {'.exe', '.node'}:
            continue  # dependency identity is hashed, not redistributed
        add(path)
        if record['reviewed_change']:
            before_dir = BASE / ('client-state-media-20260915' if record['path'] in {
                'stage4_client.cjs', 'desktop/test/stage4-client.test.cjs'} else 'restart-transaction-20260915') / 'before'
            before = before_dir / record['path']
            prior_hash = record.get('prior')
            if prior_hash is None:
                before_manifest = json.loads((before_dir.parent / 'before-hashes.json').read_text())
                prior_hash = next(item['sha256'] for item in before_manifest if item['path'] == record['path'])
            if digest(before) != prior_hash:
                raise ValueError('before snapshot mismatch: ' + record['path'])
            patch = OUT / ('diff-' + record['path'].replace('/', '_') + '.patch')
            patch.write_text(''.join(difflib.unified_diff(
                before.read_text(encoding='utf-8').splitlines(keepends=True),
                path.read_text(encoding='utf-8').splitlines(keepends=True),
                fromfile='before/' + record['path'], tofile='after/' + record['path'])), encoding='utf-8')
            add(patch)
            scoped.append({'path': record['path'], 'before_sha256': digest(before), 'after_sha256': digest(path),
                           'patch': patch.name, 'patch_sha256': digest(patch)})
    put_json(OUT / 'source-diff-manifest.json', scoped)
    add(OUT / 'source-diff-manifest.json')

    images = ROOT / 'tests/lifecycle_stage1/evidence/TEST-STAGE4-2766e90affb54f468bcd55fdf726eefe'
    for name in ['teague-af027702-af10-4e01-8f67-abfbecd7e931.png', 'intelligence-15849043-51af-44f9-ad40-12fb8f421607.png']:
        add(images / name)
    add(ROOT / 'tests/lifecycle_stage1/evidence/TEST-STAGE4-06011e7e56fc49d28fa61d5d9d30a4ba/b0e2b029ea254b8590361ef91a7044d4.stderr.log')

    findings = []
    secret_keys = {'api_key', 'access_token', 'refresh_token', 'server_key', 'client_key', 'secret', 'password', 'credential', 'token'}
    def inspect(value, trail, path):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in secret_keys and item not in (None, '', False, 'REDACTED', '[REDACTED]'):
                    findings.append({'path': str(path.relative_to(ROOT)), 'field': trail + '.' + key})
                inspect(item, trail + '.' + key, path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                inspect(item, trail + '[' + str(index) + ']', path)
    for path in sorted(selected):
        if path.suffix == '.png':
            continue  # only the two inspected TEST screenshots above
        text = path.read_text(encoding='utf-8-sig')
        if re.search(r'sk-(?:proj-)?[A-Za-z0-9_-]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', text):
            findings.append({'path': str(path.relative_to(ROOT)), 'field': 'credential-pattern'})
        if path.suffix == '.json':
            inspect(json.loads(text), '$', path)
    if findings:
        put_json(OUT / 'package-review-findings.json', findings)
        print(json.dumps({'status': 'REVIEW_REQUIRED', 'findings': findings}))
        return 2
    entries = []
    for path in sorted(selected):
        relative = path.relative_to(ROOT)
        target = BUNDLE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        if digest(path) != digest(target):
            raise ValueError('copy hash mismatch')
        entries.append({'path': relative.as_posix(), 'bytes': path.stat().st_size, 'sha256': digest(path)})
    manifest = {'created_utc': datetime.now(timezone.utc).isoformat(), 'source_root': str(ROOT),
                'purpose': 'selected TEST campaign records, not acceptance or production deployment',
                'matrix_reference_root': 'docs/lifecycle-stage4-evidence',
                'excluded': ['credentials/private handshakes', 'databases', 'raw profiles/caches', 'runtime binaries/dependencies', 'unrelated tree'],
                'files': entries}
    put_json(OUT / 'package-manifest.json', manifest)
    print(json.dumps({'status': 'PREPARED', 'files': len(entries), 'bytes': sum(x['bytes'] for x in entries),
                      'source_files_with_scoped_diffs': len(scoped), 'manifest_sha256': digest(OUT / 'package-manifest.json')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
