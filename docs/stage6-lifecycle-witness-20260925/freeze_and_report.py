from pathlib import Path
import json,hashlib,zipfile,difflib
R=Path(__file__).parent;C=R/'candidate'
S=Path(r'D:\JARVIS-STAGE6-LIVE\ea85ed4b4ef14769acbe0b5e750aaed2\code')
P=R.parent/'stage6-small-live-20260925'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,indent=2,sort_keys=True)
before=load(R/'before.json')
for x in before:
    p=Path(x['path']);assert (p.stat().st_size,p.stat().st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
receipt=load(P/'archive-receipt.json');zp=Path(receipt['archive']);assert sha(zp)==receipt['sha256']
manifest=load(P/'archive-manifest.json')
with zipfile.ZipFile(zp) as z:
    assert len(z.namelist())==112 and z.testzip() is None
    for x in manifest:
        assert hashlib.sha256(z.read(x['member'])).hexdigest()==x['sha256']
        assert sha(Path(x['path']))==x['sha256']
    assert z.read('archive-manifest.json')==(P/'archive-manifest.json').read_bytes()
changes=[];patch=[];old=load(R/'predecessor-manifest.json');oldnames={x['name'] for x in old}
for x in old:
    p=C/x['name'];h=sha(p)
    if h!=x['sha256']:
        changes.append(dict(name=x['name'],beforeSHA256=x['sha256'],afterSHA256=h))
        if p.suffix=='.cpp':patch.extend(difflib.unified_diff((S/x['name']).read_text().splitlines(True),p.read_text().splitlines(True),fromfile='predecessor/'+x['name'],tofile='successor/'+x['name']))
assert {x['name'] for x in changes}=={'authority_trace_v3.cpp','startup_trace.cpp','authority_trace_v3.obj','J6AuthorityTraceV3.exe','J6StartupTrace.exe'}
(R/'integration.diff').write_text(''.join(patch))
rows=[]
for p in sorted(C.rglob('*')):
    if p.is_file():rows.append(dict(name=str(p.relative_to(C)),bytes=p.stat().st_size,sha256=sha(p)))
write(C/'witness-source-v1.json',rows)
# Existing manifest format is preserved; neither manifest lists itself/the other.
write(C/'small-source-v3.json',rows)
syntax=[]
for p in [C/'analyze_lifecycle_witness_v1.py',C/'preserve_lifecycle_witness_v1.py',R/'integrate.py',R/'prepare_offline_tests.py',R/'test_witness.py',Path(__file__)]:
    compile(p.read_text(),str(p),'exec');syntax.append(str(p))
write(R/'final-syntax-result.json',dict(status='PASS',files=syntax,method='compile(source, absolute_path, exec); no bytecode'))
write(R/'after.json',dict(changedExisting=changes,addedCandidate=[x for x in rows if x['name'] not in oldnames],candidateManifestSHA256=sha(C/'witness-source-v1.json'),candidateFiles=len(rows)))
write(R/'preservation-result.json',dict(status='PASS',predecessorFilesVerified=len(before),latestArchiveMembers=112,latestArchiveSHA256=sha(zp),historicalEvidenceChanged=False,frozenCheckerChanged=False,finalizerChanged=False,preservationPolicyChanged=False,helperHandoffChanged=False,existingTelemetryChanged=False,protectedVMAccess=False,productionChange=False))
native=load(R/'callback-replay-sibling.json')
write(R/'validation-summary.json',dict(status='LIFECYCLE_WITNESS_IMPLEMENTED_AND_TESTED',pythonTests=45,nativeAssertions=native['checks'],authorityBuild='PASS',detailedBuild='PASS',authorityExport='PASS',detailedExport='PASS',liveValidation=False,UAC=False,candidateManifestSHA256=sha(C/'witness-source-v1.json'),historicalCause='UNCONFIRMED'))
hash_lines='\n'.join('- `'+x['name']+'`: before `'+x['beforeSHA256']+'`; after `'+x['afterSHA256']+'`.' for x in changes)
text=f'''# LIFECYCLE_WITNESS_IMPLEMENTED_AND_TESTED

TEST-only offline successor: `{C}`.
Candidate manifest SHA-256: `{sha(C/'witness-source-v1.json')}` ({len(rows)} files).
No observer/live ETW run, UAC, protected VM/configuration access, production change,
medium/large run or source acceptance commit occurred. Historical ETW-loss cause
remains UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Change and boundary

Only two existing observer sources changed. Both callbacks use one static
65,536-record single-producer numeric buffer; overflow never overwrites and makes
the diagnostic incomplete. A scope starts after the process-provider/START/STOP
gate, before existing identity decoding. Field-validity bits distinguish not
decoded from decoded-invalid. No new TDH call, handle query, QPC call, lock,
callback allocation or callback I/O was added by the witness. Original selector
allocation/I/O and timing remain as before; this is not a claim those original
callbacks never allocate. Parent and instance states are sampled at their actual
existing decisions. Unevaluated state is null, never inferred false.

Unknown-parent rejection still precedes invalid-identity checking where the old
code did so. STOP still needs an exact existing row. No deferred selection,
retry, insertion reordering, forced match or acceptance rule changed.

Export runs after ProcessTrace thread.join(), with run, session, channel, manifest
and actual executable-file SHA-256, schema, frequency, quiescence and overflow.
The existing finalizer rejects unknown run-tree artifacts; therefore sidecars
are run-named siblings OUTSIDE that tree. The finalizer, checker, preservation
policy, helper-handoff and existing telemetry are byte-identical to predecessor.
Separate four-file diagnostic archival is non-acceptance and preserves first
failure. Export failure is explicit or a missing sidecar; neither may pass
diagnostic completeness. Export work still counts against unchanged deadlines.

The analyzer requires independent exact identities AND conservative event-time
windows, uses sequence when available, rejects stale bindings, preserves PID
reuse ambiguity and does not infer lost payloads from absent callbacks. Normalized
input provenance must be independently verified by the review procedure; this
analyzer is not a replacement identity authority. Invalid PID decoding in a
target time window remains identity-unresolved, not false callback absence.

## Validation

- `build-offline.cmd`: MSVC 19.44 / C++17 / O2 builds of both observers and offline
  replay executable passed; no observer binaries executed.
- `candidate\\WitnessOfflineTests.exe`: {native['checks']} native assertions PASS.
  Replays the actual original and modified callback bodies with stubbed OS/TDH
  inputs, comparing decoded-query order, rows, faults, discarded counts, clocks
  and authority captures. This is OFFLINE equivalence coverage, not ETW proof.
- `export-offline\\WitnessExportOffline.exe <fixture-run> authority|detailed`:
  both post-quiescence serializer fixtures PASS; binary/manifest/run binding,
  CREATE_NEW overwrite rejection and inaccessible export destination tested.
- `python -B test_witness.py`: 45 tests PASS (`tests-final-45.log`). Covers
  disposition, point-in-time state, PID reuse, missing evidence, overflow,
  bindings, static hot-path constraints, exact preserved acceptance rules,
  sidecar placement and NON-ACCEPTANCE archive verification.
- Python syntax: six affected/utility files compile without writing bytecode.
- Source/binary pre/post hashes and complete integration diff recorded separately.

## Preserved transitional findings

`tests-first.log`: 37 tests, 36 PASS, 1 change-inventory failure; a rebuilt object
file was omitted from the intended-change list. Corrected reporting, not runtime.
`build-export.log`: standalone export-fixture compile failed on the Windows
DUPLICATE macro; new internal enum renamed DUPLICATE_EVENT, serialized disposition
still DUPLICATE. Subsequent complete builds passed. Both logs retained.
An interim preservation-policy extension was reviewed against the strict frozen
finalizer and superseded by sibling export; its proposed contents and tests are
preserved as transitional artifacts, not the final design. Policy restored
byte-for-byte. Sandbox CIM census returned Access denied; host read-only census
completed with no Windows UAC. No failed live attempt was retried.

## Exact changed predecessor artifacts

{hash_lines}

Added source artifacts: lifecycle_witness_v1.hpp, lifecycle_witness_export_v1.hpp,
analyze_lifecycle_witness_v1.py, preserve_lifecycle_witness_v1.py,
witness_offline_tests.cpp and witness_export_offline.cpp. All other new build,
manifest and evidence artifacts are enumerated in after.json / archive manifest.

## Limits and rollback

No live overhead, loss reproduction or Stage 6 acceptance has been established.
The prior eight historical instances cannot be retroactively reconstructed with
this newly added witness. It may overflow during future collection; incompleteness
must remain explicit. The offline candidate still requires the existing bounded
fresh-D:-workspace rebinding/preflight under a future owner-approved procedure.

Rollback: leave this separate successor unused and retain the unchanged original
235-file candidate. No production restore, VM action or source rollback is needed.
Evidence archives must be retained, not overwritten or deleted.

One proposed live diagnostic procedure is in ONE-RUN-OWNER-REVIEW.md. STOP for
owner review; the procedure is not execution authorization.
'''
(R/'REPORT.md').write_text(text,encoding='utf-8')
print(json.dumps(dict(candidateFiles=len(rows),manifestSHA256=sha(C/'witness-source-v1.json'),changedExisting=len(changes),historicalArchive='112 verified')))
