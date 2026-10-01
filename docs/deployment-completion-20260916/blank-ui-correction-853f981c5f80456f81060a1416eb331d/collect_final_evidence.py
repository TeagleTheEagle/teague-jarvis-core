"""Read validated TEST artifacts; write only this nonsecret evidence directory."""
import ast
import difflib
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

out = Path(__file__).resolve().parent
repo = out.parents[2]
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
save = lambda name, value: (out/name).write_text(json.dumps(value, indent=2), encoding='utf-8')
pre = read(out/'pre-change.json')
candidate = read(out/'candidate.json')
actual = read(out/'actual-client-bd29756dc43a41ef999e94198db672db.json')
new = Path(candidate['package']['package'])
old = repo.parent/'deployment-test-releases/TEST-PACKAGE-8b61892cb3a44bca8035a6412b4892c7'
result = {'candidate_manifest': digest(new/'manifest.json'), 'packages': [], 'source': [], 'diagnosis_preserved': [], 'syntax': [], 'exports': []}

for label, root in [('old', old), ('candidate', new)] + [('installed-'+str(i), Path(r).parents[1]/'releases'/candidate['manifest']) for i, r in enumerate(actual['roots'])]:
    manifest = read(root/'manifest.json')
    failures = [x['path'] for x in manifest['files'] if not (root/x['path']).is_file() or digest(root/x['path']) != x['sha256']]
    result['packages'].append({'label': label, 'path': str(root), 'manifest_sha256': digest(root/'manifest.json'), 'files': len(manifest['files']), 'mismatches': failures})

for entry in pre['tracked_file_hashes']:
    p = repo/entry['path']
    result['source'].append({'path': entry['path'], 'before': entry['sha256'], 'after': digest(p) if p.is_file() else None})
result['tracked_drift'] = [x['path'] for x in result['source'] if x['before'] != x['after']]
for entry in pre['previous_diagnostic']:
    p = Path(entry['path'])
    result['diagnosis_preserved'].append({'path': str(p), 'sha256': digest(p), 'unchanged': digest(p) == entry['sha256']})

changed = ['deployment_test/package.py', 'tests/deployment_contract/test_electron_startup.cjs', 'tests/deployment_contract/blank_ui_validation.py']
for name in changed:
    target = out/'source'/name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repo/name, target)
before = (out/'before/deployment_test/package.py').read_text()
after = (repo/'deployment_test/package.py').read_text()
(out/'source-changes.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='before/deployment_test/package.py', tofile='after/deployment_test/package.py')))
unchanged = ['stage4_client.cjs', 'tests/deployment_contract/fixtures.py', 'tests/lifecycle_stage4/fixtures.py']
result['reviewed_unchanged_sources'] = [{'path': n, 'before': digest(out/'before'/n), 'after': digest(repo/n), 'unchanged': digest(out/'before'/n) == digest(repo/n)} for n in unchanged]
result['changed_sources'] = [{'path': n, 'sha256': digest(repo/n)} for n in changed]

node = Path('C:/Users/jonny/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
for name in ['deployment_test/package.py', 'tests/deployment_contract/blank_ui_validation.py']:
    ast.parse((repo/name).read_text(), filename=name)
    result['syntax'].append({'command': 'ast.parse(path.read_text(), filename=path)', 'path': name, 'result': 'PASS', 'bytecode_written': False})
for p in [new/'app/client-launcher.cjs', new/'app/deployment-entry.cjs', repo/'stage4_client.cjs', repo/'tests/deployment_contract/test_electron_startup.cjs']:
    cmd = [str(node), '--check', str(p)]
    check = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    result['syntax'].append({'command': cmd, 'exit': check.returncode, 'stdout': check.stdout, 'stderr': check.stderr})

logs = out/'client-logs'
logs.mkdir(exist_ok=True)
for i, root in enumerate(map(Path, actual['roots'])):
    for source in root.iterdir():
        if source.is_file() and ('stderr' in source.name or source.suffix == '.png'):
            target = logs/(str(i)+'-'+source.name)
            shutil.copyfile(source, target)
            result['exports'].append({'source': str(source), 'copy': str(target.relative_to(out)), 'sha256': digest(source), 'copy_matches': digest(source) == digest(target), 'bytes': source.stat().st_size})
cleanup = repo/'docs/deployment-completion-20260916/visible-test-session-4cea89950d7d4ccf94513841834f66de.json'
shutil.copyfile(cleanup, out/'old-core-cleanup.json')
result['old_core_cleanup_sha256'] = digest(cleanup)
result['actual_checks'] = len(actual['records'])
result['actual_failures'] = sum(not x['passed'] for x in actual['records'])
result['paid_calls'] = actual['paid_calls']
result['physical_media'] = actual['physical_media']
result['production_changed_by_campaign'] = actual['production_changed']
result['runtime_payload_differences'] = candidate['differences']
save('final-validation.json', result)
print(json.dumps({k: result[k] for k in ['candidate_manifest', 'packages', 'tracked_drift', 'reviewed_unchanged_sources', 'actual_checks', 'actual_failures']}, indent=2))
assert not result['tracked_drift']
assert all(not x['mismatches'] for x in result['packages'])
assert all(x['unchanged'] for x in result['diagnosis_preserved']+result['reviewed_unchanged_sources'])
assert all(x.get('exit', 0) == 0 for x in result['syntax'])
assert result['actual_failures'] == 0
