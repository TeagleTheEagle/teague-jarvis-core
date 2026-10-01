import pathlib, hashlib, json, uuid, shutil, difflib
R=pathlib.Path(__file__).resolve().parent
OLD=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\ac2f7b1000034e9bbcb0486fcb6ef9cb\code')
H=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\3316657ba1864413a0c95ea1dc7bf6ff\code')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(H/'trace_sink.hpp')=='02d7b459e2da6e7998ebff0fdf8d76c7e6e339774ffee6d7e4c84fca25fb8b36'
C=OLD.parent.parent/uuid.uuid4().hex/'code';C.mkdir(parents=True)
before=[];changes=[]
for name in ('authority_trace.cpp','startup_trace.cpp','durable_sink.hpp','trace_sink.hpp','sink_test.cpp','durable_test.cpp','J6ProbeNative.exe'):
 p=(H if name=='trace_sink.hpp' else OLD)/name
 before.append(dict(path=str(p),sha256=sha(p)))
 shutil.copy2(p,C/name)
shutil.copy2(R/'trace_telemetry.hpp',C/'trace_telemetry.hpp')
def replace(s,a,b,n=1):
 assert s.count(a)==n,(a,s.count(a),n)
 return s.replace(a,b)
for name in ('authority_trace.cpp','startup_trace.cpp'):
 p=C/name;old=p.read_text();s=old
 s=replace(s,'#define WIN32_LEAN_AND_MEAN','#define WIN32_LEAN_AND_MEAN\n#include "trace_telemetry.hpp"')
 s=replace(s,'std::lock_guard<std::mutex> l(guard);','j6t::Lock l(guard);',s.count('std::lock_guard<std::mutex> l(guard);'))
 s=replace(s,'static bool Field(EVENT_RECORD* e,const wchar_t* name,std::vector<BYTE>& v){','static bool Field(EVENT_RECORD* e,const wchar_t* name,std::vector<BYTE>& v){j6t::Scope timing(j6t::Metadata);')
 schema='RawSchemas' if name=='startup_trace.cpp' else 'Schemas'
 s=replace(s,f'static std::vector<std::string> {schema}(EVENT_RECORD* e){{',f'static std::vector<std::string> {schema}(EVENT_RECORD* e){{j6t::Scope timing(j6t::Metadata);')
 if name=='authority_trace.cpp':
  s=replace(s,'static void WINAPI Event(EVENT_RECORD* e){try{','static void WINAPI Event(EVENT_RECORD* e){j6t::CallbackScope timing;try{')
  s=replace(s,'Capture(r,true);','timing.selected=true;Capture(r,true);')
  s=replace(s,'Capture(r,false);','timing.selected=true;Capture(r,false);')
  s=replace(s,'lifecycleSink->add(o.str())','j6t::measure(j6t::Admission,[&]{return lifecycleSink->add(o.str());})')
 else:
  s=replace(s,'static void WINAPI Event(EVENT_RECORD* e){','static void WINAPI Event(EVENT_RECORD* e){j6t::CallbackScope timing;')
  s=replace(s,'if(!target)return;','if(!target)return;timing.selected=true;')
  s=replace(s,'sink->add(o.str())','j6t::measure(j6t::Admission,[&]{return sink->add(o.str());})')
 s=replace(s,'ULONG start=StartTraceW(&sessionHandle,session.c_str(),p);','ULONG start=j6t::telemetry.call("StartTrace",[&]{return StartTraceW(&sessionHandle,session.c_str(),p);});')
 s=replace(s,'TRACEHANDLE consumer=OpenTraceW(&log);','j6t::telemetry.query(sessionHandle,session.c_str(),"afterStartTrace");auto openBegin=j6t::now();TRACEHANDLE consumer=OpenTraceW(&log);')
 s=replace(s,'ULONG enable=openError?openError:','j6t::telemetry.phase("OpenTrace",openBegin,j6t::now(),openError);ULONG enable=openError?openError:')
 import re
 s=re.sub(r'EnableTraceEx2\(([^;]*?)\)',lambda m:'j6t::telemetry.call("EnableProvider'+('File' if '&FileProvider' in m[1] else 'Registry' if '&RegProvider' in m[1] else 'Process')+'",[&]{return EnableTraceEx2('+m[1]+');})',s)
 s=replace(s,'std::atomic<ULONG> consumed{ULONG_MAX};','j6t::telemetry.query(sessionHandle,session.c_str(),"afterEnable");std::atomic<ULONG> consumed{ULONG_MAX};')
 s=replace(s,'consumed=ProcessTrace(&consumer,1,nullptr,nullptr);','auto b=j6t::now();j6t::telemetry.phase("ProcessTraceEntry",b,b);consumed=ProcessTrace(&consumer,1,nullptr,nullptr);j6t::telemetry.phase("ProcessTraceReturn",b,j6t::now(),consumed);')
 s=replace(s,'LONGLONG begin=Q();bool requested=false;','j6t::telemetry.phase("ReadyPublished",Q(),Q(),ready?0:1);j6t::telemetry.query(sessionHandle,session.c_str(),"ready");LONGLONG begin=Q();bool requested=false;')
 s=replace(s,'){Sample();if(GetFileAttributesW','){j6t::telemetry.poll(sessionHandle,session.c_str(),freq.QuadPart);Sample();if(GetFileAttributesW')
 s=replace(s,'ULONG flush=ControlTraceW(sessionHandle,session.c_str(),p,EVENT_TRACE_CONTROL_FLUSH);','j6t::telemetry.phase("StopRequestedOrLoopEnded",Q(),Q(),requested?0:1);j6t::telemetry.query(sessionHandle,session.c_str(),"beforeFlush");ULONG flush=j6t::telemetry.call("FlushTrace",[&]{return ControlTraceW(sessionHandle,session.c_str(),p,EVENT_TRACE_CONTROL_FLUSH);});')
 s=replace(s,'ULONG stop=ControlTraceW(sessionHandle,session.c_str(),p,EVENT_TRACE_CONTROL_STOP);','j6t::telemetry.query(sessionHandle,session.c_str(),"beforeStop");ULONG stop=j6t::telemetry.call("StopTrace",[&]{return ControlTraceW(sessionHandle,session.c_str(),p,EVENT_TRACE_CONTROL_STOP);});')
 s=replace(s,'out<<"]}";bool wrote=', 'out<<"]}";if(!Write(L"loss-telemetry.json",j6t::telemetry.json())||j6t::telemetry.errors.load())++faults;bool wrote=')
 p.write_text(s,encoding='utf8');changes.append(dict(name=name,before=hashlib.sha256(old.encode()).hexdigest(),after=sha(p)))
 (R/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='frozen/'+name,tofile='candidate/'+name)))
for name in ('durable_sink.hpp','trace_sink.hpp'):
 p=C/name;old=p.read_text();s='#include "trace_telemetry.hpp"\n'+old
 for a,b in [('WriteFile(','j6t::write('),('FlushFileBuffers(','j6t::flush('),('CloseHandle(','j6t::close(')]:s=s.replace(a,b)
 p.write_text(s,encoding='utf8');changes.append(dict(name=name,before=hashlib.sha256(old.encode()).hexdigest(),after=sha(p)))
 (R/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='frozen/'+name,tofile='candidate/'+name)))
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(C),before=before,changes=changes),f,indent=2)
print(C)
