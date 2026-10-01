import json,hashlib,uuid,difflib
from pathlib import Path
R=Path(__file__).parent
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pre=load(R/'preflight.json');frozen=load(R/'candidate-frozen.json');C=Path(frozen['code']);old=Path(pre['source']);root=Path(load(R/'run.json')['path'])
for x in pre['checks']:assert sha(Path(x['path']))==x['sha256'],x['path']
for x in frozen['files']:assert sha(Path(x['path']))==x['sha256'],x['path']
changed=[]
before={x['name']:x for x in load(R/'candidate.json')['before']}
for name in ('authority_trace.cpp','owned_entry.cpp','qualified_launch.ps1','J6AuthorityTrace.exe','J6OwnedEntry.dll'):
 changed.append(dict(name=name,before=before[name]['sha256'],after=sha(C/name),path=str(C/name)))
 if name.endswith(('.cpp','.ps1')):
  with (R/(name+'.diff')).open('x') as f:f.writelines(difflib.unified_diff((old/name).read_text().splitlines(True),(C/name).read_text().splitlines(True),fromfile=str(old/name),tofile=str(C/name)))
k=load(root/'etw-result.json');fails=[r for r in k['rows'] if r['imageError']]
facts=dict(imageFailures=len(fails),errorCodes=sorted({r['imageError'] for r in fails}),allFailedQueriesBeganAfterKernelStop=all(r['imageBeginQpc']>r['stopQpc'] for r in fails),failures=[dict(pid=r['pid'],created=r['created'],error=r['imageError'],queryBegin=r['imageBeginQpc'],stopQpc=r['stopQpc'],deltaTicks=r['imageBeginQpc']-r['stopQpc']) for r in fails])
with (R/'image-query-failure.json').open('x') as f:json.dump(facts,f,indent=2)
run=uuid.uuid4().hex;(R/'final'/run).mkdir()
with (R/'preservation-after.json').open('x') as f:json.dump(dict(status='PASS',priorChecksUnchanged=len(pre['checks']),candidateFilesUnchanged=len(frozen['files']),checkerSHA256=sha(C/'cleanup_checker.py'),hostRun=run,changed=changed,protectedAccess=False,productionChanged=False),f,indent=2)
print(json.dumps(dict(hostRun=run,facts=facts,candidateFiles=len(frozen['files']))))
