import json,hashlib,uuid,shutil,subprocess
from pathlib import Path
R=Path(__file__).parent
old=Path(json.loads((R/'preflight.json').read_text())['source'])
C=Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=[]
for p in old.iterdir():
 if p.is_file():
  shutil.copy2(p,C/p.name);before.append(dict(path=str(p),name=p.name,sha256=sha(p)))
def edit(name,func):
 p=C/name;s=p.read_text();t=func(s);assert s!=t,name;p.write_text(t)
def tracer(s):
 s=s.replace('std::wstring image;','std::wstring image,handleImage;ULONGLONG handleCreated=0;DWORD imageError=0;LONGLONG imageBegin=0,imageEnd=0;')
 needle='r.reason="RETAINED_MATCHING_KERNEL_CREATION";'
 assert s.count(needle)==1
 s=s.replace(needle,'r.handleCreated=FT(a);r.imageBegin=Q();wchar_t image[32768];DWORD count=32768;if(QueryFullProcessImageNameW(r.handle,0,image,&count))r.handleImage.assign(image,count);else r.imageError=GetLastError();r.imageEnd=Q();'+needle)
 needle='<<J(U(r.image))<<",\\\"startQpc\\\":"'
 assert needle in s
 s=s.replace(needle,'<<J(U(r.image))<<",\\\"handleImage\\\":"<<J(U(r.handleImage))<<",\\\"handleCreated\\\":\\\""<<r.handleCreated<<"\\\",\\\"imageError\\\":"<<r.imageError<<",\\\"imageBeginQpc\\\":"<<r.imageBegin<<",\\\"imageEndQpc\\\":"<<r.imageEnd<<",\\\"startQpc\\\":"')
 return s
edit('authority_trace.cpp',tracer)
def owned(s):
 # Preserve RunCollector unchanged; add a fixed qualification-only export using the same tracing implementation.
 start=s.index('extern "C" __declspec(dllexport) int RunCollector')
 f=s[start:].replace('RunCollector(', 'RunQualification(').replace('const wchar_t* path,const wchar_t* caseName','const wchar_t* path')
 f=f.replace('std::wstring root=path,mode=caseName;if(!Bounded(root)||(mode!=L"normal"&&mode!=L"hash-start-failure"))return 91;', 'std::wstring root=path;if(!Bounded(root))return 91;')
 f=f.replace('traced_collect.py\\\" "+run+L" "+mode','qualified_worker.py\\\" "+run')
 assert 'traced_collect.py' not in f
 f=f.replace('work.stdout','worker.stdout').replace('work.stderr','worker.stderr')
 needle='if(!DebugSetProcessKillOnExit(FALSE))return 96;'
 insertion='''FILETIME a{},b{},c{},d{};wchar_t image[32768];DWORD count=32768;
 if(!GetProcessTimes(pi.hProcess,&a,&b,&c,&d)||!QueryFullProcessImageNameW(pi.hProcess,0,image,&count))return 98;
 std::ostringstream ident;ident<<"{\\\"pid\\\":"<<pi.dwProcessId<<",\\\"created\\\":\\\""<<FT(a)<<"\\\",\\\"image\\\":"<<J(U(std::wstring(image,count)))<<",\\\"createBeginQpc\\\":"<<launch<<",\\\"createEndQpc\\\":"<<createEnd<<"}";
 if(!Write(root+L"\\\\worker-created.json",ident.str()))return 99;
 '''
 f=f.replace(needle,needle+insertion)
 return s+'\n'+f
edit('owned_entry.cpp',owned)
def launcher(s):
 cs='''
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
using System.Threading.Tasks;
public static class J6Qualification {
 [DllImport("DLL_PATH",CharSet=CharSet.Unicode)] public static extern int RunQualification(string root);
 public static Task<int> Start(string root) { return Task.Run(() => RunQualification(root)); }
}
'@
'''.replace('DLL_PATH',str(C/'J6OwnedEntry.dll').replace('\\','\\\\'))
 s=s.replace('try {\n $tracer=',cs+'\ntry {\n $tracer=')
 a=s.index(' $worker=Start-Process');b=s.index(" Save 'process-identities.json'",a)
 s=s[:a]+''' $worker=[J6Qualification]::Start($root)
 $born=[Diagnostics.Stopwatch]::StartNew()
 while(!(Test-Path -LiteralPath (Join-Path $root 'worker-created.json'))){if($worker.IsCompleted -or $born.Elapsed.TotalSeconds -gt 30){throw 'Worker creation evidence missing'};Start-Sleep -Milliseconds 100}
 $wi=Get-Content -Raw -LiteralPath (Join-Path $root 'worker-created.json')|ConvertFrom-Json
'''+s[b:]
 s=s.replace("pid=$worker.Id;created=$worker.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()","pid=$wi.pid;created=$wi.created")
 s=s.replace('$worker.HasExited','$worker.IsCompleted').replace('$worker.WaitForExit(20000)','$worker.Wait(20000)').replace('$worker.ExitCode','$worker.Result')
 return s
edit('qualified_launch.ps1',launcher)
# workspace.py/ps1 derive paths from their own locations; no global environment change.
V=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207');S=Path(r'C:\Program Files (x86)\Windows Kits\10');ver='10.0.26100.0'
builds=[]
for src,out,dll in [('authority_trace.cpp','J6AuthorityTrace.exe',False),('owned_entry.cpp','J6OwnedEntry.dll',True)]:
 args=[str(V/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/W4']+(['/LD'] if dll else [])+[str(C/src),'/Fo'+str(C/(src+'.obj')),'/Fe'+str(C/out),'/I'+str(V/'include')]+['/I'+str(S/'Include'/ver/x) for x in ('ucrt','shared','um')]+['/link','/LIBPATH:'+str(V/'lib/x64')]+['/LIBPATH:'+str(S/'Lib'/ver/x/'x64') for x in ('ucrt','um')]+['bcrypt.lib','advapi32.lib','tdh.lib','ole32.lib']
 p=subprocess.run(args,cwd=C,capture_output=True,text=True);builds.append(dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
 if p.returncode:break
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(C),before=before,builds=builds,after=[dict(path=str(p),sha256=sha(p)) for p in C.iterdir() if p.is_file()]),f,indent=2)
print(json.dumps(dict(code=str(C),builds=builds)))
assert len(builds)==2 and all(b['exit']==0 for b in builds)
