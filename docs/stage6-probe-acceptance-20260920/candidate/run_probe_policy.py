import json,unittest,uuid,time,sys
from workspace import CODE,new_run,activate_temp
r=new_run('probe-policy-'+uuid.uuid4().hex);activate_temp(r)
with (r/'tests.txt').open('x') as f:
 start=time.monotonic();result=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_probe_policy'))
v=dict(executed=result.testsRun,passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),seconds=time.monotonic()-start,status='PASS' if result.wasSuccessful() else 'FAIL')
(r/'result.json').write_text(json.dumps(v,indent=2));print(json.dumps(dict(path=str(r),**v)));sys.exit(not result.wasSuccessful())
