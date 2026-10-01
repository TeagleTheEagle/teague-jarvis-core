"""One authorized run: preservation and preparation only. Never launches observers."""
import pathlib,json,hashlib,zipfile,os,sys,datetime,traceback
R=pathlib.Path(r'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-one-trace-diagnostic-v4-20260923')
O=R.parent/'stage6-workspace-binding-v4-20260923'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
assert pathlib.Path.cwd()==C
assert not (R/'preflight.json').exists() and not (R/'preflight-failure.json').exists()
try:
 receipt=read(O/'archive-receipt.json');a=pathlib.Path(receipt['archive']);m=a.parent/'manifest.json'
 assert sha(a)==receipt['archiveSHA256'] and sha(m)==receipt['manifestSHA256']
 members=read(m)['files']
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==len(members)==receipt['members']==2207 and len(set(z.namelist()))==len(members)
  for x in members:
   with z.open(x['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
 v=read(O/'before.json')
 for x in v['inputs']:
  p=pathlib.Path(x['path']);s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
 prior=pathlib.Path(v['predecessor']).parent/'verify_preservation.py'
 exec(compile(prior.read_text().split('result=')[0],str(prior),'exec'),{'__file__':str(prior)})
 assert sha(C/'small-source-v3.json')=='d2f6738f5d7c3f22fe361f6cb1da174f630d8e150574009b59825d88321ed4d7'
 import workspace_binding_v4 as b
 rows=b.manifest();runtime=b.runtime_policy()
 assert len(rows)==229
 for key in ('PATH','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PSModulePath','TEMP','TMP'):
  for item in os.environ.get(key,'').split(os.pathsep):
   if 'jarvis-stage6' in item.casefold():b.need(pathlib.Path(item).is_absolute() and pathlib.Path(item).is_relative_to(C),'OLD_WORKSPACE_ENV')
 for key in ('PYTHONHOME','PYTHONPATH','PYTHONSTARTUP'):b.need(not os.environ.get(key),'AMBIENT_PYTHON_OVERRIDE')
 os.environ['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(x['path']).parent) for x in runtime['executables'].values()))
 os.environ['PSModulePath']=os.pathsep.join(runtime['moduleRoots']);os.environ['PYTHONNOUSERSITE']='1'
 b.environment(runtime)
 import failure_preserve_v4 as fp
 census=fp.host_census(C);write('prelaunch-census.json',census)
 assert census['available'] and census['processes']==[] and census['traces']==[] and census['unknown']==[], 'HOST_CENSUS_NOT_ZERO'
 dataset=[dict(name=x['name'],sha256=x['sha256'],bytes=x['bytes']) for x in rows if x['name'].startswith('small-synthetic/')]
 assert len(dataset)==12 and sum(x['bytes'] for x in dataset)==786432
 source=[dict(path=str(C/x['name']),bytes=x['bytes'],sha256=x['sha256'],mtimeNs=(C/x['name']).stat().st_mtime_ns) for x in rows]
 write('candidate-before.json',source)
 from small_binding_v3 import make
 root=make('normal');os.environ['TEMP']=os.environ['TMP']=str(root/'temp')
 binding=b.prepare(root);assert b.verify(root)==binding
 write('preflight.json',dict(status='PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=str(C),run=root.name,root=str(root),manifestSHA256=sha(C/'small-source-v3.json'),bindingSHA256=sha(root/b.NAME),dataset=dataset,datasetManifestSHA256=binding['datasetManifestSHA256'],DLL=binding['launcherDLL'],observers=binding['observers'],runtimeManifestSHA256=sha(C/'shared-runtime-v4.json'),preservationTool=binding['preservationTool'],preservationPolicySHA256=binding['preservationPolicySHA256'],preservationDestination=binding['preservationDestination'],archiveMembersVerified=len(members),originalInputsVerified=len(v['inputs']),liveLaunches=0,UAC=False,protectedAccess=False,productionChange=False))
 print(json.dumps(read(R/'preflight.json'),indent=2))
except BaseException as exc:
 write('preflight-failure.json',dict(status='BLOCKED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),liveLaunches=0,UAC=False,protectedAccess=False,productionChange=False));raise
