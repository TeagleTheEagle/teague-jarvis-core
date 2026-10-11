import pathlib,json,hashlib,difflib,zipfile
R=pathlib.Path(__file__).resolve().parent;cfg=json.loads((R/'candidate.json').read_text());C=pathlib.Path(cfg['code']);O=pathlib.Path(cfg['original'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes=[]
for x in cfg['originalFiles']:
 p=O/x['name'];assert sha(p)==x['sha256'],x['name']
 n=C/x['name']
 if sha(n)!=sha(p):
  changes.append(dict(name=x['name'],before=sha(p),after=sha(n)))
  (R/(x['name'].replace('/','_')+'.diff')).write_text(''.join(difflib.unified_diff(p.read_text().splitlines(True),n.read_text().splitlines(True),fromfile=str(p),tofile=str(n))))
assert {x['name'] for x in changes}=={'evidence_support.py','large_collect.py','baseline-allowlist.json'}
newnames=['small_binding_v2.py','small_coverage_v2.py','small_check_v2.py','small_launch_v2.ps1','small_finalize_v2.py','tracker_adapter_v2.py','support_verifier.py','test_v2.py','test_tracker.py','tracker_regression.py','fixture_support.py']
with (R/'stop-source-hashes.json').open('x') as f:json.dump(dict(originalVerified=len(cfg['originalFiles']),changes=changes,newFiles=[dict(name=n,sha256=sha(C/n)) for n in newnames],candidateSourceManifestSHA256=sha(C/'small-source-v2.json'),checkerV1Unchanged=True,nativeBinariesUnchanged=True),f,indent=2)
with (R/'cleanup-blocker.json').open('x') as f:json.dump(dict(status='BLOCKED',operation='Get-CimInstance Win32_Process',error='Access denied',censusCompleted=False,retry=False,UACRequested=False,source='host_preflight.ps1:17',partialFile='final/f5ef9a484a26428aaf83718ebae7a3d9/final-host-state.json'),f,indent=2)
(R/'REPORT.md').write_text('''# Stage 6 v2 TEST implementation — stopped at final cleanup census

Status: BLOCKED pending permission for read-only final cleanup census. Implementation and focused tests completed; final process/trace cleanup NOT VERIFIED. No live integrated acceptance run occurred.

Final tests: 27 checker/binding/finalizer methods passed (with additional parameterized negative cases), and 21 tracker methods passed using tiny disposable child processes. Earlier 23-method transitional run also passed and remains preserved; do not add it again to the final total of 48. Python AST checks passed. PowerShell launcher syntax validation has not yet been recorded. No live kernel-authority qualification or collector acceptance claimed.

Implemented separate v2 binding, coverage, checker, helper adapter, finalizer and launcher candidate. Independent tracker corroboration is limited to OS_CONSOLE_HELPER with missing tracer image, preserving original tracer facts and rejecting contradictions. Direct creator-owned/native rules and qualified error-87 path remain unchanged. Binding records actual run/declaration/source/session/producer identities; exact handle acquisition timing added. Finalizer uses existing actual checker, recursive artifact inventory, durable flush, immutable result/seal and archive verification. Synthetic-only allowlist rebased to the new tiny workspace; no protected roots permitted.

Exact source hashes/diffs: stop-source-hashes.json and *.diff. Three copied files changed: evidence_support.py, large_collect.py, baseline-allowlist.json. New versioned modules are listed in the hash file. All 183 original candidate files remain unchanged; v1 checker, native launcher/tracers and authority verifiers remain unchanged. No production file changed. Rollback is selection of the original candidate, retaining this evidence.

Tests use actual existing qualifier/coverage functions and serialized segment manifests, plus synthetic adapter/finalizer fixtures. Finalizer unit tests deliberately replace the full live checker/census so fault paths can be isolated; they are not substitute live acceptance. Historical evidence was read only. The 21 tracker tests exercise actual tiny processes and acquisition/close/join fault cases. No new observer, trace session, UAC prompt or hash worker launched. Tiny process tests reported cleanup, but that does not replace the denied final independent host census.

Blocker: final host_preflight.ps1 call failed at Get-CimInstance Win32_Process with Access denied. The exclusively created empty partial census file is preserved unchanged. No retry or broader-access request executed. Live process/trace counts are UNKNOWN, not zero. Owner instructed a stop before new access/elevation requirements or defects beyond scope.

Candidate runtime modules are tested, but final source freeze/reconciliation and PowerShell syntax validation remain pending along with final host census and canonical archive copy/verification. Do not launch this candidate yet. No changes to thresholds, native binaries, production, protected VM/configuration or dataset. No medium/large/59.7 GB run, backup or restore.

Next action requiring owner approval: repeat ONLY the existing read-only host census in the known host command context with sandbox access sufficient for Win32_Process/logman enumeration; no Administrator token or UAC is requested. Then complete pending syntax/source/evidence finalization for this same action. No live integrated run included.

Stage 6 remains INCOMPLETE. Historical causes UNCONFIRMED. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
''')
files=sorted(p for p in R.rglob('*') if p.is_file())
manifest=[dict(name=p.relative_to(R).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in files]
archive=R/'stopped-evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(R).as_posix())
 z.writestr('archive-input-manifest.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(archive) as z:
 for x in manifest:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
with (R/'local-archive-receipt.json').open('x') as f:json.dump(dict(localOnly=True,membersVerified=len(manifest)+1,archive=str(archive),sha256=sha(archive),canonicalArchiveCompleted=False),f,indent=2)
print(json.dumps(dict(status='BLOCKED',originalHashesVerified=len(cfg['originalFiles']),changes=changes,localArchiveSHA256=sha(archive)),indent=2))
