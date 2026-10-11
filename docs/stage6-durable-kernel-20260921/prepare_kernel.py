import json,uuid,subprocess,hashlib
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code'])
source=(C/'kernel_trace.cpp').read_text()
source=source.replace('#define WIN32_LEAN_AND_MEAN','#define WIN32_LEAN_AND_MEAN\n#define NOMINMAX\n#include "durable_sink.hpp"',1)
insert=r'''
static std::unique_ptr<DurableSink> lifecycleSink;
static unsigned long long lifecycleCaptured=0;
static void Capture(const Row&r,bool start){
 std::ostringstream o;o<<"{\"source\":\"Microsoft-Windows-Kernel-Process\",\"scope\":"<<J(U(session))<<",\"kind\":"<<J(start?"start":"stop")<<",\"pid\":"<<r.pid<<",\"created\":\""<<r.created<<"\",\"sequence\":\""<<r.sequence<<"\",\"parentPid\":"<<r.parent<<",\"parentSequence\":\""<<r.parentSequence<<"\",\"image\":"<<J(U(r.image))<<",\"eventQpc\":"<<(start?r.start:r.stop)<<",\"callbackQpc\":"<<(start?r.notified:r.stopNotified)<<",\"exitFiletime\":\""<<(start?0:r.exitFT)<<"\",\"exitCode\":"<<r.exitCode<<",\"version\":"<<(start?r.version:r.stopVersion)<<"}";
 if(!lifecycleSink->add(o.str()))++faults;else ++lifecycleCaptured;
}
'''
needle='static void WINAPI Event(EVENT_RECORD* e)'
assert source.count(needle)==1;source=source.replace(needle,insert+'\n'+needle)
needle='r.schema=Schemas(e);Acquire(r);';assert needle in source;source=source.replace(needle,'r.schema=Schemas(e);Capture(r,true);Acquire(r);')
needle='r.stopSchema=Schemas(e);}';assert needle in source;source=source.replace(needle,'r.stopSchema=Schemas(e);Capture(r,false);}')
needle='std::vector<BYTE> buffer(sizeof(EVENT_TRACE_PROPERTIES)+1024);';assert needle in source;source=source.replace(needle,'lifecycleSink=std::make_unique<DurableSink>(folder,"kernel-authority",8192);\n '+needle)
needle=' std::ostringstream out;out<<"{\\\"requestedStop';assert needle in source
source=source.replace(needle,' lifecycleSink->finish();if(lifecycleSink->fault())++faults;\n'+needle)
with (R/'authority_trace.cpp').open('x') as f:f.write(source)
with (C/'authority_trace.cpp').open('x') as f:f.write(source)
# Fresh launcher variant: same bounded approvals/closure, new exact TEST tracer.
launch=(C/'identity_launch.ps1').read_text().replace('J6StartupTrace.exe','J6AuthorityTrace.exe').replace('identity_worker.py','qualified_worker.py')
with (R/'qualified_launch.ps1').open('x') as f:f.write(launch)
with (C/'qualified_launch.ps1').open('x') as f:f.write(launch)
worker=(C/'identity_worker.py').read_text()
worker=worker.replace('from journal import ticks,frequency','from journal import ticks,frequency,PublisherWatch')
worker=worker.replace('b=NativeBridge(root);b.install();probes=[];failure=None', '''ready=json.loads((root/'app-ready.json').read_text(encoding='utf-8-sig'))
watch=PublisherWatch(ready);health_samples=[]
def health():
 watch.check()
 v=json.loads((root/'app-health.json').read_text(encoding='utf-8-sig'))
 age=(ticks()-v['qpc'])/v['frequency']
 if v['pid']!=ready['pid'] or not v['healthy'] or not 0<=age<10:raise RuntimeError('Unhealthy live application observer')
 health_samples.append(dict(qpc=ticks(),age=age))
b=NativeBridge(root);b.install();probes=[];failure=None''')
worker=worker.replace('lambda:None,lambda v:None','health,lambda v:None')
worker=worker.replace("if failure:raise RuntimeError(failure)","watch.close()\nsave('live-health-checks.json',health_samples)\nif failure:raise RuntimeError(failure)")
with (R/'qualified_worker.py').open('x') as f:f.write(worker)
with (C/'qualified_worker.py').open('x') as f:f.write(worker)
V=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207');S=Path(r'C:\Program Files (x86)\Windows Kits\10');ver='10.0.26100.0'
args=[str(V/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/W4',str(C/'authority_trace.cpp'),'/Fo'+str(C/'authority_trace.obj'),'/Fe'+str(C/'J6AuthorityTrace.exe'),'/I'+str(V/'include')]+['/I'+str(S/'Include'/ver/x) for x in ('ucrt','shared','um')]+['/link','/LIBPATH:'+str(V/'lib/x64')]+['/LIBPATH:'+str(S/'Lib'/ver/x/'x64') for x in ('ucrt','um')]+['bcrypt.lib','advapi32.lib','tdh.lib','ole32.lib']
p=subprocess.run(args,cwd=C,capture_output=True,text=True)
with (R/('kernel-build-'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),f,indent=2)
print(p.stdout,p.stderr);raise SystemExit(p.returncode)
