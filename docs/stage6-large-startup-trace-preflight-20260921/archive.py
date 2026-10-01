import pathlib,json,hashlib,zipfile,os
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=read(R/'preflight.json');h=read(R/'host-check.json')
assert not h['processes'] and not h['traces'] and h['traceExit']==0
for x in p['sourceChecks']:assert sha(pathlib.Path(x['path']))==x['expected']
citations='\n'.join(f"- `{x['path']}:{x['line']}` — `{x['text'].strip()}`" for x in p['codeEvidence'])
report=f'''# Stage 6 large synthetic collector with startup tracing — preflight

**BLOCKED. No large synthetic acceptance run occurred.**

## Exact blocker

The frozen large collector and the bounded startup-trace experiment are separate validated paths. They are **not integrated**. Running the existing large launcher would start `J6BaselineTrace.exe` and ordinary `Probe` instances, not `J6StartupTrace.exe` plus the non-elevated `J6EntryObserve.exe` entry-marker controller. Therefore it would not meet the new requirement to capture startup evidence during the large monitored run.

The previous `INTERNAL_STARTUP_TRACE_VALIDATED` disposition applied only to the bounded diagnostic experiment. It did not validate the large collector's trace integration. It must not be promoted into that claim.

### Source evidence

{citations}

The entry marker is supplied by the controller that creates the unchanged probe with `DEBUG_ONLY_THIS_PROCESS` and sets a hardware PE-entry breakpoint. Merely enabling the new kernel tracer does **not** add that marker to ordinary collector-launched probes.

Detailed kernel startup selection currently includes `J6Probe.exe` and its direct creation/sequence-qualified `conhost.exe` helper. It does not provide the same detailed coverage for the Python sampler/hash workers. Helpers have kernel scheduling/image/file/registry events where selected, but their own executable-entry markers and console-creation request call are not supplied by the validated debugger, which observes only its own probe. The new requirement for all monitored probe/helper processes therefore needs an explicit evidence-coverage contract; missing markers cannot be manufactured or labeled captured.

The bounded full-trace experiment retained 183,217 events for 80 probes under a 200,000-record limit. Overflow fails closed. That is only 16,783 records of remaining capacity in that experiment. The longer two-pass collector's volume is **unvalidated**, not proven to overflow. Simply increasing capacity or dropping events would not constitute validated integration.

## Preflight results actually obtained

| Check | Result |
|---|---|
| Frozen collector hashes | PASS: 84/84 |
| Frozen diagnostic hashes | PASS: 96/96 |
| Current integrated candidate hashes | PASS: 100/100 |
| Validated startup-trace hashes | PASS: 109/109 |
| Calibration evidence hash | PASS |
| Relocated dataset manifest hash | PASS |
| Synthetic inventory | 12 files; 59,665,402,098 bytes |
| Synthetic sizes / modification timestamps | Match preserved manifest |
| Synthetic root ancestry / file links | No root reparse point; files regular, single-link |
| Fresh SHA-256 of all 59.7 GB | NOT RUN after integration blocker; no fresh content-equality claim |
| Prior startup trace archive | 532 members verified |
| Prior process-call tracing archive | 262 members verified |
| Prior failed large-run archive | 196 members verified |
| Other historical archives / complete run preflight | NOT completed after integration blocker |
| D: free space | {p['DfreeBytes']:,} bytes ({p['DfreeBytes']/2**30:.2f} GiB) |
| Matching diagnostic / VirtualBox processes | 0 in read-only host inventory |
| Diagnostic trace sessions | 0 |
| UAC observer launches | 0 |
| Hash worker launches | 0 |
| New monitored hash pass #1 / #2 | NOT RUN / NOT RUN |
| New heartbeat / sampler / lifecycle acceptance | NOT RUN |
| New successful baseline manifest | NOT CREATED |

The metadata/manifest checks are not substitutes for the required fresh dataset content hashes or complete path-containment preflight. Those checks must be completed for a later authorized integrated run. No protected files were accessed to establish preservation; the task did not touch them.

## Minimum next step for review

Authorize a **narrow TEST-only collector/startup-trace integration and small sacrificial integration validation**, before reattempting the large campaign. Preserve the existing frozen candidates and all failed evidence. Proposed work is limited to:

1. A separate reviewed launch/adapter path wiring the validated read-only tracer and non-elevated entry observer to the actual collector's probe lifecycle. Preserve the real probe PID/creation identity, retained handles, health callbacks, cancellation and the existing 13.6-second launch deadline / 15-second observer semantics. A controller-process exit is not a substitute for the probe's exit.
2. Define and test trace coverage for each owned helper/sampler/hash-worker role. Preserve UNKNOWN where a supported event/marker is unavailable; any exclusion from the requested evidence needs explicit disposition. Do not add arbitrary process attachment or privileged execution authority.
3. Establish bounded, loss-detecting evidence retention suitable for the long run. Keep live state on D:, durable finalization and fail-closed overflow. The exact retention mechanism requires review/validation; this preflight does not approve or implement a redesign.
4. Exercise the composed path on a small synthetic dataset: two hash passes, startup markers, per-process attribution, sampler behavior, stale-heartbeat failure, deadline failure, trace overflow, finalization and cleanup. Verify original source hashes remain intact and quantify tracing overhead within the composed collector.
5. Only after that integration gate passes, repeat the complete large-run preflight, including all dataset SHA-256 hashes, historical archive requirements and the two established per-run UAC prompts.

Likely new/affected validation components: the large-launch adapter beside `large_launch.ps1`, probe adapter beside `large_collect.py` / `probe_timing.py`, diagnostic entry controller, startup tracer's selection/retention, and integration evidence/reconciliation. No JARVIS production/Core behavior change is indicated. No implementation was performed in this pass.

## Preservation / disposition

Only new preflight/report/archive tooling and evidence were written. All 389 checked candidate files still match their frozen hashes. Existing failure records and archives are unchanged. No process termination, VM launch, protected hashing, production change, security change or timeout/threshold change occurred.

Historical 17.195-second probe and sampler delay causes remain **UNCONFIRMED**. No common cause is established. **HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.**

This is an integration-readiness block, **not a newly reproduced collector/runtime failure**. The previously failed collector run remains failed. Protected baseline eligibility remains **UNAUTHORIZED**. No real protected-baseline execution procedure is released as ready from this blocked result.

Final status: **BLOCKED**. Stop for review.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
files=[dict(name=f.name,source=str(f),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(R.iterdir()) if f.is_file()]
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 LARGE STARTUP TRACE PREFLIGHT 20260921');A.mkdir(exist_ok=False)
raw=(json.dumps(dict(status='BLOCKED',files=files),sort_keys=True,indent=2)+'\n').encode()
with (A/'archive-manifest.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x['source'],x['name'])
 z.writestr('archive-manifest.json',raw)
with (A/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(files)+1
 for x in files:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']==sha(pathlib.Path(x['source']))
 assert z.read('archive-manifest.json')==raw
with (A/'REPORT.md').open('xb') as f:f.write((R/'REPORT.md').read_bytes());f.flush();os.fsync(f.fileno())
receipt=dict(status='HASH_VERIFIED',disposition='BLOCKED',path=str(A),members=len(files)+1,zipSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'archive-manifest.json'),reportSHA256=sha(A/'REPORT.md'))
for d in (R,A):
 with (d/'archive-verification.json').open('x') as f:json.dump(receipt,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(receipt))
