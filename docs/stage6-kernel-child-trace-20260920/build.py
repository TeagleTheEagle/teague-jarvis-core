import pathlib,subprocess,json,hashlib,shutil,uuid
r=pathlib.Path(__file__).parent
p=json.loads((r/'plan.json').read_text()); d=pathlib.Path(p['live_code'])
src=r/'kernel_trace.cpp'; dst=d/src.name
history=d/('build-history-'+uuid.uuid4().hex);history.mkdir()
for name in ('kernel_trace.cpp','J6KernelTrace.exe'):
 if (d/name).exists():shutil.copyfile(d/name,history/name)
shutil.copyfile(src,dst)
vc=pathlib.Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207')
sdk=pathlib.Path(r'C:\Program Files (x86)\Windows Kits\10')
args=[str(vc/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/W4',str(dst),'/I'+str(vc/'include')]
args += ['/I'+str(sdk/'Include/10.0.26100.0'/x) for x in ('um','shared','ucrt')]
args += ['/Fo'+str(d/'kernel_trace.obj'),'/Fe'+str(d/'J6KernelTrace.exe'),'/link','/LIBPATH:'+str(vc/'lib/x64')]
args += ['/LIBPATH:'+str(sdk/'Lib/10.0.26100.0'/x/'x64') for x in ('um','ucrt')]
args += ['tdh.lib','advapi32.lib','ole32.lib']
q=subprocess.run(args,cwd=d,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
out=dict(command=args,exit=q.returncode,output=q.stdout,sourceSha256=hashlib.sha256(src.read_bytes()).hexdigest())
if not q.returncode:out['exeSha256']=hashlib.sha256((d/'J6KernelTrace.exe').read_bytes()).hexdigest()
with (r/('build-result-'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(q.returncode)
