"""Disposable challenge-file diagnosis only. No Core, credentials or production imports."""
import ctypes, hashlib, json, os, runpy, subprocess, sys, time, traceback, uuid
from pathlib import Path
BASE=Path(__file__).resolve().parents[2]
H=BASE/'tests/lifecycle_stage1/harness.py'
h=runpy.run_path(str(H))
E=h['BASE']
TARGET='response.json' if '--response' in sys.argv else 'challenge.json'
def save(p,x): p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def reader(root,mode):
    assert root.is_relative_to(E) and (root/'TEST_ONLY').read_text()=='NO PRODUCTION SERVICES'
    events=[]; deadline=time.monotonic()+15
    save(root/'reader-ready.json',h['process_identity'](os.getpid()))
    while not (root/'go').exists() and time.monotonic()<deadline: time.sleep(.001)
    while not (root/'stop').exists() and time.monotonic()<deadline:
        start=time.perf_counter_ns()
        try:
            with h['ipc_guard'](root/TARGET) if mode.startswith(('held','closed')) else __import__('contextlib').nullcontext():
             if mode=='held-delete':
                 k=h['k']; handle=k.CreateFileW(str(root/TARGET),0x80000000,7,None,3,0,None)
                 if handle==ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
                 try:
                     (root/'held').touch(); time.sleep(.04)
                 finally: k.CloseHandle(handle)
             elif mode in ('held-default','closed-default'):
                 with (root/TARGET).open('r',encoding='utf8') as f:
                     f.read(); (root/'held').touch(); time.sleep(.04)
             else: h['read'](root/TARGET)
            events.append({'start':start,'end':time.perf_counter_ns(),'success':True})
        except Exception as x: events.append({'start':start,'end':time.perf_counter_ns(),'error':repr(x)})
        if mode.startswith(('held','closed')): break
        time.sleep(.015 if mode=='poll15' else 0)
    save(root/'reader-events.json',events)
def main():
    run=E/('TEST-IPC-GUARD-'+uuid.uuid4().hex);run.mkdir()
    before=hashlib.sha256(H.read_bytes()).hexdigest(); results=[]
    (run/'diagnostic-source.py').write_bytes(Path(__file__).read_bytes())
    env={k:os.environ[k] for k in ('SystemRoot','WINDIR','TEMP','TMP') if k in os.environ}
    for mode in ('none','poll15','fast','held-default','held-delete','closed-default'):
        for trial in range(10):
            root=run/f'{mode}-{trial:02}';root.mkdir();(root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
            h['write'](root/TARGET,{'challenge':'initial'})
            child=None
            if mode!='none':
                child=subprocess.Popen([sys.executable,'-I',__file__,'reader',str(root),mode]+(['--response'] if TARGET=='response.json' else []),env=env,stdin=subprocess.DEVNULL,close_fds=True,creationflags=0x08000000)
                end=time.monotonic()+5
                while not (root/'reader-ready.json').exists():
                    if time.monotonic()>end: raise TimeoutError('reader ready')
                    time.sleep(.002)
                (root/'go').touch()
                if mode.startswith(('held','closed')):
                    while not (root/'held').exists():
                        if time.monotonic()>end: raise TimeoutError('reader held')
                        time.sleep(.001)
            if mode=='closed-default': child.wait(timeout=16)
            attempts=[]
            try:
                for n in range(1 if mode.startswith(('held','closed')) else 200):
                    challenge=uuid.uuid4().hex; start=time.perf_counter_ns()
                    try:
                        h['write'](root/TARGET,{'challenge':challenge})
                        attempts.append({'challenge':challenge,'start':start,'end':time.perf_counter_ns(),'published':True})
                    except Exception as x:
                        attempts.append({'challenge':challenge,'start':start,'end':time.perf_counter_ns(),'published':False,'exception':type(x).__name__,'errno':getattr(x,'errno',None),'winerror':getattr(x,'winerror',None),'source_temp':getattr(x,'filename',None),'destination':getattr(x,'filename2',None),'traceback':traceback.format_exc()})
                        break # No retry after failure.
                    if mode!='none': time.sleep(.001)
            finally:
                (root/'stop').touch()
                if child: child.wait(timeout=16)
            row={'mode':mode,'trial':trial,'writer_identity':h['process_identity'](os.getpid()),'executable':sys.executable,'executable_sha256':hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),'reader_identity':json.loads((root/'reader-ready.json').read_text()) if child else None,'reader_exit':child.returncode if child else None,'attempts':attempts}
            save(root/'writer-events.json',row);results.append(row)
        print(mode,'complete',flush=True)
    summary={'target':TARGET,'stage1_before':before,'stage1_after':hashlib.sha256(H.read_bytes()).hexdigest(),'unique_challenges_only':True,'no_retry':True,'cases':[{'mode':m,'trials':10,'failed_trials':sum(any(not a['published'] for a in r['attempts']) for r in results if r['mode']==m),'successful_publications':sum(sum(a['published'] for a in r['attempts']) for r in results if r['mode']==m)} for m in ('none','poll15','fast','held-default','held-delete','closed-default')]}
    save(run/'summary.json',summary)
    save(run/'hashes.json',{str(p.relative_to(run)):hashlib.sha256(p.read_bytes()).hexdigest() for p in run.rglob('*') if p.is_file()})
    print(str(run));print(json.dumps(summary))
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='reader': reader(Path(sys.argv[2]).resolve(),sys.argv[3])
    else:main()
