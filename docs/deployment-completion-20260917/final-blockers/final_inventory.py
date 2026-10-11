"""One final inventory; restart helpers receive their fresh integration namespace."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
D=Path(__file__).resolve().parent;R=D.parents[2];O=D/'final-suite';O.mkdir(exist_ok=False)
inventory=json.loads((R/'docs/deployment-completion-20260916/blank-ui-final-acceptance-0e09edabe3084197b3b7741807475e02/command-inventory.json').read_text())
records=[]
for item in inventory:
    command=list(item['command']);name=item['name']
    if name in ('fallback-restart','deep-restart'):
        source='fallback-integration' if name=='fallback-restart' else 'deep-integration'
        prior=next(x for x in records if x['name']==source);assert prior['exit']==0
        root=Path(json.loads((O/(source+'.log')).read_text())['root']).resolve()
        assert root.parent==R/'tests/lifecycle_stage1/evidence' and root.name.startswith('TEST-STAGE4-')
        assert (root/'TEST_ONLY').read_text()=='NO PRODUCTION SERVICES'
        command.append(str(root))
    rec={'name':name,'command':command,'cwd':str(R),'started':time.time()};log=O/(name+'.log')
    print('START',name,flush=True)
    with log.open('x',encoding='utf8') as out:
        p=subprocess.Popen(command,cwd=R,stdout=out,stderr=subprocess.STDOUT,close_fds=True,creationflags=0x08000000)
        rec['pid']=p.pid
        try:rec['exit']=p.wait(900)
        except subprocess.TimeoutExpired:rec.update(exit=None,retained_for_review=True)
    rec.update(elapsed=time.time()-rec['started'],sha256=hashlib.sha256(log.read_bytes()).hexdigest(),log=str(log));records.append(rec)
    (O/'commands.json').write_text(json.dumps(records,indent=2))
    print('END',name,rec['exit'],flush=True)
    if rec['exit']!=0:sys.exit(1)
print('FINAL INVENTORY PASS',len(records),flush=True)
