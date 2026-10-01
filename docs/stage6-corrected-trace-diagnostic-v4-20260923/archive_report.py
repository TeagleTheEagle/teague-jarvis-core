"""Finalize report and copy already-stopped failure evidence. Not a success finalizer."""
import pathlib,json,hashlib,zipfile,os
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-path-filter-fix-20260923'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
pre=read(P/'preflight.json');C=pathlib.Path(pre['candidate']);root=pathlib.Path(pre['root']);pres=pathlib.Path(pre['preservationDestination'])/('FAILURE-EVIDENCE-'+root.name)
summary=read(R/'run-summary.json');tele=read(R/'telemetry-analysis.json');handoff=read(R/'terminal-rejection.json')
classes={k:'UNCONFIRMED as a cause of historical trace loss; no loss reproduced in this attempt' for k in ['TRANSIENT_ETW_BUFFER_EXHAUSTION','CONSUMER_CALLBACK_STALL','METADATA_OR_LOCK_STALL','EVENT_RATE_BURST','WRITER_BACKPRESSURE','DISK_PERSISTENCE_PRESSURE','CPU_SCHEDULING_DELAY','OTHER_EVIDENCED_CAUSE']}
write(R/'causal-classification.json',dict(classifications=classes,currentHandoffPredicateFailure='PROVEN by recorded QPC ordering; separate from historical ETW-loss causation',historicalTraceLossCause='UNCONFIRMED'))
a=tele['sessions']['authority'];d=tele['sessions']['detail']
table=[]
metrics=[('Final EventsLost',a['finalEventsLost'],d['finalEventsLost']),('Final real-time/log buffer loss','0 / 0','0 / 0'),('Valid / total query samples',f"{a['validQuerySamples']} / {a['sampleCount']}",f"{d['validQuerySamples']} / {d['sampleCount']}"),('Sample span (seconds)',round(a['captureSampleSpanSeconds'],6),round(d['captureSampleSpanSeconds'],6)),('Minimum sampled FreeBuffers',a['minSampledFreeBuffers'],d['minSampledFreeBuffers']),('Maximum sampled NumberOfBuffers',a['maxSampledNumberOfBuffers'],d['maxSampledNumberOfBuffers']),('Peak received callbacks/sec',round(a['wholeCaptureMaxReceivedRate'],2),round(d['wholeCaptureMaxReceivedRate'],2)),('Peak completed callbacks/sec',round(a['wholeCaptureMaxCompletedRate'],2),round(d['wholeCaptureMaxCompletedRate'],2)),('Sampled consumer CPU seconds',a['sampledConsumerCPUSeconds'],d['sampledConsumerCPUSeconds']),('Mean / maximum selected-event delivery lag, seconds',f"{a['deliveryLag']['meanSeconds']:.6f} / {a['deliveryLag']['maxSeconds']:.6f}",f"{d['deliveryLag']['meanSeconds']:.6f} / {d['deliveryLag']['maxSeconds']:.6f}"),('Writer queue peak records / bytes',f"{a['queueHighItems']} / {a['queueHighBytes']}",f"{d['queueHighItems']} / {d['queueHighBytes']}"),('Final persisted records / bytes',f"{a['finalQueue']['persisted']} / {a['finalQueue']['persistedBytes']}",f"{d['finalQueue']['persisted']} / {d['finalQueue']['persistedBytes']}"),('Final queued records / bytes / pending segments','0 / 0 / 0','0 / 0 / 0'),('Finalizations',a['finalQueue']['finalizations'],d['finalQueue']['finalizations'])]
table=['| Measurement (whole capture) | Authority | Detail |','|---|---:|---:|']+[f'| {label} | {x} | {y} |' for label,x,y in metrics]
report=f'''# Single corrected trace diagnostic — rejected run

TRACE_DIAGNOSTIC_RUN_FAILED

NO_TRACE_LOSS_REPRODUCED

Run: `{root.name}`. Exactly one normal small synthetic run; no retry. Three configured sequential observer prompts reached readiness. No unexpected fourth observer path is present in the fixed launcher. No candidate/settings/deadline correction was made.

## Outcome and first failure

The collector returned exit 0, both hash passes matched all 12 files / 786,432 bytes, source metadata remained unchanged, and Phase A was produced. Acceptance failed at the independent terminal receipt: terminal-failure-v3.json reports `handoff`; the launcher then recorded `Authority terminal failure` and permanent rejection. The authority observer exited 95, detailed observer 0, application observer 0. No success finalizer or acceptance seal ran.

The exact console helper was PID 17376, creation FILETIME 134346269041455542, kernel sequence 64543, parent collector PID 22000 / creation 134346269039786128 / sequence 64542. This is an instance-bound comparison, not PID-only inference.

At QPC frequency 10,000,000:

- Local handle closed: 4597138042977.
- Authority retained handle: 4597138960704 (**91.7727 ms later**).
- Authority image capture began: 4597138960727 (**91.7750 ms later**).
- Kernel START timestamp: 4597117305220; START callback: 4597138959870 (**2.165465 s delivery delay**).

The unchanged terminal_receipt_v3.hpp:54 requires both retained-handle acquisition and image-capture start BEFORE localCloseQpc. The recorded ordering fails that predicate. This establishes the immediate rejection condition, not the underlying cause of historical EventsLost or the reason Windows delivered this event later. No correction or contract amendment is implemented.

## Trace-loss findings

Neither session recorded a nonzero EventsLost sample or final counter. First loss time, last increment time, before/during/after-loss rates, near-loss CPU/slow spans/lag/queue/persistence and correlated loss timing are therefore **NOT APPLICABLE**, not fabricated zeros. Buffer pressure preceding loss and callback stalling before loss cannot be established because no loss occurred. Whole-capture observations follow:

{chr(10).join(table)}

Authority: 38 sampled received/completed callbacks, 28 selected records. Detail: last sample 1,634,423 received / 1,634,422 completed, 197,158 selected records. These are sampling snapshots; the one-callback difference is an in-flight observation, not evidence of an event being lost. Final selected-record persistence was complete with empty queues. Supporting CIM queue: 40 enqueued, persisted and removed; zero remaining and no reported tap error/overflow.

Both telemetry sidecars passed the existing offline diagnostic-format verifier with zero telemetry errors/overflow. The final detailed query returned status 4201 after stop with EventsLost=null; that unavailable sample was excluded from FreeBuffers minima and was not treated as a healthy zero counter. The independently recorded final ETW counters were zero. Authority's sampled CPU counter delta was zero; accounting granularity means this must not be interpreted as proof of zero CPU work.

Detailed slow spans across the capture: metadata max 491.0964 ms; serialization 491.1223 ms; guard hold 491.1312 ms; callback 491.1386 ms; guard wait 696.0165 ms; flush 341.9011 ms; rotation 345.6173 ms; write 27.0859 ms. Nested spans overlap and their durations must not be added as independent time. Authority's longest recorded slow span was flush 70.3032 ms. None is a measured near-loss correlation.

The detail session dynamically reached 45 buffers; requested settings were unchanged (64 KiB, requested min 4/max 64, 1-second flush; Windows reported effective minimum 32). No tuning occurred. Full provider/mode/keyword values and all requested statistics are preserved in telemetry-analysis.json and the raw sidecars.

All eight candidate historical loss mechanisms remain UNCONFIRMED as causes. Metadata/guard delays, callback-rate bursts and writer queue growth are observed, but this run provides no loss transition to connect them causally. Historical authority loss 13 / detailed loss 120,281 remain unchanged and unexplained. This early rejected run does not disprove historical loss or prove the complete pipeline reliable.

## Cleanup and acceptance distinction

The required terminal receipt, pre-shutdown workload census, observer tail, independent acceptance exit record and final acceptance census were not produced. The missing six acceptance artifacts are listed in run-summary.json and FAILURE-MANIFEST.json. Failure-preservation status is correctly FAILURE_EVIDENCE_PARTIAL; the actual available bytes were archived without hash mismatch.

Failure cleanup completed. The launcher reports all three observers exited; the independent failure-preserver instance census records 18/18 instances absent. Later independent host census: zero matching diagnostic processes, zero trace sessions, no VirtualBox process, no unknown census entry. These cleanup observations do not replace the missing acceptance chain.

Original cleanupEntryQpc=4597137520330; deadlineQpc=4597337520330; unchanged 20-second budget. Preserver post-archive census QPC=4597325410144, **18.7889814 seconds after cleanup entry**, within that original deadline. Nevertheless acceptance remains FAILED because the terminal handoff/receipt chain failed. No deadline reset or extension occurred.

Maximum observed heartbeat interval: 1.2409768 seconds (<10). Both small hash passes completed in 0.0380522 and 0.0387835 seconds. These successes do not override rejection.

## Preservation

The NON-ACCEPTANCE failure archive independently reopened and verified **92 members**, including 90 original run evidence files and both diagnostic sidecars. Archive SHA-256: `ff11dc295eff89d39e1c6ac0315b3f2e8bd81030f21381d2ef59afb513d5e509`. Failure manifest SHA-256: `d99f038e566ba8ba1697d9082a44d382b80a6b8ce492e39113c933d5116d84b2`.

All 229 candidate hashes and pre-run modification times unchanged; binding hash unchanged; runtime identities reverified; predecessor and frozen historical inputs unchanged. Frozen checker SHA-256: `e6fbefd3fd463c6c8e09d0e8273a81b46ee2806515cae05e7837ea905a3e69d6`. No production or protected VM/configuration access or change. No medium/large run, 59.7 GB hashing or provider call. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Canonical archive receipt is adjacent to this report. New files are limited to this run's evidence, preflight records, failure preservation, and offline report/archive tools. Candidate source was not edited. Rollback requires no source or production restoration; retain the rejected run and stop using this attempt.

## Next owner review

Review the instance-bound helper handoff ordering and its preserved timings before authorizing any correction or new attempt. No automatic retry or implementation follows this report. Stage 6 remains incomplete. STOPPED FOR OWNER REVIEW.
'''
with (R/'REPORT.md').open('x') as f:f.write(report)
files=[]
for base,label in ((R,'report'),(root,'run'),(pres,'failure-preservation')):
 for at,dirs,names in os.walk(base,followlinks=False):
  for name in dirs+names:
   p=pathlib.Path(at)/name
   if p.lstat().st_file_attributes&0x400:raise ValueError('REPARSE_IN_EVIDENCE')
  for name in names:
   if name.startswith('.env'):raise ValueError('ENV_IN_EVIDENCE')
   p=pathlib.Path(at)/name;files.append(dict(path=label+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
for name in ('preflight.json','candidate-before.json','prelaunch-census.json','preflight.py','ONE-RUN-OWNER-REVIEW.md'):
 p=P/name;files.append(dict(path='approved-preflight/'+name,source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
for x in read(C/'small-source-v3.json'):
 p=C/x['name'];assert sha(p)==x['sha256'];files.append(dict(path='candidate/'+pathlib.PureWindowsPath(x['name']).as_posix(),source=str(p),bytes=x['bytes'],sha256=x['sha256']))
p=C/'small-source-v3.json';files.append(dict(path='candidate/small-source-v3.json',source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TRACE DIAGNOSTIC V4 FAILED 20260923');dest.mkdir(parents=True,exist_ok=False)
write(dest/'manifest.json',dict(kind='REJECTED SINGLE RUN; NON-ACCEPTANCE EVIDENCE',run=root.name,files=files))
archive=dest/'rejected-trace-diagnostic.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x['source'],x['path'])
with archive.open('r+b') as f:os.fsync(f.fileno())
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(files)==len(set(z.namelist()))
 for x in files:
  with z.open(x['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
  assert sha(pathlib.Path(x['source']))==x['sha256']
for x in read(R/'run-inventory.json'):
 p=root/x['path'];s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
receipt=dict(status='VERIFIED',archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=sha(dest/'manifest.json'),members=len(files),acceptanceSeal=False,runStatus='TRACE_DIAGNOSTIC_RUN_FAILED',diagnosis='NO_TRACE_LOSS_REPRODUCED')
write(dest/'archive-receipt.json',receipt);write(R/'archive-receipt.json',receipt)
print(json.dumps(receipt,indent=2))
