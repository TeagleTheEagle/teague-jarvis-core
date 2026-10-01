import pathlib,json,hashlib,re,datetime,difflib
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code']);pre=json.loads((R/'frozen-before.json').read_text());cal=json.loads((R/'calibration.json').read_text());repo=R.parent.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
h=read(R/'pre-live-post-cancel.json');assert not h['processes'] and not h['traces'] and h['traceExit']==0
for x in pre['candidateHashes']:assert sha(pathlib.Path(x['path']))==sha(C/x['name'])==x['expected']
app=[]
for x in pre['applicationHashes']:
 assert sha(repo/x['path'])==x['expected'];app.append(dict(path=x['path'],sha256=x['expected']))
frozen=read(R/'candidate-source.json')
for x in frozen:assert sha(C/x['name'])==x['sha256']
for x in cal['created']:
 s=(pathlib.Path(cal['source'])/x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
reg=next(C.glob('baseline-regress-*/results.json'));commands=read(reg);assert len(commands)==9 and all(x['exit']==0 for x in commands)
counts={n:int(re.search(r'Ran (\d+) tests',(reg.parent/(n+'.stderr')).read_text()).group(1)) for n in ('baseline','integration','dual','kernel','hardening')}
counts.update(probe=read(next(C.glob('probe-policy-*/result.json')))['executed'],monitor=read(C/'focused-result.json')['executed'])
queue=read(next(C.glob('queue-tests-*/result.json')));fin=read(next(C.glob('finalization-tests-*/result.json')))
run=C/'protected-4a00fe17ee1b454a9376fb5573b7b5c5'
error=(run/'launcher-error.txt').read_text();assert 'operation was canceled by the user' in error
assert not any((run/n).exists() for n in ('etw-ready.json','app-ready.json','observer-identities.json','hash-pass-1.json','baseline-manifest.json','integration-result.json'))
changed=[x for x in frozen if x['name'] not in {y['name'] for y in pre['candidateHashes']}]
summary=dict(status='BLOCKED',blocker='Windows UAC canceled native tracer launch before observers or hash worker started',run=str(run),candidate=str(C),candidateFiles=len(frozen),newFiles=changed,original73Unchanged=True,applicationHashes=app,unitCounts=counts,totalTests=sum(counts.values()),queueAssertions=queue['results']['checks'],finalizationAssertions=fin['checks'],commands=commands,largeCalibration=cal,monitoredLargeRun='NOT STARTED: UAC cancellation',dryRun1='NOT RUN',dryRun2='NOT RUN',protectedAccess=False,productionChanged=False,matchingDiagnosticProcesses=0,diagnosticTraceSessions=0,realProtectedCaptureAuthorized=False,retryPerformed=False,UACReuse='NOT SUPPORTED BY CURRENT RUN-BOUND ARCHITECTURE; retain per-run prompts')
with (R/'summary.json').open('x') as f:json.dump(summary,f,indent=2)
rows='\n'.join('| '+x['name']+' | '+x['sha256']+' |' for x in changed)
report=f'''# Protected-baseline collector integration — BLOCKED

Windows reported cancellation of the J6BaselineTrace.exe UAC launch before either observer or the monitored worker started. The single launch attempt was preserved; no reissue/retry occurred. No monitor/runtime defect is established by that cancellation. The candidate is implemented and component-tested, **not acceptance-validated**.

## Mandatory result

| # | Item | Result |
|---|---|---|
| 1 | Files changed | 11 new candidate source/config/binary files listed below; 73 existing files unchanged |
| 2 | Pre-change hashes | frozen-before.json records every original candidate hash; candidate-source.json records 84 final candidate hashes; adapter-diff.patch records the separate adapter changes |
| 3 | Old restrictions | dry_contract.source_for/inventory/validate: two fixed synthetic scenarios, exactly 12 .bin files, campaign90; dry_collect.main: actual campaign90; app_monitor and kernel_trace: monitor180 |
| 4 | New mode | Explicit protected_baseline entry points; deterministic recursive mixed-extension inventory; exact root allowlist; realProtectedAccess=false and no approved protected roots in frozen configuration |
| 5 | Read-only guarantees | Binary rb handles, final-path/volume/file-ID verification before reading, metadata checks, worker audit-hook mutation defense; no VirtualBox API or source writes in collector. This is not an OS sandbox against malicious native code |
| 6 | Containment | PASS component tests: traversal, unapproved roots, real VM/config rejection before access, duplicate paths, actual NTFS junction, hardlink and opened-handle escape |
| 7 | Measured throughput | {cal['bytesPerSecond']/1e6:.3f} MB/s using slower complete logical hash pass; cache/volume effects remain relevant |
| 8 | Estimated two-pass duration | {cal['conservativeTwoPassSeconds']:.3f}s for 59,665,402,098 bytes on measured synthetic D: workload; not a demonstrated C: duration |
| 9 | Proposed campaign | {cal['campaignSeconds']}s = ceil30(2 x estimated two-pass duration + 30s), synthetic candidate only |
| 10 | Proposed monitor | {cal['monitorSeconds']}s = campaign + 120s; both application and kernel bounds adjusted only in separate baseline adapters |
| 11 | Long-run monitor | NOT RUN; planned target {cal['longRunTargetSeconds']}s (1.5 x estimated two-pass duration) |
| 12 | Dataset | 12 synthetic files, 59,665,402,098 bytes, including 32/16/7GiB files and nested mixed extensions; no VM copy |
| 13 | Calibration hash pass 1 | PASS: {cal['passes'][0]['seconds']:.3f}s; no live-observer acceptance claimed |
| 14 | Calibration hash pass 2 | PASS: {cal['passes'][1]['seconds']:.3f}s; every SHA-256 matches; no live-observer acceptance claimed |
| 15 | Metadata | Calibration and final metadata unchanged for all 12 large dataset files; focused negative tests mutate only their own separate fixtures |
| 16 | Baseline-style manifest | Focused manifest/ordering checks passed; no large monitored baseline manifest exists |
| 17 | Failure injection | 37 new tests PASS; injected unreadable/evidence/archive/manifest/worker/observer/heartbeat/deadline failures plus real junction and source-mutation cases. No claim of live fault-injection acceptance |
| 18 | Protected-mode Dry Run #1 | NOT RUN |
| 19 | Protected-mode Dry Run #2 | NOT RUN |
| 20 | Max heartbeat | NOT MEASURED for new large mode; observers never started; historical approximately1.06s values are not reused as current evidence |
| 21 | Lifecycle reconciliation | No monitored workload started. Launcher returned failure; after-check found zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions |
| 22 | Archive | See accompanying archive-verification.json for exact count/hash; finalized preparation/failure evidence only, not successful large-run evidence |
| 23 | Cleanup | PASS for canceled launch: no diagnostic helper left running; no force termination |
| 24 | Protected VM/configuration | NOT ACCESSED |
| 25 | Production | UNCHANGED; {len(app)} application hashes verified |
| 26 | Limits | Monitored long run, finite-bound validation and two large protected-mode dry runs are outstanding; C: throughput may differ; synthetic reads may be cached; real capture/topology reconciliation is not approved by this result |
| 27 | Protected-baseline eligibility | NOT ELIGIBLE |
| 28 | Final status | BLOCKED — UAC cancellation |

## Exact test results

{json.dumps(counts,sort_keys=True)}; total {sum(counts.values())} unittest cases passed. Queue {queue['results']['checks']} assertions passed including existing collision stress; finalization {fin['checks']} assertions passed. Nine command groups returned0. Exact commands and outputs are archived. Safety thresholds remain heartbeat10s/probe13.6s/independent observer15s. No observed acceptance failure was hidden by increasing a threshold.

## Candidate additions

Candidate: `{C}`

| Added file | Final SHA-256 |
|---|---|
{rows}

No original file in the old validated candidate or either old dry-run archive was modified. Test preparation/report scripts are separate under this report directory. The build emitted one inherited C4456 variable-shadow warning; compilation and Python/PowerShell syntax checks succeeded.

## Preserved preparation failures

`pre-live.json` records a report-only preflight self-match: its inline PowerShell command contained the candidate ID and matched its own broad process filter. No observer launched. `pre_live.ps1` now records/excludes its own process explicitly. `pre-live-large-validation.json` then passed. The frozen candidate was not modified by this reporting correction.

Failed launch directory: `{run}`. Original launcher-error.txt and PREPARED state remain unmodified. Windows explicitly reported the UAC operation was canceled; neither observer readiness nor hash output exists. The post-cancellation check is `pre-live-post-cancel.json`.

## UAC reduction decision

Gate-wide elevated reuse is not supported by this architecture without a new lifecycle/control design. The native tracer binds to one root PID/creation time and output directory; Health binds run-specific observer identities; acceptance requires their shutdown and finalized streams. A persistent elevated broker would require changing those contracts. Following the owner's fallback instruction, preserve per-run diagnostic prompts. No UAC/security-policy/ACL change, persistent privileged service, broad command channel or elevated Codex session was introduced. No elevated helper remains from this canceled launch.

## Next action and rollback

When the owner is ready to approve the two diagnostic prompts, resume the first monitored synthetic large-data run in a fresh directory, preserving this cancellation. Do not count it as Dry Run #1. Recheck frozen hashes/processes/traces first. Then complete long-duration/large-data acceptance and both separately identified full dry runs under the approved stop rules. No real protected capture is eligible yet.

Rollback: retain all evidence, stop using the new candidate and select the untouched original sacrificial harness. No production/VM/ACL rollback is needed. Do not delete the approximately59.7GB synthetic dataset or historical evidence automatically.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. Historical PID9240/13340 causes and prior storage stalls remain unconfirmed; this work does not reinterpret failed historical runs.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
print(json.dumps(dict(status='BLOCKED',tests=sum(counts.values()),queue=queue['results']['checks'],finalization=fin['checks'],sourceFiles=len(frozen),original73Unchanged=True,applicationHashes=len(app))))
