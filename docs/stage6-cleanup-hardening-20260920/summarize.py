import pathlib,json,hashlib,sys,difflib
R=pathlib.Path(__file__).resolve().parent;plan=json.loads((R/'plan.json').read_text(encoding='utf-8-sig'));C=pathlib.Path(plan['live_code']);OLD=pathlib.Path(plan['previous'])
sys.path.insert(0,str(C));from tree_reconcile import match_child
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def arr(v):return v if isinstance(v,list) else [v]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (R/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
cases=[]
for root in sorted(C.glob('harden-?-*')):
 if not (root/'diagnostic-result.json').exists():continue
 result=read(root/'diagnostic-result.json');rows=read(root/'probe-timings.json');tree=read(root/'tree-handles.json');ev=read(root/'event-tree-reconciliation.json');taps=arr(read(root/'tap.json'));h=[json.loads(l) for l in (root/'heartbeat.jsonl').read_text(encoding='utf-8-sig').splitlines()];samples=read(root/'collector-samples.json')
 corrected=[match_child(x['start'],tree['rows'],taps) for x in ev['children']]
 values=[]
 for row in rows:
  ts=row['finalKernelTimes'];freq=row['frequency'];v=dict(pid=row['pid'],control=row['control'],created=ts[0],exit=ts[1],life=(int(ts[1])-int(ts[0]))/1e7,createSeconds=(row['createProcessReturnedQpc']-row['createProcessCalledQpc'])/freq,observerSeconds=(row['observerReturnedQpc']-row['observerWaitEnteredQpc'])/freq,observerResult=row['observerResult'],native=row.get('nativeMarkers'))
  values.append(v)
 case=dict(phase=result['phase'],path=str(root),status=result['status'],probes=len(rows),starts=ev['probeStarts'],stops=ev['probeStops'],children=len(corrected),retainedChildIdentities=sum(x['retainedMatches']==1 for x in corrected),missingChildHandles=sum(x['retainedMatches']!=1 for x in corrected),childStops=sum(x['stopMatches']==1 for x in corrected),maxLifetime=max(v['life'] for v in values),maxCreate=max(v['createSeconds'] for v in values),maxHeartbeat=max([(b['ticks']-a['ticks'])/a['frequency'] for a,b in zip(h,h[1:])],default=0),maxHeartbeatAge=max(x['age'] for x in samples),treeRows=len(tree['rows']),treeAllExited=tree['allExited'],treeClosed=tree['allHandlesClosed'],treeErrors=tree['errors'],maxTreeScan=tree['maxScanSeconds'],hardReproduced=result['hardDeadlineReproduced'],queue=ev['queue'],monitorExit=read(root/'monitor-exit.json'),probesDetail=values,correctedMatching=corrected)
 cases.append(case)
save('campaign-summary.json',cases)
oldcheck=[dict(**x,unchanged=sha(pathlib.Path(x['path']))==x['sha256']) for x in read(R/'source-before.json')];save('previous-source-verification.json',oldcheck)
original=read(R/'candidate-source.json');changes=[];final=[];diff=[]
for name in sorted({x['name'] for x in original}|{'tree_reconcile.py','test_tree_reconcile.py'}):
 p=C/name;old=OLD/name;row=dict(path=str(p),name=name,sha256=sha(p),size=p.stat().st_size);final.append(row)
 if not old.exists() or sha(old)!=sha(p):
  changes.append(dict(name=name,beforeSHA256=sha(old) if old.exists() else None,afterSHA256=sha(p)))
  if p.suffix in ('.py','.ps1','.cs','.c'):diff.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],p.read_text().splitlines(True),fromfile='previous/'+name,tofile='candidate/'+name))
save('final-source.json',final);save('files-changed.json',changes);(R/'final-diff.patch').write_text(''.join(diff))
preservation=[dict(**x,unchanged=sha(pathlib.Path(x['path']))==x['sha256']) for x in read(R/'historical-preservation-before.json')];save('historical-preservation-after.json',preservation)
syntax=[]
for row in final:
 p=pathlib.Path(row['path'])
 if p.suffix=='.py':compile(p.read_text(encoding='utf-8-sig'),str(p),'exec');syntax.append(str(p))
save('syntax-python.json',dict(files=syntax,count=len(syntax),result='PASS',method='compile(source, absolute_path, exec); no execution or pycache'))
print(json.dumps([dict(phase=x['phase'],probes=x['probes'],children=x['children'],retained=x['retainedChildIdentities'],missing=x['missingChildHandles'],maxLifetime=x['maxLifetime'],heartbeat=x['maxHeartbeat']) for x in cases]))
