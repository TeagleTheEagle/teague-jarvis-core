import json,importlib.util,copy
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-durable-kernel-20260921';run=Path(json.loads((R/'run.json').read_text())['path'])
spec=importlib.util.spec_from_file_location('q',P/'qualification.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
d=json.loads((R/'qualification-inputs.json').read_text());processes=q.load(run/'process-identities.json');worker=next(x for x in processes if x['role']=='worker');rows=d['kernel']['rows'];root=next(r for r in rows if (r['pid'],r['created'])==(worker['pid'],worker['created']))
scope={root['sequence']}
while True:
 new=scope|{r['sequence'] for r in rows if r['parentSequence'] in scope}
 if new==scope:break
 scope=new
tracked=[r for r in rows if r['sequence'] in scope];proven={(h['pid'],h['created']) for h in d['handles']}
missing=[dict(pid=r['pid'],created=r['created'],sequence=r['sequence'],image=r['image'],reason='Retained kernel handle exists but independent handle-image comparison record is absent') for r in tracked if r['handleRetained'] and (r['pid'],r['created']) not in proven]
empty=copy.deepcopy(d);empty['handles']=[];empty['natives']=[]
try:actual=q.qualify(**empty)['status'];reason=None
except (ValueError,KeyError) as e:actual='FAIL';reason=str(e)
result=dict(status='FAIL' if missing or actual!='FAIL' else 'PASS',trackedWorkerAndDescendants=len(tracked),infrastructureIdentities=len(rows)-len(tracked),retainedTracked=sum(r['handleRetained'] for r in tracked),independentlyImageVerified=len(proven),missingRequiredHandleImageEvidence=missing,omittedVerificationTest=dict(expected='FAIL',actual=actual,reason=reason,passed=actual=='FAIL'),frozenCheckerChanged=False,conclusion='Positive probe proof is preserved, but the draft qualifier cannot qualify full coverage. Combined validation must not run.')
with (R/'coverage-audit.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
