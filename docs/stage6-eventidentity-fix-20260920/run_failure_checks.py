import unittest,pathlib,json,time,sys
R=pathlib.Path(__file__).resolve().parent
names=['test_queue_finalization','test_failure_campaigns']
start=time.monotonic()
with (R/'failure-checks.txt').open('x') as f:
 r=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
v=dict(modules=names,executed=r.testsRun,passed=r.testsRun-len(r.failures)-len(r.errors)-len(r.skipped),failed=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),seconds=time.monotonic()-start)
with (R/'failure-checks.json').open('x') as f:json.dump(v,f,indent=2)
print(json.dumps(v));sys.exit(not r.wasSuccessful())
