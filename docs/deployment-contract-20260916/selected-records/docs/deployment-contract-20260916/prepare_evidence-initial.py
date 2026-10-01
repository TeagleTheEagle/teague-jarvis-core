"""Prepare an explicit, nonsecret documentation archive; never run a Core."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    assert not path.exists(), f'Preserve existing evidence: {path.name}'
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')

accepted = load(ROOT/'docs/lifecycle-stage5-evidence/source-final.json')
observed = load(HERE/'inspected-source.json')
rechecked = [dict(path=row['path'], expected=row['sha256'], sha256=sha(ROOT/row['path']))
             for row in accepted]
inspected = [dict(path=row['path'], expected=row['sha256'], sha256=sha(ROOT/row['path']))
             for row in observed]
assert len(rechecked) == 31 and all(x['expected'] == x['sha256'] for x in rechecked)
assert len(inspected) == 18 and all(x['expected'] == x['sha256'] for x in inspected)
checks = load(HERE/'preflight-results.json')
assert len(checks) == 16 and all(x['passed'] for x in checks)
syntax = []
for name in ('preflight.py', 'prepare_evidence.py'):
    compile((HERE/name).read_text(encoding='utf-8'), name, 'exec')
    syntax.append(dict(path=name, result='PASS', operation='compile source in memory; no bytecode file'))
write(HERE/'final-reconciliation.json', dict(
    timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    accepted_source=rechecked, inspected_source=inspected, syntax=syntax,
    accepted_paths=31, inspected_paths=18, all_matched=True,
    stage4='CLOSED - preserved', stage5='isolated PASS - preserved',
    deployment='REVIEW REQUIRED; runtime relocation/enrollment not validated',
    runtime_regressions_rerun=False, cores_launched=0, production_databases_opened=0,
    production_changed=False, acceptance_commit_created=False))

relative = 'docs/deployment-contract-20260916/'
names = ['REVIEW.md', 'preflight.py', 'prepare_evidence.py', 'Copy-SelectedEvidence.ps1',
         'ARCHIVE-NOTES.md', 'summary.json', 'preflight-results.json',
         'accepted-source-verification.json', 'inspected-source.json', 'dependencies.json',
         'final-reconciliation.json']
paths = [relative+name for name in names] + [
    'docs/CORE-COMPLETION-CHECKLIST.md',
    'docs/lifecycle-stage5-evidence/REVIEW.md',
    'docs/lifecycle-stage5-evidence/source-final.json',
    'docs/lifecycle-stage5-evidence/requirement-to-evidence.json',
    'docs/lifecycle-stage4-evidence/stage4-acceptance-20260916/REVIEW.md',
    'docs/lifecycle-stage4-evidence/stage4-acceptance-20260916/requirement-to-evidence.json',
    'docs/lifecycle-stage4-evidence/human-lifecycle-6738c043c1194d60820000d6a741a479.json',
    'docs/lifecycle-stage4-evidence/completion-campaign-20260915/cutover-rehearsal-2d3eb60e240c4ca6949b7819274132eb.json',
]
bundle = HERE/'selected-records'
assert not bundle.exists(), 'Preserve existing selected records'
prepared = []
for relative_path in paths:
    source = ROOT/relative_path
    assert source.is_file() and source.suffix in ('.md', '.json', '.py', '.ps1')
    text = source.read_text(encoding='utf-8-sig')
    assert not re.search(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}', text), 'Potential secret; stop'
    assert '-----BEGIN PRIVATE KEY-----' not in text, 'Potential secret; stop'
    prepared.append((relative_path, source, sha(source)))
files = []
for relative_path, source, expected in prepared:
    target = bundle/relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert sha(target) == expected
    files.append(dict(path=relative_path, sha256=expected, bytes=target.stat().st_size))
write(HERE/'manifest.json', dict(
    purpose='Selected nonsecret deployment contract/preflight evidence, not a runnable release',
    timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), files=files,
    exclusions=['runtime binaries', 'production data', 'credentials', 'private TEST configuration',
                'profiles', 'environment files', 'unrelated working-tree files'],
    historical_evidence_unchanged=True))
print(json.dumps(dict(files=len(files), frozen_paths=31, inspected_paths=18,
                      all_hashes_match=True, deployment_validated=False)))
