import pathlib,json,hashlib,sys,traceback,zipfile,os
R=pathlib.Path(__file__).resolve().parent;P=R.parent/'stage6-checker-v2-20260923'
C=pathlib.Path(json.loads((P/'candidate.json').read_text())['code']);run=C/'protected-8145cedf8db843959b8ba58dfd62717b';live=C.parent/('live-'+run.name)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read(P/'final-verification.json');cfg=read(P/'candidate.json');O=pathlib.Path(cfg['original'])
for x in cfg['originalFiles']:assert sha(O/x['name'])==x['sha256']
for x in v['source']:assert sha(C/x['name'])==x['sha256']
assert sha(C/'small-source-v2.json')==v['candidateManifestSHA256']
archive=read(P/'canonical-archive-receipt.json');assert sha(pathlib.Path(archive['archive']))==archive['archiveSHA256']
sys.path.insert(0,str(C));import small_check_v2
try:
 result=small_check_v2.check(run);checker=dict(status='UNEXPECTED_PASS',result=result)
except Exception as exc:checker=dict(status='REJECTED',type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc())
assert checker['status']=='REJECTED'
tree=read(run/'tree-handles.json');support=read(run/'tree-image-support.json');kernel=read(run/'etw-result.json');detail=read(run/'detail/etw-result.json');hb=read(run/'app-heartbeats.json')
unclosed=[r for r in tree['rows'] if not r['closed'] or r['signalObservedQpc'] is None];keys={(r['pid'],r['created']) for r in unclosed}
one=read(run/'hash-pass-1.json');two=read(run/'hash-pass-2.json')
data=dict(status='LIVE_PROCESS_EVIDENCE_DEFECTIVE',run=run.name,primary=read(run/'primary-failure.json'),collectorPid=support['anchor']['pid'],unclosedAtCollectorCleanup=unclosed,externalKernelMatches=[r for r in kernel['rows'] if (r['pid'],r['created']) in keys],collectorKernel=[r for r in kernel['rows'] if r['pid']==support['anchor']['pid'] and r['created']==support['anchor']['created']],checker=checker,launcher=read(run/'launcher-result.json'),hashPassesMatch=one['files']==two['files'],metadata=read(run/'metadata-verified.json'),kernelLoss={k:kernel[k] for k in ('faults','eventsLost','realtimeBuffersLost','buffersLost')},detailLoss={k:detail[k] for k in ('faults','eventsLost','realtimeBuffersLost','buffersLost')},maxHeartbeat=max((r['interval'] for r in hb),default=None),queue=read(run/'app-result.json')['queue'],cleanup=read(R/'final/71dffb95180c4c8b9f8f2b6b6d6baf2b/final-host-state.json'),sourceHashesUnchanged=len(v['source']),originalHashesUnchanged=len(cfg['originalFiles']),retry=False,finalizerRun=False,negativeInjectionsRun=False,protectedAccess=False,productionChanged=False)
with (R/'failure-summary.json').open('x') as f:json.dump(data,f,indent=2)
(R/'REPORT.md').write_text(f'''# Stage 6 — single small live v2 attempt

LIVE_PROCESS_EVIDENCE_DEFECTIVE

Exactly one run: {run.name}. Candidate unchanged. Preserved preflight: 183 original files, 194 candidate files and 363 canonical archive members verified; zero initial matching processes/traces. Three established observer UAC prompts were explicitly approved; no other elevation or VM action.

Primary failure: tree-cleanup / Incomplete retained tree. Collector PID {data['collectorPid']} recorded allExited=false, allHandlesClosed=false, supportingEvidenceValid=false. One outstanding identity: conhost.exe PID 8436, creation FILETIME 134345949607928089, parent collector PID 15280, kernel sequence 55622 / parent sequence 55621. Its image capture was valid and live; it remained unsignaled (258) at collector cleanup. External tracer subsequently recorded STOP, exit code 0 and closed its retained handle. Later cleanup does not retroactively validate the failed collector result.

Actual versioned checker evaluated these fresh outputs once and rejected them: {checker['reason']}. Acceptance finalizer NOT RUN. Stale/cross-run and other fault injections NOT RUN after the unexpected live failure; no claim of completing those requirements. No retry, rule change, source correction, medium/large/protected run or frozen checker replacement.

Both small hash passes matched: {data['hashPassesMatch']}. Maximum recorded heartbeat interval: {data['maxHeartbeat']} seconds. Kernel loss counters: {data['kernelLoss']}. Detailed trace loss counters: {data['detailLoss']}. These partial successes do not establish integrated acceptance; complete authority/coverage/finalizer qualification did not pass.

All observers exited with code 0; collector and launcher reported failure. Final independent host census PASS at {data['cleanup']['utc']}: 0 matching processes and 0 diagnostic trace sessions. The failed collector's local handle-closure proof remains failed even though no live process remains.

Evidence: failure-summary.json contains exact identity/timing/handle rows, checker rejection, observer exits, queue and census. Source hashes unchanged: 194 candidate, 183 original. Prior canonical archive digest unchanged. All run files, driver stdout/stderr, binding, health, kernel/detail/native evidence and preserved failure are included in the new failure archive, with every member hash-verified. See archive-receipt.json.

Supported finding: the newly included collector-owned console helper was still live at in-collector cleanup and exited later. A cleanup-order dependency is a candidate explanation; this run does not by itself prove the complete cause or authorize a correction. Next proposed action is narrow read-only lifecycle/cleanup-order diagnosis for that exact helper. No timeout increase or evidence relaxation proposed.

Production unchanged; protected VM/configuration not accessed. Historical causes remain UNCONFIRMED; 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. Stage 6 remains INCOMPLETE. STOP for owner review.
''')
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 SMALL LIVE V2 FAILURE 20260923 8145cedf');dest.mkdir(exist_ok=False)
pairs=[]
for prefix,root in [('report',R),('live-run',run),('driver',live)]:
 for base,dirs,names in os.walk(root,followlinks=False):
  for name in dirs+names:assert not (pathlib.Path(base)/name).lstat().st_file_attributes&0x400
  for name in names:
   p=pathlib.Path(base)/name;pairs.append((prefix+'/'+p.relative_to(root).as_posix(),p))
pairs.sort();manifest=[dict(path=n,bytes=p.stat().st_size,sha256=sha(p)) for n,p in pairs]
with (dest/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
zpath=dest/'evidence.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for n,p in pairs:z.write(p,n)
with zipfile.ZipFile(zpath) as z:
 assert len(z.namelist())==len(manifest)
 for m in manifest:
  b=z.read(m['path']);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
for m,(_,p) in zip(manifest,pairs):assert sha(p)==m['sha256']
receipt=dict(status='HASH_VERIFIED',membersVerified=len(manifest),archive=str(zpath),archiveSHA256=sha(zpath),manifestSHA256=sha(dest/'manifest.json'))
for p in (R/'archive-receipt.json',dest/'receipt.json'):
 with p.open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(dict(result=data['status'],checker=checker['reason'],maxHeartbeat=data['maxHeartbeat'],hashMatch=data['hashPassesMatch'],archive=receipt),indent=2))
