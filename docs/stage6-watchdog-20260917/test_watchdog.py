from pathlib import Path
import importlib.util,json,sys,subprocess,time,types
from unittest.mock import patch,MagicMock
D=Path(__file__).resolve().parent;S=Path(json.loads((D.parent/'stage6-separated-io-20260917/source.json').read_text())['source']);sys.path.insert(0,str(S));spec=importlib.util.spec_from_file_location('tested_fixture',S/'tests/deployment_contract/fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
rows=[]
def check(name,result):
 rows.append({'case':name,'passed':bool(result)})
 if not result:raise AssertionError(name)
check('stage-update bound is finite 45',f.control_timeout('stage-update')==45)
check('all other existing controls retain 35',all(f.control_timeout(x)==35 for x in ('stage-rollback','initialize','configuration','enroll-update','commit-update','abort-update','inspect')))
b=types.SimpleNamespace(state='synthetic',python_command=lambda role:['TEST_ONLY']);c=types.SimpleNamespace(cwd=D,env={},keys={},r=types.SimpleNamespace(transport=types.SimpleNamespace(identity=lambda pid:{'pid':pid,'created':1,'exe_digest':'synthetic'})),controls=[],save=lambda:None)
child=MagicMock();child.pid=123;child.communicate.side_effect=subprocess.TimeoutExpired('TEST_ONLY',45)
with patch.object(f.subprocess,'Popen',return_value=child):
 try:f.InstalledCampaign.control(c,b,'stage-update',request={'synthetic':True})
 except subprocess.TimeoutExpired:check('timeout propagates rather than returning success',True)
 else:check('timeout propagates rather than returning success',False)
check('one communication attempt only',child.communicate.call_count==1)
check('corrected bound reaches actual communicate call',child.communicate.call_args.kwargs['timeout']==45)
check('timeout has no false successful control record',not c.controls)
# Real disposable sleeping child proves the wait still expires; it exits by itself.
p=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(47)'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=0x08000000)
peer=f.ClientCampaign.__module__
start=time.monotonic();timed_out=False
try:p.communicate(timeout=f.control_timeout('stage-update'))
except subprocess.TimeoutExpired:timed_out=True;elapsed=time.monotonic()-start
finally:p.communicate(timeout=8)
check('actual stalled TEST child trips finite watchdog',timed_out)
check('stalled TEST child exits naturally',p.returncode==0)
(D/'watchdog-results.json').write_text(json.dumps({'checks':rows,'observed_deadline_seconds':elapsed if timed_out else None,'child_pid':p.pid,'child_exit':p.returncode,'core_started':False,'production_changed':False},indent=2));print(json.dumps({'checks':len(rows),'passed':sum(x['passed'] for x in rows)}))
