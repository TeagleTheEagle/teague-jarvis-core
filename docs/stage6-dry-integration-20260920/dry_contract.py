"""Canonical TEST-only contract. No legacy mode/diagnostic-letter translation."""
import pathlib,json,os,hashlib,time,sys,uuid
from workspace import CODE,check_path,run_dir,new_run,activate_temp
FULL=pathlib.Path(r'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-heartbeat-journal-20260918\sacrificial')
PHASES=('PREPARED','OBSERVERS_READY','WORKLOAD_RUNNING','HASH1_COMPLETE','HASH2_COMPLETE','METADATA_VERIFIED','WORKLOAD_CLOSED','OBSERVERS_CLOSED','CLEANUP_VERIFIED','FINALIZED','MANIFESTED','ARCHIVED','VERIFIED')
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,v):
 check_path(p)
 with pathlib.Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
def write_state(root,v):
 p=check_path(root/'state.pending');save(p,v);os.replace(p,check_path(root/'state.json'))
def state(root):return read(root/'state.json')
def advance(root,expected,target,proof=None):
 v=state(root)
 if v.get('failed') or v['phase']!=expected or PHASES.index(target)!=PHASES.index(expected)+1:raise ValueError('Invalid/stale phase transition')
 v['phase']=target;v['sequence']+=1;v['history'].append(dict(phase=target,qpc=time.perf_counter_ns(),proof=proof));write_state(root,v)
def reject_reparse(p):
 for q in (p,*p.parents):
  if q.is_symlink() or q.is_junction():raise ValueError('Reparse source forbidden')
def source_for(root,scenario):
 if scenario=='miniature':return check_path(root/'synthetic')
 if scenario=='dry1':return FULL
 raise ValueError('Unsupported scenario')
def inventory(p):
 reject_reparse(p);files=sorted(p.iterdir())
 if len(files)!=12 or any(not f.is_file() or f.suffix!='.bin' or f.is_symlink() or f.is_junction() for f in files):raise ValueError('Exactly 12 regular sacrificial .bin files required')
 return {f.name:dict(bytes=f.stat().st_size,mtime_ns=f.stat().st_mtime_ns) for f in files}
def validate(root,v):
 if set(v)!={'version','run','scenario','source','inventory','thresholds'} or v['version']!=1 or v['run']!=root.name:raise ValueError('Invalid canonical contract; legacy mode/phase configurations rejected')
 expected=source_for(root,v['scenario'])
 # Reject unapproved source text before resolving/opening anything supplied by caller.
 if v['source']!=str(expected):raise ValueError('Source is not the fixed sacrificial allowlist')
 if v['thresholds']!={'warning':5.0,'probe':13.6,'observer':15.0,'heartbeat':10.0,'campaign':90.0}:raise ValueError('Deadline modification forbidden')
 reject_reparse(expected)
 if inventory(expected)!=v['inventory']:raise ValueError('Sacrificial metadata changed')
 return v
def load(root):return validate(root,read(root/'contract.json'))
def prepare(scenario):
 if scenario not in ('miniature','dry1'):raise ValueError('Unsupported scenario')
 root=new_run('integrated-'+scenario+'-'+uuid.uuid4().hex);activate_temp(root)
 source=source_for(root,scenario)
 if scenario=='miniature':
  source.mkdir()
  for i in range(12):
   with (source/(str(i).zfill(2)+'.bin')).open('xb') as f:f.write(bytes([i])*4096);f.flush();os.fsync(f.fileno())
 contract=dict(version=1,run=root.name,scenario=scenario,source=str(source),inventory=inventory(source),thresholds=dict(warning=5.0,probe=13.6,observer=15.0,heartbeat=10.0,campaign=90.0))
 validate(root,contract);save(root/'contract.json',contract);save(root/'state.json',dict(phase='PREPARED',sequence=0,failed=False,history=[dict(phase='PREPARED',qpc=time.perf_counter_ns())]))
 return root
if __name__=='__main__':
 if sys.argv[1]=='prepare':print(prepare(sys.argv[2]))
 elif sys.argv[1]=='ready':
  root=run_dir(sys.argv[2]);load(root);advance(root,'PREPARED','OBSERVERS_READY')
 elif sys.argv[1]=='closed':
  root=run_dir(sys.argv[2]);load(root)
  for name in ('app-exit.json','launcher-result.json'):
   v=read(root/name)
   if not v['exited'] or v['exitCode']!=0:raise RuntimeError('Observer failed to close')
  advance(root,'WORKLOAD_CLOSED','OBSERVERS_CLOSED')
 else:raise ValueError('Unknown operation')
