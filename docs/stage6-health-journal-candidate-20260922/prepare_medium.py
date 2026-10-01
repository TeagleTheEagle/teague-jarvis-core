import ast,difflib,hashlib,json,os,uuid
from pathlib import Path
R=Path(__file__).resolve().parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
pre=load(R/'candidate.json');C=Path(pre['code']);old=Path(pre['old'])
assert load(R/'focused-result.json')['status']=='PASS' and load(R/'regression-results.json')['status']=='PASS' and load(R/'readiness-result.json')['status']=='PASS'
assert load(C/'focused-result.json')['passed']==69
final=list(C.glob('finalization-tests-*/result.json'));assert len(final)==1 and load(final[0])['status']=='PASS'
q=load(C/'queue-regression-6993349670044b778310cb8dcb1b32c3/queue-regression.json');assert q['regression']['checks']==222 and q['regression']['status']=='PASS'
for x in pre['priorFiles']:assert sha(x['path'])==x['sha256']
run='identity-'+uuid.uuid4().hex;root=C/run;root.mkdir();(root/'temp').mkdir();(root/'analysis').mkdir()
before={n:(C/n).read_text(encoding='utf8') for n in ('medium-declaration.json','medium-intent.json','qualified_launch.ps1')}
d=load(C/'medium-declaration.json');priorRuntime=Path(d['codeRoot']);d.update(runId=run,codeRoot=str(C),evidenceRoot=str(root));(C/'medium-declaration.json').write_text(json.dumps(d,indent=2),encoding='utf8')
(C/'medium-intent.json').write_text(json.dumps(dict(evidenceRoot=str(root),declarationSHA256=sha(C/'medium-declaration.json')),indent=2),encoding='utf8')
a=str(priorRuntime/'J6OwnedEntry.dll').replace('\\','\\\\');b=str(C/'J6OwnedEntry.dll').replace('\\','\\\\');s=before['qualified_launch.ps1'];assert s.count(a)==1;(C/'qualified_launch.ps1').write_text(s.replace(a,b),encoding='utf8')
for n,s in before.items():
    (R/(n+'.binding.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),(C/n).read_text().splitlines(True),fromfile='prior-binding',tofile=str(C/n))),encoding='utf8')
paths=[C/Path(x['path']).relative_to(old) for x in pre['priorFiles']]+[C/'health_reader.py',C/'health_publication.ps1']
for p in paths:
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf8'))
rows=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)]
save(C/'medium-source-freeze.json',dict(schema='stage6-medium-source-freeze-v1',files=rows));save(R/'candidate-frozen.json',dict(files=rows))
import sys
sys.path[:0]=[str(C/'medium-checker'),str(C)]
import fresh_binding as fb
assert fb.bound(C)[0]==root
save(R/'run.json',dict(run=run,path=str(root)))
host=uuid.uuid4().hex;(R/'final'/host).mkdir(parents=True)
with (R/'host_preflight.ps1').open('xb') as f:f.write((R.parent/'stage6-medium-v5-fresh-20260922/host_preflight.ps1').read_bytes())
save(R/'medium-preflight.json',dict(code=str(C),root=str(root),hostRun=host,sourceFiles=len(rows),focusedChecks=184,queueAssertions=222,finalizationAssertions=load(final[0])['checks'],oneAttempt=True))
print(json.dumps(load(R/'medium-preflight.json')))
