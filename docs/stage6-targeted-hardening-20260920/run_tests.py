import unittest,json,pathlib,uuid,sys,time
from workspace import new_run,activate_temp,CODE
root=new_run('hardening-tests-'+uuid.uuid4().hex);activate_temp(root)
modules=['test_hardening_scope','test_livepaths','test_journal','test_processes','test_finalization','test_extended_finalization','test_probe_handles','test_event_rejection','test_queue_finalization','test_failure_campaigns','test_probe_policy']
start=time.monotonic()
with (root/'tests.txt').open('x') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(modules))
out=dict(path=str(root),tests=r.testsRun,failed=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),seconds=time.monotonic()-start,modules=modules)
(root/'result.json').write_text(json.dumps(out,indent=2));print(json.dumps(out));sys.exit(not r.wasSuccessful())
