"""Read-only OS identity census of already-recorded TEST identities; no cleanup."""
from pathlib import Path
import collections,json,sys,time
D=Path(__file__).resolve().parent;R=D.parents[2]
sys.path.insert(0,str(R/'tests/lifecycle_stage2'));import pipe_transport as pt
expected={}
def walk(x):
    if isinstance(x,dict):
        if {'pid','created','exe_digest'}<=x.keys() and isinstance(x['pid'],int):
            p={k:x[k] for k in ('pid','created','exe_digest')};p['created']=int(p['created'])
            expected[(p['pid'],p['created'],p['exe_digest'])]=p
        for v in x.values():walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
for p in (D/'raw-evidence').glob('*.json'):walk(json.loads(p.read_text()))
walk(json.loads((D/'coordinator-results.json').read_text()))
rows=[]
for p in expected.values():
    row={'expected':p}
    try:
        actual=pt.identity(p['pid']);row.update(actual=actual,status='MATCHING_TEST_IDENTITY_LIVE' if actual==p else 'PID_REUSED_NOT_TOUCHED')
    except OSError as e:row.update(status='ABSENT' if e.errno in (87,1168) else 'UNKNOWN',errno=e.errno,winerror=getattr(e,'winerror',None))
    except pt.Rejected as e:row.update(status='ABSENT' if str(e)=='PROCESS_DEAD' else 'UNKNOWN',reason=str(e))
    rows.append(row)
out={'at':time.time(),'rows':rows,'counts':dict(collections.Counter(x['status'] for x in rows)),'no_termination':True,
     'limitation':'Native probe does not persist its Electron child and idle-process creation identities. Those children were waited by the completed probe; separate current command/process census is supplemental, not historical proof.'}
target=D/'process-reconciliation.json';assert not target.exists();target.write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({'identities':len(rows),'counts':out['counts'],'no_termination':True}))
