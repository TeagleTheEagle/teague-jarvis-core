"""One authorized run: preservation and preparation only. Never launches observers."""
import pathlib,json,hashlib,zipfile,os,sys,datetime,traceback
R=pathlib.Path(r'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-path-filter-fix-20260923')
O=R.parent/'stage6-workspace-binding-v4-20260923'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
def dataset_records(rows, candidate):
 """Compare Windows-relative names without rewriting authoritative records."""
 expected={
  '00.bin':'de2f256064a0af797747c2b97505dc0b9f3df0de4f489eac731c23ae9ca9cc31',
  '01.bin':'916b144867c340614f515c7b0e5415c74832d899c05264ded2a277a6e81d81ff',
  '02.bin':'da1acff5c9defdd68bfa1435c4b43e8d43ed10fcc7cbcb77a85c4482d5f5bda3',
  '03.bin':'3af3f1d870212fe8fcfe6eb321fd14d009bccc953fce3f59f698f0c446a1a39a',
  '04.bin':'ac32e587c08925897c80a703080b055606911082361fbb25198873cfca8b72d0',
  '05.bin':'ac5f57d984b20f78b36a294e26cc99512a1196eb96e4c30d7cec153813e93e1b',
  '06.bin':'570c8bbac0dfe325a89e8193cdb88560d4ce244ac2de3b5226791203107d74f5',
  '07.bin':'07dcb6d11a03624831513672ffdb84d6b1730f54e90aaace444fe3a8ea9b2163',
  '08.bin':'0e7424be9627f88499110c34e21214ed91e026e1657d9be3bd54e3e7e09fd867',
  '09.bin':'83c57546e5a31f700e7adc9edc55118bf2677bd04f0fc9089c6477b1646ffa1f',
  '10.bin':'fbd7cceab2e0f5696b4628188d3d6e4ec3f4222c02638db114d8611cb3b7f2c3',
  '11.bin':'1dfa33e4c49e3c0a9ef0b609c3fb26c5211f7cff763fa72194d884d15d86e68e'}
 candidate=b.safe(pathlib.Path(candidate),pathlib.Path(candidate))
 selected=[];seen=set()
 for row in rows:
  name=row.get('name');b.need(isinstance(name,str) and bool(name),'MALFORMED_MANIFEST_PATH')
  parts=name.replace('/','\\').split('\\')
  win=pathlib.PureWindowsPath(name)
  b.need(not win.drive and not win.root,'ABSOLUTE_MANIFEST_PATH')
  b.need(all(p and p not in ('.','..') and p==p.rstrip(' .') and not any(ord(c)<32 or c in '<>:"|?*' for c in p) for p in parts),'MALFORMED_MANIFEST_PATH')
  key='\\'.join(parts).casefold()
  b.need(key not in seen,'DUPLICATE_NORMALIZED_PATH');seen.add(key)
  if parts[0].casefold()!='small-synthetic':continue
  b.need(len(parts)==2 and parts[0]=='small-synthetic' and parts[1] in expected,'UNEXPECTED_DATASET_ENTRY')
  b.need(type(row.get('bytes')) is int and row['bytes']==65536,'DATASET_SIZE')
  b.need(row.get('sha256')==expected[parts[1]],'DATASET_EXPECTED_HASH')
  selected.append((row,parts))
 b.need(len(selected)==12 and {parts[1] for _,parts in selected}==set(expected),'DATASET_MANIFEST_COUNT')
 dataset=b.safe(candidate/'small-synthetic',candidate)
 b.need(dataset.is_dir(),'MISSING_DATASET')
 # Exact on-disk inventory; no ignored extra file, directory, or alias.
 entries=list(dataset.iterdir())
 b.need(len(entries)==12 and {p.name for p in entries}==set(expected),'DATASET_DISK_INVENTORY')
 result=[]
 for row,parts in selected:
  p=b.safe(candidate.joinpath(*parts),candidate)
  b.need(p.is_file() and p.stat().st_nlink==1,'MISSING_OR_LINKED_DATASET_FILE')
  b.need(p.stat().st_size==row['bytes'],'DATASET_SIZE')
  b.need(sha(p)==row['sha256'],'DATASET_HASH')
  result.append(dict(name=row['name'],sha256=row['sha256'],bytes=row['bytes']))
 b.need(sum(x['bytes'] for x in result)==786432,'DATASET_TOTAL_BYTES')
 return result

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
 dataset=dataset_records(rows,C)
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
