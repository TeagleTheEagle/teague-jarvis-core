import pathlib,json,hashlib,sys,zipfile,contextlib
R=pathlib.Path(__file__).parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
v=load(R/'preflight-result.json');C=pathlib.Path(v['candidate']);root=pathlib.Path(v['runRoot']);P=R.parent/'stage6-authority-independent-20260925';S=P/'candidate';before=load(P/'before.json');old=pathlib.Path(before['predecessor'])
sys.path.insert(0,str(C));import failure_preserve_v4 as f
assert load(R/'postrun-census.json')['status']=='PASS' and load(R/'recorded-instance-postrun.json')['clean']
comparisons=[]
for base,name,expected in [(C,'small-source-v3.json',v['sourceManifestSHA256']),(C,'witness-source-v1.json',v['witnessManifestSHA256']),(S,'small-source-v3.json',load(P/'successor-binding.json')['candidateManifestSHA256']),(S,'witness-source-v1.json',load(P/'successor-binding.json')['diagnosticManifestSHA256']),(old,'small-source-v3.json',before['manifestSHA256'])]:
 assert sha(base/name)==expected
 rows=load(base/name)
 for row in rows:
  p=base/row['name'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
 comparisons.append(dict(base=str(base),manifest=name,sha256=expected,files=len(rows),status='PASS'))
for row in before['files']:assert (old/row['name']).stat().st_mtime_ns==row['mtimeNs']
for receipt in v['archives']:assert sha(pathlib.Path(receipt['archive']))==receipt['sha256']
assert sha(P/'successor-binding.json')==v['successorBindingSHA256']
assert sha(root/'workspace-binding-v4.json')==v['workspaceBindingSHA256']
one=load(root/'hash-pass-1.json')['files'];two=load(root/'hash-pass-2.json')['files'];assert one==two and len(one)==12
for row in one.values():
 p=pathlib.Path(row['fullPath']);assert p.stat().st_mtime_ns==row['mtime_ns'] and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
save(R/'preservation-verification.json',dict(status='PASS',manifests=comparisons,historicalArchives='UNCHANGED',predecessorMetadata='UNCHANGED',datasetFiles=12,datasetBytes=786432,hashPassesMatch=True,metadataUnchanged=True,candidateChangesDuringRun=False,frozenCheckerChanged=False,protectedVMAccess=False,productionChange=False))
previous=load(R.parent/'stage6-witness-live-20260925'/'preflight-result.json');oldrun=pathlib.Path(previous['runRoot'])
summary=load(R/'analysis-summary.json');stats={};configuration=[]
for channel,base,prior in [('authority',root,oldrun),('detailed',root/'detail',oldrun/'detail')]:
 t=load(base/'loss-diagnostic-v2.json');end=load(base/'etw-result.json');s=t['samples'];cfg=t['configuration'];pcfg=load(prior/'loss-diagnostic-v2.json')['configuration']
 diff={k:dict(before=pcfg.get(k),after=cfg.get(k)) for k in set(cfg)|set(pcfg) if cfg.get(k)!=pcfg.get(k)}
 if channel=='authority':assert set(diff)=={'mode'} and cfg['mode']==(pcfg['mode']|0x08000000) and not pcfg['mode']&0x08000000
 else:assert not diff and not cfg['mode']&0x08000000
 configuration.append(dict(channel=channel,current=cfg,previous=pcfg,differences=diff))
 rates=[]
 for a,b in zip(s,s[1:]):
  dt=(b['endQpc']-a['endQpc'])/t['frequency']
  rates.append(dict(beginQpc=a['endQpc'],endQpc=b['endQpc'],seconds=dt,receivedPerSecond=(b['received']-a['received'])/dt,completedPerSecond=(b['callbacks']-a['callbacks'])/dt,eventsLost=b['eventsLost'],cpu100ns=b['cpu100ns']-a['cpu100ns']))
 save(R/(channel+'-callback-rates.json'),rates)
 last=s[-1];duration=max(x['duration']['maxTicks'] for x in s);lag=max(x['deliveryLag']['maxTicks'] for x in s)
 stats[channel]=dict(finalEventsLost=end['eventsLost'],effectiveAllocatedBuffersMin=min(x['numberOfBuffers'] for x in s),effectiveAllocatedBuffersMax=max(x['numberOfBuffers'] for x in s),effectiveAllocatedBuffersFinal=last['numberOfBuffers'],minimumSampledFreeBuffers=min(x['freeBuffers'] for x in s),buffersWritten=last['buffersWritten'],realTimeBuffersLost=end['realtimeBuffersLost'],logBuffersLost=end['buffersLost'],received=last['received'],completed=last['callbacks'],selected=last['selected'],maximumSampledReceiveRate=max(x['receivedPerSecond'] for x in rates),maximumSampledCompletionRate=max(x['completedPerSecond'] for x in rates),callbackDurationMaxSeconds=duration/t['frequency'] if any(x['duration']['count'] for x in s) else None,deliveryLagMaxSeconds=lag/t['frequency'] if any(x['deliveryLag']['count'] for x in s) else None,durationAndLagUnavailableReason=None if any(x['duration']['count'] for x in s) else 'No duration/delivery-lag histogram samples in existing telemetry; zero bins are not measured zero latency.',queueHighItems=t['queueHighItems'],queueHighBytes=t['queueHighBytes'],finalQueue=t['finalQueue'],slowSpans=t['slowSpans'],errors=t['errors'],overflow=t['overflow'],incrementWindows=summary[channel]['incrementWindows'],configuration=cfg)
save(R/'configuration-comparison.json',configuration);save(R/'telemetry-summary.json',stats)
assert stats['authority']['finalEventsLost']==0 and stats['detailed']['finalEventsLost']>0
targets=load(R/'independent-targets.json')['instances'];analyses={ch:load(R/(ch+'-analysis.json'))['instances'] for ch in ('authority','detailed')}
pres=C.parent/'preservation-v4'/('FAILURE-EVIDENCE-'+v['run']);pm=load(pres/'FAILURE-MANIFEST.json');pr=load(pres/'preservation-result.json')
pa=pres/('FAILURE-EVIDENCE-'+v['run']+'.zip');assert sha(pa)==pr['archiveSHA256'];f.verify_archive(pa)
origin=load(root/'cleanup-origin-v3.json');launch=load(root/'integration-launcher.json');hb=load(root/'app-heartbeats.json');heartbeat=max(x['interval'] for x in hb)
end_event=next(x for x in launch if x['event']=='FINAL_SHUTDOWN')
lines=['# CROSS_SESSION_COUPLING_SUPPORTED','',
'Run remains REJECTED. Stage 6 remains INCOMPLETE. Authority EventsLost = 0; detailed EventsLost = 100,564. This matches owner-predeclared CASE A, supporting authority cross-session coupling as a contributor. One run does not establish historical root cause or qualify the detailed observer.',
'',f"Run: `{v['run']}`",f"Workspace: `{C}`",'Exactly one normal small attempt, three approved observer launches, no retry and no configuration changes during execution.',
'','## Configuration and inputs','Authority requested mode 0x00000100 -> 0x08000100 only. Runtime returned authority mode 0x08400100; previous returned mode 0x00400100. The XOR is exactly 0x08000000. Detailed returned mode remains 0x02400100 (requested 0x02000100). Windows-added flags are distinguished from the requested mode. Every other recorded configuration field matches the preceding run. Source comparison confirms only the authority flag change; only the two approved workspace-path JSON files were rebound before launch.',
'Both 12-file / 786,432-byte synthetic SHA-256 passes matched; metadata unchanged. Frozen successor, predecessor, detailed observer, checker/finalizer and historical archives verify unchanged. Runtime/DLL/workspace bindings passed preflight.',
'','## First failure and acceptance','The launcher recorded `Management census incomplete` at QPC '+str(next(x['qpc'] for x in launch if x['event']=='EXCEPTION'))+'. Collector returned 0; Phase A and terminal receipt were recorded before this failure. Pre-shutdown management census did not complete, so the acceptance shutdown/census path could not close. Detailed terminal EventsLost independently rejects the run. No checker or success finalizer was invoked. No repair or additional experiment was performed.',
'Authority observer exited 0, detailed observer 95, application observer 0. The original failure archive remains FAILURE_EVIDENCE_PARTIAL because expected acceptance records are missing; it is not a complete acceptance seal. Its 91 members hash-verify with zero mismatches. Missing records: '+', '.join(pm['missingArtifacts'])+'.',
'','## Exact target process instances','The following correlation uses creator-retained native handles or independently creation-verified helper handles. It does not replace authoritative evidence. Detailed JSON retains each callback, sequence, disposition, admission and independently bounded loss-overlap interval.',
'','| Role | PID | Creation FILETIME | Authority START / STOP | Detailed START / STOP | Authority loss overlap | Detailed loss overlap |','|---|---:|---|---|---|---|---|']
for target in targets:
 ar=next(x for x in analyses['authority'] if x['role']==target['role']);dr=next(x for x in analyses['detailed'] if x['role']==target['role'])
 def outcomes(x):return ' / '.join(x[k]['outcome'] for k in ('START','STOP'))
 def overlaps(x):return ' / '.join(str(x[k]['lossInSurroundingInterval']) for k in ('START','STOP'))
 lines.append(f"| {target['role']} | {target['pid']} | {target['created']} | {outcomes(ar)} | {outcomes(dr)} | {overlaps(ar)} | {overlaps(dr)} |")
lines+=['','CALLBACK_ADMITTED means observed and selected/admitted; NOT_OBSERVED_BEFORE_SELECTION does not establish a selector rejection. Missing observations leave selector disposition/admission UNKNOWN. Exact analyzer labels and records are preserved without reinterpretation.',
'','## Buffer / callback / persistence context','| Measure | Authority | Detailed |','|---|---:|---:|']
for key in ('finalEventsLost','effectiveAllocatedBuffersMin','effectiveAllocatedBuffersMax','effectiveAllocatedBuffersFinal','minimumSampledFreeBuffers','buffersWritten','realTimeBuffersLost','logBuffersLost','received','completed','selected','maximumSampledReceiveRate','maximumSampledCompletionRate','callbackDurationMaxSeconds','deliveryLagMaxSeconds','queueHighItems','queueHighBytes','errors','overflow'):
 lines.append(f"| {key} | {stats['authority'][key]} | {stats['detailed'][key]} |")
lines+=['','Rates are differences between sampled counters divided by the actual sampled QPC interval, not instantaneous peak rates. Null detailed duration/lag means the existing histogram had no observations; it must not be reported as zero latency. No telemetry was added.',
'Both final writer queues have zero pending items/bytes and zero writer error. Authority persisted 28 selected records, detailed 122,969. Draining all admitted records does not recover upstream loss. Minimum sampled free buffers do not rule out pressure between samples. All raw counters, per-sample callback rates, loss increments and existing slow spans are archived.']
for ch in ('authority','detailed'):
 lines+=['',f'### {ch} EventsLost increments']
 if not stats[ch]['incrementWindows']:lines.append('None observed; final count 0.')
 for x in stats[ch]['incrementWindows']:lines.append(f"- QPC {x['beginQpc']}–{x['endQpc']}: {x['fromCount']} -> {x['toCount']}")
lines+=['','## Cleanup and preservation',f"Maximum heartbeat interval {heartbeat:.7f} seconds (<10). Original cleanup origin/deadline {origin['cleanupEntryQpc']} / {origin['deadlineQpc']}, frequency {origin['frequency']}. The 20-second absolute deadline was not reset. Launcher FINAL_SHUTDOWN occurred {(end_event['qpc']-origin['cleanupEntryQpc'])/origin['frequency']:.7f} seconds after origin. This does not establish acceptance cleanup because the required census/exit proof path failed.",
'Post-run read-only host census: zero matching diagnostic/VirtualBox processes and zero trace sessions. Independent recorded-instance census: 16 identities, all absent, zero unknown/live. This is eventual cleanup proof only; it does not erase the failed management census.',
'A separate post-quiescence NON-ACCEPTANCE archive includes raw run evidence, original failure archive and manifest, diagnostic sidecars, exact correlation, candidate/bindings, telemetry and preservation checks. It supplements the original partial archive without rewriting it. See archive-receipt.json for member verification and SHA-256.',
'Protected VM/configuration not accessed; production unchanged. No medium/large/59.7 GB run. No buffer/provider/deadline/checker/finalizer change. Historical causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.',
'','## Disposition','CROSS_SESSION_COUPLING_SUPPORTED. No Stage 6 PASS. STOP for owner review. Detailed loss and the management-census failure remain unresolved; no correction is authorized or implemented in this action.']
with (R/'REPORT.md').open('x',encoding='utf-8') as out:out.write('\n'.join(lines)+'\n')
sources=[]
for p in root.rglob('*'):
 if p.is_file():sources.append(('raw-run/'+p.relative_to(root).as_posix(),p))
for p in pres.iterdir():
 if p.is_file():sources.append(('original-failure-preservation/'+p.name,p))
for p in C.glob(v['run']+'.*lifecycle-witness*.json'):sources.append(('diagnostic-sidecars/'+p.name,p))
for row in load(C/'small-source-v3.json'):sources.append(('candidate/'+pathlib.PureWindowsPath(row['name']).as_posix(),C/row['name']))
for name in ('small-source-v3.json','witness-source-v1.json'):sources.append(('candidate/'+name,C/name))
for p in R.iterdir():
 if p.is_file() and p.name not in ('evidence.zip','archive-manifest.json','archive-receipt.json'):sources.append(('report/'+p.name,p))
manifest=[]
with contextlib.ExitStack() as stack:
 held=[]
 for name,p in sorted(sources):
  stream=stack.enter_context(f.locked_read(p));data=stream.read();digest=hashlib.sha256(data).hexdigest();held.append((name,p,stream,digest));manifest.append(dict(member=name,path=str(p),bytes=len(data),sha256=digest))
 with zipfile.ZipFile(R/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
  for name,p,stream,digest in held:stream.seek(0);z.writestr(name,stream.read())
  z.writestr('archive-manifest.json',json.dumps(manifest,indent=2))
 with zipfile.ZipFile(R/'evidence.zip') as z:
  assert len(z.namelist())==len(manifest)+1 and z.testzip() is None
  for row in manifest:assert hashlib.sha256(z.read(row['member'])).hexdigest()==row['sha256']
 for name,p,stream,digest in held:stream.seek(0);assert hashlib.file_digest(stream,'sha256').hexdigest()==digest
save(R/'archive-manifest.json',manifest)
receipt=dict(status='PASS',label='NON-ACCEPTANCE POST-QUIESCENCE EVIDENCE',archive=str(R/'evidence.zip'),sha256=sha(R/'evidence.zip'),verifiedMembers=len(manifest)+1,bytes=(R/'evidence.zip').stat().st_size,runOutcome='REJECTED',diagnosis='CROSS_SESSION_COUPLING_SUPPORTED',originalPartialArchiveUnchanged=True)
save(R/'archive-receipt.json',receipt);print(json.dumps(receipt))
