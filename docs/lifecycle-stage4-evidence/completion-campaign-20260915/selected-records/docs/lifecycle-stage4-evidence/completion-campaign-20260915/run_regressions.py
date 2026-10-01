"""Bounded approved Stage 4 regression campaign; stop on any failed command."""
import datetime,hashlib,json,os,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[3];os.chdir(ROOT)
OUT=pathlib.Path(__file__).resolve().parent
PY=[str(ROOT/'.venv/Scripts/python.exe'),'-B'];F='tests/lifecycle_stage4/fixtures.py';T='tests/lifecycle_stage4/test_stage4.py'
NODE=str(pathlib.Path(os.environ['USERPROFILE'])/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
commands=[('stage1',PY+['tests/lifecycle_stage1/test_stage1.py']),('stage2',PY+['tests/lifecycle_stage2/test_stage2.py']),('stage3',PY+['tests/lifecycle_stage3/test_stage3.py'])]
commands += [(name,PY+[T,flag]) for name,flag in [('ownership','--ownership-tests'),('controller-recovery','--controller-recovery-tests'),('inspection','--inspection-tests'),('repair','--repair-tests'),('repair-loop','--repair-loop-audit')]]
commands += [('response-commit',PY+[T,'--response-commit-tests','--response-rounds','34']),('python',PY+[str(OUT/'python_regression_guard.py')]),('providers',PY+['-m','unittest','discover','-s','tests','-p','test_stage4*.py']),('desktop',[NODE,'--test',*[str(p) for d in ('desktop','intelligence') for p in sorted((ROOT/d/'test').glob('*.test.cjs'))]])]
commands += [('native',PY+[F,'--native-probe']),('bootstrap',PY+[F,'--bootstrap-probe'])]
commands += [(name,PY+[F,flag]) for name,flag in [('normal','--real-app-probe'),('emergency','--real-app-emergency'),('deadline','--real-app-deadline'),('expiry','--real-app-controller-expiry'),('inspection-cancel','--real-app-inspection-cleanup'),('inspection-detach','--real-app-inspection-detach'),('inspection-emergency','--real-app-inspection-emergency'),('repair-cancel','--real-app-repair-cleanup'),('repair-detach','--real-app-repair-detach'),('repair-emergency','--real-app-repair-emergency'),('repair-drain','--real-app-repair-drain'),('event-polling','--real-app-event-polling')]]
commands += [('fallback-integration',PY+['tests/provider_fallback_integration.py']),('deep-integration',PY+['tests/astra_deep_review_integration.py']),('deep-pipe',PY+['tests/astra_pipe_probe.py'])]
# A continuation must be an explicit invocation listing the remaining names;
# prior failures/results are never overwritten or silently retried.
if len(sys.argv)>1:commands=[x for x in commands if x[0] in sys.argv[1:]]
records=[];stamp=datetime.datetime.now().strftime('%H%M%S');result_path=OUT/('regressions-'+stamp+'.json')
for name,cmd in commands:
 log=OUT/(name+'-'+stamp+'.log');started=time.time();print('START',name,flush=True)
 with log.open('w') as stream:
  child=subprocess.Popen(cmd,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,close_fds=True,creationflags=0x08000000)
  code=child.wait()
 records.append({'name':name,'command':cmd,'cwd':str(ROOT),'pid':child.pid,'exit':code,'started':started,'elapsed':time.time()-started,'log':str(log)})
 result_path.write_text(json.dumps(records,indent=2));print('END',name,'exit',code,flush=True)
 if code:raise SystemExit(code)
print('RESULTS',result_path,flush=True)
