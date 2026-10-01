import ast,datetime,hashlib,json,os,zipfile
from pathlib import Path
R=Path(__file__).parent
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 MEDIUM 20260922')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
pre=load(R/'preflight.json');C=Path(pre['code']);K=Path(pre['checker']);root=Path(pre['root']);ready=load(R/'ready.json');metric=load(R/'metrics.json');checked=load(R/'checker-result.json')
import sys
sys.path[:0]=[str(K),str(C)];import fresh_binding as fb;import checker_medium as ck
fb.verify_intake(C);assert ck.evaluate()==checked
assert sha(C/'medium-source-freeze.json')==ready['freezeSHA256']
for x in pre['checks']+load(R/'candidate-frozen.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
host=load(root/'final-host-state.json');assert host['status']=='PASS' and host['matchingProcessCount']==host['diagnosticTraceCount']==0
frozen=Path(pre['originalRuntime'])/'cleanup_checker.py';small=Path(pre['originalChecker'])/'checker_v2.py'
assert sha(frozen)=='e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6'
assert sha(small)=='a0c5bf094841bf428bb62073082627e4e3ca88d1b330f3bcd8d611ecc51f2945'
launch=load(root/'launcher-identity.json');born=datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)+datetime.timedelta(microseconds=int(launch['created'])/10);end=datetime.datetime.fromisoformat(host['utc'].replace('Z','+00:00'))
duration=(end-born).total_seconds()
sourceResult=dict(status='PASS',originalFrozenSHA256=sha(frozen),originalSmallCheckerSHA256=sha(small),mediumCheckerInitialSHA256=next(x['sha256'] for x in load(R/'candidate-frozen.json')['files'] if x['path']==str(K/'checker_medium.py')),mediumCheckerFinalSHA256=sha(K/'checker_medium.py'),sourceFreezeSHA256=sha(C/'medium-source-freeze.json'),comparisons=len(pre['checks'])+len(load(R/'candidate-frozen.json')['files']),historicalCauses='UNCONFIRMED',protectedAccess=False,productionChanged=False)
assert sourceResult['mediumCheckerInitialSHA256']==sourceResult['mediumCheckerFinalSHA256']
save(R/'preservation-after.json',sourceResult)
for p in R.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
sources=[]
for prefix,base in [('review',R),('medium-workspace',C)]:
 for p in sorted(base.rglob('*')):
  if p.is_file():
   assert not p.is_symlink() and not p.is_junction() and p.name!='.env' and '__pycache__' not in p.parts
   sources.append((prefix+'/'+p.relative_to(base).as_posix(),p))
intake_fixture=Path(load(R/'fresh-binding-tests.json')['fixture'])
for p in sorted(intake_fixture.rglob('*')):
 if p.is_file():sources.append(('intake-negative-fixture/'+p.relative_to(intake_fixture).as_posix(),p))
for folder in ('stage6-checker-integration-20260922','stage6-small-combined-20260922'):
 for name in ('archive-verification.json','acceptance-seal.json','REPORT.md'):
  p=R.parent/folder/name;sources.append(('references/'+folder+'/'+name,p))
sources.append(('review/REPORT.md',R/'REPORT.md'));members=len(sources)+1
report=f'''# Stage 6 medium sacrificial attempt

**INCONCLUSIVE — required capacity telemetry is incomplete.**

One live attempt was executed. No retry, checker patch during execution, deadline change, protected VM access, large-data hashing or production change occurred. Preparation passed **162/162** checks: 114 existing regressions, 43 medium declaration/rule checks and 5 fresh-intake checks. Native binaries, writer/finalizer and monitor were unchanged.

All observed correctness checks passed: 64 probes, 132 complete canonical process instances, 264 authoritative records, 15 durable/hash-verified segments, no gaps/duplicates/overlaps/missing segments, no lost authority, no deadline violations, healthy heartbeat and complete cleanup. The medium checker returned EVIDENCE_VALIDATED_PENDING_ARCHIVE, not overall medium acceptance.

The unchanged writer does not persist per-segment flush samples, individual hash durations, backpressure-event counts or continuous queue time series. Therefore the required p95 flush, maximum individual hash duration and backpressure-event count are **NOT RECORDED**. Aggregate time/maxima cannot establish those values. This is incomplete measurement coverage, not evidence of a failed durability mechanism or a confirmed historical delay cause. No MEDIUM_VALIDATED acceptance seal is issued.

## Mandatory report

| # | Item | Actual result |
|---|---|---|
| 1 | Run ID | `{root.name}` |
| 2 | Workload | Frozen declaration: 16 idle + 16 sequential churn + 32 overlap in four batches of eight; one direct worker; all observed helpers/observer |
| 3 | Input/data size | No payload dataset; synthetic lifecycle activity only. Authoritative output {metric['authoritativeBytes']:,} bytes; no 59.7 GB hashing |
| 4 | Elapsed workload | {metric['workload']['elapsedSeconds']:.7f} s, first probe launch request to final probe reconciliation, monotonic QPC |
| 5 | Campaign duration | {duration:.6f} s from launcher creation to final independent host inspection, including UAC, observer startup/closure and analysis; archive preparation follows separately. Writer lifetime {metric['writerWindowSeconds']:.7f} s |
| 6 | Authoritative records | 264 |
| 7 | Records/sec | {metric['recordRateWriterWindow']:.6f} over the full writer window; not maximum sustainable producer throughput |
| 8 | Persisted run evidence | {metric['currentEvidenceBytes']:,} bytes including intake manifest at post-run measurement; authoritative bytes {metric['authoritativeBytes']:,} |
| 9 | Segments | 15 |
| 10 | Segment sizes | {metric['segmentSizeMin']:,}–{metric['segmentSizeMax']:,} bytes; mean {metric['segmentSizeMean']:.3f}; target unchanged 8,192 bytes |
| 11 | First sequence | 1 |
| 12 | Last sequence | 264 |
| 13 | Gaps | 0 |
| 14 | Duplicate sequences | 0 |
| 15 | Overlaps | 0 |
| 16 | Missing segments | 0 |
| 17 | Durable segments | 15 |
| 18 | Segment hashes | PASS, all bytes independently reopened and verified |
| 19 | Manifest | Component manifest/seal and fresh intake PASS; global medium acceptance NOT SEALED |
| 20 | Writer capacity | 65,536 items / 67,108,864 bytes, unchanged |
| 21 | Writer high-water | {metric['queueItemsHighWater']} items / {metric['queueBytesHighWater']:,} bytes |
| 22 | Finalizer capacity | 2 pending/in-service segments, unchanged |
| 23 | Finalizer high-water | 2 |
| 24 | Maximum utilization | Finalizer 100%; writer items {metric['queueItemsUtilizationPercent']:.6f}%, bytes {metric['queueBytesUtilizationPercent']:.6f}% |
| 25 | Backpressure events | NOT RECORDED; accumulated backpressure time {metric['backpressureSeconds']:.7f} s. No count inferred from elapsed time |
| 26 | Rejected authoritative admissions | 0 |
| 27 | Average durable flush | {metric['averageFlushSeconds']:.9f} s, recorded total / 15 completed segments |
| 28 | p95 durable flush | NOT RECORDED; cannot reconstruct from aggregate/max |
| 29 | Maximum durable flush | {metric['maxFlushSeconds']:.7f} s |
| 30 | Average segment hash | {metric['averageHashSeconds']:.9f} s, recorded total / 15 segments |
| 31 | Maximum segment hash | NOT RECORDED |
| 32 | Kernel START | 132 |
| 33 | Kernel STOP | 132 |
| 34 | Canonical identities | 132 |
| 35 | False unique matches | 0 |
| 36 | Authoritative ambiguity | 0 |
| 37 | Direct creator captures | 65 (64 probes + worker) |
| 38 | Tracer helper verifications | 2; infrastructure application observer separately verified |
| 39 | Qualified post-exit helpers | 64, explicitly distinct from creator/tracer images. Previous small-run 16 remain historical, not rewritten |
| 40 | Missing mandatory evidence | 0 |
| 41 | Contradictions | 0 |
| 42 | Native PE entries | 65 |
| 43 | CIM unique | 0 |
| 44 | CIM ambiguous | 258 |
| 45 | CIM unmatched | 1 |
| 46 | Maximum heartbeat | {metric['maxHeartbeat']:.7f} s; maximum measured age {metric['maxHeartbeatAge']:.7f} s; unchanged threshold <10 s |
| 47 | Slow heartbeat warnings | Separate warning counter NOT RECORDED; all observed intervals/ages below hard threshold |
| 48 | Slow probe warnings | 0 |
| 49 | Maximum probe lifetime | {metric['workload']['maxProbeSeconds']:.7f} s from kernel creation/exit FILETIME |
| 50 | Hard deadline violations | 0; 13.6 s hard / 15 s independent observer unchanged |
| 51 | Application observer | Healthy collection/finalization, exit 0; sampler NOT APPLICABLE because qualified process-only pipeline does not launch one |
| 52 | Tracer | Healthy, no kernel loss/error, exit 0 |
| 53 | Writer | No fault, all 264 attempted/accepted/written, threads exited |
| 54 | Finalizer | Complete, bounded, all 15 manifested; 193 records progressed while finalizing |
| 55 | Checker | EVIDENCE_VALIDATED_PENDING_ARCHIVE; no manual override, not full measurement acceptance |
| 56 | Version | `stage6-checker-input-v3`, `stage6-medium-combined-v1`, `stage6-medium-declaration-v1`; kernel contract unchanged |
| 57 | Queues | Empty/reconciled, complete secondary persistence |
| 58 | Trace finalization | PASS; zero diagnostic trace sessions after exit |
| 59 | Cleanup | PASS: launcher reports worker, observer and tracer exited 0; final host inventory zero matching processes; all 132 identities reconciled |
| 60 | Archive members | {members}; see independent archive-verification.json |
| 61 | Archive verification | Complete only with accompanying hash-verified receipt; failed/inconclusive disposition is preserved, not promoted by archive success |
| 62 | Frozen checker hashes | Initial/final identical `{sourceResult['originalFrozenSHA256']}` |
| 63 | Candidate hashes | Validated small checker unchanged `{sourceResult['originalSmallCheckerSHA256']}`. Medium pre-run/final identical `{sourceResult['mediumCheckerFinalSHA256']}` |
| 64 | Protected VM access | NONE; no protected VM/configuration file read, hashing or VirtualBox invocation |
| 65 | Production change | NONE |
| 66 | Historical 21/1 | UNCHANGED; new 258/1 is a separate run |
| 67 | Historical causes | UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED |
| 68 | 59.7 GB justified | NO; do not extrapolate this finite lifecycle run to large protected-collector readiness |
| 69 | Next proposed gate | Review minimal TEST writer telemetry to record immutable per-segment flush/hash durations and backpressure count, validate it offline/small, then separately authorize any new medium attempt. No implementation or retry undertaken here |
| 70 | Final status | INCONCLUSIVE |

## Scale and boundedness

Against the validated small run, direct probes increased 4x and measured probe-work duration increased from {metric['smallCalibration']['elapsedSeconds']:.7f} to {metric['workload']['elapsedSeconds']:.7f} s ({metric['durationScale']:.3f}x). Segments increased from 4 to 15. The finalizer reached its two-credit bound and completed with no rejected admissions. These observations support correctness/bounded operation for this finite attempt; they do not prove long-duration rate stability or omitted queue-time-series measurements. No actual PID reuse occurred; existing rejection fixtures do not count as live reuse.

Observed writer-window rates: {metric['byteRateWriterWindow']:.3f} authoritative bytes/s and {metric['segmentsPerMinuteWriterWindow']:.3f} segments/minute. Those include startup/UAC/closure waits and are not isolated finalizer-service throughput. Maximum active append was {metric['maxAppendSeconds']:.7f} s; append total {metric['appendSeconds']:.7f} s. Full measured aggregates and explicit unavailable fields are in metrics.json.

## Exact preparation changes / preservation

`changes.json`, `preparation-changes.json`, source diffs and candidate-frozen.json identify every copied/new artifact and hash. Changed only the new copy's launcher DLL path, worker workload selection, declaration-aware combined adapter and versioned input schema. Added separate fresh-binding/medium checker/analyzer support. Original frozen checker, original small checker and all native runtime/monitor/writer binaries remained unchanged. No changes occurred after the medium source freeze. {sourceResult['comparisons']} preservation comparisons passed.

Commands (Python uses the bundled interpreter with -B): prepare.py; read-only host_preflight.ps1; install.py; validate_preparation.py (114+43); freeze.py (5 binding checks); final preflight; qualified_launch.ps1 -Run {root.name}; one kernel UAC then one application-observer UAC; analyze_medium.py; final host inventory; evaluate.py; metrics.py; report_archive.py. Exact command outputs are preserved by their JSON result files and the task tool transcript. No calibration rerun or second medium attempt.

The checker remains separate and does not replace either prior candidate. Rollback is to stop selecting the new medium TEST workspace; no production files or configuration require restoration. Preserve all evidence and the unsuccessful overall disposition. No cleanup deletion is required.

STOP. No large validation, protected baseline capture, VM activity or production operation is authorized by this result.
'''
with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report);f.flush();os.fsync(f.fileno())
rows=[dict(name=n,source=str(p),bytes=p.stat().st_size,sha256=sha(p)) for n,p in sources]
assert len({x['name'] for x in rows})==len(rows) and not A.exists();A.mkdir()
save(A/'manifest.json',dict(schema='stage6-medium-evidence-archive-v1',runId=root.name,status='INCONCLUSIVE',accepted=False,files=rows))
with (A/'evidence.zip').open('xb') as stream:
 with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for x in rows:z.write(x['source'],x['name'])
  z.write(A/'manifest.json','manifest.json')
 stream.flush();os.fsync(stream.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist()))==members and z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for x in rows:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']==sha(x['source'])
fb.verify_intake(C)
for x in pre['checks']+load(R/'candidate-frozen.json')['files']:assert sha(x['path'])==x['sha256']
receipt=dict(status='PASS',archive=str(A/'evidence.zip'),archiveBytes=(A/'evidence.zip').stat().st_size,membersVerified=members,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
disposition=dict(status='INCONCLUSIVE',accepted=False,reason='Required medium capacity telemetry not recorded by unchanged writer; no failure cause inferred',attempts=1,retries=0,runId=root.name,archiveSHA256=receipt['archiveSHA256'],reportSHA256=receipt['reportSHA256'],sourceFreezeSHA256=sha(C/'medium-source-freeze.json'),nextRunAuthorized=False)
save(R/'final-disposition.json',disposition);save(A/'final-disposition.json',disposition)
assert sha(R/'archive-verification.json')==sha(A/'archive-verification.json') and sha(R/'final-disposition.json')==sha(A/'final-disposition.json')
print(json.dumps(dict(status='INCONCLUSIVE',receipt=receipt,correctness='PASS',telemetry='INCOMPLETE',run=root.name)))
