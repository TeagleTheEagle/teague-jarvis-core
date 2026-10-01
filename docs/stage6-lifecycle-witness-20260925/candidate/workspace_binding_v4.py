"""Prospective TEST binding only. No observer, tracing or acceptance authority."""
import ctypes,hashlib,json,os,pathlib,re,shutil,sys
from workspace import CODE,check_path,run_dir
SCHEMA='stage6-workspace-binding-v4'
NAME='workspace-binding-v4.json'
DLL_SHA='ff2454390795bb302cdb68990b7f52fc02db7efedb55d2bbd3dd2cbd0e1da7ef'
CLASSES=['RUN-LOCAL','CANDIDATE-LOCAL','APPROVED SHARED RUNTIME','FORBIDDEN OLD-WORKSPACE DEPENDENCY']
def need(ok,reason):
 if not ok:raise ValueError(reason)
def pairs(rows):
 d={}
 for k,v in rows:need(k not in d,'DUPLICATE_KEY');d[k]=v
 return d
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=pairs)
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(v):return hashlib.sha256(encoded(v)).hexdigest()
def write(p,v):
 with pathlib.Path(p).open('xb') as f:f.write(encoded(v));f.flush();os.fsync(f.fileno())
def safe(p,base):
 p=pathlib.Path(p);base=pathlib.Path(base)
 need(p.is_absolute() and '..' not in p.parts and ':' not in str(p)[2:] and p.is_relative_to(base),'PATH_OUTSIDE_APPROVED_ROOT')
 for q in (p,*p.parents):
  if q.exists() or q.is_symlink():need(not(q.lstat().st_file_attributes&0x400),'REPARSE')
 need(p.resolve().is_relative_to(base.resolve()),'RESOLVED_ESCAPE')
 return p
def local(name):
 p=pathlib.Path(name);need(not p.is_absolute() and '..' not in p.parts and ':' not in name,'MANIFEST_ESCAPE')
 p=safe(CODE/p,CODE);need(p.is_file() and p.stat().st_nlink==1,'MISSING_LOCAL_DEPENDENCY');return p
def entry(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def manifest():
 rows=read(CODE/'small-source-v3.json');seen=set()
 for row in rows:
  name=row['name'];need(name.casefold() not in seen,'DUPLICATE_SOURCE');seen.add(name.casefold());p=local(name)
  need((p.stat().st_size,sha(p))==(row['bytes'],row['sha256']),'SOURCE_HASH')
 return rows
def policy():
 p=read(CODE/'preservation-policy-v4.json')
 need(p['schema']=='stage6-preservation-policy-v4' and p['candidate']==str(CODE),'POLICY_CANDIDATE')
 need(p['preservationRoot']==str(CODE.parent/'preservation-v4'),'OLD_PRESERVATION_ROOT')
 safe(pathlib.Path(p['preservationRoot']),CODE.parent)
 return p
def runtime_policy():
 p=read(CODE/'shared-runtime-v4.json');need(p['schema']=='stage6-shared-runtime-v4','RUNTIME_SCHEMA')
 expected=dict(python=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe',powershell=r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',logman=r'C:\Windows\System32\logman.exe')
 need(set(p['executables'])==set(expected),'RUNTIME_IDENTITY_MISSING')
 for name,path in expected.items():
  row=p['executables'][name];need(row['path']==path and row.get('version') and row.get('sha256'),'RUNTIME_IDENTITY_MISSING')
  f=safe(path,pathlib.Path(path).parent);need(sha(f)==row['sha256'],'RUNTIME_HASH')
 approved=[pathlib.Path(expected['python']).parent,pathlib.Path(expected['pwsh']).parent,pathlib.Path(r'C:\Windows\System32')]
 need(p.get('components') and p.get('osIdentity') and p.get('moduleRoots'),'RUNTIME_COMPONENT_IDENTITY_MISSING')
 for row in p['components']:
  f=pathlib.Path(row['path']);roots=[r for r in approved if f.is_relative_to(r)];need(roots,'UNAPPROVED_RUNTIME_COMPONENT');safe(f,roots[0]);need(sha(f)==row['sha256'],'RUNTIME_COMPONENT_HASH')
 for x in p['moduleRoots']:
  f=pathlib.Path(x);need(any(f.is_relative_to(r) for r in approved),'MODULE_ROOT');safe(f,next(r for r in approved if f.is_relative_to(r)))
 return p
def tool(name):return runtime_policy()['executables'][name]['path']
def environment(p,cwd=None,env=None,search=None,imports=None):
 env=os.environ if env is None else env;cwd=pathlib.Path.cwd() if cwd is None else pathlib.Path(cwd)
 safe(cwd,CODE);need(cwd==CODE,'CWD_NOT_CANDIDATE')
 # Reject old roots before resolving any caller-supplied environment location.
 for key in ('PATH','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PSModulePath','TEMP','TMP'):
  for item in env.get(key,'').split(os.pathsep):
   if not item:continue
   if 'jarvis-stage6' in item.casefold():need(pathlib.Path(item).is_absolute() and pathlib.Path(item).is_relative_to(CODE),'OLD_WORKSPACE_ENV')
 for key in ('PYTHONHOME','PYTHONPATH','PYTHONSTARTUP'):
  need(not env.get(key),'AMBIENT_PYTHON_OVERRIDE')
 if imports is None:imports=sys.path
 allowed=[CODE,pathlib.Path(p['executables']['python']['path']).parent]
 for text in imports:
  f=pathlib.Path(text or str(cwd));need(f.is_absolute() and any(f.is_relative_to(r) for r in allowed),'PYTHON_IMPORT_ROOT')
 # Only paths for the named tools are considered, never invoke an ambient result.
 for name in ('python','pwsh','powershell','logman'):
  found=search(name+'.exe') if search else shutil.which(name+'.exe',path=env.get('PATH',''))
  if found:need(pathlib.Path(found)==pathlib.Path(p['executables'][name]['path']),'AMBIENT_TOOL_MISMATCH_'+name)
 return dict(cwd='candidate-only',ambientPythonOverrides='forbidden',oldWorkspaceEnvironment='forbidden',toolLaunch='absolute-only',pythonUserSite='disabled-for-children',powerShellProfiles=False,powerShellModules='declared-roots-only',temp='run-local',environmentDump=False)
def child_environment(root):
 p=runtime_policy();environment(p);env=os.environ.copy()
 env['PYTHONNOUSERSITE']='1';env['PSModulePath']=os.pathsep.join(p['moduleRoots'])
 env['TEMP']=env['TMP']=str(safe(root/'temp',root))
 # Per-child only; the host environment is never changed.
 env['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(v['path']).parent) for v in p['executables'].values()))
 return env
def snapshot(root,check_environment=True):
 root=safe(pathlib.Path(root),CODE);need(root.parent==CODE and re.fullmatch('protected-[0-9a-f]{32}',root.name),'RUN_BINDING')
 rows=manifest();from small_binding_v3 import validate
 declaration=read(root/'small-declaration-v3.json');validate(root,declaration)
 p=runtime_policy();env=environment(p) if check_environment else dict(cwd='candidate-only',ambientPythonOverrides='forbidden',oldWorkspaceEnvironment='forbidden',toolLaunch='absolute-only',pythonUserSite='disabled-for-children',powerShellProfiles=False,powerShellModules='declared-roots-only',temp='run-local',environmentDump=False)
 allow=read(CODE/'baseline-allowlist.json');need(allow==dict(syntheticRoots=[str(CODE/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False),'DATASET_ALLOWLIST')
 data=[]
 for i in range(12):
  f=local('small-synthetic/'+str(i).zfill(2)+'.bin');s=f.stat();data.append(dict(name=f.name,**entry(f),mtimeNs=s.st_mtime_ns,fileId=s.st_ino,volume=s.st_dev))
 need(len(list((CODE/'small-synthetic').iterdir()))==12 and sum(x['bytes'] for x in data)==786432,'DATASET_INVENTORY')
 dll=entry(local('J6OwnedEntry.dll'));need(dll['sha256']==DLL_SHA,'DLL_HASH')
 pol=policy();scripts=[dict(name=x['name'],**entry(local(x['name']))) for x in rows if pathlib.Path(x['name']).suffix in ('.py','.ps1','.cs')]
 return dict(schema=SCHEMA,dependencyClasses=CLASSES,run=root.name,workspaceRoot=str(CODE.parent),candidateRoot=str(CODE),evidenceRoot=str(root),candidateManifestSHA256=sha(CODE/'small-source-v3.json'),datasetRoot=str(CODE/'small-synthetic'),datasetManifestSHA256=digest(data),dataset=data,launcherDLL=dll,observers=[entry(local(n)) for n in ('J6AuthorityTraceV3.exe','J6StartupTrace.exe')],probe=entry(local('J6Probe.exe')),scripts=scripts,runtimes=p,sharedRuntimeManifestSHA256=sha(CODE/'shared-runtime-v4.json'),preservationTool=entry(local('failure_preserve_v4.py')),preservationPolicySHA256=sha(CODE/'preservation-policy-v4.json'),preservationDestination=pol['preservationRoot'],smallDeclarationSHA256=sha(root/'small-declaration-v3.json'),entryPoints=['one_run_v4.py','external_driver_v4.py','small_launch_v4.ps1','traced_collect.py','small_finalize_v4.py','failure_preserve_v4.py'],environmentPolicy=env)
def prepare(root):
 v=snapshot(root);write(root/NAME,v);return v
def verify(root,check_environment=True):
 need((pathlib.Path(root)/NAME).is_file(),'MISSING_WORKSPACE_BINDING');v=read(pathlib.Path(root)/NAME)
 need(v.get('schema')==SCHEMA,'BINDING_SCHEMA');need(v==snapshot(root,check_environment),'WORKSPACE_BINDING_MISMATCH');return v
def dll_path():
 f=local('J6OwnedEntry.dll');need(sha(f)==DLL_SHA,'DLL_HASH');return f
def assert_loaded(path):need(pathlib.Path(path)==dll_path(),'LOADED_MODULE_MISMATCH')
def load_dll():
 f=dll_path()
 from failure_preserve_v4 import locked_read
 with locked_read(f) as stream:
  need(hashlib.file_digest(stream,'sha256').hexdigest()==DLL_SHA,'DLL_HASH')
  dll=ctypes.WinDLL(str(f),winmode=0x900) # DLL-load-dir + System32; no PATH/CWD.
  k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetModuleFileNameW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint32]
  b=ctypes.create_unicode_buffer(32768);n=k.GetModuleFileNameW(dll._handle,b,len(b));need(0<n<len(b),'MODULE_PATH_UNAVAILABLE');assert_loaded(b.value);return dll
if __name__=='__main__':
 need(len(sys.argv)==3 and sys.argv[1] in ('prepare','verify'),'BINDING_COMMAND')
 root=run_dir(sys.argv[2]);print(json.dumps(dict(status='PASS',run=(prepare(root) if sys.argv[1]=='prepare' else verify(root))['run'])))
