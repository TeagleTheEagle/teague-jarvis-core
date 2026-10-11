"""Explicit protected_baseline mode. This campaign permits synthetic roots only."""
import pathlib,os,json,hashlib,uuid,datetime,shutil,sys
from workspace import CODE,check_path,new_run,run_dir,activate_temp
from dry_contract import read,save,sha,state,advance,write_state,PHASES
DENIED=(r'C:\Users\jonny\VirtualBox VMs',r'C:\Users\jonny\.VirtualBox')
def approved(source):
 text=str(source)
 # Never resolve a caller path before checking its explicit approval entry.
 allowed=read(CODE/'baseline-allowlist.json')
 protected=allowed.get('approvedProtectedRoots',[])
 is_protected=text in protected and allowed.get('realProtectedAccess') is True
 if any(text.casefold().startswith(x.casefold()) for x in DENIED) and not is_protected:raise ValueError('Real protected access NOT authorized in this campaign')
 p=pathlib.Path(source)
 if not p.is_absolute() or '..' in p.parts:raise ValueError('Absolute approved root required')
 # Only explicit roots generated for this synthetic campaign; never arbitrary caller filesystem access.
 if not is_protected:
  if str(p) not in allowed['syntheticRoots']:raise ValueError('Unapproved root')
  check_path(p)
 elif p.drive.upper() not in ('C:','D:') or ':' in str(p)[2:]:raise ValueError('Local approved protected root required')
 for q in (p,*p.parents):
  if q.exists() and q.lstat().st_file_attributes&0x400:raise ValueError('Reparse root rejected')
 return p
def metadata(p):
 s=p.lstat()
 if s.st_file_attributes&0x400 or not p.is_file() or s.st_nlink!=1:raise ValueError('Nonregular/reparse/hardlink source')
 return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,LastWriteTimeUtc=datetime.datetime.fromtimestamp(s.st_mtime_ns/1e9,datetime.timezone.utc).isoformat(),fileId=s.st_ino,volume=s.st_dev)
def inventory(source):
 base=approved(source);rows={};seen=set()
 for directory,dirs,names in os.walk(base,followlinks=False):
  dirs.sort(key=str.casefold);names.sort(key=str.casefold)
  for name in dirs+names:
   p=pathlib.Path(directory)/name
   if p.lstat().st_file_attributes&0x400:raise ValueError('Reparse entry rejected')
   rel=p.relative_to(base).as_posix()
   if ':' in rel or '..' in pathlib.PurePosixPath(rel).parts or rel.casefold() in seen:raise ValueError('Duplicate/escaping source path')
   seen.add(rel.casefold())
  for name in names:
   p=pathlib.Path(directory)/name;rel=p.relative_to(base).as_posix();rows[rel]=dict(metadata(p),fullPath=str(p),relativePath=rel)
 if not rows:raise ValueError('Empty source')
 return dict(sorted(rows.items(),key=lambda x:x[0].casefold()))
def limits():
 v=read(CODE/'baseline-limits.json')
 if not 90<=v['campaign']<=3600 or not v['campaign']+90<=v['monitor']<=3720 or not 0<=v['hold']<v['campaign']-30:raise ValueError('Finite reviewed duration bounds required')
 if (v['heartbeat'],v['probe'],v['observer'])!=(10.0,13.6,15.0):raise ValueError('Safety threshold modification')
 return v
def validate(root,v):
 if set(v)!={'version','mode','run','scenario','source','inventory','thresholds','synthetic'} or v['version']!=1 or v['mode']!='protected_baseline' or v['scenario']!='protected_baseline' or v['run']!=root.name or not isinstance(v['synthetic'],bool):raise ValueError('Explicit canonical baseline contract required')
 base=approved(v['source'])
 if v['synthetic']!=(str(base) in read(CODE/'baseline-allowlist.json')['syntheticRoots']):raise ValueError('Source classification mismatch')
 if root.is_relative_to(base) or base.is_relative_to(root):raise ValueError('Source/output overlap')
 if v['thresholds']!=limits():raise ValueError('Duration policy drift')
 if inventory(base)!=v['inventory']:raise ValueError('Source metadata/identity drift')
 return v
def load(root):return validate(root,read(root/'contract.json'))
def prepare(source):
 base=approved(source)
 if shutil.disk_usage(CODE).free<2**30:raise RuntimeError('Insufficient live evidence headroom')
 data=inventory(base);root=new_run('protected-'+uuid.uuid4().hex);activate_temp(root)
 v=dict(version=1,mode='protected_baseline',scenario='protected_baseline',run=root.name,source=str(base),inventory=data,thresholds=limits(),synthetic=str(base) in read(CODE/'baseline-allowlist.json')['syntheticRoots'])
 validate(root,v);save(root/'contract.json',v);save(root/'state.json',dict(phase='PREPARED',sequence=0,failed=False,history=[dict(phase='PREPARED',qpc=__import__('time').perf_counter_ns())]))
 return root
def install_write_guard(root):
 """Worker defense against accidental Python writes/operations outside its D: run, not an OS sandbox."""
 def permitted(p):
  if isinstance(p,int):return False
  try:return check_path(pathlib.Path(os.fsdecode(p))).is_relative_to(root)
  except (ValueError,TypeError):return False
 def audit(event,args):
  if event=='open':
   path,mode,flags=args
   writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
   if writing and not permitted(path):raise PermissionError('Worker writes restricted to live run')
  elif event in ('os.remove','os.rmdir','os.mkdir','os.chmod','os.utime','os.truncate'):
   if not permitted(args[0]):raise PermissionError('Source mutation denied')
  elif event in ('os.rename','os.link','os.symlink'):
   if not permitted(args[0]) or not permitted(args[1]):raise PermissionError('Source mutation denied')
  elif event in ('subprocess.Popen','os.system','os.startfile'):raise PermissionError('Worker process launch denied')
 sys.addaudithook(audit)
if __name__=='__main__':
 if sys.argv[1]=='prepare':print(prepare(sys.argv[2]))
 elif sys.argv[1]=='ready':
  root=run_dir(sys.argv[2]);load(root);advance(root,'PREPARED','OBSERVERS_READY')
 elif sys.argv[1]=='closed':
  root=run_dir(sys.argv[2]);load(root)
  for name in ('app-exit.json','launcher-result.json'):
   v=read(root/name)
   if not v['exited'] or v['exitCode']!=0:raise RuntimeError('Observer failed closure')
  advance(root,'WORKLOAD_CLOSED','OBSERVERS_CLOSED')
 else:raise ValueError('Unsupported operation')
