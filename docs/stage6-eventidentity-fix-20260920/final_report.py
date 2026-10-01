"""Nonsecret evidence reconciliation. Reads only this candidate and prior evidence inventories."""
import pathlib,json,hashlib,difflib,datetime,sys
R=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
preserved=read(R/'preserved-before.json');changes=[]
for e in preserved:
 p=pathlib.Path(e['path']);st=p.stat()
 if sha(p)!=e['sha256'] or st.st_size!=e['bytes'] or st.st_mtime_ns!=e['mtime_ns']:changes.append(str(p))
write('preservation-final.json',dict(files=len(preserved),changes=changes,status='PASS' if not changes else 'FAIL',protectedVMAccess='NOT PERFORMED; no protected hashing authorized',scope='prior validation source/evidence trees only'))
sources=[];diffs=[]
for p in sorted(R.iterdir()):
 if p.suffix in ('.py','.ps1','.cs','.exe'):
  old=R/'source-before'/p.name
  sources.append(dict(path=str(p),sha256=sha(p),before_sha256=sha(old) if old.exists() else None,changed=not old.exists() or sha(old)!=sha(p)))
  if old.exists() and p.suffix!='.exe' and sha(old)!=sha(p):diffs.extend(difflib.unified_diff(old.read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(old),tofile=str(p)))
write('source-final.json',sources)
(R/'source.diff').write_text(''.join(diffs),encoding='utf-8')
queue=read(next(R.glob('queue-tests-*/result.json')))
focused=read(R/'focused-current.json')
runs={}
for name in ('smoke','loads','dry1','dry2'):
 d=R/name
 if (d/'reconciliation.json').exists():runs[name]=read(d/'reconciliation.json')
 elif d.exists():runs[name]={'status':'FAIL' if any((d/n).exists() for n in ('collector-failure.json','monitor-failure.json')) else 'INCOMPLETE'}
 else:runs[name]={'status':'NOT RUN'}
extra=read(R/'failure-checks.json') if (R/'failure-checks.json').exists() else {'status':'NOT RUN'}
valid=not changes and all(runs[n]['status']=='PASS' and (R/n/'acceptance.json').exists() for n in ('loads','dry1','dry2')) and focused['passed']==50 and extra.get('passed')==7
status='MONITOR_VALIDATED' if valid else 'MONITOR_STILL_DEFECTIVE'
summary=dict(status=status,runs=runs,queue=queue,focused=focused,failureChecks=extra,preservation=not changes,historicalPIDs='UNPROVEN',historicalStage1='UNCONFIRMED',protectedBaselineEligible=valid,productionChanges=False,protectedAccess=False)
write('summary.json',summary)
lines=['# EventIdentifier correction — final report', '',status,'',
 'Blocking failure: C: sustained hashing produced a 14.5649514-second interval between heartbeats 153 and 154. The threshold remains 10 seconds. Maximum sampled reader age was 8.3645728 seconds. Failure was first detected by offline reconciliation after all five workloads finished; no further campaign was run. workload-failure-analysis.json preserves the exact interval and surrounding trace. Adjacent traces localize 7.6266274 seconds between serialization end and append begin, followed by 6.1961153 seconds spanning append/persistence/removal. Those measurements do not establish whether underlying I/O, scheduling or another mechanism caused the delay.',
 'Five-workload disposition: idle PASS; C: reads PASS; C: hashing FAIL (heartbeat); CPU-only PASS; D: hashing PASS. Per-phase reconciliation fields in raw evidence refer to event-pipeline completeness only, not full workload acceptance. Full five-workload gate FAIL.',
 '## 1–6. Source, defect and mechanism',
 'All changes are new files under '+str(R)+'. One preparation script also exists at '+str(R.parent/'prepare_eventidentity_fix.py')+'. No original source was edited. Exact source paths and before/after SHA-256 values: source-before.json, source-final.json; source.diff records candidate changes. New files have no pre-change hash.',
 'Old Drain used Remove-Event -EventIdentifier, deleting all queued siblings with a collided external number. Teardown had the same destructive risk. New event_queue.cs assigns monotonic bounded QueueSequence at enqueue under the concrete collection SyncRoot, keys by reference identity, and removes exactly one reference-matched index only after AppendAllText succeeds. External numbers and PIDs are never destructive keys. Single outstanding selection and atomic publishing guard reject competing consumers; unexpected disappearance fails closed. No queue lock spans disk I/O. See DESIGN.md for complete lock/write/failure/rollback semantics.',
 'Sequence uniqueness is protected by the same lock for every producer; the 20,000-entry collector bound fails before integer overflow. Actual PSEventArgsCollection and live-session reference behavior were tested.',
 '', '## 7–8. Collision tests and stress',
 'queue-tests result: '+json.dumps(queue),
 'The required collision cases are covered by the named C# groups and their FIFO/sibling/retry assertions; duplicate-PID rejection is additionally covered by focused test_event_rejection. The stress uses four concurrent producers, 10,000 events, seven repeating external IDs and one active consumer.',
 '', '## 9–15. Real probes, regressions, workload/heartbeat/pipeline totals',
 'Focused regression result: '+json.dumps(focused),
 'Real run results: '+json.dumps(runs,indent=2),
 'START/STOP callback evidence comes from the instrumented subscriber; enqueue evidence is separately recorded. Parallel WMI observation shares the native provider and is not an independent kernel source. Retained handles/GetProcessTimes independently prove process exits; those exits are never synthesized into STOP records.',
 '', '## 16–21. Failure injection, dry runs and durability',
 'Additional failure checks: '+json.dumps(extra)+'. New test_queue_finalization.py and test_failure_campaigns.py were prepared but NOT RUN because phase 8 failed. They are not accepted validation evidence.',
 'Earlier focused tests cover publisher/producer death, reader death/restart, malformed/partial heartbeat, ten-second stale rejection, identity changes, hashing-child death, finalizer death, final flush failure and archive corruption. Collision tests cover event-write denial, zero removals and retry refusal. Additional checks cover actual selected-queue consumer termination, residue, late queue failure, malformed events and ambiguous identity.',
 'Dry1: '+runs['dry1']['status']+'; Dry2: '+runs['dry2']['status']+'. Full failure-injection phase NOT RUN. Monitor heartbeat final flush completed, but workload evidence acceptance/finalization was not attempted after reconciliation failed. Passing focused fsync tests do not make this failed workload accepted. Top-level preservation archive verification is recorded separately in archive-verification.json; it archives failure, not a successful dry run.',
 '', '## 22–27. Limits, preservation and disposition',
 'Historical PID 13248 / 22544 / 21896 individual causes remain UNPROVEN. Historical timing delays remain unexplained. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.',
 'EventIdentifier collisions were subsequently proven to cause deterministic queue-event loss and the defect was corrected. This does not attribute the original three losses or prove all timing mechanisms reliable.',
 f'Prior validation evidence preservation: {len(preserved)} files checked; {len(changes)} changed. No protected VM/configuration paths were opened. No VirtualBox launch, production change, credential access or protected hashing was performed.',
 'Protected-baseline eligibility: '+('eligible for a separate owner-approved retry, NOT executed' if valid else 'NOT ELIGIBLE'),
 'Rollback: stop using this new validation candidate. Preserve all candidate/old evidence. Do not restore any VM or production file. The original monitor remains known-defective.',
 'Final status: '+status]
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write('\n\n'.join(lines)+'\n')
print(json.dumps(dict(status=status,preservedFiles=len(preserved),changes=changes)))
