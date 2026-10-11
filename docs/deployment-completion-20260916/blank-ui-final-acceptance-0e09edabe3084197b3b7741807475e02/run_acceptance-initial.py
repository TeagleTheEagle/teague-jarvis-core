"""Execute the existing Stage 4 regression inventory, stopping at its first failure."""
import hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
PY=[str(ROOT/'.venv/Scripts/python.exe'),'-B']
prior=json.loads((ROOT/'docs/lifecycle-stage5-evidence/regressions-081519.json').read_text())
# These are the existing Stage 4 regressions; the source inventory's folder
# name does not introduce any Stage 5 campaign or new authority.
order=['response-commit','event-polling']+[x['name'] for x in prior if x['name'] not in ('response-commit','event-polling')]
lookup={x['name']:x for x in prior}
commands=[{'name':n,'command':lookup[n]['command'],'cwd':str(ROOT)} for n in order]
commands += [
 {'name':'restart-transaction','command':PY+['tests/lifecycle_stage4/test_stage4.py','--restart-transaction-tests'],'cwd':str(ROOT)},
 {'name':'full-start-crash-restart','command':PY+['tests/lifecycle_stage4/fixtures.py','--restart-campaign'],'cwd':str(ROOT)},
 {'name':'fallback-restart','command':PY+['tests/provider_history_restart.py'],'cwd':str(ROOT)},
 {'name':'deep-restart','command':PY+['tests/astra_restart_probe.py'],'cwd':str(ROOT)}]
# Check the inventory before launching anything; missing scripts are a review
# item, never permission to substitute an invented acceptance path.
for item in commands:
 for arg in item['command'][1:]:
  if str(arg).endswith('.py'):assert (ROOT/arg).is_file(),arg
(OUT/'command-inventory.json').write_text(json.dumps(commands,indent=2))
records=[]
for item in commands:
 name=item['name'];log=OUT/(name+'-'+uuid.uuid4().hex+'.log')
 rec={**item,'started':time.time(),'log':str(log)}
 print('START',name,flush=True)
 with log.open('x',encoding='utf-8') as stream:
  p=subprocess.Popen(item['command'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,close_fds=True,creationflags=0x08000000)
  rec['pid']=p.pid
  try:rec['exit']=p.wait(timeout=900)
  except subprocess.TimeoutExpired:rec['exit']=None;rec['retained_for_review']=True
 rec['elapsed']=time.time()-rec['started'];rec['sha256']=hashlib.sha256(log.read_bytes()).hexdigest();records.append(rec)
 (OUT/'regressions.json').write_text(json.dumps(records,indent=2))
 print('END',name,'exit',rec['exit'],flush=True)
 if rec['exit']!=0:
  print('STOP; failure preserved:',log,flush=True);sys.exit(1)
print('AUTOMATED NON-ELECTRON INVENTORY PASS',len(records),flush=True)
