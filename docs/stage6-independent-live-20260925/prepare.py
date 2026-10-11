import pathlib,json,hashlib,shutil,uuid,os,sys,zipfile
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-authority-independent-20260925';S=P/'candidate'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def verify(base,rows):
 seen=set()
 for row in rows:
  rel=pathlib.PureWindowsPath(row['name']);assert not rel.is_absolute() and '..' not in rel.parts and ':' not in str(rel)
  assert str(rel).casefold() not in seen;seen.add(str(rel).casefold());p=base/rel
  for part in (p,*p.parents):
   assert not part.lstat().st_file_attributes&0x400
   if part==base:break
  assert p.stat().st_nlink==1 and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
v=dict(status='BLOCKED',liveStarted=False,UAC=False)
try:
 assert load(R/'preflight-census.json')['status']=='PASS'
 binding=load(P/'successor-binding.json');before=load(P/'before.json')
 assert sha(S/'small-source-v3.json')==sha(S/'witness-source-v1.json')==binding['candidateManifestSHA256']=='139bf0df392dae0a201baa6bcee1f6b4bb612583201b599df780c9e86d96885a'
 rows=load(S/'small-source-v3.json');assert len(rows)==245;verify(S,rows)
 old=pathlib.Path(before['predecessor']);verify(old,before['files'])
 for row in before['files']:assert (old/row['name']).stat().st_mtime_ns==row['mtimeNs']
 archives=[]
 for folder,receipt_name in [(P,'archive-verification.json'),(R.parent/'stage6-witness-live-20260925','archive-receipt.json'),(R.parent/'stage6-lifecycle-witness-20260925','archive-receipt.json')]:
  receipt=load(folder/receipt_name);a=pathlib.Path(receipt['archive']);assert sha(a)==receipt['sha256']
  with zipfile.ZipFile(a) as z:
   assert len(z.namelist())==receipt['verifiedMembers'] and z.testzip() is None
   for row in load(folder/'archive-manifest.json'):assert hashlib.sha256(z.read(row.get('member',row.get('name')))).hexdigest()==row['sha256']
  archives.append(receipt)
 source=(S/'authority_trace_v3.cpp').read_bytes();prior=(old/'authority_trace_v3.cpp').read_bytes()
 assert source==prior.replace(b'p->LogFileMode=EVENT_TRACE_REAL_TIME_MODE;',b'p->LogFileMode=EVENT_TRACE_REAL_TIME_MODE|EVENT_TRACE_INDEPENDENT_SESSION_MODE;',1)
 assert b'EVENT_TRACE_INDEPENDENT_SESSION_MODE' not in (S/'startup_trace.cpp').read_bytes()
 assert sha(S/'J6AuthorityTraceV3.exe')==binding['authoritySHA256']
 assert sha(S/'J6StartupTrace.exe')==sha(old/'J6StartupTrace.exe')==binding['detailedSHA256']
 expected_changes={'authority_trace_v3.cpp','authority_trace_v3.obj','J6AuthorityTraceV3.exe'}
 assert {x['name'] for x in before['files'] if sha(S/x['name'])!=x['sha256']}==expected_changes
 C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True,exist_ok=False);(C.parent/'preservation-v4').mkdir();v['candidate']=str(C)
 for row in rows:
  dst=C/row['name'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['name'],dst)
 verify(C,rows);changes=[]
 for name in ('baseline-allowlist.json','preservation-policy-v4.json'):
  p=C/name;previous=dict(sha256=sha(p),value=load(p));data=load(p)
  if name=='baseline-allowlist.json':data=dict(syntheticRoots=[str(C/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False)
  else:data.update(candidate=str(C),preservationRoot=str(C.parent/'preservation-v4'))
  p.write_text(json.dumps(data,indent=2),encoding='utf-8');changes.append(dict(name=name,before=previous,after=dict(sha256=sha(p),value=data)))
 fresh=[dict(name=x['name'],bytes=(C/x['name']).stat().st_size,sha256=sha(C/x['name'])) for x in rows]
 assert {x['name'] for x,y in zip(rows,fresh) if x!=y}=={'baseline-allowlist.json','preservation-policy-v4.json'}
 for name in ('small-source-v3.json','witness-source-v1.json'):save(C/name,fresh)
 save(R/'rebind.json',changes);save(R/'candidate-manifest.json',fresh)
 os.chdir(C);sys.path[0]=str(C)
 import workspace_binding_v4 as b
 assert b.manifest()==fresh;runtime=b.runtime_policy();b.policy()
 for key in ('PYTHONHOME','PYTHONPATH','PYTHONSTARTUP'):assert not os.environ.get(key)
 for key in ('PATH','PSModulePath','TEMP','TMP'):
  for item in os.environ.get(key,'').split(os.pathsep):
   if 'jarvis-stage6' in item.casefold():assert pathlib.Path(item).is_relative_to(C)
 os.environ['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(x['path']).parent) for x in runtime['executables'].values()))
 os.environ['PSModulePath']=os.pathsep.join(runtime['moduleRoots']);os.environ['PYTHONNOUSERSITE']='1';b.environment(runtime)
 data=[x for x in fresh if pathlib.PureWindowsPath(x['name']).parts[0]=='small-synthetic'];assert len(data)==12 and sum(x['bytes'] for x in data)==786432
 from small_binding_v3 import make
 root=make('normal');b.prepare(root);b.verify(root)
 for channel in ('authority','detailed'):
  for suffix in ('lifecycle-witness-v1.json','lifecycle-witness-export-failure-v1.json'):assert not (C/(root.name+'.'+channel+'-'+suffix)).exists()
 verify(S,rows)
 v.update(status='PASS',run=root.name,runRoot=str(root),workspaceBindingSHA256=sha(root/b.NAME),sourceManifestSHA256=sha(C/'small-source-v3.json'),witnessManifestSHA256=sha(C/'witness-source-v1.json'),candidateFiles=245,datasetFiles=12,datasetBytes=786432,archives=archives,successorBindingSHA256=sha(P/'successor-binding.json'),authoritySHA256=sha(C/'J6AuthorityTraceV3.exe'),detailedSHA256=sha(C/'J6StartupTrace.exe'),protectedVMAccess=False,productionChange=False)
except BaseException as e:
 v['error']=repr(e);raise
finally:
 save(R/'preflight-result.json',v);print(json.dumps(v))
