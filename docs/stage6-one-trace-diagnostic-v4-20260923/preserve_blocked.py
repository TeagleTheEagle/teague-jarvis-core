"""Preserve pre-launch failure only. No run preparation, observers or retry."""
import pathlib,json,hashlib,os,sys,zipfile,datetime
R=pathlib.Path(r'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-one-trace-diagnostic-v4-20260923')
O=R.parent/'stage6-workspace-binding-v4-20260923'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code')
DEST=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TRACE DIAGNOSTIC V4 PREFLIGHT BLOCKED 20260923')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
assert (R/'preflight-failure.json').exists() and not (R/'preflight.json').exists()
rows=read(C/'small-source-v3.json')
assert sha(C/'small-source-v3.json')=='d2f6738f5d7c3f22fe361f6cb1da174f630d8e150574009b59825d88321ed4d7'
for x in rows:
 p=C/x['name'];assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
inputs=read(O/'before.json')['inputs']
for x in inputs:
 p=pathlib.Path(x['path']);s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
dataset=[x for x in rows if pathlib.PureWindowsPath(x['name']).parts[0]=='small-synthetic']
assert len(dataset)==12 and sum(x['bytes'] for x in dataset)==786432
write(R/'read-only-diagnosis.json',dict(classification='PREFLIGHT_HELPER_PATH_SEPARATOR_DEFECT',causeConfirmed=True,failingFile=str(R/'preflight.py'),filterLine=40,assertionLine=41,observedNames='Windows backslash-separated manifest names',filterUsed="name.startswith('small-synthetic/')",filterMatches=0,actualDatasetFiles=12,actualDatasetBytes=786432,dataset=dataset,candidateDefectEstablished=False,preflightRetried=False,implementationChanged=False,liveLaunches=0,UACRequests=0,freshRunCreated=False,bindingRecordCreated=False))
sys.path.insert(0,str(C));import workspace_binding_v4 as b;import failure_preserve_v4 as fp
b.runtime_policy()
census=fp.host_census(C);write(R/'final-census.json',census)
assert census['available'] and census['processes']==[] and census['traces']==[] and census['unknown']==[]
write(R/'preservation.json',dict(candidateFiles=229,candidateManifestSHA256=sha(C/'small-source-v3.json'),predecessorRecordedInputs=len(inputs),frozenCheckerSHA256=sha(C/'medium-checker/frozen_reference.py'),runtimeComponents=1055,sourceDrift=0,liveDiagnosticProcesses=0,traceSessions=0,VirtualBoxProcesses=0,protectedAccess=False,productionChange=False,priorArchiveMembersVerifiedByPreflight=2207,liveLaunches=0,UACRequests=0))
fields=['final EventsLost','first loss QPC/time','final loss increment QPC/time','minimum sampled FreeBuffers','maximum NumberOfBuffers','callback receive rate around first loss','callback completion rate around first loss','consumer-thread CPU around first loss','delivery lag before/during/after loss','slow metadata spans within +/-2 seconds','slow lock/guard spans within +/-2 seconds','slow writer spans within +/-2 seconds','writer queue high-water near loss','durable/persistence progress near loss','whether buffer pressure preceded loss','whether callback progress stalled before loss','whether consumer CPU changed','correlated authority/detail loss timing']
causes=['TRANSIENT_ETW_BUFFER_EXHAUSTION','CONSUMER_CALLBACK_STALL','METADATA_OR_LOCK_STALL','EVENT_RATE_BURST','WRITER_BACKPRESSURE','DISK_PERSISTENCE_PRESSURE','CPU_SCHEDULING_DELAY','OTHER_EVIDENCED_CAUSE']
write(R/'telemetry-findings.json',dict(runStatus='BLOCKED',diagnosisStatus='TRACE_LOSS_CAUSE_UNCONFIRMED',runOccurred=False,sessions={s:{k:'NOT OBSERVED — observer not launched' for k in fields} for s in ('authority','detail')},classifications={k:'UNCONFIRMED' for k in causes},historicalAuthorityEventsLost=13,historicalDetailEventsLost=120281,historicalCause='UNCONFIRMED'))
report='''# One-run trace diagnostic v4 — BLOCKED before launch

Primary status: BLOCKED
Diagnosis status: TRACE_LOSS_CAUSE_UNCONFIRMED

The newly authored preflight helper failed its dataset assertion at line 41. At line 40 it selected manifest names using `startswith('small-synthetic/')`. The unchanged Windows manifest stores `small-synthetic\\00.bin` through `small-synthetic\\11.bin`; this incorrect filter selected zero entries. Read-only inspection confirms all 12 correct files and 786,432 bytes remain present and hash-valid. This is a defect in this action's new preflight helper, not an established defect in the frozen candidate, dataset or binding implementation.

Before the assertion, verification completed for the 2,207-member prior offline archive, predecessor/frozen preservation records, the 229-file candidate, approved runtime identities and zero-process/zero-trace host census. No fresh run directory or binding was created. No observer, collector, hash worker, UAC prompt or live diagnostic was started. No retry or correction was performed.

Final read-only checks: all 229 candidate hashes and 223 predecessor input records unchanged; all 1,055 shared runtime components reverified; frozen checker unchanged. Final census: zero matching diagnostic processes, zero trace sessions, zero VirtualBox processes, zero unknown census entries. Production and protected VM/configuration were not accessed or changed. No candidate or historical evidence file was modified.

No new telemetry exists. telemetry-findings.json explicitly marks all 18 requested measurements unavailable for both sessions; it does not substitute false zeros. All eight proposed trace-loss causes remain UNCONFIRMED. Historical authority loss 13 and detail loss 120,281 remain unchanged. Historical 21 AMBIGUOUS / 1 UNMATCHED remain unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

The first failure, exact failed helper and traceback, read-only diagnosis, hashes and censuses are preserved. This is NON-ACCEPTANCE evidence; no success finalizer or seal was invoked.

Proposed next action for owner review: correct only the new preflight helper's dataset-name selection using validated Windows path components (or the exact 12 manifest names), add a focused separator fixture, then seek/confirm authorization to resume preflight for the still-unexecuted single live diagnostic. Do not change the candidate manifest, dataset, binding rules, deadlines, ETW settings or checker. No such correction is implemented here.

Archive verification is recorded in the adjacent archive-receipt.json. STOPPED FOR OWNER REVIEW.
'''
with (R/'REPORT.md').open('x') as f:f.write(report)
files=[]
for p in sorted(R.iterdir()):
 if p.is_file():files.append(dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)))
DEST.mkdir(parents=True,exist_ok=False)
write(DEST/'manifest.json',dict(kind='NON-ACCEPTANCE PREFLIGHT FAILURE',files=files))
a=DEST/'blocked-preflight.zip'
with zipfile.ZipFile(a,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(R/x['path'],x['path'])
with a.open('r+b') as f:os.fsync(f.fileno())
with zipfile.ZipFile(a) as z:
 assert len(z.namelist())==len(files)==len(set(z.namelist()))
 for x in files:
  with z.open(x['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
  assert sha(R/x['path'])==x['sha256']
receipt=dict(status='VERIFIED',archive=str(a),archiveSHA256=sha(a),manifestSHA256=sha(DEST/'manifest.json'),members=len(files),acceptance_seal=False,liveRun=False)
write(DEST/'archive-receipt.json',receipt);write(R/'archive-receipt.json',receipt)
print(json.dumps(receipt,indent=2))
