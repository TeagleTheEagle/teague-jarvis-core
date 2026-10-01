import json,hashlib,uuid,difflib,collections
from pathlib import Path
R=Path(__file__).parent
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pre=load(R/'preflight.json');frozen=load(R/'candidate-frozen.json');C=Path(frozen['code']);old=Path(pre['code']);root=Path(load(R/'run.json')['path'])
for x in pre['checks']:assert sha(Path(x['path']))==x['sha256'],x['path']
for x in frozen['files']:assert sha(Path(x['path']))==x['sha256'],x['path']
cov=load(R/'analysis/coverage-live-result.json');assert cov['status']=='PASS' and cov['requiredIdentities']==cov['verifiedIdentities'] and cov['missingRequired']==cov['contradictory']==0
inputs=load(R/'analysis/coverage-live-inputs.json');k=load(root/'etw-result.json');natives=inputs['natives'];timings=[]
for h in inputs['handles']:
 if h['source']!='creator-owned-handle':continue
 n=next(n for n in natives if (n['pid'],n['created'])==(h['pid'],h['created']));r=next(r for r in k['rows'] if (r['pid'],r['created'])==(h['pid'],h['created']));f=h['frequency']
 timings.append(dict(pid=h['pid'],created=h['created'],queryMs=(h['queryEndQpc']-h['queryBeginQpc'])*1000/f,queryThroughDurableMs=(n['identityPersistedQpc']-h['queryBeginQpc'])*1000/f,queryBeforeNative=True,durableBeforeNative=True,exitedBeforeKernelCallback=r['stopQpc']<r['startCallbackQpc'],evidenceSHA256=h['evidenceSHA256']))
changes=[]
for p in sorted(C.iterdir()):
 if p.is_file() and ((old/p.name).exists() and sha(p)!=sha(old/p.name)):
  changes.append(dict(path=str(p),before=sha(old/p.name),after=sha(p)))
  if p.suffix in ('.cpp','.ps1','.py'):
   with (R/(p.name+'.diff')).open('x') as f:f.writelines(difflib.unified_diff((old/p.name).read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(old/p.name),tofile=str(p)))
host=uuid.uuid4().hex;(R/'final'/host).mkdir()
with (R/'preservation-after.json').open('x') as f:json.dump(dict(status='PASS',oldComparisons=len(pre['checks']),frozenFiles=len(frozen['files']),hostRun=host,checkerSHA256=sha(C/'cleanup_checker.py'),changes=changes,protectedAccess=False,productionChanged=False),f,indent=2)
with (R/'timing-summary.json').open('x') as f:json.dump(dict(rows=timings,count=len(timings),maxQueryMs=max(x['queryMs'] for x in timings),maxQueryThroughDurableMs=max(x['queryThroughDurableMs'] for x in timings),exitBeforeKernelCallback=sum(x['exitedBeforeKernelCallback'] for x in timings),classes=dict(collections.Counter(x['role'] for x in cov['identities']))),f,indent=2)
print(json.dumps(dict(hostRun=host,coverage=dict(required=cov['requiredIdentities'],verified=cov['verifiedIdentities'],missing=cov['missingRequired'],contradictory=cov['contradictory']),changes=[Path(x['path']).name for x in changes],timings=load(R/'timing-summary.json'))))
