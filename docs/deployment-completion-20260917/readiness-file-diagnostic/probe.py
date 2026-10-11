"""Disposable file-only Windows diagnostic. No Core, credentials or providers."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import traceback
import uuid

def main():
    root=Path(__file__).parent/('run-'+uuid.uuid4().hex)
    root.mkdir()
    crt=ctypes.CDLL('ucrtbase')
    crt._get_doserrno.argtypes=[ctypes.POINTER(ctypes.c_ulong)]
    records=[]
    for mode in ('overlap','writer_finished'):
        for trial in range(500):
            path=root/(mode+'-'+str(trial)+'.json')
            temporary=path.with_suffix('.tmp')
            ready=threading.Event();finished=threading.Event();writer={}
            def publish():
                try:
                    temporary.write_text(json.dumps({'trial':trial,'mode':mode}),encoding='utf8')
                    writer['replace_start_ns']=time.perf_counter_ns();ready.set()
                    os.replace(temporary,path)
                    writer['replace_return_ns']=time.perf_counter_ns()
                except BaseException as exc:
                    writer['error']={'type':type(exc).__name__,'errno':getattr(exc,'errno',None),'winerror':getattr(exc,'winerror',None),'traceback':traceback.format_exc()}
                finally:finished.set()
            thread=threading.Thread(target=publish);thread.start()
            record={'mode':mode,'trial':trial,'path':str(path),'writer':writer}
            try:
                if not ready.wait(2):raise TimeoutError('writer start')
                if mode=='writer_finished' and not finished.wait(2):raise TimeoutError('writer completion')
                until=time.monotonic()+2
                while not path.exists():
                    if time.monotonic()>until:raise TimeoutError('publication visibility')
                record['read_start_ns']=time.perf_counter_ns()
                try:content=path.read_text(encoding='utf8')
                except OSError as exc:
                    native=ctypes.c_ulong();crt._get_doserrno(ctypes.byref(native))
                    record['error']={'type':type(exc).__name__,'errno':exc.errno,'winerror':getattr(exc,'winerror',None),'ucrt_doserrno':native.value,'operation':'Path.read_text -> open','traceback':traceback.format_exc()}
                else:
                    record['valid']=json.loads(content)=={'trial':trial,'mode':mode}
                record['read_return_ns']=time.perf_counter_ns()
            finally:
                thread.join(3)
                record['writer_exited']=not thread.is_alive()
                records.append(record)
            if thread.is_alive() or writer.get('error'):break
    report={'scope':'FILE_ONLY_NO_CORE','pid':os.getpid(),'records':records,'summary':{mode:{'trials':sum(r['mode']==mode for r in records),'read_errors':sum(r['mode']==mode and 'error' in r for r in records),'valid':sum(r['mode']==mode and r.get('valid',False) for r in records)} for mode in ('overlap','writer_finished')},'caution':'CRT doserrno is supplementary thread-local diagnostic evidence, not a captured native syscall trace.'}
    (root/'result.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({'evidence':str(root/'result.json'),'summary':report['summary']}))

if __name__=='__main__':main()
