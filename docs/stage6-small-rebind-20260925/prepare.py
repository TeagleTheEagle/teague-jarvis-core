import pathlib,json,hashlib,shutil,uuid
R=pathlib.Path(__file__).parent
S=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\d45028a56e344926a311c04ba01f6a80\code')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):
 s=p.stat();return dict(path=str(p),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=sha(p))
def write(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
def safe(p):
 for x in (p,*p.parents):
  if x.exists():assert not x.lstat().st_file_attributes&0x400,str(x)
 assert p.stat().st_nlink==1,str(p)
if __name__=='__main__':
 assert sha(S/'small-source-v3.json')=='6a86a4f287388c8c58b3df4333792217b5205305f2157043a5a2ba5456c0b15b'
 rows=json.loads((S/'small-source-v3.json').read_text());assert len(rows)==235
 names=set();before={}
 for r in rows:
  n=pathlib.PureWindowsPath(r['name']);assert not n.is_absolute() and not n.drive and '..' not in n.parts and ':' not in r['name']
  k=n.as_posix().casefold();assert k not in names;names.add(k)
  assert not any(t in k for t in ['loss_measurement_v3','timestamp-reuse','qualification-harness','attribution'])
  p=S/r['name'];safe(p);assert (p.stat().st_size,sha(p))==(r['bytes'],r['sha256']);before[str(p)]=rec(p)
 before[str(S/'small-source-v3.json')]=rec(S/'small-source-v3.json')
 # Preserve previously recorded predecessor/historical inputs and deferred branch.
 for report in ['stage6-helper-handoff-v1-20260923','stage6-qualification-harness-v1-20260924']:
  old=json.loads((R.parent/report/'before.json').read_text())
  for x in old['inputs']:
   assert rec(pathlib.Path(x['path']))==x,x['path'];before[x['path']]=x
 for report in ['stage6-final-qualification-run-20260924','stage6-helper-handoff-live-20260923']:
  for p in (R.parent/report).rglob('*'):
   if p.is_file():before[str(p)]=rec(p)
 C=S.parent.parent/uuid.uuid4().hex/'code'
 write(R/'before.json',dict(source=str(S),candidate=str(C),inputs=list(before.values())))
 C.mkdir(parents=True)
 for r in rows:
  p=C/r['name'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/r['name'],p);assert sha(p)==r['sha256']
 assert {p.relative_to(C).as_posix().casefold() for p in C.rglob('*') if p.is_file()}==names
 write(R/'copy-verification.json',dict(files=235,status='PASS',names=sorted(names)))
 allow=C/'baseline-allowlist.json';v=json.loads(allow.read_text());assert v==dict(syntheticRoots=[str(S/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False)
 v['syntheticRoots']=[str(C/'small-synthetic')];allow.write_text(json.dumps(v,indent=2),encoding='utf8')
 policy=C/'preservation-policy-v4.json';v=json.loads(policy.read_text());assert v['candidate']==str(S) and v['preservationRoot']==str(S.parent/'preservation-v4')
 v.update(candidate=str(C),preservationRoot=str(C.parent/'preservation-v4'));policy.write_text(json.dumps(v,indent=2),encoding='utf8')
 out=[];diff=[]
 for r in rows:
  p=C/r['name'];out.append(dict(name=r['name'],bytes=p.stat().st_size,sha256=sha(p)))
  if sha(p)!=r['sha256']:diff.append(r['name'])
 assert set(diff)=={'baseline-allowlist.json','preservation-policy-v4.json'}
 write(C/'small-source-v3.json',out)
 data=[r for r in out if pathlib.PureWindowsPath(r['name']).parts[0]=='small-synthetic'];assert len(data)==12 and sum(r['bytes'] for r in data)==786432
 write(R/'rebind.json',dict(candidate=str(C),changed=diff,unchangedFiles=233,manifest=rec(C/'small-source-v3.json'),dataset=data,liveRunStarted=False))
 print(C)
