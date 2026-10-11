"""One-run evidence preparation only. No observers, UAC or acceptance execution."""
import pathlib,sys,os,json,hashlib,zipfile,datetime
R=pathlib.Path(__file__).parent
P=R.parent/'stage6-helper-handoff-v1-20260923'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\d45028a56e344926a311c04ba01f6a80\code')
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2)
result=dict(startUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='BLOCKED',liveStarted=False,UAC=False)
try:
 census=json.loads((R/'preflight-census.json').read_text());assert census['status']=='PASS'
 receipt=json.loads((P/'archive-receipt.json').read_text())
 assert sha(receipt['archive'])==receipt['archiveSHA256'] and sha(receipt['manifest'])==receipt['manifestSHA256']
 inv=json.loads(pathlib.Path(receipt['manifest']).read_text())
 with zipfile.ZipFile(receipt['archive']) as z:
  assert len(z.namelist())==receipt['verifiedMembers']==len(set(z.namelist()))
  for row in inv['files']:
   with z.open(row['member']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
 result['priorArchiveVerifiedMembers']=receipt['verifiedMembers']
 before=json.loads((P/'before.json').read_text())
 for row in before['inputs']:
  f=pathlib.Path(row['path']);s=f.stat();assert (s.st_size,s.st_mtime_ns,sha(f))==(row['bytes'],row['mtimeNs'],row['sha256']),str(f)
 result['preservedInputs']=len(before['inputs'])
 assert sha(C/'small-source-v3.json')=='6a86a4f287388c8c58b3df4333792217b5205305f2157043a5a2ba5456c0b15b'
 # Reject ambient overrides before setting only the reviewed process-local runtime scope.
 for key in ('PYTHONHOME','PYTHONPATH','PYTHONSTARTUP'):assert not os.environ.get(key),'AMBIENT_PYTHON_OVERRIDE_'+key
 for key in ('PATH','PSModulePath','TEMP','TMP'):
  for value in os.environ.get(key,'').split(os.pathsep):
   if 'jarvis-stage6' in value.casefold():assert pathlib.Path(value).is_relative_to(C),'OLD_WORKSPACE_ENV_'+key
 os.chdir(C);sys.path[0]=str(C)
 import workspace_binding_v4 as b
 rows=b.manifest();runtime=b.runtime_policy();b.policy()
 os.environ['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(x['path']).parent) for x in runtime['executables'].values()))
 os.environ['PSModulePath']=os.pathsep.join(runtime['moduleRoots']);os.environ['PYTHONNOUSERSITE']='1'
 b.environment(runtime)
 data=[r for r in rows if pathlib.PureWindowsPath(r['name']).parts[0]=='small-synthetic']
 names=[pathlib.PureWindowsPath(r['name']).as_posix().casefold() for r in data]
 assert len(names)==len(set(names))==12 and sum(r['bytes'] for r in data)==786432
 assert sorted(x.name for x in (C/'small-synthetic').iterdir())==[f'{i:02}.bin' for i in range(12)]
 assert json.loads((C/'baseline-allowlist.json').read_text())==dict(syntheticRoots=[str(C/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False)
 assert 'stage6-helper-handoff-v1' in (C/'helper_handoff_v1.py').read_text()
 result.update(candidate=str(C),sourceManifestSHA256=sha(C/'small-source-v3.json'),candidateFiles=len(rows),datasetFiles=12,datasetBytes=786432,dataset=[dict(**r,mtimeNs=(C/r['name']).stat().st_mtime_ns) for r in data],authoritySHA256=sha(C/'J6AuthorityTraceV3.exe'),dllSHA256=sha(b.dll_path()),runtimeManifestSHA256=sha(C/'shared-runtime-v4.json'),policySHA256=sha(C/'preservation-policy-v4.json'))
 from small_binding_v3 import make
 root=make('normal');result['run']=root.name;result['runRoot']=str(root)
 b.prepare(root);b.verify(root)
 result.update(workspaceBindingSHA256=sha(root/b.NAME),status='PASS',protectedAccess=False,productionChange=False)
except BaseException as exc:
 result['error']=type(exc).__name__+': '+str(exc)
 write('preflight-result.json',result);print(json.dumps(result));raise
else:
 write('preflight-result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='dataset'}))
