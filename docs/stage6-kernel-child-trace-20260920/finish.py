import pathlib,json,hashlib,subprocess,datetime,collections,sys
r=pathlib.Path(__file__).parent;p=json.loads((r/'plan.json').read_text());code=pathlib.Path(p['live_code']);repo=r.parent.parent
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,x):
 with (r/n).open('x') as f:json.dump(x,f,indent=2)
prior=json.loads((r.parent/'stage6-cleanup-hardening-20260920/repository-after.json').read_text())
current=[]
for x in prior['applicationFiles']:
 q=repo/x['path'];current.append(dict(path=x['path'],sha256=h(q),matchesPrevious=h(q)==x['sha256']))
git={}
for n,args in [('head',['rev-parse','HEAD']),('status',['status','--porcelain=v1','-unormal'])]:
 q=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True);git[n]=dict(exit=q.returncode,stdout=q.stdout,stderr=q.stderr)
put('application-preservation.json',dict(files=current,allUnchanged=all(x['matchesPrevious'] for x in current),git=git))
before=json.loads((r/'source-before.json').read_text());cmp=[]
for x in before:cmp.append(dict(name=x['name'],expected=x['sha256'],current=h(code/x['name']),historical=h(pathlib.Path(x['path'])),unchanged=x['sha256']==h(code/x['name'])==h(pathlib.Path(x['path']))))
put('inherited-source-preservation.json',dict(files=cmp,allUnchanged=all(x['unchanged'] for x in cmp)))
final=[dict(name=q.name,path=str(q),sha256=h(q),size=q.stat().st_size) for q in sorted(code.iterdir()) if q.is_file() and q.suffix in ('.py','.ps1','.cs','.cpp','.exe')]
put('final-source.json',final)
cases=[];identities={}
for root in sorted(list(code.glob('etw-smoke-*'))+list(code.glob('etw-stress-*'))+list(code.glob('kernel-e-*'))):
 if not (root/'etw-result.json').exists():continue
 e=json.loads((root/'etw-result.json').read_text());rows=e['rows'];ready=json.loads((root/'etw-ready.json').read_text());frequency=ready['frequency'];main=[]
 if (root/'probe-timings.json').exists():main=json.loads((root/'probe-timings.json').read_text())
 j=dict(run=root.name,root=str(root),etwObserved=len(rows),etwLost=e['eventsLost'],etwFaults=e['faults'],mainProbes=len(main),maxMainLifetime=max([(int(x['finalKernelTimes'][1])-int(x['finalKernelTimes'][0]))/1e7 for x in main],default=None),hardDeadline=any(x.get('hardDeadlineFailure') for x in main),independentObserverFailures=sum(x.get('independentObserverFailed',False) for x in main))
 if (root/'kernel-reconciliation.json').exists():
  k=json.loads((root/'kernel-reconciliation.json').read_text());j.update(kernelStatus=k['status'],retained=k['retained'],nonretained=k['justifiedNonretained'],unknown=k['unknown'])
 if (root/'diagnostic-result.json').exists():
  d=json.loads((root/'diagnostic-result.json').read_text());j.update(collectorStatus=d['status'],primary=d['primary_failure'])
 if (root/'collector-samples.json').exists():
  samples=json.loads((root/'collector-samples.json').read_text());j['maxHeartbeatAge']=max([s['age'] for s in samples],default=None)
 if (root/'event-tree-reconciliation.json').exists():
  t=json.loads((root/'event-tree-reconciliation.json').read_text());j.update(wmiStarts=t['probeStarts'],wmiStops=t['probeStops'],oldPollingMissing=len(t['unproven']),queue=t['queue'])
 if (root/'worker-trace.json').exists():
  wt=json.loads((root/'worker-trace.json').read_text());reads=[(x['readEnd']-x['start'])/frequency for x in wt if x['stage']=='read.hash'];j['maxSacrificialReadSeconds']=max(reads,default=None)
 cases.append(j)
 for x in rows:identities[(x['pid'],x['created'])]=dict(pid=x['pid'],created=x['created'],image=x['image'],kernelExit=x['exitFiletime'],exitCode=x['exitCode'],scope=root.name)
 l=json.loads((root/'launcher.json').read_text());identities[(l['pid'],l['creationFiletime'])]=dict(pid=l['pid'],created=l['creationFiletime'],image=l['image'],scope='launcher')
 for n in ('launch.json','etw-ready.json'):
  if (root/n).exists():
   x=json.loads((root/n).read_text());
   if 'created' in x:identities[(x['pid'],x['created'])]=dict(pid=x['pid'],created=x['created'],image=x.get('executable'),scope='monitor')
 # ETW monitor exit was observed through the launcher-held Process handle.
put('campaign-summary.json',cases);put('known-identities.json',list(identities.values()))
print(json.dumps(dict(cases=cases,applicationUnchanged=all(x['matchesPrevious'] for x in current),applicationFiles=len(current),inheritedSourceFiles=len(cmp),inheritedSourceUnchanged=all(x['unchanged'] for x in cmp),identityCount=len(identities)),indent=2))
