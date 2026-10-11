"""Archive exact previously recorded stale readiness; validate corrected crash cleanup."""
from pathlib import Path
import hashlib,json,sys,traceback
D=Path(__file__).resolve().parent;R=D.parents[2]
sys.path[:0]=[str(R),str(R/'tests/lifecycle_stage4')]
from fixtures import RestartCampaign
import stage4_runtime as r
prior=json.loads((D.parent/'readiness-publication-fix/cleanup-reconciliation.json').read_text())
archive=D/'retired-readiness';archive.mkdir(exist_ok=False);retired=[]
for name in prior['remaining_readiness_artifacts']:
    path=Path(name);root=r.exclusion.validate(path.parent)
    assert root.parent==r.exclusion.BASE and root.name.startswith('TEST-STAGE4-')
    data=json.loads(path.read_text());pin=data['peer']
    assert data['identity']['namespace']==root.name
    try:live=r.transport.identity(pin['pid'])
    except OSError as exc:
        if exc.errno!=87:raise
        live=None
    except r.transport.Rejected as exc:
        if str(exc)!='PROCESS_DEAD':raise
        live=None
    assert live!=pin,'Recorded TEST coordinator still live; STOP'
    content=path.read_bytes();target=archive/(root.name+'-'+path.name)
    target.write_bytes(content);assert target.read_bytes()==content
    digest=hashlib.sha256(content).hexdigest();path.unlink()
    retired.append({'path':str(path),'identity':pin,'current':live,'sha256':digest,'preserved':str(target),'removed':not path.exists()})
    (D/'retired-readiness.json').write_text(json.dumps(retired,indent=2))
c=RestartCampaign();c.path=D/'cleanup-crash-tests.json'
try:
    for stage in ('before-intent','intent','claimed','spawned'):
        c.fault_case(stage)
    for root in c.roots:
        leftovers=list(root.glob('coordinator-*.json*'))
        c.check('no coordinator readiness or temp artifacts after crash recovery',not leftovers,root=str(root),leftovers=[str(x) for x in leftovers])
    for item in c.coordinators:c.check('owned coordinator exited',item['process'].poll() is not None,pid=item['process'].pid)
    for root,core,identity in c.cores:
        c.check('recorded Core identity exited',r.exclusion.process_identity(identity['pid'])!={k:identity[k] for k in ('pid','created')},identity=identity)
        with r.exclusion.Lock(root,'core.lock'):pass
except BaseException:
    c.records.append({'case':'cleanup validation failure','passed':False,'traceback':traceback.format_exc()})
    raise
finally:c.save()
print(json.dumps({'checks':len(c.records),'failures':sum(not x['passed'] for x in c.records),'retired':len(retired),'evidence':str(c.path)}))
