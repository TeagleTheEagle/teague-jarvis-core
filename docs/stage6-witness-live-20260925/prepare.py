import pathlib,json,hashlib,shutil,uuid,os,sys,zipfile
R=pathlib.Path(__file__).parent
P=R.parent/'stage6-lifecycle-witness-20260925'
S=P/'candidate'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
v=dict(status='BLOCKED',liveStarted=False,UAC=False)
try:
 assert load(R/'preflight-census.json')['status']=='PASS'
 archives=[]
 for report in (P,R.parent/'stage6-small-live-20260925'):
  receipt=load(report/'archive-receipt.json');a=pathlib.Path(receipt['archive'])
  assert sha(a)==receipt['sha256']
  with zipfile.ZipFile(a) as z:
   assert len(z.namelist())==receipt['verifiedMembers'] and z.testzip() is None
   for row in load(report/'archive-manifest.json'):assert hashlib.sha256(z.read(row['member'])).hexdigest()==row['sha256']
  archives.append(receipt)
 manifest=load(S/'witness-source-v1.json')
 assert sha(S/'witness-source-v1.json')==sha(S/'small-source-v3.json')=='3c8efb4e22ed98ef4e6a5e63a7a0040f36d10fbe40e1cb427eba760fc9e46576'
 assert len(manifest)==245
 def verify(base,rows):
  seen=set()
  for row in rows:
   rel=pathlib.PureWindowsPath(row['name']);assert not rel.is_absolute() and '..' not in rel.parts and ':' not in str(rel)
   assert str(rel).casefold() not in seen;seen.add(str(rel).casefold());p=base/rel
   for part in (p,*p.parents):
    assert not part.lstat().st_file_attributes&0x400
    if part==base:break
   assert p.stat().st_nlink==1 and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
 verify(S,manifest)
 old=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\ea85ed4b4ef14769acbe0b5e750aaed2\code')
 assert sha(old/'small-source-v3.json')=='5966bdb43ed1efaa85f6956dd0552c7459f2eef4e1d7970e5143ac1376b316ef'
 verify(old,load(old/'small-source-v3.json'))
 C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
 C.mkdir(parents=True,exist_ok=False);(C.parent/'preservation-v4').mkdir()
 v['candidate']=str(C)
 for row in manifest:
  dst=C/row['name'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['name'],dst)
 verify(C,manifest)
 changes=[]
 for name in ('baseline-allowlist.json','preservation-policy-v4.json'):
  p=C/name;before=dict(sha256=sha(p),value=load(p));data=load(p)
  if name=='baseline-allowlist.json':data=dict(syntheticRoots=[str(C/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False)
  else:data.update(candidate=str(C),preservationRoot=str(C.parent/'preservation-v4'))
  p.write_text(json.dumps(data,indent=2),encoding='utf-8')
  changes.append(dict(name=name,before=before,after=dict(sha256=sha(p),value=data)))
 rows=[dict(name=x['name'],bytes=(C/x['name']).stat().st_size,sha256=sha(C/x['name'])) for x in manifest]
 for name in ('small-source-v3.json','witness-source-v1.json'):save(C/name,rows)
 save(R/'rebind.json',changes);save(R/'candidate-manifest.json',rows)
 os.chdir(C);sys.path[0]=str(C)
 import workspace_binding_v4 as b
 assert b.manifest()==rows
 runtime=b.runtime_policy();b.policy()
 for key in ('PYTHONHOME','PYTHONPATH','PYTHONSTARTUP'):assert not os.environ.get(key)
 for key in ('PATH','PSModulePath','TEMP','TMP'):
  for item in os.environ.get(key,'').split(os.pathsep):
   if 'jarvis-stage6' in item.casefold():assert pathlib.Path(item).is_relative_to(C)
 os.environ['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(x['path']).parent) for x in runtime['executables'].values()))
 os.environ['PSModulePath']=os.pathsep.join(runtime['moduleRoots']);os.environ['PYTHONNOUSERSITE']='1';b.environment(runtime)
 data=[x for x in rows if pathlib.PureWindowsPath(x['name']).parts[0]=='small-synthetic']
 assert len(data)==12 and sum(x['bytes'] for x in data)==786432
 from small_binding_v3 import make
 root=make('normal');b.prepare(root);b.verify(root)
 for channel in ('authority','detailed'):
  for suffix in ('lifecycle-witness-v1.json','lifecycle-witness-export-failure-v1.json'):assert not (C/(root.name+'.'+channel+'-'+suffix)).exists()
 verify(S,manifest)
 v.update(status='PASS',run=root.name,runRoot=str(root),workspaceBindingSHA256=sha(root/b.NAME),sourceManifestSHA256=sha(C/'small-source-v3.json'),witnessManifestSHA256=sha(C/'witness-source-v1.json'),candidateFiles=len(rows),datasetFiles=12,datasetBytes=786432,archives=archives,protectedVMAccess=False,productionChange=False)
except BaseException as e:
 v['error']=repr(e);raise
finally:
 save(R/'preflight-result.json',v);print(json.dumps(v))
