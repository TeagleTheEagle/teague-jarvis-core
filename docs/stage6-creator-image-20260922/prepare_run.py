import json,uuid,hashlib
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-required-coverage-20260921';C=Path(json.loads((R/'candidate.json').read_text())['code'])
assert json.loads((R/'coverage-tests.json').read_text())['passed']==44
assert json.loads((R/'rapid-result.json').read_text())['status']=='PASS'
s=(P/'analyze_v2.py').read_text().replace("O=R/'analysis-v2'","O=R/'analysis'")
for a,b in [('probe','DIRECT_PROBE'),('worker','DIRECT_WORKER'),('console','OS_CONSOLE_HELPER'),('infrastructure','APPLICATION_OBSERVER')]:s=s.replace("role='"+a+"'","role='"+b+"'")
start=s.index(' handleEvidence.append(');end=s.index('\ncoverageInputs=',start)
replacement='''
 if role in ('DIRECT_PROBE','DIRECT_WORKER'):
  ep=root/f"early-image-{r['pid']}-{r['created']}.json";e=q.load(ep)
  q.require(e['source']=='creator-owned-handle' and e['recordId']==str(r['pid'])+'-'+r['created'] and identity(e)==key,'EARLY_RECORD_BINDING')
  ns=[n for n in native if identity(n)==key];q.require(len(ns)==1,'EARLY_NATIVE_BINDING');n=ns[0]
  h=dict(e,retained=True,exited=n['finalWait']==0,closed=True,exitFiletime=n['exitFiletime'],exitCode=n['exitCode'],identityPersistedQpc=n.get('identityPersistedQpc',0),evidenceSHA256=q.sha(ep))
  handleEvidence.append(h)
 else:
  handleEvidence.append(dict(pid=r['pid'],created=r['created'],handleCreated=r.get('handleCreated'),image=r.get('handleImage',''),imageError=r.get('imageError'),source='tracer-opened-handle',queryBeginQpc=r.get('imageBeginQpc',0),queryEndQpc=r.get('imageEndQpc',0),
   retained=r['handleRetained'],exited=r['signalObservedQpc']>0,closed=r['handleClosed'],exitFiletime=r['exitFiletime'],exitCode=r['exitCode'],
   qualifiedPostExit=not r['handleRetained'],reason=r['reason'],openError=r['openError'],attemptBegin=r['handleAttemptBeginQpc'],attemptEnd=r['handleAttemptQpc']))
'''
s=s[:start]+replacement+s[end:]
# Ensure the declared direct worker and each probe cannot disappear from coverage.
s=s.replace('coverageInputs=dict(',"q.require(identity(worker) in {identity(x) for x in expected} and probeKeys <= {identity(x) for x in expected},'DECLARED_PROCESS_MISSING')\ncoverageInputs=dict(")
with (R/'analyze.py').open('x') as f:f.write(s)
frozen=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in C.iterdir() if p.is_file()]
for p in (R/'coverage.py',R/'analyze.py',R/'DESIGN.md'):frozen.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
with (R/'candidate-frozen.json').open('x') as f:json.dump(dict(code=str(C),files=frozen),f,indent=2)
name='identity-'+uuid.uuid4().hex;root=C/name;root.mkdir();(root/'temp').mkdir()
with (R/'run.json').open('x') as f:json.dump(dict(run=name,path=str(root)),f,indent=2)
print(name)
