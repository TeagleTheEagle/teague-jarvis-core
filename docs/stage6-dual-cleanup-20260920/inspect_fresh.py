"""Phase D/F evidence inventory only; does not seal cleanup acceptance."""
import pathlib,json,sys,collections
root=pathlib.Path(sys.argv[1]);R=pathlib.Path(__file__).parent
def read(n):return json.loads((root/n).read_text(encoding='utf-8-sig'))
e=read('etw-result.json');s=read('stress-result.json');a=read('app-result.json');tree=read('tree-handles.json');events=[json.loads(l) for l in (root/'app-events.jsonl').read_text(encoding='utf-8-sig').splitlines()]
rows=e['rows'];roots=[x for x in rows if x['pid']==s['collectorPid']];assert len(roots)==1
scope={roots[0]['sequence']}
while True:
 updated=scope|{x['sequence'] for x in rows if x['parentSequence'] in scope}
 if updated==scope:break
 scope=updated
tracked=[x for x in rows if x['sequence'] in scope];handles={(x['pid'],x['created']):x for x in tree['rows']};facts=[]
for x in tracked:
 starts=[v for v in events if v['kind']=='start' and v['pid']==x['pid']];stops=[v for v in events if v['kind']=='stop' and v['pid']==x['pid']]
 h=handles.get((x['pid'],x['created']));kept=bool(h) or x['handleRetained']
 facts.append(dict(pid=x['pid'],created=x['created'],sequence=x['sequence'],parentPid=x['parentPid'],image=x['image'],appStarts=len(starts),appStops=len(stops),appStartParent=starts[0]['parentPid'] if len(starts)==1 else None,appStartName=starts[0]['name'] if len(starts)==1 else None,kernelStart=x['startQpc'],kernelStop=x['stopQpc'],handleRetained=kept,acquisitionBegin=x.get('handleAttemptBeginQpc'),openError=x['openError'],postExitOrdering=not kept and x.get('handleAttemptBeginQpc',0)>x['stopQpc']>0,handleSource='TOOLHELP_OR_LAUNCHER' if h else ('ETW' if x['handleRetained'] else 'NONE')))
summary=dict(run=str(root),status='EVIDENCE_INVENTORY_ONLY',identityTotal=len(facts),appStarts=sum(x['appStarts'] for x in facts),appStops=sum(x['appStops'] for x in facts),kernelCreates=sum(bool(x['kernelStart']) for x in facts),kernelExits=sum(bool(x['kernelStop']) for x in facts),retained=sum(x['handleRetained'] for x in facts),postExit=sum(x['postExitOrdering'] for x in facts),missingApplicationPairs=[x['pid'] for x in facts if x['appStarts']!=1 or x['appStops']!=1],appCollectorSuccess=a['success'],appQueue=a['queue'],kernelFaults=e['faults'],kernelEventsLost=e['eventsLost'],workStatus=s['status'],outsideTrackedKernelIdentities=[dict(pid=x['pid'],created=x['created'],image=x['image'],reason='Outside stress collector descendant tree; infrastructure') for x in rows if x['sequence'] not in scope],identities=facts)
with (root/'dual-evidence-inventory.json').open('x') as f:json.dump(summary,f,indent=2)
print(json.dumps({k:v for k,v in summary.items() if k not in ('identities','outsideTrackedKernelIdentities')},indent=2))
