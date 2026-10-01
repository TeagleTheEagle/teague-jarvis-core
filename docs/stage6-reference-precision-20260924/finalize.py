"""Preservation/report/archive only; no fixture execution."""
import pathlib,json,hashlib,zipfile,datetime,ast
from context_config import R,PREV,PRECISE,FIXTURE,LIVE,load,sha,put,verify
if __name__=='__main__':
 result=load(R/'result.json');census=load(R/'final-census.json')
 assert census['processCount']==census['traceCount']==0
 pre=load(R/'preservation-before.json')
 for row in pre['records']:verify(row)
 for row in pre['originalHarness']:verify(row)
 for row in load(R/'repetition-driver-freeze.json'):verify(row)
 assert sha(R/'protocol.json')==pre['protocolSHA256']
 assert sha(FIXTURE/'J6AttributionFixture.exe')==pre['fixtureSHA256']
 archiveMembers=0
 for receipt in pre['archives']:
  assert sha(receipt['archive'])==receipt['archiveSHA256']
  with zipfile.ZipFile(receipt['archive']) as z:
   assert len(z.namelist())==len(set(z.namelist()))==receipt['membersVerified']
   m=z.read('archive-manifest.json');assert hashlib.sha256(m).hexdigest()==receipt['manifestSHA256']
   for row in json.loads(m)['entries']:
    verify(row)
    with z.open(row['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
   archiveMembers+=len(z.namelist())
 historical=load(R.parent/'stage6-final-measurement-v3-20260924'/'historical-precheck.json')
 assert sha(historical['archive'])==historical['archiveSHA256']
 h=load(R.parent/'stage6-identity-capacity-recalibration-20260921'/'freeze.json')
 hroot=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
 for row in h['candidateHashes']:assert sha(hroot/row['name'])==row['sha256']
 syntax=[]
 for p in R.glob('*.py'):
  ast.parse(p.read_text(),filename=str(p));syntax.append(dict(path=str(p),sha256=sha(p),syntax='PASS'))
 put(R/'preservation-after.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),recordsVerified=len(pre['records']),priorArchiveMembersVerified=archiveMembers,originalHarnessUnchanged=True,fixtureUnchanged=True,protocolUnchanged=True,repetitionDriverUnchanged=True,historicalCandidateHashes=len(h['candidateHashes']),historicalArchiveUnchanged=True,syntax=syntax,productionAccess=False,protectedVMAccess=False,UAC=False,liveETW=False))
 q=result['primary'];n=result['nsDifference'];t=result['throughputPercent'];elapsed=load(R/'execution.json')['elapsedSeconds']
 report=f'''# Component-attribution reference precision only

**{result['status']}**

Reference fixture and all existing callback/recorder/harness code remain unchanged. No rebuild, selftest or component-attribution mode ran. No UAC, live ETW, observer integration, optimization, production or protected VM operation occurred.

## Fixed design

16 reference processes x 40 balanced pairs = **640 pairs / 1,280 measured arms / 1,280,000,000 measured callbacks**. Each arm: 1,000,000 useful callbacks and the binary's unchanged, excluded 20,000-callback warm-up. Total excluded warm-up work: 25,600,000 callbacks. Actual AB pairs: 320; BA: 320. Ordinary noisy trials retained; **0 exclusions / 0 retries / 0 harness errors**. Elapsed {elapsed:.3f} seconds.

The fixture hardcodes callback count and has no command-line option to increase it. Rebuilding would change the required reference, so precision was improved through bounded repetition of the existing executable. Original launch() source executes unchanged via runpy. A new outer path-view adapter only routes raw outputs into fresh per-batch D: directories; executable path, CWD, process flags, warm-up, CPU accounting, trial ordering and callback semantics remain original. No observer/provider/buffer/queue/deadline changes. The original 1,200-second offline launcher bound stays unchanged; the outer 5,400-second budget only stops additional launches, and did not trigger.

The target was predeclared **95% half-width <=0.25 percentage points**, a profiling prerequisite, not the <=1% overhead acceptance screen. Prior group variance predicted about 0.19 points under stable conditions; this was not a guarantee. No interim estimate controlled stopping. All 16 batches completed before analysis.

## CPU and compatibility

Primary paired CPU increase: **{q['mean']:+.6f}%**.

95% interval: **[{q['lower']:+.6f}%, {q['upper']:+.6f}%]**.

Half-width: **{q['halfwidth']:.6f} percentage points**; target met: **{result['precisionMet']}**.

Compatibility classification: **{result['compatibility']}** against preserved [1.191267%, 1.608880%]. Interval overlap: {result['intervalOverlap']}. A different point estimate alone is not a reproducibility defect. Compatibility is evaluated only when precision is sufficient. This reference result does not itself clear the <=1% diagnostic overhead screen or approve integration.

Per pair: d = 100*(FULL thread CPU / BASELINE thread CPU - 1), using existing Windows GetThreadTimes kernel+user counters. CPU is not inferred from wall time. Calculate t95 across 16 batch means (df15, 2.131449545559) and across 128 adjacent five-pair group means (df127, 1.978819534681). Use the larger half-width about their common equally weighted mean. Batch half-width {q['batchInterval']['halfwidth']:.6f}; five-pair-group half-width {q['fivePairGroupInterval']['halfwidth']:.6f}. This conservative envelope covers both chosen variance groupings; it still assumes sufficiently stable, independent groups and does not bound systematic host bias.

Raw per-pair baseline/full CPU, absolute CPU difference, percentage delta, ns/callback and actual order are in pairs.json and order.json. Original raw trial output and creator-handle-derived process/main-thread identities are archived without alteration.

| Supplementary measure | Result |
|---|---:|
| Baseline average ns/callback | {result['baselineMeanNs']:.6f} |
| Full average ns/callback | {result['fullMeanNs']:.6f} |
| Paired added ns/callback | {n['mean']:+.6f} [{n['lower']:+.6f}, {n['upper']:+.6f}] |
| Throughput paired change | {t['mean']:+.6f}% [{t['lower']:+.6f}, {t['upper']:+.6f}] |
| Process CPU paired change | {result['processCpuPercent']['mean']:+.6f}% |
| Wall-time paired change | {result['wallPercent']['mean']:+.6f}% |
| Individual-pair SD | {result['pairSD']:.6f} percentage points |
| Batch lag-1 correlation, descriptive | {result['batchLag1Correlation']} |
| First eight batch mean | {result['firstEightBatchMean']:+.6f}% |
| Last eight batch mean | {result['lastEightBatchMean']:+.6f}% |

No supplementary metric substitutes for the approved dispatcher CPU measure. No noisy trial was deleted or reclassified because of its value. Existing sampled callback latencies, allocation counts and process high-water remain in raw records; no new profiler was enabled.

## Identity and verification

Existing executable: `{FIXTURE / 'J6AttributionFixture.exe'}`.

SHA-256: `{pre['fixtureSHA256']}`.

The original full-reference callback's compiled object instructions match the original benchmarked callback before measurement; their preserved hash is {pre['referenceInstructionSHA256']}. Original source/header/object/executable, compiler/link command, build log and launch harness hashes remain unchanged afterward. No rebuild. Only new outer orchestration/calculation/report files were created in this report directory and fresh evidence under `{LIVE}`. Exact hashes are archived.

Machine context comes from preflight-census.json: AMD Ryzen 7 3700X / 16 logical processors, reported Windows 10.0.26200.0. No affinity, priority, scheduler, power, security or environment settings changed. Existing executable and working directory preserved. The original launcher retains process and main-thread handles, verifies creation identities, observes exit and closes handles; all 16 processes returned exit code 0. No process-name/PID-only substitution supplies the recorded identity.

Commands: bundled Python `-B <report>\\preflight_check.py`, `-B <report>\\repeat_reference.py`, `-B <report>\\analyze_reference.py`, `-B <report>\\finalize.py`. Every fixture invocation is exactly `J6AttributionFixture.exe reference`. No invocation of selftest, attribution, CLOCK_ONLY, STORAGE_ONLY or BOOKKEEPING_ONLY.

All preserved predecessor/candidate/evidence records reverified, both previous archives reverified (36 + 143 members), original frozen checker and historical records unchanged. Historical 21 AMBIGUOUS / 1 UNMATCHED remains unchanged. Historical ETW loss cause: **UNCONFIRMED**. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

Final read-only host census at {census['utc']}: **0 matching processes / 0 diagnostic trace sessions**. No protected VM/configuration files were opened or hashed; no VirtualBox was launched; production untouched.

The new bounded nonsecret canonical archive preserves raw pairs, order, protocol, calculations, source hashes, process identities and final census. archive-receipt.json contains actual archive path/hash/member verification. No previous archive overwritten. Broad project sync is not used because it would overwrite unrelated records. No commit or later Stage 6 activity.

## Disposition

STOP regardless of outcome. If REFERENCE_PRECISION_ESTABLISHED, the adjacent owner-review procedure describes the separately gated component experiment. If precision is not established, no extra batches run automatically. If evidence is inconsistent at adequate precision, preserve it as BENCHMARK_REPRODUCIBILITY_DEFECT rather than optimizing or relaxing the threshold. The historical +1.40% result remains preserved; this action does not retroactively alter it.
'''
 with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report)
 procedure=f'''# Bounded component-attribution procedure — OWNER REVIEW ONLY

Current reference status: **{result['status']}**. No execution is authorized by this precision-only action. If status is not REFERENCE_PRECISION_ESTABLISHED, this procedure is BLOCKED and must not run.

1. Obtain explicit owner authorization for the component experiment. Verify this report's finalized archive/receipt, result.json and full reference identity; do not overwrite the older inconclusive reference-result.json or pretend its old prerequisite passed.
2. Reverify the same fixture `{FIXTURE / 'J6AttributionFixture.exe'}`, SHA-256 `{pre['fixtureSHA256']}`, original source/header/object, identical full-reference callback instructions and original launcher. Require no matching processes/traces and no protected or production access. No UAC is expected; any elevation request stops the procedure.
3. Create exactly one fresh D: evidence directory and fresh report identity. A narrowly reviewed outer binding must validate this new precision result and its hashes before calling the unchanged original launch('attribution') function. Route only its raw files to the new directory while retaining the original executable and CWD, as demonstrated by the reference-only path adapter. Do not invoke the old script's __main__ or mutate its immutable previous decision to pass its old gate. The attribution binding/calculation wrapper must be reviewed before execution; it has not been implemented or run in this action.
4. Execute existing binary **attribution** mode exactly once. It runs 40 blocks x five variants = 200 measured trials, each 1,000,000 callbacks and 20,000 excluded warm-up callbacks. Maximum measured callbacks: 200,000,000. Variant IDs: 0 BASELINE_DISABLED, 1 FULL_ENABLED_REFERENCE, 2 CLOCK_ONLY, 3 STORAGE_ONLY, 4 BOOKKEEPING_ONLY. Existing order: five rotations of [0,1,4,2,3], then reversed rotations, repeated four times. No extra blocks, retries, reordered launches, threshold changes or rebuild.
5. Preserve creator-owned process/main-thread identities and exit evidence using the original launcher; preserve its 1,200-second offline phase bound. On malformed output, API/count/order/identity error, interruption, source drift or nonzero exit: reject that attempt, preserve partial evidence and stop. Do not delete ordinary noisy trials.
6. Analyze paired within-block contrasts against A using dispatcher CPU, plus ns/callback and throughput. Average adjacent four-block groups and use the predeclared t95 df9 method from the component protocol. Report C-A, D-A, E-A, conditional B-D, conditional D-E and residual B-C-D+A with uncertainty. Do not sum isolated physical costs as though independence were proven. Compiler-fused checks/layout and replay resets remain explicitly disclosed.
7. Recheck B-A against the preserved precise result and this new reference interval; materially inconsistent evidence stops interpretation as BENCHMARK_REPRODUCIBILITY_DEFECT. Report original screen <=1% unchanged. D uses a substituted arrival timestamp and is NOT valid completion evidence; even a favorable D result does not itself validate real timestamp reuse.
8. No optimization follows. Timestamp reuse can be proposed only if its contextual saving is supported with uncertainty and the remaining full-store cost supports the 1% target; preserve all required diagnostic capability in a separate reviewed implementation plan. Otherwise report uncertain/multiple costs honestly.
9. Final read-only census must show 0 matching processes / 0 traces. Reverify unchanged sources/history, archive all raw/calculation/identity/failure evidence and hash-verify it. Stop for owner review. No live ETW, observer integration, medium/large/59.7GB, protected VM, production, backup/restore or later gate.

No runnable approval bypass is supplied. The exact executable mode/count/order above is fixed; the fresh evidence binding must be reviewed, and this precision-only authorization cannot launch it.
'''
 with (R/'COMPONENT-PROCEDURE-OWNER-REVIEW.md').open('x',encoding='utf8') as f:f.write(procedure)
 dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 REFERENCE PRECISION 20260924 9f34d820');assert not dest.exists();dest.mkdir()
 entries=[]
 for root,prefix in [(R,'report'),(LIVE,'raw')]:
  for p in sorted(root.rglob('*')):
   if not p.is_file():continue
   s=p.stat();assert not s.st_file_attributes&0x400
   assert not p.name.lower().startswith('.env') and p.suffix.lower() not in {'.key','.pem','.token','.sqlite','.db'}
   entries.append(dict(path=str(p),name=prefix+'/'+p.relative_to(root).as_posix(),bytes=s.st_size,sha256=sha(p)))
 archive=dest/'evidence.zip'
 with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
  for row in entries:z.write(row['path'],row['name'])
  z.writestr('archive-manifest.json',json.dumps(dict(status=result['status'],stage6Acceptance=False,entries=entries),sort_keys=True,indent=2))
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==len(entries)+1
  for row in entries:
   with z.open(row['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
   assert sha(row['path'])==row['sha256']
  manifestHash=hashlib.sha256(z.read('archive-manifest.json')).hexdigest()
 receipt=dict(archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=manifestHash,membersVerified=len(entries)+1,bytes=archive.stat().st_size,status='HASH_VERIFIED',referenceStatus=result['status'])
 put(R/'archive-receipt.json',receipt);put(dest/'archive-receipt.json',receipt)
 assert sha(R/'archive-receipt.json')==sha(dest/'archive-receipt.json')
 print(json.dumps(receipt))
