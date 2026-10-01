import datetime, hashlib, json, pathlib, zipfile

R = pathlib.Path(__file__).parent
C = R / 'candidate'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, value):
    with (R / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2)

B = json.loads((R / 'before.json').read_text())
binding = json.loads((R / 'successor-binding.json').read_text())
S = pathlib.Path(B['predecessor'])
for row in B['files']:
    p = S / row['name']
    assert p.stat().st_size == row['bytes']
    assert p.stat().st_mtime_ns == row['mtimeNs']
    assert sha(p) == row['sha256']
for name, key in [('small-source-v3.json', 'candidateManifestSHA256'), ('witness-source-v1.json', 'diagnosticManifestSHA256')]:
    assert sha(C / name) == binding[key]
    rows = json.loads((C / name).read_text())
    assert len(rows) == 245
    for row in rows:
        p = C / row['name']
        assert p.stat().st_size == row['bytes'] and sha(p) == row['sha256']
archives = []
for values in B.values():
    if isinstance(values, list):
        for row in values:
            if isinstance(row, dict) and 'archive' in row and 'sha256' in row:
                assert sha(pathlib.Path(row['archive'])) == row['sha256']
                archives.append(row['archive'])
assert len(archives) == 2
assert json.loads((R / 'final-census.json').read_text())['status'] == 'PASS'
for p in R.glob('*.py'):
    compile(p.read_text(), str(p), 'exec')
save('final-preservation.json', dict(status='PASS', candidateFiles=245, predecessorFiles=245,
    predecessorMetadataUnchanged=True, historicalArchivesUnchanged=archives,
    pythonSyntaxFiles=sorted(p.name for p in R.glob('*.py')),
    protectedVMAccess=False, productionChange=False, liveETW=False, UAC=False,
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))

report = '''# AUTHORITY_INDEPENDENT_SESSION_SUCCESSOR_READY

Offline TEST successor only. No live ETW, UAC, medium/large validation, protected VM/configuration access, or production operation occurred.

## Isolated configuration change

Authority requested LogFileMode: `EVENT_TRACE_REAL_TIME_MODE` (0x00000100) -> `EVENT_TRACE_REAL_TIME_MODE | EVENT_TRACE_INDEPENDENT_SESSION_MODE` (0x08000100). XOR delta: 0x08000000 only.

Detailed requested LogFileMode remains 0x02000100, with the independent-session flag absent. Its source and executable are byte-identical. Authority buffers, FlushTimer, QPC, provider/keyword/level, per-processor behavior, callbacks, selector, diagnostic recording, helper handoff, telemetry and deadlines are unchanged. Checker/finalizer files and zero-loss rejection predicates are unchanged.

Only authority_trace_v3.cpp and its rebuilt authority_trace_v3.obj/J6AuthorityTraceV3.exe differ among the 245 predecessor artifacts. Before/after SHA-256 values are in successor-binding.json. Fresh source manifests and binding are added; original source and historical evidence remain unchanged.

## Validation

- `python -B offline_proof.py`: 16 tests PASS, zero failures/errors; offline-tests.log records the exact cases.
- `cmd /c build-authority.cmd`: PASS. Only the authority executable rebuilt. Existing C4456 shadowing warning retained; no new warning.
- `cmd /c syntax-proof.cmd`: PASS. Twelve SDK-backed compile-time assertions verify modes and unchanged fail-closed EventsLost return behavior; actual authority source syntax also passes.
- Python in-memory syntax compilation: PASS, no bytecode written. Exact files in python-syntax.json and final-preservation.json.
- Final preservation: all 245 candidate and 245 predecessor files verified; predecessor sizes/modification times unchanged; both historical archive hashes unchanged.
- Read-only host census: zero matching diagnostic/VirtualBox processes and zero matching trace sessions. See final-census.json.

## Integrity and limits

Candidate manifest SHA-256: 139bf0df392dae0a201baa6bcee1f6b4bb612583201b599df780c9e86d96885a

Authority executable SHA-256: c405202381a2fed890512c553cc8b631cfc2f03e4d2ef955aa8f236d02949aef

Detailed executable SHA-256: 5225e63c654a63fff05e4002475e8caae5910d4d11822a13119bf2791fc35634

This proves the requested configuration delta offline. Windows session startup, returned mode and runtime loss behavior are NOT validated here. Stage 6 remains incomplete. Historical ETW-loss cause remains UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

The preparation candidate remains on C: and must not be launched in place. A separately approved live attempt requires the existing bounded fresh D: workspace path rebind and new immutable run binding; this is not represented as already performed.

## Preservation, rollback and next step

All writes were limited to this new TEST preparation/evidence directory. To roll back, leave this successor unused and retain the predecessor; no deployment or runtime rollback is needed. No historical file was overwritten.

Archive member hashes and verification are recorded in archive-manifest.json and archive-verification.json. The canonical evidence-copy result is recorded separately after copying. Archive failure must not be represented as success.

Exact proposed one-run inputs, three UAC commands, unchanged limits, fail-closed rules and predeclared interpretations are in ONE-RUN-OWNER-REVIEW.md. OWNER REVIEW ONLY: no live run is authorized or executed by this report. STOP.
'''
with (R / 'REPORT.md').open('x', encoding='utf-8') as f:
    f.write(report)
members = []
for p in sorted(R.rglob('*')):
    if p.is_file():
        members.append(dict(name=p.relative_to(R).as_posix(), bytes=p.stat().st_size, sha256=sha(p)))
save('archive-manifest.json', members)
zpath = R / 'evidence.zip'
with zipfile.ZipFile(zpath, 'x', compression=zipfile.ZIP_DEFLATED) as z:
    for row in members:
        z.write(R / row['name'], row['name'])
with zipfile.ZipFile(zpath) as z:
    assert len(z.namelist()) == len(members)
    for row in members:
        data = z.read(row['name'])
        assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
receipt = dict(status='PASS', archive=str(zpath), sha256=sha(zpath), bytes=zpath.stat().st_size,
    verifiedMembers=len(members), manifestSHA256=sha(R / 'archive-manifest.json'))
save('archive-verification.json', receipt)
print(json.dumps(receipt, indent=2))
