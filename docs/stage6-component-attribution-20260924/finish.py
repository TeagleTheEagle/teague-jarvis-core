"""Preserve stopped offline attribution experiment. Does not launch fixtures."""
import json,pathlib,statistics,math,datetime,hashlib,zipfile,ast
from prepare import R,W,C,P,OLD,load,sha,put,verify
def ci(values):
 means=[statistics.mean(values[i:i+5]) for i in range(0,40,5)];m=statistics.mean(means);h=2.364624251*statistics.stdev(means)/math.sqrt(8)
 return dict(mean=m,halfwidth=h,lower=m-h,upper=m+h,n=8,groups=means)
if __name__=='__main__':
 ref=load(R/'reference-result.json');assert ref['status']=='MORE_PROFILING_REQUIRED'
 assert not (W/'raw'/'attribution.jsonl').exists()
 census=load(R/'final-census.json');assert census['processCount']==census['traceCount']==0
 before=load(R/'before.json')
 for row in before['preserved']:verify(row)
 prior=before['archive'];assert sha(prior['archive'])==prior['archiveSHA256']
 with zipfile.ZipFile(prior['archive']) as z:
  for row in json.loads(z.read('archive-manifest.json'))['entries']:
   with z.open(row['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
  assert hashlib.sha256(z.read('archive-manifest.json')).hexdigest()==prior['manifestSHA256']
 for row in load(R/'experiment-source-freeze.json'):assert sha(row['path'])==row['sha256']
 assert sha(W/'loss_measurement_v3.hpp')==sha(C/'loss_measurement_v3.hpp')
 historical=load(OLD/'historical-precheck.json');assert sha(historical['archive'])==historical['archiveSHA256']
 histfreeze=load(R.parent/'stage6-identity-capacity-recalibration-20260921'/'freeze.json')
 histroot=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
 for row in histfreeze['candidateHashes']:assert sha(histroot/row['name'])==row['sha256']
 raw=[json.loads(s) for s in (W/'raw'/'reference.jsonl').read_text().splitlines()];assert len(raw)==80
 pairs=[]
 for b in range(40):
  two=raw[b*2:b*2+2];a=next(x for x in two if x['variant']==0);f=next(x for x in two if x['variant']==1)
  pairs.append(dict(pair=b,order='AB' if two[0]['variant']==0 else 'BA',baseline=a,full=f,cpuPercent=100*(f['dispatcherCpu100ns']/a['dispatcherCpu100ns']-1),baselineNs=a['dispatcherCpu100ns']*100/a['callbacks'],fullNs=f['dispatcherCpu100ns']*100/f['callbacks'],deltaNs=(f['dispatcherCpu100ns']-a['dispatcherCpu100ns'])*100/a['callbacks'],throughputPercent=100*(a['wallSeconds']/f['wallSeconds']-1)))
 put(R/'reference-pairs.json',pairs)
 summary=dict(status='MORE_PROFILING_REQUIRED',measuredPairs=40,measuredTrials=80,measuredCallbacks=80000000,warmupCallbacks=1600000,maximumAuthorizedMeasuredTrials=280,attributionBlocksExecuted=0,baselineNs=statistics.mean(x['baselineNs'] for x in pairs),fullNs=statistics.mean(x['fullNs'] for x in pairs),cpuPercent=ci([x['cpuPercent'] for x in pairs]),deltaNs=ci([x['deltaNs'] for x in pairs]),throughputPercent=ci([x['throughputPercent'] for x in pairs]),referenceMaterialDisagreementEstablished=False,precisionGateMet=False,precisionLimitPercentagePoints=.75,componentCostsMeasured=False,exclusions=[],retries=0,harnessErrors=[],newOptimizationImplemented=False)
 put(R/'result.json',summary)
 syntax=[]
 for p in sorted(R.glob('*.py')):
  ast.parse(p.read_text(),filename=str(p));syntax.append(dict(path=str(p),sha256=sha(p),result='PASS'))
 put(R/'verification.json',dict(preservedRecordsVerified=len(before['preserved']),originalCandidateFiles=240,priorArchiveMembers=143,historicalCandidateFiles=len(histfreeze['candidateHashes']),historicalArchiveUnchanged=True,experimentFrozenFilesVerified=len(load(R/'experiment-source-freeze.json')),syntax=syntax,originalRecorderUnchanged=True,originalFullCallbackInstructionsIdentical=True,productionAccess=False,protectedVMAccess=False,UAC=False,liveETW=False))
 cpu=summary['cpuPercent'];ns=summary['deltaNs'];th=summary['throughputPercent']
 report=f'''# Offline component attribution — prerequisite inconclusive

**MORE_PROFILING_REQUIRED**

The experiment stopped at its predeclared reference-precision prerequisite. No attribution blocks, automatic retry, optimization, live tracing or UAC followed. The preserved +1.40% overhead conflict is NOT overturned.

## Protocol and result

Predeclared: 40 AB/BA reference pairs, followed only if compatible/precise by 40 five-variant blocks. Maximum 280 measured trials / 280 million measured callbacks. All trials use 1,000,000 callbacks plus an excluded 20,000-callback warm-up. Reference order alternates AB/BA (20 each). Planned attribution uses the recorded ten-row balanced order repeated four times. No CPU affinity, priority, power/security settings or process deadlines changed.

Executed: **40 pairs / 80 measured trials / 80,000,000 callbacks**, plus 1,600,000 warm-up callbacks. **0 attribution blocks**. No excluded noisy trials, replacement trials or harness errors. All raw trial records retained. Partial variants executed only their tiny integrity selftests, not measured attribution trials.

Reference full-recorder CPU increase: **{cpu['mean']:+.6f}%**, 95% interval **[{cpu['lower']:+.6f}%, {cpu['upper']:+.6f}%]**. Halfwidth **{cpu['halfwidth']:.6f} percentage points**, exceeding this experiment's predeclared 0.75-point precision prerequisite. This additional reproducibility-precision criterion was an experiment-design choice, not a change to the owner's <=1% screen.

The interval overlaps the old [1.191267%, 1.608880%] interval. **Material reference disagreement was NOT established. Compatibility was not established with the precision required by this protocol either.** Status is therefore MORE_PROFILING_REQUIRED, not BENCHMARK_REPRODUCIBILITY_DEFECT. No attempt was made to change the gate after seeing results.

Calculation: pair i is 100*(FULL CPU / BASELINE CPU - 1). Average each five adjacent pairs, then take the mean and t-based 95% interval across eight group means using critical value 2.364624251 (df7). Grouping accounts for neighboring-trial dependence; inference still assumes sufficiently independent/stable groups. CPU is the original fixture's Windows callback-thread GetThreadTimes kernel+user accounting. Wall time is supplementary. Exact primary-thread identities, creator handles/FILETIMEs and process exits are preserved.

| Variant | CPU increase vs A | 95% interval | ns/callback delta | Throughput change |
|---|---:|---:|---:|---:|
| A BASELINE_DISABLED | 0 by definition | Not a separate estimate | 0; absolute {summary['baselineNs']:.6f} | 0 by definition |
| B FULL_ENABLED_REFERENCE | {cpu['mean']:+.6f}% | [{cpu['lower']:+.6f}, {cpu['upper']:+.6f}]% | {ns['mean']:+.6f} [{ns['lower']:+.6f}, {ns['upper']:+.6f}] | {th['mean']:+.6f}% [{th['lower']:+.6f}, {th['upper']:+.6f}] |
| C CLOCK_ONLY | NOT MEASURED | NOT AVAILABLE | NOT AVAILABLE | NOT AVAILABLE |
| D STORAGE_ONLY | NOT MEASURED | NOT AVAILABLE | NOT AVAILABLE | NOT AVAILABLE |
| E BOOKKEEPING_ONLY | NOT MEASURED | NOT AVAILABLE | NOT AVAILABLE | NOT AVAILABLE |

Extra-QPC cost, record/store cost, bookkeeping cost and interaction residual: **NOT ESTABLISHED**. Do not derive component shares from aggregate reference cost. Timestamp reuse is still plausible, but **not strongly justified by new component measurements**, because none ran. Whether <=1% is achievable without reducing diagnostic capability remains unproven. No implementation optimization or threshold change is recommended as accepted by this result.

## Fixture definitions and compiled-code audit

All variants are confined to `{W}` and labelled BENCHMARK_ONLY / not live eligible. The original recorder source/header/binary in `{C}` are untouched. The new executable uses the same C++17 /O2 build settings, synthetic event, TDH decoding, common clocks, mutex, sparse latency sampling and trial loop for every variant. It uses a common indirect callback call, so it is a NEW fixture binary, not claimed bit-identical to the old executable.

- A: original callback with recorder disabled.
- B: original callback and recorder enabled, source copied verbatim. The generated callback object's instruction listing is **identical** to the original. Recorder header SHA-256 is identical.
- C: replaces only the enabled recorder branch with its extra QPC call; no record/counter writes.
- D: full branch with completionQpc assigned existing arrivalQpc instead of calling QPC. This is intentionally incomplete timing evidence, ONLY an attribution fixture—not an acceptable timestamp-reuse implementation.
- E: preserves enable/bounds/sequence/count/overflow work, without QPC or 88-byte stores. Existing reset condition remains; sequence reads may observe prior initialized storage, and this replay difference is not a pure hardware store-cost measurement.

Compiled QPC sites: B and C five; D and E four. A shares B's callback but skips the enabled-only site. No new lock-prefixed instruction appears inside these callback listings. The compiler folds redundant checks where no clock call separates them. Thus B-D would include clock/branch-layout interactions; C-A would be a separate clock-only contrast. D-E would include stores and generated-code interactions. A future measured residual B-C-D+A must not be described as proof that physical components add independently.

The original full callback body remains unchanged; no lifecycle schema, required evidence, observer callback, control-thread instrumentation, provider, buffer, queue or cleanup logic was edited. Partial variants must never be copied to live observers or treated as acceptance instrumentation.

## Build, tests and commands

- Existing Visual Studio 2022 BuildTools, x64, `/EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE`, Advapi32/TDH/Psapi; build exit 0. New binary SHA-256: `{sha(W/'J6AttributionFixture.exe')}`.
- `J6AttributionFixture.exe selftest`: **37/37 PASS**, including original recorder checks, mode counts, same decode allocation counts and stored sequence/disposition checks. These are integrity tests, not evidence of equivalent diagnostic power for partial variants.
- `<bundled Python> -B <report>\\audit.py`: unchanged full callback instruction listing verified, original header verified, per-variant disassembly preserved.
- `<bundled Python> -B <report>\\run.py reference`: exactly one reference phase, exit 0, 40 pairs; stopped at precision gate. No invocation of `run.py attribution`.
- Retained Windows process/main-thread handles record creation identity, exit and CPU; selftest/reference processes exited normally, handles closed. Final census below independently checks leftovers.
- Python syntax checked using ast.parse; no bytecode caches created. All harness/source hashes recorded. Reference source freeze unchanged after execution.

## Preservation / cleanup

Every record in before.json reverified; original 240-file candidate unchanged, original predecessor/frozen/historical evidence unchanged. Prior 143-member archive reverified; historical candidate and archive unchanged. Historical **21 AMBIGUOUS / 1 UNMATCHED** preserved. Historical ETW loss cause remains **UNCONFIRMED**. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Final read-only host census: **0 matching diagnostic processes / 0 trace sessions**, timestamp {census['utc']}. No VM files/configuration accessed; no VirtualBox launched; production unchanged. No new Windows elevation. All new work is separate offline fixture/evidence only. No acceptance commit or later Stage 6 gate.

Only this report/tooling folder and the new benchmark-only D: directory were created/changed. Exact new file hashes are in the archive manifest. Original implementation files remain unchanged. A new bounded canonical archive contains raw trials, paired calculations, protocol, source diff, build/selftest, generated-code audit, identities, preservation and census. archive-receipt.json records actual completed hash verification; no old archive overwritten. The broad snapshot sync script is avoided because it would overwrite unrelated records.

## Next owner review

Review the now-demonstrated reference uncertainty and the declared precision prerequisite before authorizing another experiment. A future proposal can predeclare a larger, still-bounded reference sample or revise the measurement design; neither has been executed here. Do not optimize QPC/storage, relax the <=1% threshold, or infer component shares from these data. All five variants and the original reference are preserved for review.

Rollback: no existing recorder changed; retain the new directory as non-acceptance experimental evidence. No rollback action is required. STOP.
'''
 with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report)
 dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 COMPONENT ATTRIBUTION 20260924 7f29a680');assert not dest.exists();dest.mkdir()
 entries=[]
 for root,prefix in [(R,'report'),(W,'offline-fixture')]:
  for p in sorted(root.rglob('*')):
   if not p.is_file():continue
   s=p.stat();assert not s.st_file_attributes&0x400
   assert not p.name.lower().startswith('.env') and p.suffix.lower() not in {'.key','.pem','.token','.sqlite','.db'}
   entries.append(dict(path=str(p),name=prefix+'/'+p.relative_to(root).as_posix(),bytes=s.st_size,sha256=sha(p)))
 archive=dest/'evidence.zip'
 with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
  for x in entries:z.write(x['path'],x['name'])
  z.writestr('archive-manifest.json',json.dumps(dict(status='MORE_PROFILING_REQUIRED',acceptance=False,entries=entries),indent=2,sort_keys=True))
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(entries)+1
  for x in entries:
   with z.open(x['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
   assert sha(x['path'])==x['sha256']
  mh=hashlib.sha256(z.read('archive-manifest.json')).hexdigest()
 receipt=dict(archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=mh,membersVerified=len(entries)+1,bytes=archive.stat().st_size,status='VERIFIED_NON_ACCEPTANCE_EVIDENCE')
 put(R/'archive-receipt.json',receipt);put(dest/'archive-receipt.json',receipt)
 assert sha(R/'archive-receipt.json')==sha(dest/'archive-receipt.json')
 print(json.dumps(dict(result=summary,archive=receipt),indent=2))
