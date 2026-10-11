"""Single-case observation of the original native fixture. No production or runtime edits."""
from pathlib import Path
import ast,ctypes as c,hashlib,importlib.util,inspect,json,os,subprocess,sys,time,traceback,uuid
D=Path(__file__).resolve().parent;R=D.parents[2]
sys.path.insert(0,str(R/'tests/lifecycle_stage2'));import pipe_transport as pt
spec=importlib.util.spec_from_file_location('fixture_diagnostic',R/'tests/lifecycle_stage4/fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
events=[];start=time.perf_counter_ns()
def log(event,**kw):events.append(dict(event=event,ns=time.perf_counter_ns(),wall=time.time(),**kw))
def process_meta(pid):
    h=pt.check(pt.k.OpenProcess(0x1000,False,pid));token=pt.H()
    try:
        times=[pt.w.FILETIME() for _ in range(4)];pt.check(pt.k.GetProcessTimes(h,*map(c.byref,times)))
        pt.check(pt.a.OpenProcessToken(h,8,c.byref(token)));size=pt.D();pt.a.GetTokenInformation(token,1,None,0,c.byref(size));buf=c.create_string_buffer(size.value)
        pt.check(pt.a.GetTokenInformation(token,1,buf,size,c.byref(size)));sid=c.cast(buf,c.POINTER(pt.P))[0];text=pt.w.LPWSTR()
        pt.check(pt.a.ConvertSidToStringSidW(sid,c.byref(text)))
        try:owner=text.value
        finally:pt.k.LocalFree(text)
        session=pt.D();pt.check(pt.a.GetTokenInformation(token,12,c.byref(session),c.sizeof(session),c.byref(size)))
        return dict(pid=pid,created=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime,owner_sid=owner,session_id=session.value)
    finally:
        if token:pt.k.CloseHandle(token)
        pt.k.CloseHandle(h)
original_io=pt.Pipe.io;original_close=pt.Pipe.close;original_listen=pt.listen;original_run=subprocess.run;OriginalPopen=subprocess.Popen
def io(self,operation,*args,**kwargs):
    log('io_begin',operation=operation,deadline=self.deadline,timeout=kwargs.get('timeout',1200))
    try:
        result=original_io(self,operation,*args,**kwargs);log('io_end',operation=operation,result=result);return result
    except Exception as e:
        log('io_exception',operation=operation,exception=type(e).__name__,reason=str(e),errno=getattr(e,'errno',None),winerror=getattr(e,'winerror',None),traceback=traceback.format_exc());raise
def close(self):log('pipe_close',handle_present=self.h is not None);return original_close(self)
def listen(name,*a,**kw):
    p=original_listen(name,*a,**kw);log('pipe_listening',endpoint=name,sddl=pt.acl(p));return p
class Popen(OriginalPopen):
    def __init__(self,*a,**kw):
        log('process_launch');super().__init__(*a,**kw);log('process_created',identity=process_meta(self.pid))
def run(command,**kwargs):
    config=json.loads(kwargs['input']);assert set(config)<= {'nativePath','endpoint','peer','action'}
    log('client_command',command=command,config=config,cwd=os.getcwd(),environment=kwargs['env'])
    result=original_run(command,**kwargs);log('client_result',stdout=result.stdout,stderr=result.stderr,returncode=result.returncode);return result
pt.Pipe.io=io;pt.Pipe.close=close;pt.listen=listen;subprocess.Popen=Popen;subprocess.run=run
source=inspect.getsource(f.native_probe);tree=ast.parse(source)
for node in ast.walk(tree):
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cases' for t in node.targets):node.value=ast.Tuple(elts=[ast.Constant('correct')],ctx=ast.Load())
ast.fix_missing_locations(tree);exec(compile(tree,str(R/'tests/lifecycle_stage4/fixtures.py'),'exec'),f.__dict__)
out=D/('original-single-'+uuid.uuid4().hex);out.mkdir();f.BASE=out
log('server_identity',identity=pt.identity(os.getpid()),process=process_meta(os.getpid()))
paths=[R/'tests/lifecycle_stage4/fixtures.py',R/'tests/lifecycle_stage2/pipe_transport.py',R/'stage4_native/peer_identity.cc',R/'stage4_client.cjs',R/'desktop/test/stage4-client.test.cjs',R/'desktop/node_modules/electron/dist/electron.exe',R.parent/'stage4-toolchain/peer-build/Release/peer_identity.node']
hashes=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
failure=None
try:f.native_probe()
except Exception as e:failure=dict(exception=type(e).__name__,reason=str(e),traceback=traceback.format_exc())
finally:
    (out/'trace.json').write_text(json.dumps(dict(events=events,failure=failure,hashes=hashes,electron_version='44.2.0',runtime_modified=False,
      observation='Original fixture isolated to correct case through AST selection. Pipe operations delegated unchanged; Popen identity queries add observation overhead. No launch args or deadlines changed.',start_ns=start),indent=2),encoding='utf8')
print(json.dumps({'evidence':str(out),'failure':failure,'io_errors':[x for x in events if x['event']=='io_exception'],'client':[x for x in events if x['event']=='client_result']},ensure_ascii=True))
