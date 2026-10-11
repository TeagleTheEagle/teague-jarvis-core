"""Approved ordered TEST gates; stop at first nonzero exit, retain every log."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
D=Path(__file__).resolve().parent
R=D.parents[2]
inventory=json.loads((R/'docs/deployment-completion-20260916/blank-ui-final-acceptance-0e09edabe3084197b3b7741807475e02/command-inventory.json').read_text())
indexed={x['name']:x for x in inventory}
assert not (D/'validation.json').exists()
commands=[indexed['native'],{'name':'native-readiness-unit','command':[str(R/'.venv/Scripts/python.exe'),'-B','tests/lifecycle_stage4/test_native_readiness.py']},indexed['desktop'],indexed['event-polling'],indexed['response-commit']]
commands += [{**x,'name':'acceptance-'+x['name']} for x in inventory]
records=[]
for item in commands:
    log=D/(item['name']+'.log')
    rec={**item,'started':time.time(),'log':str(log),'cwd':str(R)}
    print('START',item['name'],flush=True)
    with log.open('x',encoding='utf8') as f:
        p=subprocess.Popen(item['command'],cwd=R,stdout=f,stderr=subprocess.STDOUT,close_fds=True,creationflags=0x08000000)
        rec['pid']=p.pid
        try:rec['exit']=p.wait(900)
        except subprocess.TimeoutExpired:rec.update(exit=None,retained_for_review=True)
    rec['elapsed']=time.time()-rec['started'];rec['sha256']=hashlib.sha256(log.read_bytes()).hexdigest();records.append(rec)
    (D/'validation.json').write_text(json.dumps(records,indent=2))
    print('END',item['name'],rec['exit'],flush=True)
    if rec['exit']!=0:sys.exit(1)
