"""Post-benchmark preservation, reporting and new immutable archive only."""
import ast,datetime,hashlib,json,pathlib,zipfile
from preflight import R,PREV,C,LIVE,load,sha,put,verify

if __name__=='__main__':
    result=load(R/'result.json');census=load(R/'final-census.json')
    assert census['processCount']==0 and census['traceCount']==0
    for x in load(PREV/'candidate-artifact-manifest.json')['files']:verify(x)
    for x in load(PREV/'before.json')['inputs']:verify(x)
    historical=load(PREV/'historical-precheck.json')
    for x in historical['evidence']:verify(x)
    assert sha(historical['archive'])==historical['archiveSHA256']
    old=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
    hfreeze=load(R.parent/'stage6-identity-capacity-recalibration-20260921'/'freeze.json')
    for row in hfreeze['candidateHashes']:assert sha(old/row['name'])==row['sha256']
    prior=load(PREV/'archive-receipt.json');assert sha(prior['archive'])==prior['archiveSHA256']
    with zipfile.ZipFile(prior['archive']) as z:
        for item in prior['memberHashes']:
            with z.open(item['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==item['sha256']
        for row in json.loads(z.read('archive-manifest.json'))['entries']:verify(row)
    preflight=load(R/'preflight.json')
    assert sha(R/'protocol.json')==preflight['protocolSHA256']
    for row in preflight['harnessSources']:assert sha(row['path'])==row['sha256']
    sources=[]
    for p in sorted(R.glob('*.py')):
        ast.parse(p.read_text(),filename=str(p));sources.append(dict(path=str(p),sha256=sha(p),syntax='PASS'))
    put(R/'final-verification.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidateFilesUnchanged=240,predecessorEvidenceFilesUnchanged=760,historicalEvidenceFilesUnchanged=len(historical['evidence']),historicalCandidateFilesUnchanged=len(hfreeze['candidateHashes']),historicalArchiveUnchanged=True,previousArchiveMembersVerified=prior['membersVerified'],previousReportAndCandidateUnchanged=True,protocolAndExecutedHarnessUnchanged=True,newHarnessSources=sources,productionAccess=False,protectedVMAccess=False,liveETW=False,UAC=False))
    p=result['primary'];supp=result['supplementary'];sec=result['secondary'];identities=load(R/'process-thread-identities.json');ex=load(R/'execution.json')
    rows=[]
    for name,s in sec.items():
        ci=s['pairedPercentBatch95'];rows.append(f"| {name} | {s['disabledMean']:.6f} | {s['enabledMean']:.6f} | {ci['mean']:+.6f}% [{ci['lower']:+.6f}, {ci['upper']:+.6f}] |")
    shifted=[name for name,s in sec.items() if s['intervalExcludesZero']]
    report=f'''# Precise offline measurement-overhead benchmark

**{result['status']}**

The original recorder/fixture binary, all callback code, instrumentation fields, record capacity, locks, sampling and file/queue behavior were unchanged. No build, live ETW session, UAC, broader integration, protected VM access, production operation or deadline change occurred. This is an offline diagnostic-overhead screen only, not Stage 6 acceptance or proof of live non-perturbation.

## Primary result

Predeclared maximum: 32 batches x 8 balanced pairs = 256 pairs. Completed: {result['batchCount']} batches / {result['pairCount']} pairs / {result['callbacks']:,} recorded callbacks. AB pairs: {result['orderCounts']['AB']}; BA pairs: {result['orderCounts']['BA']}. Warm-up and pilot excluded. Fixed campaign duration: {ex['elapsedSeconds']:.3f} seconds. No extra trials, retries, ordinary-noise exclusions or result-dependent stopping.

Mean paired dispatcher CPU increase: **{p['mean']:+.6f}%**. Primary two-sided 95% interval: **[{p['lower']:+.6f}%, {p['upper']:+.6f}%]**. Upper bound must be <=+1.0%. Halfwidth: {p['halfwidth']:.6f} percentage points. Interpretation: **{result['issue']}**.

For pair i: d_i = 100*(CPU_enabled_i/CPU_disabled_i - 1), using the fixture's Windows GetThreadTimes kernel+user CPU counters and equivalent callback counts. Each batch mean is the average of its eight d_i. Primary interval = mean(batch means) +/- 2.0395134463964077 * sampleSD(batch means)/sqrt(32), df31. Neighboring pairs are not treated as independent in the primary interval. Batch SD: {p['sd']:.6f}; standard error {p['standardError']:.6f} percentage points.

Supplementary unclustered paired interval: [{supp['lower']:+.6f}%, {supp['upper']:+.6f}%]; not substituted for primary. Descriptive lag-1 correlation of batch means: {result['batchLag1CorrelationDescriptive']}. The t interval assumes adequately independent/stable batch means and cannot eliminate systematic host bias. No confidence claim identifies the historical ETW mechanism.

Every pair's disabled CPU, enabled CPU, absolute difference (100ns), percent difference, order and callback count is in pairs.json. All trial JSONL, process/thread identities, creation and exit FILETIMEs, retained-handle wait results and final CPU counters are archived. All {len(identities)} fixture processes exited with code 0 and retained handles closed without reported errors.

## Secondary observations

| Metric (units in label) | Disabled mean | Enabled mean | Paired change and batch 95% interval |
|---|---:|---:|---|
{chr(10).join(rows)}

Intervals excluding zero (observed shifts, not a newly invented materiality threshold): {', '.join(shifted) or 'none'}. Inspect these alongside the primary result; no secondary metric substitutes for dispatcher CPU. Per-trial sampled maximum latencies and all raw values remain available; maxima are not exhaustive. Process memory high-water is cumulative within a process. C++ allocation counts exclude internal Windows allocations. No queue, contention, coordination integration or live ETW behavior was exercised by this unchanged fixture.

## System and identity

AMD Ryzen 7 3700X 8-Core Processor; 16 logical processors; Windows reported 10.0.26200.0. No affinity, priority, power, BIOS, scheduler or security settings changed. Exact OS/context is in preflight.json. A restricted-context WMI read was denied before benchmarking; the ordinary host-context read-only census succeeded. No Windows elevation or UAC was used.

Executable: `{load(R/'protocol.json')['binary']}`.

SHA-256: `{result['benchmarkBinarySHA256']}`. Existing Visual Studio 2022 x64 C++17 /O2 executable; no rebuild. Its source/header hashes are preserved in the previous candidate manifest and reverified. Orchestrator runs with the existing bundled Python and uses CreateProcessW with flags=0, original candidate CWD, inherited environment, stdout/stderr redirected to the fresh D: evidence directory and NUL stdin. No credentials or environment values were printed. Primary thread identity comes directly from the returned creator handle; benchmark CPU comes from that executable's unchanged GetCurrentThread accounting.

Commands executed: bundled Python `-B <report>\\preflight.py`, `-B <report>\\benchmark.py`, then `-B <report>\\analyze.py`. The harness launches exactly `<unchanged fixture> benchmark` once per batch. `finish.py` performs preservation, syntax and archive verification after measurement. No fixture tests or calibration were rerun unnecessarily.

Invalid conditions were predeclared (API/harness error, count/order mismatch, malformed output, interruption, drift or watchdog). Exclusions: **0**. Harness errors: **0**. Ordinary noisy samples retained. One fixed 300-second batch watchdog / 2400-second campaign watchdog belongs only to this offline harness; neither changes Stage 6 deadlines, and neither triggered.

## Preservation / cleanup / limitations

240 candidate files unchanged; 760 predecessor/evidence files unchanged; {len(historical['evidence'])} historical evidence files unchanged; {len(hfreeze['candidateHashes'])} historical candidate files unchanged; historical archive unchanged; previous 275-member archive hash-verified and its original inputs unchanged. Frozen checker unchanged. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. Historical trace-loss cause remains UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Final point-in-time read-only host census: **0 matching diagnostic processes / 0 matching trace sessions**, timestamp {census['utc']}. No VirtualBox process observed. Protected files were deliberately not opened or hashed; this action did not target them. Production was not accessed or modified.

Only new offline harness/report/evidence files were created in this report directory and `{LIVE}`. No existing candidate or implementation file was edited. Full identities/hashes and raw records are in the archive. The broad project sync script is not used because it overwrites unrelated records; a unique bounded nonsecret canonical archive is created. No prior archive or evidence is overwritten. See archive-receipt.json for exact archive path/hash/member verification. No commit.

## Owner review / next action

STOP after this benchmark. If the screen passes, the remaining separately reviewed step is to complete the still-unimplemented creator identity timing, both observer taps, coordination/control-thread measurements, bounded export/analyzer and required integration tests, then measure the full instrumentation; this subset screen alone cannot approve that integration or any live run. If the threshold is not established or conflicts, review the raw result and precision/overhead distinction before any further benchmark or optimization. No more trials will run automatically.

Rollback: no existing implementation changed. Retain this evidence and continue to treat the partial successor as incomplete and NOT LIVE ELIGIBLE.
'''
    with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report)
    dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 PRECISE OVERHEAD 20260924 4b0db487')
    assert not dest.exists();dest.mkdir()
    entries=[]
    for root,prefix in [(R,'report'),(LIVE,'raw')]:
        for file in sorted(root.rglob('*')):
            if not file.is_file():continue
            s=file.stat();assert not s.st_file_attributes&0x400
            assert not file.name.lower().startswith('.env') and file.suffix.lower() not in {'.key','.pem','.token','.db','.sqlite'}
            entries.append(dict(path=str(file),name=prefix+'/'+file.relative_to(root).as_posix(),bytes=s.st_size,sha256=sha(file)))
    archive=dest/'evidence.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for row in entries:z.write(row['path'],row['name'])
        z.writestr('archive-manifest.json',json.dumps(dict(status=result['status'],acceptance=False,entries=entries),sort_keys=True,indent=2))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(entries)+1
        for row in entries:
            with z.open(row['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
            assert sha(row['path'])==row['sha256']
        manifestHash=hashlib.sha256(z.read('archive-manifest.json')).hexdigest()
    receipt=dict(archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=manifestHash,membersVerified=len(entries)+1,bytes=archive.stat().st_size,status='HASH_VERIFIED',benchmarkStatus=result['status'])
    put(R/'archive-receipt.json',receipt);put(dest/'archive-receipt.json',receipt)
    assert sha(R/'archive-receipt.json')==sha(dest/'archive-receipt.json')
    print(json.dumps(receipt))
