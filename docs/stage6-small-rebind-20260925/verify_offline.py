import pathlib,json,sys,os,unittest,ast
R=pathlib.Path(__file__).parent
C=pathlib.Path(json.loads((R/'rebind.json').read_text())['candidate'])
os.chdir(C);sys.path[0]=str(C)
import workspace_binding_v4 as b
runtime=b.runtime_policy()
os.environ['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(v['path']).parent) for v in runtime['executables'].values()))
os.environ['PSModulePath']=os.pathsep.join(runtime['moduleRoots']);os.environ['PYTHONNOUSERSITE']='1'
b.environment(runtime)
rows=b.manifest();b.policy();b.dll_path()
for r in rows:
 p=C/r['name']
 if p.suffix in ('.py','.ps1','.hpp','.cpp','.json','.cs'):
  text=p.read_text(errors='replace')
  assert 'loss_measurement_v3' not in text and 'timestamp-reuse-v1' not in text,p
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'))
import test_binding_v4,test_handoff_v1,test_coordination_v3
loader=unittest.TestLoader();suite=unittest.TestSuite()
def add(s):
 for x in s:
  if isinstance(x,unittest.TestSuite):add(x)
  elif not x.id().endswith('test_real_junction_rejection'):suite.addTest(x)
add(loader.loadTestsFromModule(test_binding_v4));add(loader.loadTestsFromModule(test_handoff_v1));add(loader.loadTestsFromModule(test_coordination_v3))
with (R/'focused-tests.txt').open('x') as f:
 result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
out=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),excluded=['real junction creation; mocked reparse rejection retained'],success=result.wasSuccessful())
with (R/'focused-tests.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));sys.exit(0 if result.wasSuccessful() else 1)
