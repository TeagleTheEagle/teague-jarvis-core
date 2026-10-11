import pathlib,json,collections
from trace_segments import verify
def inspect(root):
 root=pathlib.Path(root);read=lambda n:json.loads((root/n).read_text(encoding='utf-8-sig'))
 segments=verify(root);kernel=read('etw-result.json')['rows'];producer=read('stress-result.json')
 wanted={(producer['collectorPid'],next(x['created'] for x in kernel if x['pid']==producer['collectorPid']))}
 wanted.update((x['pid'],str(x['created'])) for x in producer['launched'])
 natives=[json.loads(p.read_text()) for p in root.glob('native-*.json') if p.name!='native-bridge-cleanup.json']
 keys=[(x['pid'],x['created']) for x in natives]
 assert len(keys)==len(set(keys)) and set(keys)==wanted,('native coverage',wanted,set(keys))
 timings=[]
 for n in natives:
  k=next(x for x in kernel if (x['pid'],x['created'])==(n['pid'],n['created']))
  assert not n['fault'] and not n['deadlineExceeded'] and n['finalWait']==0 and n['exitFiletime']==k['exitFiletime']
  assert k['startQpc']<=n['entryQpc']<=k['stopQpc']
  assert len([e for e in n['events'] if e['event']=='PE_ENTRY_EXECUTED'])==1
  t=dict(pid=n['pid'],created=n['created'],creationToPEms=(n['entryQpc']-k['startQpc'])/n['frequency']*1000,createCallMs=(n['createEndQpc']-n['createBeginQpc'])/n['frequency']*1000,PEtoPythonMs=None,PythonToMarkerMs=None,reason='Native-only J6Probe has no Python interpreter')
  markers=[]
  for p in root.glob('integration-*-*.json'):
   rows=json.loads(p.read_text());first=rows[0]
   if (first['pid'],first['created'])==(n['pid'],n['created']):markers=rows;break
  if markers:
   m=markers[0];pythonSeconds=m['pythonEntryNs']/1e9;peSeconds=n['entryQpc']/n['frequency'];assert peSeconds<=pythonSeconds<=m['qpc']/m['frequency']
   assert markers[-1]['event']=='FINAL_SHUTDOWN'
   t.update(PEtoPythonMs=(pythonSeconds-peSeconds)*1000,PythonToMarkerMs=(m['qpc']/m['frequency']-pythonSeconds)*1000,reason=None,role=m['role'])
  timings.append(t)
 bridge=read('native-bridge-cleanup.json');assert bridge['allThreadsExited'] and not bridge['errors']
 return dict(trace=segments,nativeEntries=len(natives),timings=timings,identity='PID + kernel creation FILETIME + ETW process sequence lineage',conhost='Kernel process/thread/image evidence; OS-created console helper is not an own-child PE-debug target')
if __name__=='__main__':
 import sys
 from workspace import run_dir,activate_temp
 root=run_dir(sys.argv[1]);activate_temp(root);result=inspect(root)
 with (root/'native-trace-verification.json').open('x') as f:json.dump(result,f,indent=2)
 # Only the unchanged finalizer decides collector success after native/trace gates pass.
 from baseline_finalize import finalize
 print(json.dumps(dict(native=result,collector=finalize(root))))
