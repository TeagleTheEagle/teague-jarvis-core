import ast,datetime,hashlib,json,os,statistics,sys,zipfile
from pathlib import Path
R=Path(__file__).parent;A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TELEMETRY CANDIDATE 20260922')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
pre=load(R/'candidate.json');C=Path(pre['code']);root=Path(load(R/'run.json')['path']);K=C/'medium-checker';sys.path[:0]=[str(K),str(C)]
import fresh_binding as fb
import checker_telemetry as ck
fb.verify_intake(C)
try:ck.evaluate()
except ValueError as e:assert str(e)=='SCHEMA_FIELDS:$.bundle.qualification.writer'
else:raise AssertionError('Unexpected acceptance after recorded rejection')
frozen=load(R/'candidate-frozen.json')['files']
for row in frozen:assert sha(row['path'])==row['sha256'],row['path']
for row in pre['copies']:assert sha(row['source'])==row['sha256'],row['source']
save(R/'preservation-after.json',dict(status='PASS',frozenCandidateComparisons=len(frozen),priorSourceComparisons=len(pre['copies']),sourceFreezeSHA256=sha(C/'medium-source-freeze.json'),protectedAccess=False,productionChanged=False))
save(R/'metadata-clarification.json',dict(note='The initial implementation-hashes.json before field hashes normalized decoded text, not original file bytes. Canonical raw before/after hashes are in changes.json and candidate-frozen.json; prior originals were independently reverified. Do not use the normalized hash as an original artifact identity.',initialRawHeaderSHA256=next(x['sha256'] for x in pre['copies'] if Path(x['path']).name=='durable_sink.hpp')))
v=load(root/'identity-probes.json');f=v['frequency'];probes=v['rows'];q=load(root/'analysis/qualification-result.json');w=load(root/'kernel-authority-result.json');m=load(root/'kernel-authority-manifest.json');t=load(root/'kernel-authority-telemetry.json');diag=load(R/'checker-diagnosis.json');measure=diag['telemetry'];host=load(root/'final-host-state.json')
assert host['matchingProcessCount']==host['diagnosticTraceCount']==0 and host['status']=='PASS'
sizes=[s['bytes'] for s in m['segments']];duration=(max(p['reconciledQpc'] for p in probes)-min(p['launchRequestedQpc'] for p in probes))/f
lifetime=[(int(p['finalKernelTimes'][1])-int(p['finalKernelTimes'][0]))/1e7 for p in probes]
start=datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)+datetime.timedelta(microseconds=int(load(root/'launcher-identity.json')['created'])/10)
end=datetime.datetime.fromisoformat(host['utc'].replace('Z','+00:00'))
metrics=dict(workloadSeconds=duration,campaignThroughCleanupSeconds=(end-start).total_seconds(),records=w['written'],bytes=m['bytes'],segments=len(sizes),sizes=dict(min=min(sizes),max=max(sizes),mean=statistics.mean(sizes)),writerWindowSeconds=w['elapsedSeconds'],writerWindowRecordsPerSecond=w['written']/w['elapsedSeconds'],writerWindowBytesPerSecond=m['bytes']/w['elapsedSeconds'],writerWindowSegmentsPerMinute=len(sizes)*60/w['elapsedSeconds'],measurement=measure,backpressureSeconds=t['backpressure']['ticks']/t['frequency'],queueItemsHighWater=w['peakQueueItems'],queueBytesHighWater=w['peakQueueBytes'],finalizerHighWater=w['peakPending'],maxHeartbeat=q['maxHeartbeat'],maxAge=q['maxHeartbeatAge'],maxProbeSeconds=max(lifetime),slowProbeWarnings=sum(len(p['slowWarnings']) for p in probes),hardDeadlineViolations=q['deadlineViolations'],retained=q['retained'],postExit=q['qualifiedPostExit'],cim=q['cim'],runEvidenceBytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),rateLimit='Writer-lifetime denominator includes startup/closure; not isolated service or sustainable throughput.',sampler='NOT APPLICABLE: process-only pipeline does not launch one.')
save(R/'metrics.json',metrics)
entries=[
 ('Run ID',root.name),('Workload','64 probes: 16 idle / 16 churn / 32 overlap, one worker; fresh TEST identity'),('Input/data size',f"Process events only; {m['bytes']} authoritative bytes; no source dataset hashing"),('Workload seconds',duration),('Campaign through final cleanup seconds',(end-start).total_seconds()),('Authoritative records',w['written']),('Records/sec (writer lifetime)',metrics['writerWindowRecordsPerSecond']),('Run evidence bytes',metrics['runEvidenceBytes']),('Segments',len(sizes)),('Segment bytes',metrics['sizes']),('First sequence',m['segments'][0]['first']),('Last sequence',m['segments'][-1]['last']),('Gaps',0),('Duplicates',0),('Overlaps',0),('Missing segments',0),('Durable segments',len(sizes)),('Segment hashes','PASS'),('Durable manifest','PASS; does not confer campaign acceptance'),('Writer capacity','65536 items / 67108864 bytes; unchanged'),('Writer high-water',f"{w['peakQueueItems']} items / {w['peakQueueBytes']} bytes"),('Finalizer capacity',2),('Finalizer high-water',w['peakPending']),('Maximum queue utilization',f"Finalizer {100*w['peakPending']/2}%; writer items {100*w['peakQueueItems']/65536:.6f}%; writer bytes {100*w['peakQueueBytes']/67108864:.6f}%"),('Backpressure events',t['backpressure']),('Rejected admissions',w['attempted']-w['accepted']),('Average flush seconds',measure['flush']['meanSeconds']),('p95 flush seconds (nearest rank)',measure['flush']['p95Seconds']),('Maximum flush seconds',measure['flush']['maxSeconds']),('Average readback/hash seconds',measure['readbackHashVerification']['meanSeconds']),('Maximum readback/hash seconds',measure['readbackHashVerification']['maxSeconds']),('Kernel START',q['starts']),('Kernel STOP',q['stops']),('Canonical identities',q['unique']),('False unique',q['falseUnique']),('Authoritative ambiguity',q['authoritativeAmbiguous']),('Direct creator captures',65),('Tracer-helper verifications',2),('Qualified post-exit helpers',q['qualifiedPostExit']),('Missing mandatory identity evidence',0),('Identity contradictions',0),('Native entries',q['realNativeCount']),('CIM unique',q['cim'].get('UNIQUE_CORRELATED',0)),('CIM ambiguous',q['cim'].get('AMBIGUOUS',0)),('CIM unmatched',q['cim'].get('UNMATCHED',0)),('Max heartbeat seconds',q['maxHeartbeat']),('Slow heartbeat warnings','NOT CONFIGURED — explicitly approved; <10-second failure threshold unchanged'),('Slow probe warnings',metrics['slowProbeWarnings']),('Maximum probe seconds',max(lifetime)),('Hard deadline violations',q['deadlineViolations']),('Application observer','Exit 0; secondary finalization complete; sampler not instantiated'),('Tracer','Exit 0; no recorded kernel loss'),('Writer','No fault; attempted/accepted/written equal; threads exited'),('Finalizer','15 manifested segments; two-credit bound preserved'),('Checker','REJECT: SCHEMA_FIELDS:$.bundle.qualification.writer'),('Version','stage6-checker-telemetry-v4 composed with unchanged v3 lifecycle rules'),('Queue drain','PASS; 843 telemetry transition snapshots; exact state/lag reconciliation'),('Trace finalization','PASS; zero trace sessions'),('Cleanup','PASS; creation-bound process evidence closed; final host census zero'),('Archive member count','See verified receipt'),('Archive verification','Required before final disposition; see receipt'),('Original source hashes','156/156 unchanged'),('Frozen candidate hashes','160/160 unchanged'),('Protected VM access','NONE'),('Production change','NONE'),('Historical 21 ambiguous / 1 unmatched','UNCHANGED; new 258/5 is separate'),('Historical causes','UNCONFIRMED; HISTORICAL STAGE 1 CAUSE: UNCONFIRMED'),('59.7 GB justified','NO: medium checker gate rejected'),('Next proposed gate','Separately versioned projection correction + analyzer-produced fixtures; do not patch frozen run or automatically retry'),('Final status','MEDIUM_CHECKER_DEFECTIVE; Stage 6 INCOMPLETE')]
assert len(entries)==70
report='''# Stage 6 telemetry candidate and single medium attempt

**MEDIUM_CHECKER_DEFECTIVE — Stage 6 INCOMPLETE.**

250 final focused checks passed (21 native cases, 40 telemetry checks, 21 composition checks, 114 prior checker regressions, 43 declaration checks, 5 intake checks, 6 baseline comparisons). One live medium attempt followed. No medium retry, large validation, protected access or production operation occurred.

## Exact blocker and diagnosis

The public checker rejected `SCHEMA_FIELDS:$.bundle.qualification.writer`. New telemetry was correctly verified on disk, but the wrapper's v3 compatibility view normalized only top-level manifest/writer records, omitting the duplicate writer embedded in the analyzer's qualification report. The strict schema correctly rejected the extra fields.

Read-only diagnosis proved the nested writer equals the authoritative writer exactly. Normalizing only that proven duplicate in an in-memory diagnostic replay makes the existing rules pass. This is diagnostic evidence, NOT acceptance, and does not alter frozen code or the rejected run. The synthetic composition fixture lacked the actual analyzer's new nested telemetry fields, so it missed this integration case.

Minimum proposed correction: in a new versioned candidate, require nested raw writer equality before applying the same projection to the duplicate. Add a positive fixture from actual analyzer output and rejection fixtures for nested-writer substitutions, missing timing and unknown fields. Preserve this attempt as rejected. The owner medium contract requires stopping when a frozen checker defect is discovered; no checker patch or new medium attempt was performed.

## Required medium results

| # | Requirement / measurement | Actual result |
|---|---|---|
'''
report+=''.join(f'| {i} | {key} | {str(value).replace(chr(10)," ")} |\n' for i,(key,value) in enumerate(entries,1))
report+='''
## Changes, failure preservation and rollback

Changed only new TEST candidate copies: `durable_sink.hpp`, its compiled test/tracer binaries, launcher DLL-path binding, declaration/intent paths. Added `telemetry.py`, `checker_telemetry.py`, telemetry policy, focused tests and evidence tooling. The existing v3 checker/schema/adapter and original frozen sources stayed unchanged. The new wrapper makes telemetry mandatory before composing existing rules; its nested-copy omission is the current blocker. `changes.json` contains exact raw-byte before/after hashes and final diffs. `candidate-frozen.json` binds final source/binaries. The initial normalized-text hash is clarified in `metadata-clarification.json`.

Telemetry uses a preallocated 65536 x 80-byte (5,242,880-byte) queue trace, existing locked transitions, per-segment ticks and separately hashed finalization evidence on D:. No new live filesystem appends, observer authority, process deadlines or heartbeat limits. Flush p95 uses nearest rank; with 15 samples it equals the maximum. Readback/hash duration includes record validation, not pure CPU hash cost. Queue lag and two actual completed backpressure episodes are verified. Finite performance samples do not prove long-duration sustainable throughput or actual PID reuse (none observed).

Preserved preparation failures: initial fault-19 test did not reach a blocked predicate (20 passed / 1 failed); corrected only that injected test path and reran 21/21. Initial path preparation used single backslashes against a C# escaped DLL path and stopped before launch; corrected binding only. Initial legacy regression completed checks but failed exclusive locator creation because a prior locator was copied; a new output location preserved it and the fresh 114+43 regressions passed. Intermediate compiler outputs and line-ending normalization are retained. Existing tracer variable-shadowing warning remains disclosed.

The first final host inspection recorded one pwsh PID 17320, created during that inspection. Its parent command contained the D: scope string matched by the inspector. Subsequent read-only inspection found that PID absent, and the unchanged inspector invoked without an embedded D: parent command recorded zero matching processes/traces. No process was terminated and no exclusion rule was changed. Both observations are preserved; the exact prior command-line identity was not captured in the blocked record.

Both initial and corrected native test processes were reconciled by retained creator process handles, creation time, image identity and kernel signal/exit times. Comparison runs also retained creation/exit proof. All actual medium components reported exit 0. No cleanup deletion occurred.

Rollback: stop selecting this new TEST workspace; retain all evidence and the prior candidate. No production restore or VM action is needed. Original failed/inconclusive archives remain unchanged. The accepted Stage 4/5 application baseline was not edited. No acceptance commit, acceptance seal, protected hashing or production activation was created.

## Stage 6 remaining path

The current immediate gate is the checker integration defect. Medium acceptance must pass before large synthetic protected-collector validation is eligible. Then the existing preservation-safe roadmap still requires qualified collector evidence, separately authorized protected baseline capture, OS-enforced source isolation and validation-copy preparation, qualifying clean-Windows recovery/deployment evidence, and the applicable owner-controlled cutover decision. This finite process run is not a substitute for any of those gates. No protected-source permission, VM operation or production authorization is inferred from passing telemetry tests.

Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
'''
with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report);f.flush();os.fsync(f.fileno())
sources=[]
for label,base in [('review',R),('candidate',C),('intake-fixture',Path(load(R/'fresh-binding-tests.json')['fixture']))]:
 for p in sorted(base.rglob('*')):
  assert not p.is_symlink() and not p.is_junction(),p
  if p.is_file():
   assert p.name!='.env' and '__pycache__' not in p.parts,p
   sources.append(dict(name=label+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
assert not A.exists();A.mkdir()
save(A/'manifest.json',dict(schema='stage6-telemetry-archive-v1',status='MEDIUM_CHECKER_DEFECTIVE',accepted=False,runId=root.name,files=sources))
with (A/'evidence.zip').open('xb') as out:
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for item in sources:z.write(item['source'],item['name'])
  z.write(A/'manifest.json','manifest.json')
 out.flush();os.fsync(out.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist()))==len(sources)+1
 assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for item in sources:
  data=z.read(item['name']);assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']==sha(item['source'])
fb.verify_intake(C)
for row in frozen:assert sha(row['path'])==row['sha256']
for row in pre['copies']:assert sha(row['source'])==row['sha256']
receipt=dict(status='PASS',archive=str(A/'evidence.zip'),membersVerified=len(sources)+1,archiveBytes=(A/'evidence.zip').stat().st_size,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
disposition=dict(status='MEDIUM_CHECKER_DEFECTIVE',stage6='INCOMPLETE',accepted=False,attempts=1,retries=0,reason='SCHEMA_FIELDS:$.bundle.qualification.writer',archiveSHA256=receipt['archiveSHA256'],reportSHA256=receipt['reportSHA256'],nextRunAuthorized=False,productionChanged=False,protectedAccess=False)
save(R/'final-disposition.json',disposition);save(A/'final-disposition.json',disposition)
assert sha(R/'final-disposition.json')==sha(A/'final-disposition.json')
print(json.dumps(dict(status=disposition['status'],receipt=receipt,metrics=metrics)))
