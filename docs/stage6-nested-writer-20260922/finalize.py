import ast,difflib,hashlib,json,os,sys,zipfile
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-telemetry-candidate-20260922';A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 NESTED WRITER CORRECTION 20260922')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
pre=load(R/'candidate.json');C=Path(pre['code']);old=Path(pre['originalCode']);root=Path(pre['originalRun']['path']);K=C/'medium-checker'
assert load(R/'test-results.json')['passed']==44
wrappers=list(R.glob('wrapper-checks-*.json'));timings=list(R.glob('telemetry-checks-*.json'))
assert len(wrappers)==len(timings)==1 and load(wrappers[0])['passed']==21 and load(timings[0])['passed']==40
host=load(R/'final/fcfa1431ac13465aa6d79fb491e92c75/final-host-state.json');assert host['status']=='PASS' and host['matchingProcessCount']==host['diagnosticTraceCount']==0
changed=[]
for row in pre['copies']:
 assert sha(row['source'])==row['sha256'],row['source']
 if sha(row['path'])!=row['sha256']:changed.append(dict(**row,afterSHA256=sha(row['path'])))
assert len(changed)==1 and Path(changed[0]['path']).name=='checker_telemetry.py'
sys.path[:0]=[str(K),str(C)];import fresh_binding as fb
fb.verify_intake(old)
assert load(P/'final-disposition.json')['status']=='MEDIUM_CHECKER_DEFECTIVE' and load(P/'final-disposition.json')['accepted'] is False
assert sha(pre['archive']['archive'])==pre['archive']['archiveSHA256']
files=[p for p in C.iterdir() if p.is_file()]+[p for p in K.iterdir() if p.is_file()]
for p in files:
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf8'))
rows=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]
save(R/'candidate-freeze.json',dict(schema='stage6-offline-checker-freeze-v1',version='stage6-checker-telemetry-v5',files=rows,liveBindingPrepared=False))
save(R/'preservation.json',dict(status='PASS',priorFrozenFilesVerified=len(pre['copies']),changedNewCopies=changed,candidateFiles=len(rows),priorArchiveSHA256=pre['archive']['archiveSHA256'],priorIntakeSHA256=sha(root/'intake-manifest.json'),originalDisposition='MEDIUM_CHECKER_DEFECTIVE',productionChanged=False,protectedAccess=False,liveRuns=0))
report=f'''# Stage 6 nested-writer checker correction

**CHECKER_CORRECTION_VALIDATED. Stage 6 remains INCOMPLETE.**

Only the approved nested-writer correction was implemented. No medium attempt, observer/tracer start, large run, protected VM access, production change or acceptance commit occurred.

## Change

New candidate: `{C}`.

Exactly one existing candidate source changed: `medium-checker/checker_telemetry.py`, version `stage6-checker-telemetry-v5`.

Before: `{changed[0]['sha256']}`.

After: `{changed[0]['afterSHA256']}`.

The checker now requires `qualification.writer` to be a complete raw copy of the authoritative writer. Canonical JSON comparison preserves number/bool distinctions that ordinary Python equality can erase. A missing or contradictory copy rejects before conversion. Only after equality is established does the nested copy receive the same compatibility conversion as the top-level writer. Unknown remaining fields still fail the existing strict schema. Conversion operates on a deep copy; original evidence is not mutated.

All other copied source and native binaries remain byte-identical. No runtime, writer/finalizer, observer, queue bound, heartbeat/deadline, security or authority change was made. The existing checker/schema/adapter and telemetry verifier were not changed.

## Verification

**105/105 checks PASS; 0 failures.**

| Group | Result |
|---|---|
| Actual-analyzer fixture, equality, preservation and rejection checks | 44/44 |
| Existing composition regressions, with the synthetic analyzer duplicate made representative | 21/21 |
| Existing telemetry regressions | 40/40 |

The actual fixture is derived from the preserved run `{root.name}` through the existing analyzer adapter. It is bound to the original intake, qualification report, writer report and archive hashes. The original v4 checker reproduces `SCHEMA_FIELDS:$.bundle.qualification.writer`; v5 passes the regression replay. This is a regression result, not new live acceptance. The old run remains **MEDIUM_CHECKER_DEFECTIVE** and its archive/disposition were not changed.

Negatives include missing nested writer, missing timing, mismatched counts/hashes/order/states, bool/int/float substitutions, matching unknown fields, missing creator/native evidence, unknown helper authority, kernel loss, forced CIM matching, heartbeat at 10 seconds, deadline violation, unproven cleanup, missing/overflowed telemetry and unbound public evaluation. Public CLI evaluation refuses the new copy without a fresh run binding. Object-key ordering alone remains permissible.

Exact commands used the bundled Python interpreter with `-B`: `prepare.py`, `test_correction.py`, `regressions.py`, and `finalize.py`. Regression execution receipts preserve subprocess commands/output. Syntax was parsed without writing bytecode. `host_preflight.ps1 -RunId fcfa1431ac13465aa6d79fb491e92c75` recorded zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions. No cleanup termination was needed.

Before preparation, all {len(pre['copies'])} prior frozen source hashes and all 1,561 members of the previous archive verified. After tests, prior source hashes and immutable run intake verified again. `candidate-freeze.json` records all {len(rows)} copied/final candidate file hashes. Exact diff and the original checker bytes are preserved separately.

## Acceptance boundary and next step

The checker correction is validated offline. This does not retroactively pass the rejected medium run or satisfy fresh medium acceptance. No change was made inside that frozen campaign.

Next proposed action: one separately authorized fresh medium attempt. Prepare its new TEST run identity, declaration/intent, local launcher binding and source freeze; use this validated checker version with the unchanged qualified native pipeline. Preflight must verify prior archives, candidate hashes, D: containment/capacity, zero processes/traces and fresh output paths. Use the existing two per-run UAC prompts. Keep the 64-probe workload, queue bounds, 10-second heartbeat limit, 13.6-second hard deadline and 15-second independent observer period unchanged. No automatic retry. Require complete lifecycle/telemetry, strict public checker evaluation, cleanup and archive verification before a medium PASS.

The copied candidate is NOT a ready-to-run medium launch: its inherited prior declaration is deliberately not repurposed by this offline correction. Public evaluation currently rejects absent fresh binding. Do not run its inherited launcher without the reviewed fresh preparation.

Protected baseline capture, the 59.7 GB campaign and production remain outside this pass. Stage 6 cannot be declared complete from this correction.

## Rollback, preservation and limitations

Rollback is to stop selecting the new checker copy and preserve its evidence. Original v4 source and failed/inconclusive evidence remain untouched; no production restore, VM action or deletion is needed. No new live behavior or sustained-load claim is made. Slow-heartbeat warnings remain NOT CONFIGURED under the owner's explicit disposition; the hard health limit is unchanged.

Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. The prior medium 258 AMBIGUOUS / 5 UNMATCHED remain separate supporting evidence. Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Canonical evidence archive: `{A / 'evidence.zip'}`. Archive acceptance requires the accompanying independently verified receipt; archive verification is not campaign acceptance.
'''
with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report);f.flush();os.fsync(f.fileno())
sources=[]
for label,base in [('review',R),('candidate',C)]:
 for p in sorted(base.rglob('*')):
  assert not p.is_symlink() and not p.is_junction(),p
  if p.is_file():
   assert p.name!='.env' and '__pycache__' not in p.parts,p
   sources.append(dict(name=label+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
for name in ('REPORT.md','archive-verification.json','final-disposition.json','checker-diagnosis.json'):
 p=P/name;sources.append(dict(name='prior-reference/'+name,source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
assert not A.exists();A.mkdir()
save(A/'manifest.json',dict(schema='stage6-checker-correction-archive-v1',status='CHECKER_CORRECTION_VALIDATED',stage6Accepted=False,files=sources))
with (A/'evidence.zip').open('xb') as out:
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for x in sources:z.write(x['source'],x['name'])
  z.write(A/'manifest.json','manifest.json')
 out.flush();os.fsync(out.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist()))==len(sources)+1
 assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for x in sources:
  data=z.read(x['name']);assert len(data)==x['bytes'] and hashlib.sha256(data).hexdigest()==x['sha256']==sha(x['source'])
for x in rows:assert sha(x['path'])==x['sha256']
for x in pre['copies']:assert sha(x['source'])==x['sha256']
fb.verify_intake(old)
receipt=dict(status='PASS',archive=str(A/'evidence.zip'),archiveBytes=(A/'evidence.zip').stat().st_size,membersVerified=len(sources)+1,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
disposition=dict(status='CHECKER_CORRECTION_VALIDATED',stage6='INCOMPLETE',checks=105,failed=0,liveRuns=0,priorMediumDispositionUnchanged=True,candidateSHA256=sha(K/'checker_telemetry.py'),candidateFreezeSHA256=sha(R/'candidate-freeze.json'),archiveSHA256=receipt['archiveSHA256'],productionChanged=False,protectedAccess=False,nextGate='Separately authorized fresh medium preparation and attempt')
save(R/'final-disposition.json',disposition);save(A/'final-disposition.json',disposition)
assert sha(R/'archive-verification.json')==sha(A/'archive-verification.json') and sha(R/'final-disposition.json')==sha(A/'final-disposition.json')
print(json.dumps(dict(disposition=disposition,receipt=receipt)))
