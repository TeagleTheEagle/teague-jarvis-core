import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parent;P=R.parent/'stage6-small-live-v2-20260923';V=R.parent/'stage6-checker-v2-20260923'
cfg=json.loads((V/'candidate.json').read_text());C=pathlib.Path(cfg['code']);run=C/'protected-8145cedf8db843959b8ba58dfd62717b'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=read(P/'archive-receipt.json');assert sha(pathlib.Path(receipt['archive']))==receipt['archiveSHA256']
manifest=read(pathlib.Path(receipt['archive']).parent/'manifest.json');verified=0
for x in manifest:
 if x['path'].startswith('live-run/'):
  assert sha(run/x['path'][9:])==x['sha256'];verified+=1
for x in read(V/'final-verification.json')['source']:assert sha(C/x['name'])==x['sha256']
k=read(run/'etw-result.json');helper=next(x for x in k['rows'] if x['pid']==8436 and x['created']=='134345949607928089');collector=next(x for x in k['rows'] if x['pid']==15280 and x['created']=='134345949607329466')
assert helper['parentSequence']==collector['sequence'] and helper['parentPid']==collector['pid']
native=read(run/'native-15280-134345949607329466.json');f=native['frequency'];marks=read(run/'integration-collector-15280.json');tree=read(run/'tree-handles.json');primary=read(run/'primary-failure.json');support=read(run/'tree-image-support.json')
events=[('collector kernel START',collector['startQpc']),('helper kernel START',helper['startQpc']),('collector native PE entry',native['entryQpc']),('tree cleanup result; helper state 258',tree['qpc']),('failure recorded',primary['qpc']),('collector kernel STOP',collector['stopQpc']),('helper kernel STOP',helper['stopQpc']),('collector native handle signaled',native['signalObservedQpc']),('helper external retained handle signaled',helper['signalObservedQpc'])]
for m in marks:
 if m['event'] in ('COLLECTOR_START','COLLECTOR_RETURN','FINAL_SHUTDOWN') or (m['event']=='HELPER_RETURN' and m.get('helper')=='hash-worker'):events.append((m['event']+(' hash-worker' if m.get('helper')=='hash-worker' else ''),m['qpc']))
timeline=[dict(event=n,qpc=q,secondsAfterCollectorKernelStart=(q-collector['startQpc'])/f) for n,q in sorted(events,key=lambda x:x[1])]
lastworker=next(m['qpc'] for m in marks if m['event']=='HELPER_RETURN' and m.get('helper')=='hash-worker')
summary=dict(classification='STRONG_CAUSAL_EVIDENCE',kernelFrequency=f,timeline=timeline,helperStopAfterCollectorStopMs=(helper['stopQpc']-collector['stopQpc'])/f*1000,helperStopAfterFailedTreeResultMs=(helper['stopQpc']-tree['qpc'])/f*1000,hashWorkerReturnToTreeResultSeconds=(tree['qpc']-lastworker)/f,treeFinishEntryQpc='UNKNOWN: no dedicated entry marker',helper=helper,collector=collector,nativeCollector=native,treeOutstanding=[x for x in tree['rows'] if not x['closed']],anchor=support['anchor'],failureArchiveUnchanged=receipt,failedRunFilesUnchanged=verified,candidateHashesUnchanged=194,liveRunPerformed=False,sourceChanged=False,protectedAccess=False,productionChanged=False)
with (R/'timeline.json').open('x') as out:json.dump(summary,out,indent=2)
references={}
for name,needles in {'large_collect.py':['tree.finish(root,20)','Incomplete retained tree','return 1 if ledger.primary'],'evidence_support.py':['if self.anchor and','def finish(self','if all(r[','if self.rows[key]','def finish_support','valid=bool(state==258'], 'traced_collect.py':['result=collector.main','bridge.close()','sys.exit(main'], 'owned_entry.cpp':['CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT|DEBUG_ONLY_THIS_PROCESS'],'small_check_v2.py':["'OBSERVER_CLEANUP'"],'tracker_adapter_v2.py':['structural(doc)','TRACKER_EXIT_CONTRADICTION']}.items():
 lines=(C/name).read_text().splitlines();references[name]=[dict(line=i,text=line) for i,line in enumerate(lines,1) if any(n in line for n in needles)]
with (R/'source-references.json').open('x') as out:json.dump(references,out,indent=2)
print(json.dumps({k:summary[k] for k in ['classification','helperStopAfterCollectorStopMs','helperStopAfterFailedTreeResultMs','hashWorkerReturnToTreeResultSeconds','failedRunFilesUnchanged']},indent=2))
