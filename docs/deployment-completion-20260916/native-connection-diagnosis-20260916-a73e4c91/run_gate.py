"""Authorized ordered validation; each failed gate stops advancement."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,uuid
D=Path(__file__).resolve().parent;R=D.parents[2];PY=[str(R/'.venv/Scripts/python.exe'),'-B']
mode=sys.argv[1];records=[]
if mode=='targeted':commands=json.loads((D/'targeted_commands.json').read_text())
elif mode=='restart':
    assert all(x['exit']==0 for x in json.loads((D/'targeted-command.json').read_text()))
    commands=[{'name':'restart-gate','command':PY+['tests/lifecycle_stage4/fixtures.py','--restart-campaign']}]
elif mode=='acceptance':
    assert json.loads((D/'restart-command.json').read_text())[0]['exit']==0
    commands=json.loads((R/'docs/deployment-completion-20260916/blank-ui-final-acceptance-0e09edabe3084197b3b7741807475e02/command-inventory.json').read_text())
else:raise ValueError('Unknown gate')
assert not (D/(mode+'-command.json')).exists(),'Evidence already exists; do not overwrite or retry'
for item in commands:
    log=D/(item['name']+'-'+uuid.uuid4().hex+'.log');rec={**item,'cwd':str(R),'started':time.time(),'log':str(log)}
    print('START',item['name'],flush=True)
    with log.open('x',encoding='utf8') as stream:
        p=subprocess.Popen(item['command'],cwd=R,stdout=stream,stderr=subprocess.STDOUT,close_fds=True,creationflags=0x08000000)
        rec['pid']=p.pid
        try:rec['exit']=p.wait(timeout=900)
        except subprocess.TimeoutExpired:rec.update(exit=None,retained_for_review=True)
    rec['elapsed']=time.time()-rec['started'];rec['sha256']=hashlib.sha256(log.read_bytes()).hexdigest();records.append(rec)
    (D/(mode+'-command.json')).write_text(json.dumps(records,indent=2))
    print('END',item['name'],'exit',rec['exit'],flush=True)
    if rec['exit']!=0:print('STOP FOR REVIEW',log,flush=True);sys.exit(1)
print(mode.upper(),'PASS',len(records),flush=True)
