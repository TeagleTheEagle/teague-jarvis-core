"""Invoke existing offline integration then restart helper on its fresh TEST root."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
D=Path(__file__).resolve().parent;R=D.parents[2]
sys.path.insert(0,str(R/'tests/lifecycle_stage2'))
import pipe_transport as transport
records=[]
def run(name,args):
    path=D/(name+'.log')
    with path.open('x',encoding='utf8') as f:
        command=[str(R/'.venv/Scripts/python.exe'),'-B',*args]
        p=subprocess.Popen(command,cwd=R,stdout=f,stderr=subprocess.STDOUT,close_fds=True,creationflags=0x08000000)
        pin=transport.identity(p.pid);exit_=p.wait(30)
    records.append({'name':name,'command':command,'identity':pin,'exit':exit_,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (D/'fallback-commands.json').write_text(json.dumps(records,indent=2))
    if exit_:raise RuntimeError(name+' failed; evidence preserved')
    return json.loads(path.read_text())
first=run('fallback-integration',['tests/provider_fallback_integration.py'])
root=Path(first['root']).resolve()
assert root.parent==R/'tests/lifecycle_stage1/evidence' and root.name.startswith('TEST-STAGE4-')
assert (root/'TEST_ONLY').read_text()=='NO PRODUCTION SERVICES'
assert first['passed']==first['total']
second=run('fallback-restart',['tests/provider_history_restart.py',str(root)])
assert second['passed']==4 and records[0]['identity']!=records[1]['identity']
sys.path.insert(0,str(R));import stage4_runtime as runtime
with runtime.exclusion.Lock(root,'core.lock'):pass
result={'integration_checks':first['passed'],'restart_checks':second['passed'],'root':str(root),'fresh_processes':records,'lifetime_lock_released':True,'scope':second['scope'],'production_changed':False,'paid_calls':0}
(D/'fallback-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
