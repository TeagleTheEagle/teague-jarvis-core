import pathlib,json,hashlib,shutil,uuid
R=pathlib.Path(__file__).parent
old=json.loads((R/'candidate-v3.json').read_text());O=pathlib.Path(old['code'])
for x in old['hashes']:assert hashlib.sha256((O/x['name']).read_bytes()).hexdigest()==x['sha256']
D=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';D.mkdir(parents=True)
for p in O.iterdir():
 if p.is_file() and p.name!='hardening-hashes.json':shutil.copyfile(p,D/p.name)
shutil.copyfile(D/'J6ProbeNative.exe',D/'J6Native.exe')
p=D/'hardened_collect.py';s=p.read_text().replace('from controls import make_probe','from controls import NativeProbe').replace("make_probe('A_D')","NativeProbe(CODE/'J6Native.exe',0,'A_D')");p.write_text(s)
p=D/'bounded_sampler.py';s=p.read_text()
s=s.replace("if cleanup_injection:r.update(status='MISSING',reason='INJECTED_CLEANUP_OBSERVATION_TIMEOUT')","if cleanup_injection:r.update(status='MISSING',reason='INJECTED_CLEANUP_OBSERVATION_TIMEOUT',injection='Suppress job-empty observation for existing cleanup budget; retain raw kernel result')")
s=s.replace("if state==0 and q and acc.active==0:break","if state==0 and q and acc.active==0 and not cleanup_injection:break")
s=s.replace("   r['jobCleanupObservations']=observations", """   r['cleanupObservationTimedOut']=not (state==0 and q and acc.active==0 and not cleanup_injection)
   if cleanup_injection:
    # End only the diagnostic observation fault. No new wait/retry budget.
    state=K.WaitForSingleObject(pi.process,0)
    q=K.QueryInformationJobObject(job,1,c.byref(acc),c.sizeof(acc),None)
    r['postInjectionProof']=dict(qpc=ticks(),handleState=state,jobActive=acc.active if q else None)
   r['jobCleanupObservations']=observations""")
p.write_text(s)
test='''import unittest,threading,uuid
from unittest.mock import patch
import bounded_sampler as s
from workspace import new_run,activate_temp,CODE
from lineage import associate
from test_hardening_scope import row,ev
class Boundary(unittest.TestCase):
 def test_truncated_image_remains_unknown(self):
  r=row(7,10,20,'x');r['image']=r'D:\\J6ProbeNative.exe';e=ev(7,21,'stop',received=100);e['name']='J6ProbeNative.'
  self.assertTrue(associate([r],[e],{'x'})['unknown'])
 def test_short_helper_is_exact_binary_copy(self):
  self.assertEqual((CODE/'J6Native.exe').read_bytes(),(CODE/'J6ProbeNative.exe').read_bytes())
 def test_missing_required_job_proof_fails_closed(self):
  root=new_run('missing-proof-'+uuid.uuid4().hex);activate_temp(root)
  with patch.object(s.K,'QueryInformationJobObject',return_value=0):v=s.query(root,'normal',0,threading.Event())
  self.assertEqual(v['status'],'CLEANUP_FAILED');self.assertFalse(v['allExited']);self.assertTrue(v['handleClosed']);self.assertEqual(v['handleState'],0)
'''
(D/'test_hardening_boundary.py').write_text(test)
p=D/'run_tests.py';p.write_text(p.read_text().replace("modules=['test_hardening_scope'","modules=['test_hardening_boundary','test_hardening_scope'"))
manifest=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(D.iterdir()) if p.is_file()]
(D/'hardening-hashes.json').write_text(json.dumps(manifest,indent=2))
with (R/'candidate-v4.json').open('x') as f:json.dump(dict(code=str(D),previous=str(O),hashes=manifest,correction='Short native helper filename preserves exact image checks; exercise bounded cleanup-observation timeout and missing-proof rejection.'),f,indent=2)
print(D)
