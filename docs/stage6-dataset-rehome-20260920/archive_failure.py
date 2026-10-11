"""Archive bounded nonsecret failed-run evidence after monitoring has ended."""
import pathlib,json,hashlib,zipfile,os
R=pathlib.Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=read(R/'failure-summary.json');copy=read(R/'copy-result.json');pre=read(R/'preflight.json')
C=pathlib.Path(copy['workspace']);F=pathlib.Path(s['run']);CR=pathlib.Path(copy['run'])
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 DATASET REHOME FAILED LARGE RUN 20260920')
assert s['status']=='PROTECTED_COLLECTOR_STILL_DEFECTIVE'
assert not read(R/'identity-final.json')['exactLiveMatches']
for x in read(C/'run-source.json'):assert sha(C/x['name'])==x['sha256']
for receipt in pre['archives'].values():
 a=pathlib.Path(receipt['path']);assert sha(a/'evidence.zip')==receipt['zipSHA256'] and sha(a/'archive-manifest.json')==receipt['manifestSHA256']
probe=s['probeFailures'][0];sampler=s['sampler']['failures'][0]
report=f'''# Stage 6 synthetic dataset rehome and monitored collector result

**PROTECTED_COLLECTOR_STILL_DEFECTIVE**

Dataset rehome and preflight passed. The single monitored attempt failed; no retry or acceptance finalization occurred. No protected VM/configuration access, VirtualBox launch, production change, deadline change, security change, or real protected hashing was performed.

## Source and destination

- Old synthetic source: `{copy['source']}`
- Current approved workspace: `{C}`
- New synthetic destination: `{copy['destination']}`
- Copy evidence: `{CR}`
- Failed monitored run: `{F}`
- Calibration: `{copy['calibration']}`; SHA-256 `{copy['calibrationSHA256']}`.
- New dataset manifest: `{CR / 'dataset-manifest.json'}`; SHA-256 `{copy['manifestSHA256']}`.

Normal exclusive file-level copying was used: no links, junctions, aliases, transformations or generated content. Each old file was hashed during copying and each destination was independently re-read. All 12 old/new/calibration hashes matched. Relative paths, sizes, modification timestamps, compression/encryption flags and directory structure matched; destination file identities are distinct and link counts are one. The old dataset remains in place. Copy plus independent destination verification took {copy['seconds']:.3f} seconds.

The actual collector containment checks accepted the new dataset and rejected the old external path. All 12 canonical opened-file identities were verified. No dataset manifest routing points to the old source; provenance records intentionally retain the original path.

## Exact changes

Only validation configuration changed: `{C / 'baseline-allowlist.json'}` changes its exact synthetic root from old to new; `{C / 'run-source.json'}` updates that configuration hash. Real protected roots remain empty and realProtectedAccess remains false. Collector, guard, diagnostic executable code and thresholds did not change. Before/after hashes and original configuration bytes are in `configuration-change.json`, `allowlist-before.json`, and `run-source-before.json`. New copy/evidence/report scripts are confined to this report directory. No repository runtime or production files were edited.

## Failed acceptance and eventual cleanup are distinct

Probe PID {probe['pid']}, creation FILETIME {probe['created']}, parent PID {probe['parentPid']}, executable `{probe['image']}`:

- CreateProcess call: {probe['creationCallSeconds']:.7f} seconds.
- Fixed deadline violation observed: {probe['deadlineObservedSeconds']:.7f} seconds after launch; handle remained unsignaled (258).
- Independent 15-second wait returned timeout, observed after {probe['observerElapsedSeconds']:.7f} seconds. The configured limit was not increased.
- Kernel lifetime: {probe['kernelLifetimeSeconds']:.7f} seconds. Eventual exit code 0 and signaled handle do not erase the failure.

Sampler PID {sampler['pid']}, creation FILETIME {sampler['created']}:

- CreateProcess call: {sampler['creationCallSeconds']:.7f} seconds.
- Cleanup observation: {sampler['cleanupObservationSeconds']:.7f} seconds; allExited=false and handleState=258, although Job active count was zero.
- The existing bounded sampler cleanup requested termination. Its eventual kernel exit code was {sampler['kernelExitCode']}, and independent retained-handle/START/STOP evidence subsequently proved exit. No additional manual termination was performed.
- This remains CLEANUP_FAILED at its original acceptance boundary. Later reconciliation does not retroactively pass it.

Hash pass #1 was cancelled by workload-stop after the probe failure. Its RuntimeError('Workload cancellation') and worker nonzero exit are preserved as secondary consequences. The exact underlying causes of both delays remain UNCONFIRMED. Their temporal overlap is evidence, not proof of a shared cause.

## Mandatory collector results

| Item | Result |
|---|---|
| 1. Dataset size | {s['totalBytes']:,} bytes |
| 2. Files | {s['fileCount']} |
| 3. Largest file | {s['largestFile']['path']}: {s['largestFile']['bytes']:,} bytes |
| 4. Total monitored full-hash duration | Unavailable: no completed monitored pass |
| 5. Monitored pass #1 | Incomplete; cancelled after primary failure |
| 6. Monitored pass #2 | NOT RUN |
| 7. Complete-pass throughput | Not available; no invented measurement |
| 8. Hash equality | Copy old/new/calibration PASS; monitored two-pass equality NOT ESTABLISHED |
| 9. Source preservation | Both roots: all 30 metadata/ACL entries unchanged; file sizes/mtime unchanged |
| 10. Heartbeat | Maximum interval {s['maxHeartbeatInterval']:.7f}s; maximum age {s['maxHeartbeatAge']:.7f}s; limit 10s |
| 11. Longest monitor stage | {s['timing']['longest']['stage']}: {s['timing']['longest']['seconds']:.7f}s; timing overflow {s['timing']['overflow']} |
| 12. Sampler | 7 queries; 6 available; 1 CLEANUP_FAILED; sampler thread eventually exited |
| 13. Tracked STARTs | {s['lifecycle']['appStarts']} |
| 14. Tracked STOPs | {s['lifecycle']['appStops']} |
| 15. Tracked descendants | {s['childHelperCount']} plus collector = {s['lifecycle']['total']} |
| 16. Lineage ambiguity | {s['lineageAmbiguities']}; unexplained identities {s['lifecycle']['insufficient']} |
| 17. Probe deadlines | {s['deadlineViolations']} failure in {s['probeCount']} probes; independent observer also timed out |
| 18. Queue | {s['queue']['persisted']} enqueued/selected/persisted/removed; remaining 0; max depth {s['queue']['maxDepth']}; external EventIdentifier collisions 4; internal queue-ID collisions 0 |
| 19. Finalization | Observer durable finalization PASS; collector acceptance finalization deliberately NOT RUN |
| 20. Manifest | Copy manifest verified; successful collector baseline manifest NOT CREATED |
| 21. Manifest SHA-256 | Copy manifest `{copy['manifestSHA256']}`; failed-evidence archive has its own receipt |
| 22. Archive | Separate failed-evidence archive verified; exact count/hash in archive-verification.json |
| 23. Cleanup | 343 retained-handle exits + 29 qualified post-exit cases; zero unexplained. All 375 recorded identities including launcher/observers absent by PID+creation time. Zero matching diagnostic processes/traces. Earlier sampler-boundary failure retained |
| 24. Collector hashes | 84/84 unchanged |
| 25. Diagnostic hashes | 96/96 unchanged; integration 100/100 matches launch manifest; only reviewed synthetic configuration binding changed before launch |
| 26. Historical delays | Probe-delay and heartbeat-delay causes remain UNCONFIRMED |
| 27. Protected VM/config | NOT ACCESSED; no new protected preservation hash claim |
| 28. Production | UNCHANGED by this task |
| 29. Protected-baseline eligibility | BLOCKED; real capture remains unauthorized |
| 30. Final status | PROTECTED_COLLECTOR_STILL_DEFECTIVE |

Two transient retained-tree image-query WinError 5 records were preserved. The unchanged strict checker reconciled these using identity-bound kernel images and retained exits; no rule was weakened. The general run-review records missing hash-pass-1.json because the pass never completed; this is expected absent evidence in a failed run, not a successful pass.

## Evidence, reused validation and rollback

Newly executed: copy/hash verification, actual canonical containment/open checks, all five historical archive verifications, host process/trace preflight, one monitored run, full independent exit reconciliation, metadata/ACL/source hash verification and archive verification. The old 131-member and 133-member dry-run archives, 1,333-member collector archive, 755-member hardening archive and 120-member blocked-run archive remain unchanged. They support historical failure-injection behavior only; they are not current monitored acceptance.

Previously validated code regressions (238 collector/integration tests; 117 diagnostic tests; 222 queue assertions and 10,000-event collision stress; bounded sampler cases) were not rerun unnecessarily. Frozen byte checks establish continued applicability to unchanged code. This new failed run is not reclassified by those earlier passes.

Rollback requires no runtime change: leave both synthetic datasets and failed evidence preserved. If explicitly requested later, restore only the two saved configuration files together after verifying they have not subsequently changed. Do not weaken containment or point the current collector at the old external dataset. No rollback, deletion or retry was executed.

Next owner review: diagnose the preserved probe runtime delay and sampler creation/cleanup delay from this exact run before another monitored attempt. Keep 13.6/15/10-second limits unchanged. No real protected-baseline procedure is executable or authorized from this failed status.

HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
'''
with (R/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
paths=[('report/'+p.name,p) for p in sorted(R.iterdir()) if p.is_file()]
for label,root in [('failed-run',F),('copy-evidence',CR)]:
 for p in sorted(root.rglob('*')):
  assert not p.lstat().st_file_attributes&0x400
  if p.is_file():paths.append((label+'/'+p.relative_to(root).as_posix(),p))
for x in read(C/'run-source.json'):paths.append(('integration-candidate/'+x['name'],C/x['name']))
paths.append(('integration-candidate/run-source.json',C/'run-source.json'))
assert len({n for n,p in paths})==len(paths)
rows=[]
for name,p in paths:
 assert p.name!='.env' and not p.lstat().st_file_attributes&0x400
 rows.append(dict(name=name,source=str(p),sha256=sha(p),bytes=p.stat().st_size))
raw=(json.dumps(dict(status=s['status'],kind='PRESERVED_FAILED_SYNTHETIC_VALIDATION_NOT_ACCEPTANCE',files=rows),sort_keys=True,indent=2)+'\n').encode()
A.mkdir(exist_ok=False)
with (A/'archive-manifest.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for x in rows:z.write(x['source'],x['name'])
 z.writestr('archive-manifest.json',raw)
with (A/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(rows)+1
 for x in rows:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']==sha(pathlib.Path(x['source']))
 assert z.read('archive-manifest.json')==raw
with (A/'REPORT.md').open('xb') as f:f.write((R/'REPORT.md').read_bytes());f.flush();os.fsync(f.fileno())
receipt=dict(status='HASH_VERIFIED',disposition=s['status'],path=str(A),members=len(rows)+1,zipSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'archive-manifest.json'),reportSHA256=sha(A/'REPORT.md'),protectedBaselineAuthorized=False,productionChanged=False)
for root in (R,A):
 with (root/'archive-verification.json').open('x') as f:json.dump(receipt,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(receipt))
