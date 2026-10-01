"""Accepted-snapshot regression inventory; preserve each result and stop on failure."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,os
R=Path(__file__).resolve().parents[2];D=R/'docs/stage5-continuation-20260917'
A=Path(json.loads((R/'docs/stage5-accepted-baseline-20260917/baseline.json').read_text())['app'])
O=D/'regressions';O.mkdir(exist_ok=True)
inventory=json.loads((R/'docs/deployment-completion-20260917/final-blockers/final-suite/commands.json').read_text())
selected=set(sys.argv[1:]);records=[]
for item in inventory:
    name=item['name']
    if selected and name not in selected:continue
    cmd=[sys.executable if 'python' in item['command'][0].lower() else item['command'][0]]
    cmd += [x.replace(str(R),str(A)) for x in item['command'][1:]]
    if name in ('fallback-restart','deep-restart'):
        source='fallback-integration' if name=='fallback-restart' else 'deep-integration'
        root=Path(json.loads((O/(source+'.log')).read_text())['root']);assert root.is_relative_to(A)
        assert (root/'TEST_ONLY').read_text()=='NO PRODUCTION SERVICES'
        cmd[-1]=str(root)
    log=O/(name+'.log');assert not log.exists(), 'Use a new explicit evidence name, never overwrite failure'
    rec={'name':name,'command':cmd,'cwd':str(A),'start':time.time()};print('START',name,flush=True)
    with log.open('x',encoding='utf8') as stream:
        env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ('API_KEY','SECRET','TOKEN','PASSWORD'))}
        p=subprocess.Popen(cmd,cwd=A,env=env,stdout=stream,stderr=subprocess.STDOUT,close_fds=True,creationflags=0x08000000)
        rec['pid']=p.pid
        try:rec['exit']=p.wait(900)
        except subprocess.TimeoutExpired:rec['exit']=None
    rec.update(elapsed=time.time()-rec['start'],log=str(log),sha256=hashlib.sha256(log.read_bytes()).hexdigest());records.append(rec)
    (O/('commands-'+str(int(records[0]['start']))+'.json')).write_text(json.dumps(records,indent=2))
    print('END',name,rec['exit'],flush=True)
    if rec['exit']!=0:sys.exit(1)
