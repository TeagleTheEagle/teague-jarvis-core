import datetime, json, pathlib, sys, time, unittest
R=pathlib.Path(__file__).resolve().parent
names=['test_journal','test_processes','test_finalization','test_extended_finalization','test_probe_handles','test_event_rejection']
with (R/'focused-current.txt').open('x',encoding='utf-8') as log:
    suite=unittest.defaultTestLoader.loadTestsFromNames(names)
    started=time.monotonic()
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':sys.argv,'python':sys.executable,'modules':names,
        'executed':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'seconds':time.monotonic()-started,'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped)}
with (R/'focused-current.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
sys.exit(not result.wasSuccessful())
