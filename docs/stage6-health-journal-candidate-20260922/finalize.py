import datetime,hashlib,json,os,statistics,sys,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HEALTH JOURNAL MEDIUM PASS 20260922')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
pre=load(R/'candidate.json');mp=load(R/'medium-preflight.json');C=Path(pre['code']);root=Path(mp['root']);K=C/'medium-checker';sys.path[:0]=[str(K),str(C)]
import fresh_binding as fb
import checker_telemetry as ct
fb.verify_intake(C);check=ct.evaluate();assert check['status']=='EVIDENCE_VALIDATED_PENDING_ARCHIVE'
frozen=load(R/'candidate-frozen.json')['files']
for x in frozen:assert sha(x['path'])==x['sha256']
for x in pre['priorFiles']:assert sha(x['path'])==x['sha256']
changes=[]
for x in pre['priorFiles']:
    p=C/Path(x['path']).relative_to(Path(pre['old']))
    if sha(p)!=x['sha256']:changes.append(dict(path=str(p),before=x['sha256'],after=sha(p)))
assert {Path(x['path']).name for x in changes}=={'timed_monitor.ps1','qualified_worker.py','qualified_launch.ps1','medium-declaration.json','medium-intent.json'}
new=[dict(path=str(C/n),sha256=sha(C/n)) for n in ('health_reader.py','health_publication.ps1')]
save(R/'final-source-changes.json',dict(changed=changes,added=new,oldFrozenFilesVerified=160,newFrozenFilesVerified=162))
q=load(root/'analysis/qualification-result.json');w=load(root/'kernel-authority-result.json');m=load(root/'kernel-authority-manifest.json');t=load(root/'kernel-authority-telemetry.json');v=load(root/'identity-probes.json');host=load(root/'final-host-state.json');launch=load(root/'launcher-result.json')
assert q['status']=='PASS' and q['realProbeCount']==64 and q['unique']==132
assert host['matchingProcessCount']==host['diagnosticTraceCount']==0 and launch['error'] is None
assert launch['applicationExit']==launch['kernelExit']==launch['workerExit']==0
rows=v['rows'];duration=(max(x['reconciledQpc'] for x in rows)-min(x['launchRequestedQpc'] for x in rows))/v['frequency']
lifetimes=[(int(x['finalKernelTimes'][1])-int(x['finalKernelTimes'][0]))/1e7 for x in rows]
measure=check['rules']['telemetry'];sizes=[s['bytes'] for s in m['segments']]
journal=(root/'app-health.jsonl').read_bytes();assert journal.endswith(b'\n') and len(journal)<=1048576
jrows=[json.loads(x) for x in journal.splitlines()];assert all(x['seq']==i+1 and x['pump']==i+1 and x['run']==root.name for i,x in enumerate(jrows))
assert not (root/'app-health.json').exists() and not (root/'app-ready.pending').exists()
metrics=dict(runId=root.name,workloadSeconds=duration,records=w['written'],authoritativeBytes=m['bytes'],segments=len(sizes),segmentBytes=dict(min=min(sizes),max=max(sizes),mean=statistics.mean(sizes)),firstSequence=m['segments'][0]['first'],lastSequence=m['segments'][-1]['last'],writerSeconds=w['elapsedSeconds'],recordsPerWriterSecond=w['written']/w['elapsedSeconds'],bytesPerWriterSecond=m['bytes']/w['elapsedSeconds'],segmentsPerWriterMinute=len(sizes)*60/w['elapsedSeconds'],writerHighWaterItems=w['peakQueueItems'],writerHighWaterBytes=w['peakQueueBytes'],finalizerHighWater=w['peakPending'],backpressureSeconds=t['backpressure']['ticks']/t['frequency'],telemetry=measure,maxHeartbeat=q['maxHeartbeat'],maxHeartbeatAge=q['maxHeartbeatAge'],maxProbeSeconds=max(lifetimes),slowProbeWarnings=sum(len(x['slowWarnings']) for x in rows),hardDeadlineViolations=q['deadlineViolations'],cim=q['cim'],healthJournalBytes=len(journal),healthJournalRecords=len(jrows),runEvidenceBytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),sampler='NOT APPLICABLE: process-only medium workload',throughputLimitation='Writer-lifetime denominator includes startup/closure; not sustainable throughput or isolated service rate.')
save(R/'metrics.json',metrics)
checks=dict(focusedHealth=28,writerBoundaries=19,readinessPublication=7,existingMonitor=69,checkerComposition=21,telemetry=40,focusedTotal=184,queueAssertions=222,finalizationAssertions=157,failed=0,errors=0,skipped=0)
save(R/'test-summary.json',checks)
report=f'''# Stage 6 TEST health publication and fresh medium acceptance

**HEALTH_PUBLICATION_VALIDATED; MEDIUM_VALIDATED after archive verification. Stage 6 remains INCOMPLETE.**

Fresh run `{root.name}`. One attempt, no retry. Both required per-run UAC approvals succeeded. No change to the 10-second health limit, 13.6-second process deadline, 15-second independent observer or 120-second second-prompt gate. No large campaign, protected hashing, VM operation or production activity.

## Correction

New candidate: `{C}`. Only two existing behavioral TEST files changed: timed_monitor.ps1 and qualified_worker.py. Added health_publication.ps1 and health_reader.py. Three additional files changed only for fresh-run declaration/intent and launcher DLL-path binding. Exact raw before/after hashes are in final-source-changes.json; diffs and original freeze references are preserved.

The monitor opens a unique D: append-only health journal, serializes complete newline-delimited records, preserves durable flushing, and never truncates published records. Ready publication uses a flushed/closed staging file and non-overwriting rename after the first completed journal record. The reader reuses the unchanged bounded journal parser, checks a creation-verified publisher handle, latches failures and enforces age strictly below 10 seconds. Incomplete tails never renew health; final successful closure requires a complete tail after confirmed observer exit. Worker and observer retain their existing external result formats. The frozen v5 checker and shared journal.py are unchanged.

No authentication, authority, Core code, production behavior, kernel/native tracing, queue semantics or acceptance rule changed. Publisher closure validation is separate from live health: it does not pretend an exited publisher is healthy.

## Focused evidence

184 focused tests/checks passed, zero failures/errors/skips: 28 new Python/protocol/real PowerShell writer-reader tests; 19 writer failure/boundary checks; 7 deterministic readiness-publication checks; 69 existing monitor regressions; 21 checker composition and 40 telemetry checks. Separate existing suites passed 222 queue assertions including 10,000-event collision stress and 157 finalization assertions. These assertion counts are not mislabeled as separate live campaign trials.

The old truncate-before-write mechanism was reproduced on sacrificial data. Actual PowerShell publication was held partway through a new record: Python retained only the previous complete record, then consumed the completed record exactly once. A deliberately interrupted writer exited nonzero as expected; this is a passing negative test, not an unexpected failure. Ready publication was held after staging/flush but before rename; no final ready path existed until release. Malformed completed records, wrong identities, exactly-ten-second age, stale/future health, replacement/truncation, unavailable files, capacity overflow, write/flush failure and failed finalization rejected. Test child exits were confirmed; no forced termination occurred.

Python syntax and PowerShell parsing passed. Test commands and captured subprocess outputs are preserved in the review directory. Existing run_focused.py, queue_regression.ps1 and test_finalization_gate.ps1 were executed against this new candidate; no historical result was substituted for current acceptance.

## Actual medium results

| Requirement | Result |
|---|---|
| Workload | 64 probes: 16 idle, 16 churn, 32 overlap; one direct worker |
| Workload elapsed | {duration:.7f} seconds |
| Input size | Process events only; no dataset hashing |
| Authoritative instances | 132 |
| START / STOP | 132 / 132 |
| Records / bytes | {w['written']} / {m['bytes']} |
| Segments / first–last sequence | {len(sizes)} / {metrics['firstSequence']}–{metrics['lastSequence']} |
| Gaps / duplicate authority / missing segments | 0 / 0 / 0 under strict checker |
| Segment bytes min / mean / max | {min(sizes)} / {statistics.mean(sizes)} / {max(sizes)} |
| Segment hashes, manifest, seal | PASS |
| Writer lifetime | {w['elapsedSeconds']} seconds |
| Records/sec, bytes/sec, segments/minute over writer lifetime | {metrics['recordsPerWriterSecond']:.5f}, {metrics['bytesPerWriterSecond']:.5f}, {metrics['segmentsPerWriterMinute']:.5f} |
| Writer capacity | 65536 items / 67108864 bytes, unchanged |
| Writer high water | {w['peakQueueItems']} items / {w['peakQueueBytes']} bytes |
| Finalizer capacity / high water | 2 / {w['peakPending']} |
| Backpressure started / completed / interrupted | {t['backpressure']['started']} / {t['backpressure']['completed']} / {t['backpressure']['interrupted']} |
| Backpressure elapsed | {metrics['backpressureSeconds']:.7f} seconds |
| Rejected admissions | {w['attempted']-w['accepted']} |
| Flush mean / p95 / maximum | {measure['flush']['meanSeconds']:.8f} / {measure['flush']['p95Seconds']:.8f} / {measure['flush']['maxSeconds']:.8f} seconds |
| Readback/hash mean / maximum | {measure['readbackHashVerification']['meanSeconds']:.9f} / {measure['readbackHashVerification']['maxSeconds']:.9f} seconds |
| Queue snapshots | {measure['snapshots']}, strict transition/lag accounting PASS |
| Direct creator captures | 65 |
| Qualified post-exit helpers | 64 |
| Tracer helper verifications | 2 |
| Independently verified application observer | 1 |
| Retained handle evidence | {q['retained']} |
| Real native entries | {q['realNativeCount']} including worker |
| False uniqueness / authoritative ambiguity | 0 / 0 |
| CIM supporting evidence | {q['cim']}; preserved, not force-matched |
| Actual PID / parent PID reuse | 0 / 0; not claimed exercised |
| Maximum heartbeat / successful health age | {q['maxHeartbeat']:.7f} / {q['maxHeartbeatAge']:.7f} seconds |
| Slow heartbeat warnings | NOT CONFIGURED under approved policy |
| Slow probe warnings / deadline violations | {metrics['slowProbeWarnings']} / {q['deadlineViolations']} |
| Longest probe lifetime | {max(lifetimes):.7f} seconds |
| Complete health journal | {len(jrows)} records / {len(journal)} bytes; complete final newline |
| App / worker / kernel exit | 0 / 0 / 0 |
| Public checker | EVIDENCE_VALIDATED_PENDING_ARCHIVE, stage6-checker-telemetry-v5 |
| Final host census | Zero matching processes / zero trace sessions at {host['utc']} |
| Candidate / previous source hashes | 162 / 160 unchanged after freeze |
| Protected VM/configuration access / production change | NONE / NONE |

Raw metrics include dequeue/completion/finalizer lags and complete timing references. The throughput denominator includes observer startup/closure; this finite run does not establish sustainable throughput. With 15 segments the nearest-rank p95 equals the maximum. Readback/hash time includes read/record validation, not just CPU hashing. Sampler behavior was not exercised because this is the declared process-only medium workflow.

## Preserved failures and limitations

The earlier 221-member medium JSON-read failure archive remains unchanged, as do the prior nested-writer checker rejection and missed second-UAC-gate archive. No historical run was reclassified. The new passing evidence demonstrates the corrected mechanism, not the exact bytes observed during the prior failure. Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged; this run's supporting CIM counts are separate. Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Next genuine integration boundary

Stage 6 is not finished by medium acceptance. The copied large_launch.ps1 still waits for app-health.json (line 24) while this corrected monitor publishes app-health.jsonl. Its large_collect.py imports dry_health.Health, whose check still parses app-health.json. It also selects the older J6BaselineTrace.exe path; this is not proof that it consumes the now-qualified authority stream/checker. Running that copied launcher as-is would not be a valid next acceptance step.

The next review must identify the authoritative current large-collector integration candidate and minimally connect the validated health journal and qualified durable kernel/checker paths. Preserve both observer handle checks, collector/sample ownership, startup tracing, existing output contracts, bounded capacity and cleanup. Likely affected interfaces include large launch readiness, dry_health.Health or a dedicated large adapter, source manifest and versioned large checker binding; exact scope must be reviewed before edits. Validate that integration on small sacrificial data first, then qualify the 59.7 GB synthetic workload. Do not substitute this 64-probe run for large-data calibration, large acceptance, protected-source preservation, clean-Windows recovery or deployment/cutover requirements.

Protected VM access and real protected baseline hashing remain outside this pass. No owner approval for broad new authority or production activity is inferred from “finish Stage 6.” No acceptance commit or Stage 7 work.

## Rollback and archive

Rollback is to stop selecting this TEST candidate; preserve all artifacts. No production restore, protected VM change or evidence deletion is needed. Canonical nonsecret archive: `{A/'evidence.zip'}`. MEDIUM_VALIDATED is contingent on the accompanying completed archive-verification receipt; the receipt and final disposition are mirrored separately after verification.
'''
with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report);f.flush();os.fsync(f.fileno())
sources=[]
for label,base in [('review',R),('candidate',C)]:
    for p in sorted(base.rglob('*')):
        assert not p.is_symlink() and not p.is_junction(),p
        if p.is_file():
            assert p.name!='.env' and '__pycache__' not in p.parts,p
            sources.append(dict(name=label+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
assert not A.exists();A.mkdir()
save(A/'manifest.json',dict(status='MEDIUM_VALIDATED_PENDING_ARCHIVE',stage6Accepted=False,files=sources))
with (A/'evidence.zip').open('xb') as out:
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for x in sources:z.write(x['source'],x['name'])
        z.write(A/'manifest.json','manifest.json')
    out.flush();os.fsync(out.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
    assert len(z.namelist())==len(set(z.namelist()))==len(sources)+1
    assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
    for x in sources:
        b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(x['source'])
fb.verify_intake(C)
for x in frozen:assert sha(x['path'])==x['sha256']
for x in pre['priorFiles']:assert sha(x['path'])==x['sha256']
receipt=dict(status='PASS',archive=str(A/'evidence.zip'),membersVerified=len(sources)+1,archiveBytes=(A/'evidence.zip').stat().st_size,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
disposition=dict(status='MEDIUM_VALIDATED',healthCorrection='VALIDATED',stage6='INCOMPLETE',stage6Accepted=False,runId=root.name,attempts=1,retries=0,sourceFiles=162,liveProcesses=0,traceSessions=0,archiveSHA256=receipt['archiveSHA256'],productionChanged=False,protectedAccess=False,largeValidation=False,nextGate='Review bounded large-collector compatibility and qualified evidence integration before small/large validation')
save(R/'final-disposition.json',disposition);save(A/'final-disposition.json',disposition)
assert sha(R/'final-disposition.json')==sha(A/'final-disposition.json')
print(json.dumps(dict(disposition=disposition,archive=receipt,metrics=metrics)))
