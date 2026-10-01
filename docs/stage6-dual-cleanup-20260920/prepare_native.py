import pathlib,json,hashlib,subprocess
r=pathlib.Path(__file__).parent;d=pathlib.Path(json.loads((r/'plan.json').read_text())['live_code']);p=r/'kernel_trace.cpp';s=p.read_text();before=hashlib.sha256(p.read_bytes()).hexdigest()
replacements=[('retained=0,signal=0;','retained=0,attemptBegin=0,signal=0;'),('static void Acquire(Row& r){r.handle=OpenProcess','static void Acquire(Row& r){r.attemptBegin=Q();r.handle=OpenProcess'),(r'<<",\"handleAttemptQpc\":"<<r.retained',r'<<",\"handleAttemptBeginQpc\":"<<r.attemptBegin<<",\"handleAttemptQpc\":"<<r.retained')]
for old,new in replacements:
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
p.write_text(s);(d/'kernel_trace.cpp').write_bytes(p.read_bytes())
vc=pathlib.Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207');sdk=pathlib.Path(r'C:\Program Files (x86)\Windows Kits\10')
args=[str(vc/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/W4',str(d/'kernel_trace.cpp'),'/I'+str(vc/'include')]+['/I'+str(sdk/'Include/10.0.26100.0'/x) for x in ('um','shared','ucrt')]+['/Fo'+str(d/'kernel_trace.obj'),'/Fe'+str(d/'J6KernelTrace.exe'),'/link','/LIBPATH:'+str(vc/'lib/x64')]+['/LIBPATH:'+str(sdk/'Lib/10.0.26100.0'/x/'x64') for x in ('um','ucrt')]+['tdh.lib','advapi32.lib','ole32.lib']
q=subprocess.run(args,cwd=d,capture_output=True,text=True)
out=dict(command=args,exit=q.returncode,stdout=q.stdout,stderr=q.stderr,before=before,after=hashlib.sha256(p.read_bytes()).hexdigest(),exeSHA256=hashlib.sha256((d/'J6KernelTrace.exe').read_bytes()).hexdigest())
with (r/'native-build.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(q.returncode)
