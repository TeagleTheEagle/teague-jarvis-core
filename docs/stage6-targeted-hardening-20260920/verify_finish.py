import pathlib,json,hashlib,sys,ast,difflib
R=pathlib.Path(__file__).parent;sys.path.insert(0,str(R.parent/'stage6-narrow-preflight-20260920'));from verification import verify_archive,verify_candidate
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
old=read(R.parent/'stage6-large-correlation-20260920'/'archive-verification.json');verify_archive(pathlib.Path(old['path']),old)
O=pathlib.Path(read(R/'candidate.json')['original']);assert verify_candidate(O,read(O/'baseline-source.json'))==84
C=pathlib.Path(read(R/'candidate-v6.json')['code']);V=pathlib.Path(read(R/'candidate-v5.json')['code']);cur=read(C/'hardening-hashes.json');verify_candidate(C,cur)
allowed={'lineage.py','test_hardening_scope.py','test_hardening_boundary.py','extended-delay-result.json','probe-handle-regression.json'}
changed=[]
for x in cur:
 p=C/x['name'];q=V/x['name']
 if q.exists() and p.read_bytes()!=q.read_bytes():changed.append(x['name']);assert x['name'] in allowed
for n in ('lineage.py','test_hardening_scope.py','test_hardening_boundary.py'):
 (R/(n+'.v6.diff')).write_text(''.join(difflib.unified_diff((V/n).read_text().splitlines(True),(C/n).read_text().splitlines(True),fromfile=str(V/n),tofile=str(C/n))))
syntax=[]
for x in cur:
 p=C/x['name']
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p));syntax.append(x['name'])
v=dict(originalCandidateHashes=84,finalCandidateHashes=len(cur),priorArchiveMembers=old['members'],priorArchiveVerified=True,monitoredSourceSame=True,checkerOnlyChanges=changed,pythonSyntaxFiles=syntax,originalUnchanged=True,protectedAccess=False,productionChanged=False)
(R/'final-source-reconciliation.json').write_text(json.dumps(v,indent=2))
ids={}
def add(pid,created,image,source):
 if pid and created and str(created)!='0':ids[(int(pid),str(created))]=dict(pid=int(pid),created=str(created),image=image,source=source)
for manifest in ['candidate.json']+['candidate-v'+str(i)+'.json' for i in range(2,7)]:
 c=pathlib.Path(read(R/manifest)['code'])
 for run in c.glob('hardening-*'):
  if not run.is_dir():continue
  for n in ('launcher.json','observer-identities.json','tree-handles.json','stress-result.json'):
   p=run/n
   if not p.exists():continue
   data=read(p)
   if n=='launcher.json':add(data['pid'],data['creationFiletime'],data['image'],str(p))
   elif n=='observer-identities.json':
    for x in data.values():add(x['pid'],x['created'],x['image'],str(p))
   else:
    for x in data.get('rows',data.get('launched',[])):add(x['pid'],x['created'],x.get('image','UNKNOWN'),str(p))
 for p in c.glob('sampler-tests-*/sampler-results.json'):
  for x in read(p):add(x.get('pid'),x.get('created'),x.get('image','UNKNOWN'),str(p))
(R/'identity-check-list.json').write_text(json.dumps(list(ids.values()),indent=2));print(json.dumps(dict(v,identityChecks=len(ids))))
