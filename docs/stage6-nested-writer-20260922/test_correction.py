import ast,copy,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'candidate.json').read_text());C=Path(pre['code']);old=Path(pre['originalCode']);root=Path(pre['originalRun']['path']);K=C/'medium-checker';sys.path[:0]=[str(K),str(C)]
import checker_telemetry as ct
import checker_medium as legacy
import telemetry
import fresh_binding as fb
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,allow_nan=False).encode()).hexdigest()
fb.verify_intake(old)
bundle=legacy.adapter.read_bundle(root,root/'analysis',root/'final-host-state.json');measure=telemetry.load(root/'kernel-authority-telemetry.json');decl=legacy.load(old/'medium-declaration.json')
verified=telemetry.verify(root);originalDigest=digest(bundle)
assert bundle['qualification']['writer']==bundle['writer']
F=C/'offline-fixtures';F.mkdir()
fixture=dict(schema='stage6-analyzer-regression-fixture-v1',purpose='READ_ONLY REGRESSION; NOT NEW ACCEPTANCE',sourceRun=str(root),intakeSHA256=fb.sha(root/'intake-manifest.json'),qualificationSHA256=fb.sha(root/'analysis/qualification-result.json'),writerSHA256=fb.sha(root/'kernel-authority-result.json'),archiveSHA256=pre['archive']['archiveSHA256'],bundle=bundle,measurements=measure,declaration=decl)
save(F/'actual-analyzer-fixture.json',fixture)
checks=[]
def test(name,fn,reject=False,reason=None):
 error=None
 try:result=fn();actual='PASS'
 except (ValueError,KeyError,TypeError,OSError,IndexError) as e:actual='REJECT';error=str(e)
 expected='REJECT' if reject else 'PASS';okay=actual==expected and (reason is None or reason==error)
 checks.append(dict(case=name,expected=expected,actual=actual,reason=error,passed=okay))
 if not okay:save(R/'failed-tests.json',dict(checks=checks));raise AssertionError(name)
spec=importlib.util.spec_from_file_location('preserved_checker_v4',old/'medium-checker/checker_telemetry.py');v4=importlib.util.module_from_spec(spec);spec.loader.exec_module(v4)
test('actual analyzer reproduces original strict schema rejection',lambda:v4.rules(bundle,measure,decl),True,'SCHEMA_FIELDS:$.bundle.qualification.writer')
test('actual analyzer passes corrected rules',lambda:ct.rules(bundle,measure,decl))
test('disk telemetry verification matches rule telemetry',lambda:legacy.need(ct.rules(bundle,measure,decl)['telemetry']==verified,'METRIC_DRIFT'))
test('input evidence unchanged after compatibility conversion',lambda:legacy.need(digest(bundle)==originalDigest,'INPUT_MUTATED'))
def projected():
 b=ct.compatibility_view(bundle);legacy.need(b['writer']==b['qualification']['writer'] and 'telemetry' not in b['writer'] and all('timing' not in s for s in b['writer']['segments']),'PROJECTION');b['qualification']['writer']['fault']=999;legacy.need(b['writer']['fault']==0 and digest(bundle)==originalDigest,'ALIASED_INPUT')
test('conversion consistent and non-aliasing',projected)
mutations=[
 ('missing qualification',lambda b:b.pop('qualification'),'NESTED_WRITER_MISSING'),
 ('missing nested writer',lambda b:b['qualification'].pop('writer'),'NESTED_WRITER_MISSING'),
 ('null nested writer',lambda b:b['qualification'].update(writer=None),'NESTED_WRITER_MISSING'),
 ('partial nested telemetry',lambda b:b['qualification']['writer'].pop('telemetry'),'NESTED_WRITER_CONFLICT'),
 ('partial nested timing',lambda b:b['qualification']['writer']['segments'][0].pop('timing'),'NESTED_WRITER_CONFLICT'),
 ('nested accepted mismatch',lambda b:b['qualification']['writer'].update(accepted=1),'NESTED_WRITER_CONFLICT'),
 ('nested written mismatch',lambda b:b['qualification']['writer'].update(written=1),'NESTED_WRITER_CONFLICT'),
 ('nested fault mismatch',lambda b:b['qualification']['writer'].update(fault=1),'NESTED_WRITER_CONFLICT'),
 ('nested bool replacing zero',lambda b:b['qualification']['writer'].update(fault=False),'NESTED_WRITER_CONFLICT'),
 ('nested int replacing bool',lambda b:b['qualification']['writer'].update(threadsExited=1),'NESTED_WRITER_CONFLICT'),
 ('nested float replacing int',lambda b:b['qualification']['writer'].update(accepted=float(b['writer']['accepted'])),'NESTED_WRITER_CONFLICT'),
 ('nested manifest hash mismatch',lambda b:b['qualification']['writer']['telemetry'].update(sha256='0'*64),'NESTED_WRITER_CONFLICT'),
 ('nested telemetry version mismatch',lambda b:b['qualification']['writer']['telemetry'].update(schema='unknown'),'NESTED_WRITER_CONFLICT'),
 ('nested segment hash mismatch',lambda b:b['qualification']['writer']['segments'][0].update(sha256='0'*64),'NESTED_WRITER_CONFLICT'),
 ('nested segment order mismatch',lambda b:b['qualification']['writer']['segments'].reverse(),'NESTED_WRITER_CONFLICT'),
 ('nested missing segment',lambda b:b['qualification']['writer']['segments'].pop(),'NESTED_WRITER_CONFLICT'),
 ('nested state mismatch',lambda b:b['qualification']['writer']['segments'][0].update(states=[0]),'NESTED_WRITER_CONFLICT'),
 ('nested timing mismatch',lambda b:b['qualification']['writer']['segments'][0]['timing'].update(flushEnd=0),'NESTED_WRITER_CONFLICT'),
 ('nested unknown field',lambda b:b['qualification']['writer'].update(unrecognized=True),'NESTED_WRITER_CONFLICT'),
]
for name,mutation,reason in mutations:
 def run(mutation=mutation):
  b=copy.deepcopy(bundle);mutation(b);ct.rules(b,measure,decl)
 test(name,run,True,reason)
def unknown_both():
 b=copy.deepcopy(bundle);b['writer']['unrecognized']=True;b['qualification']['writer']['unrecognized']=True;ct.rules(b,measure,decl)
test('matching unknown fields still fail strict legacy schema',unknown_both,True)
def key_order():
 b=copy.deepcopy(bundle);b['qualification']['writer']=dict(reversed(list(b['writer'].items())));return ct.rules(b,measure,decl)
test('object key order is not a semantic conflict',key_order)
for label,mutation in [
 ('missing creator handle',lambda b:b['coverage']['handles'].pop()),
 ('missing native entry',lambda b:b['coverage']['natives'].pop()),
 ('missing kernel start',lambda b:b['events'].pop()),
 ('heartbeat at unchanged limit',lambda b:b['hb'][0].update(interval=10)),
 ('hard deadline failure',lambda b:b['qualification'].update(deadlineViolations=1)),
 ('unknown helper authority',lambda b:b['coverage']['expected'][0].update(role='OTHER_HELPER')),
 ('unproven cleanup',lambda b:b['host'].update(matchingProcessCount=1)),
 ('kernel event loss',lambda b:b['kernel'].update(eventsLost=1)),
 ('forced CIM correlation',lambda b:b['cim'][0].update(selected=['forced'])),
 ('contradictory CIM',lambda b:b['cim'][0].update(provenContradiction=True)),
]:
 def run(mutation=mutation):
  b=copy.deepcopy(bundle);mutation(b);ct.rules(b,measure,decl)
 test(label,run,True)
for label,mutation in [('missing telemetry',lambda t:t.pop('lag')),('false backpressure',lambda t:t['backpressure'].update(started=100)),('missing queue history',lambda t:t.update(snapshots=[])),('unknown telemetry schema',lambda t:t.update(schema='unknown')),('overflow',lambda t:t.update(overflow=True))]:
 def run(mutation=mutation):
  t=copy.deepcopy(measure);mutation(t);ct.rules(bundle,t,decl)
 test(label,run,True)
test('fresh public evaluation cannot reuse old binding',ct.evaluate,True)
cli=subprocess.run([sys.executable,'-B',str(K/'checker_telemetry.py'),'--evaluate-medium'],capture_output=True,text=True,timeout=20)
save(R/'public-cli-rejection.json',dict(command=cli.args,exit=cli.returncode,stdout=cli.stdout,stderr=cli.stderr))
test('public CLI refuses unbound candidate',lambda:legacy.need(cli.returncode!=0 and json.loads(cli.stdout)['status']=='REJECT','PUBLIC_BYPASS'))
for name in ('checker_telemetry.py','checker_medium.py','telemetry.py'):ast.parse((K/name).read_text(encoding='utf8'))
test('source syntax',lambda:None)
fb.verify_intake(old);assert digest(bundle)==originalDigest
result=ct.rules(bundle,measure,decl)
save(R/'actual-analyzer-replay.json',dict(status='REGRESSION_REPLAY_PASS_NOT_ACCEPTANCE',acceptance=False,originalRunDisposition='MEDIUM_CHECKER_DEFECTIVE',result=result,fixtureSHA256=fb.sha(F/'actual-analyzer-fixture.json')))
save(R/'test-results.json',dict(status='PASS',total=len(checks),passed=sum(x['passed'] for x in checks),failed=0,checks=checks,fixture=str(F/'actual-analyzer-fixture.json'),liveRuns=0))
print(json.dumps(dict(status='PASS',checks=len(checks),version=ct.VERSION,liveRuns=0,originalDispositionUnchanged=True)))
