"""Read-only evidence and exact process-identity reconciliation before advancing."""
from pathlib import Path
import hashlib,json,sys,time
D=Path(__file__).resolve().parent;R=D.parents[2]
sys.path.insert(0,str(R/'tests/lifecycle_stage2'));import pipe_transport as pt
command=json.loads((D/'restart-command.json').read_text())[0];assert command['exit']==0
log=Path(command['log']).read_text();path=Path(next(line[len('EVIDENCE '):] for line in log.splitlines() if line.startswith('EVIDENCE ')))
data=json.loads(path.read_text());assert all(x['passed'] for x in data['records'])
raw=D/'raw-evidence';raw.mkdir(exist_ok=True);copy=raw/path.name;assert not copy.exists();copy.write_bytes(path.read_bytes())
peers={}
def walk(x):
 if isinstance(x,dict):
  if {'pid','created','exe_digest'}<=x.keys():
   p={k:x[k] for k in ('pid','created','exe_digest')};peers[(p['pid'],p['created'],p['exe_digest'])]=p
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(data)
observed=[]
for p in peers.values():
 row={'expected':p}
 try:
  current=pt.identity(p['pid']);row.update(current=current,status='LIVE' if current==p else 'PID_REUSED_NOT_TOUCHED')
 except OSError as e:row.update(status='ABSENT' if e.errno in (87,1168) else 'UNKNOWN',errno=e.errno,winerror=getattr(e,'winerror',None))
 except pt.Rejected as e:row.update(status='ABSENT' if str(e)=='PROCESS_DEAD' else 'UNKNOWN',reason=str(e))
 observed.append(row)
source=json.loads((D/'preflight.json').read_text())['source_hashes']
unchanged=all(hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in source)
out={'at':time.time(),'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'checks':len(data['records']),
 'failed':sum(not x['passed'] for x in data['records']),'processes':observed,'source_unchanged_since_marker_preflight':unchanged,
 'cleanup_complete':all(x['status'] in ('ABSENT','PID_REUSED_NOT_TOUCHED') for x in observed),'no_termination':True}
(D/'restart-reconciliation.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'checks':out['checks'],'failures':out['failed'],'recorded_identities':len(observed),'cleanup_complete':out['cleanup_complete'],'source_unchanged':unchanged}))
assert out['cleanup_complete'] and unchanged
