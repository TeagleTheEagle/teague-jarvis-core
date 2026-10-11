import pathlib,json,hashlib,os,sys,zipfile
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-rebind-directory-fix-20260925';Q=R.parent/'stage6-small-rebind-20260925'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\ea85ed4b4ef14769acbe0b5e750aaed2\code')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
v=dict(status='BLOCKED',candidate=str(C),liveStarted=False,UAC=False)
try:
 assert load(R/'preflight-census.json')['status']=='PASS'
 a=load(P/'archive-receipt.json');assert sha(pathlib.Path(a['archive']))==a['sha256']
 with zipfile.ZipFile(a['archive']) as z:
  assert len(z.namelist())==a['verifiedMembers']==664 and z.testzip() is None
  for x in load(P/'archive-manifest.json'):assert hashlib.sha256(z.read(x['member'])).hexdigest()==x['sha256']
 for x in load(Q/'before.json')['inputs']:
  p=pathlib.Path(x['path']);s=p.stat();assert (s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
 assert sha(C/'small-source-v3.json')=='5966bdb43ed1efaa85f6956dd0552c7459f2eef4e1d7970e5143ac1376b316ef'
 os.chdir(C);sys.path[0]=str(C)
 import workspace_binding_v4 as b
 rows=b.manifest();assert len(rows)==235
 runtime=b.runtime_policy();policy=b.policy();dest=pathlib.Path(policy['preservationRoot']);b.safe(dest,C.parent);assert dest.is_dir()
 for key in ('PYTHONHOME','PYTHONPATH','PYTHONSTARTUP'):assert not os.environ.get(key)
 for key in ('PATH','PSModulePath','TEMP','TMP'):
  for x in os.environ.get(key,'').split(os.pathsep):
   if 'jarvis-stage6' in x.casefold():assert pathlib.Path(x).is_relative_to(C)
 os.environ['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(x['path']).parent) for x in runtime['executables'].values()));os.environ['PSModulePath']=os.pathsep.join(runtime['moduleRoots']);os.environ['PYTHONNOUSERSITE']='1';b.environment(runtime)
 data=[r for r in rows if pathlib.PureWindowsPath(r['name']).parts[0]=='small-synthetic'];assert len(data)==12 and sum(r['bytes'] for r in data)==786432
 assert sorted(p.name for p in (C/'small-synthetic').iterdir())==[f'{i:02}.bin' for i in range(12)]
 for r in rows:
  p=C/r['name']
  if p.suffix in ('.py','.ps1','.cpp','.hpp','.json','.cs'):assert 'loss_measurement_v3' not in p.read_text(errors='replace')
 assert load(C/'baseline-allowlist.json')==dict(syntheticRoots=[str(C/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False)
 from small_binding_v3 import make
 root=make('normal');b.prepare(root);b.verify(root)
 v.update(status='PASS',run=root.name,runRoot=str(root),workspaceBindingSHA256=sha(root/b.NAME),sourceManifestSHA256=sha(C/'small-source-v3.json'),candidateFiles=235,datasetFiles=12,datasetBytes=786432,archiveMembers=664,dataset=[dict(**r,mtimeNs=(C/r['name']).stat().st_mtime_ns) for r in data],preservationDirectory=str(dest))
except BaseException as e:
 v['error']=repr(e);raise
finally:
 with (R/'preflight-result.json').open('x') as f:json.dump(v,f,indent=2)
 print(json.dumps({k:x for k,x in v.items() if k!='dataset'}))
