import json,sys,time,unittest,datetime
from workspace import CODE,new_run,activate_temp
import uuid
bootstrap=new_run('focused-'+uuid.uuid4().hex);activate_temp(bootstrap)
names=['test_livepaths','test_journal','test_processes','test_finalization','test_extended_finalization','test_probe_handles','test_event_rejection','test_queue_finalization','test_failure_campaigns']
with (CODE/'focused-result.txt').open('x',encoding='utf-8') as log:
 start=time.monotonic();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),modules=names,executed=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),seconds=time.monotonic()-start)
with (CODE/'focused-result.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report));sys.exit(not result.wasSuccessful())
