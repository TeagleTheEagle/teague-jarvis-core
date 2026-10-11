import ast,datetime,hashlib,json,os,sys,zipfile
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-small-combined-20260922'
A=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 VERSIONED CHECKER INTEGRATION 20260922')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
pre=load(R/'preflight.json');state=load(R/'preservation-after.json');C=Path(pre['candidate']);W=C.parent
host=R/'final'/state['hostRun']/'final-host-state.json';assert load(host)['status']=='PASS'
sys.path.insert(0,str(C));import checker_v2 as checker
replay=checker.replay();assert replay['status']=='PASS'
assert sha(pre['frozen'])==state['frozenInitial']==state['frozenFinal']
for x in pre['checks']+load(R/'candidate-freeze.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
tests=load(load(W/'test-results-location.json')['path']);review=load(R/'review-tests.json');assert tests['passed']==83 and review['passed']==31
hist=load(R/'historical-identity-preservation.json');assert sha(hist['path'])==hist['sha256']
all_python=sorted(R.glob('*.py'))+sorted(C.glob('*.py'))
for p in all_python:ast.parse(p.read_text(encoding='utf8'))
sources=[]
for prefix,base in [('review',R),('candidate-workspace',W)]:
 for p in sorted(base.rglob('*')):
  if p.is_file():
   assert not p.is_symlink() and '__pycache__' not in p.parts and p.name!='.env' and (p.suffix.lower() in ('.py','.json','.jsonl','.md','.ps1','.txt','.diff') or p==W/'fixtures'/'34664f3917884d938d9d2425b577e579'/'archive-mismatch'/'evidence.zip')
   sources.append((prefix+'/'+p.relative_to(base).as_posix(),p))
prior=Path(pre['archive']['archive'])
for name in ('evidence.zip','manifest.json','acceptance-seal.json'):
 sources.append(('validated-small-reference/'+name,prior.parent/name))
sources.append(('historical-reference/identity-summary.json',Path(hist['path'])))
sources.append(('historical-reference/acceptance-amendment-CONTRACT.md',R.parent/'stage6-acceptance-amendment-20260921/CONTRACT.md'))
sources.append(('review/REPORT.md',R/'REPORT.md'));members=len(sources)+1
report=f'''# Stage 6 versioned checker integration

**CHECKER_INTEGRATION_VALIDATED**

This is an offline small-evidence replay and TEST checker integration gate only. No live observer, worker, process probe, medium workload, large dataset, VM or protected hashing was launched. Stage 6 remains incomplete. The frozen checker was not replaced.

The result is final only together with archive-verification.json and the hash-bound acceptance-seal.json created after independent verification. The archive contains **{members} members**, including all new fixtures, candidate source, preserved preparation failures and the complete prior 324-member combined archive as a nested reference.

## Mandatory 50-item report

| # | Item | Result / evidence |
|---|---|---|
| 1 | Frozen checker initial SHA-256 | `{state['frozenInitial']}` |
| 2 | Frozen checker final SHA-256 | `{state['frozenFinal']}`; identical |
| 3 | Versioned candidate path | `{C / 'checker_v2.py'}` |
| 4 | Candidate initial SHA-256 | `{pre['frozenSHA256']}`; exact initial copy recorded before separate integration |
| 5 | Candidate final SHA-256 | `{state['candidateFinal']}` |
| 6 | Schema version | `stage6-checker-input-v2`; adapter remains `stage6-small-combined-v1`; exact kernel contract v1 plus owner creator/helper clarification |
| 7 | Adapter input schema | `{C / 'schema.json'}`; 123,353-byte closed field/type schema, CONTRACT.md and original adapter interface. Original manifest format/version, every segment range/hash/state, canonical keys, coverage, CIM and closure are required. Overlap is independently rejected by contiguous per-segment range verification. |
| 8 | Positive fixture | PASS; 72 records, 4 segments, global sequence 1–72, 36 verified instances; positive-result.json lists satisfied rules |
| 9 | Validated evidence replay | PASS; actual archived pre-archive adapter payload parsed and fully compared with recomputed output; raw persisted files re-opened; original final sidecar/archive binding verified before and after |
| 10 | Total focused tests | **114** = 83 primary + 31 review checks |
| 11 | Passed | **114** |
| 12 | Failed / skipped | **0 / 0** checker tests; two explained pre-candidate preparation errors and one archive-preparation allowlist omission preserved separately |
| 13 | Rejection checks | **103**, comprising 72 primary rejections, 28 supplemental rejections and 3 explicit nonzero CLI rejection assertions |
| 14 | Rejection checks passed | **103/103**; other 11 are positive/control/preservation assertions; category and exact reason in JSON results |
| 15 | Non-vacuous | PASS; eight empty mandatory collection fixtures rejected, including identities, handles, images, native entries, segments, STARTs, STOPs and CIM |
| 16 | Missing segment | REJECT; disposable on-disk fixture, original untouched |
| 17 | Sequence gap | REJECT even after recalculating fixture segment hash/manifest seal |
| 18 | Duplicate sequence | REJECT even after recalculating fixture hashes |
| 19 | Corrupted hash | REJECT; byte and hash mutations tested separately |
| 20 | Missing START | REJECT, including adjusted aggregate-count fixture |
| 21 | Missing STOP | REJECT, including adjusted aggregate-count fixture |
| 22 | Authoritative ambiguity | REJECT; duplicate summary/false instance sequence collision tested |
| 23 | Missing handle | REJECT |
| 24 | Missing image | REJECT |
| 25 | Missing native entry | REJECT; native fault, deadline and invalid entry state also reject |
| 26 | Direct probe class | PASS: 16 DIRECT_PROBE creator captures |
| 27 | Direct worker class | PASS: 1 DIRECT_WORKER creator capture |
| 28 | Tracer-helper class | PASS: 2 TRACER_HELPER_VERIFIED, distinct from observer infrastructure |
| 29 | Post-exit-helper class | PASS: 16 QUALIFIED_POST_EXIT_HELPER under unchanged narrow exception; **not successful creator/tracer images** |
| 30 | Incorrect helper class | REJECT; source substitution, generic access denial, unknown helper, missing helper and false creator classification |
| 31 | CIM unique | Conditional policy-unit PASS only with stipulated independent event-bound proof and canonical key. **Not a real unique CIM observation.** Public replay still rejects invented unique matches from the current raw schema. |
| 32 | CIM ambiguous | PASS as secondary when authoritative requirements pass; real replay preserves 66 AMBIGUOUS |
| 33 | CIM unmatched | PASS as secondary; real replay preserves 1 UNMATCHED |
| 34 | CIM contradiction | REJECT when positively established; ambiguous/unmatched alone are not contradictions |
| 35 | Heartbeat failure | REJECT at 10 seconds; age and interval tested, threshold unchanged |
| 36 | Deadline failure | REJECT; native and qualification deadline failures tested |
| 37 | Incomplete finalization | REJECT; missing states/manifest/seal, pending queue, writer fault/unfinished threads, limits and secondary residue |
| 38 | Cleanup failure | REJECT; worker/native closure, host process and trace-session fixtures |
| 39 | Malformed payload | REJECT; absent fields, wrong types, duplicate JSON keys, NaN/Infinity, extra fields and forged PASS |
| 40 | Unsupported schema | REJECT missing/numeric/unknown/future schema or legacy mode; no inferred version or fallback |
| 41 | Tamper tests | PASS: segment bytes/hash/range, creation/image identity, helper class, native entry, manifest, cleanup and archive mismatch all reject |
| 42 | Frozen preservation | PASS; immutable reference path `{pre['frozen']}`; **481** final source/evidence comparisons plus archived source verification |
| 43 | Candidate cleanup | PASS; final host inventory zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions; no observer or probe launched this gate |
| 44 | Archive verification | PASS only as independently certified by archive-verification.json and final sidecar; **{members}** members checked by bytes/hash and exact membership |
| 45 | Protected VM access | NONE; no protected files/configuration opened, hashed or queried; no VirtualBox command |
| 46 | Production changes | NONE; only new TEST candidate, fixtures, reports and evidence archive written |
| 47 | Historical 21/1 | UNCHANGED; raw historical identity-summary.json SHA-256 `{hist['sha256']}` reverified; distinct from small-run 66/1 |
| 48 | Historical causes | UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. |
| 49 | Next proposed gate | Owner review of MEDIUM-PROPOSAL.md; new explicit workload declaration/binding required before live medium execution. No automatic continuation. |
| 50 | Final status | CHECKER_INTEGRATION_VALIDATED, subject to accompanying completed archive receipt/seal |

## Exact changes and commands

`preflight.json` records seven copied files and their before hashes. `changes.json` records all final hashes and new files. Only the separate copied checker_v2.py and the candidate combined.py differ from copied sources: the former is a new explicit versioned entry point; the latter changes only its qualification dependency to the local frozen copy. coverage.py, qualification.py, process_instances.py, application_authority.py and frozen_reference.py remain byte-identical to their references. New candidate schema.json, binding.json, positive-fixture.json and test_candidate.py support the bounded replay. Source-freeze.json records the candidate set. All changed source diffs are archived.

Commands used Python `C:\\Users\\jonny\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe` with `-B`:

1. `prepare.py` -> rejected expected-hash transcription error; source evidence was correct. `prepare_v2.py` -> rejected Windows default-code-page decode of UTF-8 historical report. Both preserved. `prepare_v3.py` -> PASS; 324-member prior archive and 470 initial comparisons verified.
2. `host_preflight.ps1 -RunId {pre['hostRun']}` -> PASS; read-only inventory, no UAC monitoring launch.
3. `install.py` -> wrote contract/schema before separate candidate implementation and froze all candidate files.
4. `{C / 'test_candidate.py'}` -> 83/83 PASS; disposable fixture root in test-results-location.json.
5. `review_tests.py` -> 31/31 PASS and exact original evidence replay PASS.
6. `finish.py` -> 481 comparisons PASS, 16 Python source parses PASS, source diffs/hashes recorded. archive.py independently parsed all {len(all_python)} current Python sources without bytecode writes.
7. `host_preflight.ps1 -RunId {state['hostRun']}` -> PASS; zero matching processes/traces.
8. `archive.py` -> stopped before archive creation because the deliberate archive-mismatch fixture ZIP was absent from the packaging suffix allowlist. `archive_v2.py` admits only that exact fixture ZIP, then performs exact archive/member/source verification, preservation recheck and final acceptance sidecar; actual hashes in archive-verification.json.

Full paths for scripts are under `{R}`, unless the D: candidate path is shown. No frozen legacy suite was repurposed or relabelled under the amended contract. Historical results remain under their original semantics.

## Source review, limits and rollback

SOURCE-REVIEW.md covers default PASS branches, exception handling, required/empty fields, strict types, enums/version dispatch, file paths, evidence substitution and mutable-input assumptions. The replay is restricted to the explicitly pinned accepted small archive. It is not a general medium/large checker, a signed remote proof, or an OS protection boundary against hostile same-user administrators. No actual PID reuse or new real unique CIM event match was demonstrated in this offline gate.

Preserved qualified results are replay evidence, not newly run process results: 72 kernel records / 36 instances, 17 creator captures, 2 tracer helpers, 16 qualified post-exit helpers, 1 infrastructure observer; maximum recorded heartbeat 1.0918706 seconds. Thresholds, monitors and runtime are unchanged.

Rollback: stop selecting this separate candidate and keep the frozen reference as before. No installation, runtime route, registration, configuration or production data needs restoring. Preserve the entire candidate/fixture/archive tree for audit; no deletion or automatic restoration is required.

STOP. Medium validation, the 59.7 GB campaign, protected hashing and VM operations were not performed and remain pending owner review.
'''
with (R/'REPORT.md').open('x',encoding='utf8') as f:f.write(report);f.flush();os.fsync(f.fileno())
rows=[dict(name=n,source=str(p),bytes=p.stat().st_size,sha256=sha(p)) for n,p in sources]
assert len({x['name'] for x in rows})==len(rows)
assert not A.exists();A.mkdir()
save(A/'manifest.json',dict(schema='stage6-checker-integration-archive-v2',candidate=str(C),files=rows,acceptance='PENDING_INDEPENDENT_VERIFICATION_AND_SIDECAR',sourceFreezeSHA256=sha(C/'source-freeze.json')))
with (A/'evidence.zip').open('xb') as stream:
 with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for row in rows:z.write(row['source'],row['name'])
  z.write(A/'manifest.json','manifest.json')
 stream.flush();os.fsync(stream.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist()))==members
 assert z.read('manifest.json')==(A/'manifest.json').read_bytes()
 for row in rows:
  b=z.read(row['name']);assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']==sha(row['source'])
checker.replay()
for row in pre['checks']+load(R/'candidate-freeze.json')['files']:assert sha(row['path'])==row['sha256']
assert sha(hist['path'])==hist['sha256']
receipt=dict(status='PASS',archive=str(A/'evidence.zip'),membersVerified=members,archiveBytes=(A/'evidence.zip').stat().st_size,archiveSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'manifest.json'),reportSHA256=sha(R/'REPORT.md'),frozenCheckerSHA256=sha(pre['frozen']),candidateSHA256=sha(C/'checker_v2.py'))
save(R/'archive-verification.json',receipt);save(A/'archive-verification.json',receipt)
seal=dict(schema='stage6-checker-integration-acceptance-v2',status='CHECKER_INTEGRATION_VALIDATED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),archiveSHA256=receipt['archiveSHA256'],manifestSHA256=receipt['manifestSHA256'],reportSHA256=receipt['reportSHA256'],candidateSHA256=receipt['candidateSHA256'],frozenCheckerSHA256=receipt['frozenCheckerSHA256'],cleanupSHA256=sha(host),tests=114,failed=0,nextGateAuthorized=False)
save(R/'acceptance-seal.json',seal);save(A/'acceptance-seal.json',seal)
assert sha(R/'archive-verification.json')==sha(A/'archive-verification.json') and sha(R/'acceptance-seal.json')==sha(A/'acceptance-seal.json')
save(R/'seal-verification.json',dict(status='PASS',sealSHA256=sha(R/'acceptance-seal.json'),archiveSidecar=str(A/'acceptance-seal.json')))
print(json.dumps(dict(status=seal['status'],receipt=receipt,sealSHA256=sha(R/'acceptance-seal.json'))))
