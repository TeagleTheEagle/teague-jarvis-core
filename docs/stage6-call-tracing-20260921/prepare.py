import pathlib,json,hashlib,zipfile,uuid,shutil,difflib,sys,inspect,subprocess
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=R.parent/'stage6-preserved-probe-sampler-diagnosis-20260921';receipt=read(old/'archive-verification.json');A=pathlib.Path(receipt['path'])
assert sha(A/'evidence.zip')==receipt['zipSHA256'] and sha(A/'archive-manifest.json')==receipt['manifestSHA256']
with zipfile.ZipFile(A/'evidence.zip') as z:
 rows=read(A/'archive-manifest.json')['files'];assert len(z.namelist())==receipt['members']==240
 for x in rows:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']==sha(pathlib.Path(x['source']))
frozen=read(old/'freeze.json');S=pathlib.Path(frozen['rawFiles'][0]['path']).parent.parent
for x in frozen['rawFiles']:
 p=pathlib.Path(x['path']);assert sha(p)==x['sha256'] and p.stat().st_size==x['bytes'] and p.stat().st_mtime_ns==x['mtime_ns']
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in frozen['sourceManifest']:
 p=S/x['name'];assert sha(p)==x['sha256'];shutil.copy2(p,C/x['name']);assert sha(C/x['name'])==x['sha256']
for name in ('call_trace.py','trace_driver.py','trace_launch.ps1'):shutil.copy2(R/name,C/name)
worker=(C/'sampler_worker.py').read_text()
prefix='''# Diagnostic markers only; first observable Python-script point follows these imports.
import time as _dt,sys as _ds,mmap as _dm,struct as _dst,os as _do,atexit as _da
_dv=_dm.mmap(-1,65536,tagname=_ds.argv[3]+'-calls');_di=0
def _mark(stage):
 global _di
 if _di>=1000:raise RuntimeError('Diagnostic marker overflow')
 _dv[8+_di*60:8+(_di+1)*60]=_dst.pack('<QI48s',_dt.perf_counter_ns(),_do.getpid(),stage.encode()[:48]);_di+=1;_dv[:4]=_dst.pack('<I',_di)
def _trace_close():
 _mark('atexit_begin');_mark('atexit_end');_dv.close()
_da.register(_trace_close)
_mark('script_entry_observed');_mark('runtime_imports_begin')
'''
modified=prefix+worker
replacements=[("from workspace import run_dir\n","from workspace import run_dir\n_mark('runtime_imports_end');_mark('path_validation_begin')\n"),("assert mode in", "_mark('path_validation_end')\nassert mode in"),("if mode=='slow':time.sleep(5)","if mode=='slow':_mark('delay_begin');time.sleep(5);_mark('delay_end')"),("if mode=='hung':time.sleep(60)","if mode=='hung':_mark('delay_begin');time.sleep(60);_mark('delay_end')"),("class MEM(c.Structure):","_mark('query_work_begin')\nclass MEM(c.Structure):"),("if not k.GlobalMemoryStatusEx", "_mark('memory_query_begin')\nif not k.GlobalMemoryStatusEx"),("v=[w.FILETIME()", "_mark('memory_query_end')\nv=[w.FILETIME()"),("if not k.GetSystemTimes", "_mark('system_times_begin')\nif not k.GetSystemTimes"),("out=dict(","_mark('system_times_end')\n_mark('serialization_begin')\nout=dict("),("with mmap.mmap", "_mark('serialization_end');_mark('result_mapping_begin')\nwith mmap.mmap")]
for a,b in replacements:assert modified.count(a)==1;modified=modified.replace(a,b)
modified+="\n_mark('result_mapping_end');_mark('query_work_end');_mark('cleanup_begin');_mark('cleanup_end');_mark('return_script')\n"
(C/'sampler_worker.py').write_text(modified)
(R/'sampler-worker.diff').write_text(''.join(difflib.unified_diff(worker.splitlines(True),modified.splitlines(True),fromfile='frozen/sampler_worker.py',tofile='diagnostic-copy/sampler_worker.py')))
for name in ('call_trace.py','trace_driver.py','sampler_worker.py'):compile((C/name).read_text(),str(C/name),'exec')
sys.path.insert(0,str(C));import call_trace as ct,ctypes
assert ct.wrap('test.return',lambda:7)()==7
ctypes.set_last_error(123);ct.wrap('test.last_error',lambda:None)();assert ctypes.get_last_error()==123
try:ct.wrap('test.exception',lambda:(_ for _ in ()).throw(ValueError('fixture')))()
except ValueError:pass
else:raise AssertionError('Exception swallowed')
assert len(ct.ROWS)==3 and all(x['endQpc']>=x['beginQpc'] for x in ct.ROWS)
assert ct.ROWS[-1]['error']=='ValueError' and ct.OVERFLOW==0
assert sha(C/'J6Probe.exe')==sha(S/'J6Probe.exe') and sha(C/'probe_policy.py')==sha(S/'probe_policy.py') and sha(C/'bounded_sampler.py')==sha(S/'bounded_sampler.py')
names=[x['name'] for x in frozen['sourceManifest']]+['call_trace.py','trace_driver.py','trace_launch.ps1']
manifest=[dict(name=n,sha256=sha(C/n)) for n in names];(C/'trace-source.json').write_text(json.dumps(manifest,indent=2))
run='calltrace-'+uuid.uuid4().hex;(C/run/'temp').mkdir(parents=True)
plan=dict(code=str(C),run=run,root=str(C/run),source=str(S),sourceHashes=frozen['sourceManifest'],diagnosticHashes=manifest,previousArchive=receipt,unchangedProbe=True,unchangedTimeouts=True,changedFrozenModuleOnly='sampler_worker.py in fresh diagnostic copy only',syntaxFiles=3,wrapperAssertions=8,protectedAccess=False)
with (R/'plan.json').open('x') as f:json.dump(plan,f,indent=2)
(R/'python-subprocess-call-path.txt').write_text(inspect.getsource(subprocess.Popen._get_handles)+'\n'+inspect.getsource(subprocess.Popen._execute_child))
print(json.dumps({k:v for k,v in plan.items() if k not in ('sourceHashes','diagnosticHashes','previousArchive')}))
