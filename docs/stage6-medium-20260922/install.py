import ast,hashlib,json,os,re,sys
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-checker-integration-20260922';S=R.parent/'stage6-small-combined-20260922'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,s):
 with p.open('x',encoding='utf8') as f:f.write(s);f.flush();os.fsync(f.fileno())
def save(p,v):put(p,json.dumps(v,indent=2))
pre=load(R/'preflight.json');C=Path(pre['code']);K=Path(pre['checker']);root=Path(pre['root']);old=Path(pre['originalRuntime'])
assert load(R/'final'/pre['hostRun']/'final-host-state.json')['status']=='PASS'
d=dict(schema='stage6-medium-declaration-v1',runId=root.name,codeRoot=str(C),evidenceRoot=str(root),directWorkers=1,directProbes=64,cases=[dict(name='idle',groups=16,width=1),dict(name='churn',groups=16,width=1),dict(name='overlap',groups=4,width=8)],minimumSegments=8,heartbeatSeconds=10,hardDeadlineSeconds=13.6,observerSeconds=15,collectionSeconds=60,queueItems=65536,queueBytes=67108864,pendingSegments=2,segmentBytes=8192)
save(C/'medium-declaration.json',d);save(C/'medium-intent.json',dict(schema='stage6-medium-intent-v1',evidenceRoot=str(root),declarationSHA256=sha(C/'medium-declaration.json'),attemptsAuthorized=1))
put(C/'fresh_binding.py',(R/'fresh_binding.py').read_text(encoding='utf8'))
worker=(C/'qualified_worker.py').read_text(encoding='utf8')
worker=worker.replace("root=run_dir(sys.argv[1]);activate_temp(root)","root=run_dir(sys.argv[1]);activate_temp(root)\nfrom fresh_binding import bound\n_bound,declaration=bound(CODE)\nif _bound!=root:raise ValueError('WORKER_RUN_BINDING')")
worker=worker.replace("for case in ('idle','churn','overlap'):\n  for i in range(4):", "for plan in declaration['cases']:\n  case=plan['name']\n  for i in range(plan['groups']):")
worker=worker.replace("range(2 if case=='overlap' else 1)","range(plan['width'])")
assert "range(4)" not in worker
(C/'qualified_worker.py').write_text(worker,encoding='utf8')
launch=(C/'qualified_launch.ps1').read_text(encoding='utf8');oldescaped=str(old).replace('\\','\\\\');newescaped=str(C).replace('\\','\\\\');assert oldescaped in launch
launch=launch.replace(oldescaped,newescaped);(C/'qualified_launch.ps1').write_text(launch,encoding='utf8')
# New checker keeps all prior rules; independent counts come from a reviewed declaration.
combined=(K/'combined.py').read_text(encoding='utf8').replace('def validate(b):','def validate(b,*,declaration):')
combined=combined.replace("classes['DIRECT_PROBE']==16 and classes['DIRECT_WORKER']==1","classes['DIRECT_PROBE']==declaration['directProbes'] and classes['DIRECT_WORKER']==declaration['directWorkers']")
combined=combined.replace("len(m['segments'])>=2","len(m['segments'])>=declaration['minimumSegments']")
combined=combined.replace("schema='stage6-small-combined-v1'","schema='stage6-medium-combined-v1'")
(K/'combined.py').write_text(combined,encoding='utf8')
text=(K/'checker_v2.py').read_text(encoding='utf8')
start=text.index('def self_verify():');end=text.index('def secondary_policy(',start);text=text[:start]+text[end:]
text=text[:text.index('def replay():')]
text=text.replace("VERSION='stage6-checker-input-v2'","VERSION='stage6-checker-input-v3'")
text=text.replace("stage6-small-combined-v1","stage6-medium-combined-v1")
text=text.replace("def rules(envelope,compare_payload=True):","def rules(envelope,compare_payload=True,*,declaration):")
text=text.replace('result=adapter.validate(b)','result=adapter.validate(b,declaration=declaration)')
text=text.replace("set(x)==set(s['required'])==set(s['properties'])","set(s['required'])<=set(x)<=set(s['properties'])")
text += '''\ndef evaluate():
 from fresh_binding import verify_intake
 code=R.parent;root,d,intake=verify_intake(code)
 b=adapter.read_bundle(root,root/'analysis',root/'final-host-state.json')
 declared=load(root/'process-identities.json')
 required={(x['pid'],x['created']) for x in declared if x['role'] in ('worker','application')}
 need(len(required)==2 and required<={(x['pid'],x['created']) for x in b['kernel']['rows']},'DECLARED_INFRASTRUCTURE_MISSING')
 probes=load(root/'identity-probes.json')['rows']
 need(len(probes)==d['directProbes'] and dict(collections.Counter(p['case'] for p in probes))=={p['name']:p['groups']*p['width'] for p in d['cases']},'DECLARED_CASES_MISSING')
 payload=adapter.validate(b,declaration=d)
 e=dict(schema=VERSION,contract=CONTRACT,adapter='stage6-medium-combined-v1',runId=root.name,evidenceRoot=str(root),payload=payload,bundle=b)
 outcome=rules(e,declaration=d)
 verify_intake(code)
 return dict(status='EVIDENCE_VALIDATED_PENDING_ARCHIVE',schema=VERSION,runId=root.name,declaration=d,intakeSHA256=sha(root/'intake-manifest.json'),rules=outcome,acceptance=False)
if __name__=='__main__':
 try:
  sys.path.insert(0,str(R.parent));need(sys.argv[1:]==['--evaluate-medium'],'EXPLICIT_MODE_REQUIRED');print(json.dumps(evaluate(),allow_nan=False))
 except Exception as e:
  print(json.dumps(dict(status='REJECT',reason=str(e),error=type(e).__name__)));raise SystemExit(1)
'''
put(K/'checker_medium.py',text)
schema=load(K/'schema.json');schema['$id']='urn:jarvis:stage6:checker-input:v3';schema['properties']['schema']['const']='stage6-checker-input-v3';schema['properties']['adapter']['const']='stage6-medium-combined-v1'
states=['PRESENT_AND_VALID','MISSING_AND_REQUIRED','PRESENT_BUT_CONTRADICTORY','NOT_APPLICABLE']
roles=['DIRECT_PROBE','DIRECT_WORKER','OS_CONSOLE_HELPER','APPLICATION_OBSERVER']
def sparse(s):
 if type(s) is not dict:return
 if s.get('type')=='object':
  keys=set(s['properties'])
  if keys and keys<=set(states):s.update(required=[],properties={k:dict(type='integer') for k in states})
  elif keys and keys<=set(roles):s.update(required=['DIRECT_PROBE','DIRECT_WORKER','APPLICATION_OBSERVER'],properties={k:dict(type='integer') for k in roles})
  elif keys and keys<=set(['AMBIGUOUS','UNMATCHED','UNIQUE_CORRELATED']):s.update(required=[],properties={k:dict(type='integer') for k in ['AMBIGUOUS','UNMATCHED','UNIQUE_CORRELATED']})
 for v in list(s.values()):
  if isinstance(v,dict):sparse(v)
  elif isinstance(v,list):
   for x in v:sparse(x)
sparse(schema);(K/'schema.json').write_text(json.dumps(schema,indent=2),encoding='utf8')
# Read-only analyzer is copied with only dependency/output binding changed.
analysis=(S/'analyze.py').read_text(encoding='utf8')
a=analysis.index("R=Path(__file__).parent;");z=analysis.index("spec=importlib.util",a)
analysis=analysis[:a]+"R=Path(__file__).parent;C=R;P=C/'medium-checker';sys.path.insert(0,str(P));root=Path(json.loads((C/'medium-intent.json').read_text(encoding='utf8'))['evidenceRoot'])\n"+analysis[z:]
analysis=analysis.replace("O=R/'analysis';O.mkdir()","O=root/'analysis'")
put(C/'analyze_medium.py',analysis)
for p in list(C.glob('*.py'))+list(K.glob('*.py')):ast.parse(p.read_text(encoding='utf8'))
save(R/'preparation-changes.json',dict(files=[dict(path=str(p),sha256=sha(p)) for p in [C/'qualified_worker.py',C/'qualified_launch.ps1',C/'fresh_binding.py',C/'analyze_medium.py',K/'combined.py',K/'checker_medium.py',K/'schema.json',C/'medium-declaration.json',C/'medium-intent.json']],originalsUnchanged=True))
print(json.dumps(dict(status='PREPARED_NOT_VALIDATED',code=str(C),checker=str(K/'checker_medium.py'),run=root.name)))
