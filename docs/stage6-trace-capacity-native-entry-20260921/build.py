import pathlib,json,subprocess,hashlib
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));C=pathlib.Path(read(R/'plan.json')['code']);S=pathlib.Path('D:/JARVIS-STAGE6-LIVE/68b6e62890e742b4bedb13cbb0f49e92/code')
for name in ('trace_sink.hpp','sink_test.cpp','trace_segments.py','native_bridge.py','traced_sampler_worker.py'):(C/name).write_bytes((R/name).read_bytes())
native=(C/'startup_trace.cpp').read_text()
native=native.replace('#include <algorithm>','#include <algorithm>\n#include <memory>\n#include "trace_sink.hpp"')
native=native.replace('static std::vector<std::string> startup;','static std::unique_ptr<TraceSink> sink;')
native=native.replace('    if(startup.size()>=200000){++startupOverflow;return;}','')
native=native.replace('if(startup.size()>=200000){++startupOverflow;return;}','')
native=native.replace('startup.push_back(o.str());','if(!sink->add(o.str()))++startupOverflow;')
native=native.replace('GUID guid;CoCreateGuid', 'sink=std::make_unique<TraceSink>(folder);\n GUID guid;CoCreateGuid')
native=native.replace(' std::ostringstream out;out<<', ' auto traceManifest=sink->finish();if(sink->fault()||startupOverflow)++faults;if(!Write(L"startup-events.json",traceManifest))++faults;\n std::ostringstream out;out<<')
start=native.index('out<<"]}";std::ostringstream st;');end=native.index('bool wrote=Write',start)
native=native[:start]+'out<<"]}";'+native[end:]
(C/'startup_trace.cpp').write_text(native)
# Reuse the validated own-child PE parsing, hardware breakpoint and debug loop.
old=(S/'entry_observer.cpp').read_text();prefix=old[:old.index('int wmain(')]
loop=old[old.index(' bool done=false'):old.index(' bool wrote=Write(root+')]
loop=loop.replace('if(elapsed>=13.6&&!deadline)','if(isProbe&&elapsed>=13.6&&!deadline)').replace('if(elapsed>=30)','if(elapsed>=(isProbe?30:1200))')
loop=loop.replace('if(FT(exited)&&double','if(isProbe&&FT(exited)&&double')
loop=loop.replace('if(observer.joinable())observer.join();','if(observer.joinable())observer.join();else WaitForSingleObject(pi.hProcess,1000);')
loop=loop.replace('CloseHandle(pi.hThread);CloseHandle(pi.hProcess);','')
body='''
extern "C" __declspec(dllexport) int TraceOwned(HANDLE ph,HANDLE th,DWORD pid,DWORD tid,const wchar_t* path,LONGLONG launch,BOOL isProbe){
 std::wstring root=path,mode=L"entry";if(!Bounded(root))return 91;
 PROCESS_INFORMATION pi{ph,th,pid,tid};LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);
 std::vector<std::string> events;bool fault=false,deadline=false,entry=false,debug=true;DWORD error=0;
 auto record=[&](std::string name,DWORD t,ULONGLONG address,std::wstring p=L""){if(events.size()>=4096){fault=true;return;}std::ostringstream s;s<<"{\\"event\\":"<<J(name)<<",\\"qpc\\":"<<Q()<<",\\"tid\\":"<<t<<",\\"address\\":"<<address<<",\\"path\\":"<<J(U(p))<<"}";events.push_back(s.str());};
 FILETIME created{},exited{},kt{},ut{};if(!GetProcessTimes(ph,&created,&exited,&kt,&ut))return 92;
 auto cb=launch,ce=Q(),acquired=Q();HANDLE independent=nullptr;
 std::atomic<DWORD> observed{UINT_MAX};LONGLONG ob=0,oe=0;std::thread observer;
 if(isProbe){if(!DuplicateHandle(GetCurrentProcess(),ph,GetCurrentProcess(),&independent,SYNCHRONIZE|PROCESS_QUERY_LIMITED_INFORMATION,FALSE,0))fault=true;
 if(independent)observer=std::thread([&]{ob=Q();observed=WaitForSingleObject(independent,15000);oe=Q();});}
'''
end='''
 bool wrote=Write(root+L"\\\\native-"+std::to_wstring(pid)+L"-"+std::to_wstring(FT(created))+L".json",s.str());return !wrote||fault||deadline||finalWait!=0||!entry?97:0;
}
extern "C" __declspec(dllexport) int RunCollector(const wchar_t* path,const wchar_t* caseName){
 std::wstring root=path,mode=caseName;if(!Bounded(root)||(mode!=L"normal"&&mode!=L"hash-start-failure"))return 91;
 auto code=root.substr(0,root.find_last_of(L'\\\\'));auto run=root.substr(root.find_last_of(L'\\\\')+1);
 std::wstring exe=L"C:\\\\Users\\\\jonny\\\\.cache\\\\codex-runtimes\\\\codex-primary-runtime\\\\dependencies\\\\python\\\\python.exe";
 std::wstring cmd=L"\\\""+exe+L"\\\" -B \\\""+code+L"\\\\traced_collect.py\\\" "+run+L" "+mode;
 SECURITY_ATTRIBUTES sa{sizeof(sa),0,TRUE};HANDLE handles[3];
 handles[0]=CreateFileW(L"NUL",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,0,0);
 handles[1]=CreateFileW((root+L"\\\\work.stdout").c_str(),GENERIC_WRITE,FILE_SHARE_READ,&sa,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,0);
 handles[2]=CreateFileW((root+L"\\\\work.stderr").c_str(),GENERIC_WRITE,FILE_SHARE_READ,&sa,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,0);
 for(auto h:handles)if(h==INVALID_HANDLE_VALUE){for(auto x:handles)if(x!=INVALID_HANDLE_VALUE)CloseHandle(x);return 93;}
 STARTUPINFOEXW si{};si.StartupInfo.cb=sizeof(si);si.StartupInfo.dwFlags=STARTF_USESTDHANDLES;si.StartupInfo.hStdInput=handles[0];si.StartupInfo.hStdOutput=handles[1];si.StartupInfo.hStdError=handles[2];
 SIZE_T size=0;InitializeProcThreadAttributeList(0,1,0,&size);std::vector<BYTE> attrs(size);si.lpAttributeList=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attrs.data());
 if(!InitializeProcThreadAttributeList(si.lpAttributeList,1,0,&size)||!UpdateProcThreadAttribute(si.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,handles,sizeof(handles),0,0))return 94;
 PROCESS_INFORMATION pi{};auto launch=Q();BOOL ok=CreateProcessW(exe.c_str(),cmd.data(),0,0,TRUE,CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT|DEBUG_ONLY_THIS_PROCESS,0,code.c_str(),&si.StartupInfo,&pi);
 DeleteProcThreadAttributeList(si.lpAttributeList);for(auto h:handles)CloseHandle(h);if(!ok)return 95;
 if(!DebugSetProcessKillOnExit(FALSE))return 96;
 int trace=TraceOwned(pi.hProcess,pi.hThread,pi.dwProcessId,pi.dwThreadId,path,launch,FALSE);DWORD status=STILL_ACTIVE;GetExitCodeProcess(pi.hProcess,&status);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return trace?trace:int(status);
}
'''
(C/'owned_entry.cpp').write_text(prefix+body+loop+end)
collector=(C/'traced_collect.py').read_text().replace(' marks=Marks(root,', ' from native_bridge import NativeBridge\n bridge=NativeBridge(root)\n marks=Marks(root,')
collector=collector.replace('  collector.Managed=Managed;', '  bridge.install()\n  collector.Managed=Managed;')
collector=collector.replace('  marks.close(status)','  try:bridge.close()\n  finally:marks.close(status)')
(C/'traced_collect.py').write_text(collector)
launch=(C/'traced_launch.ps1').read_text()
oldLine=next(x for x in launch.splitlines() if "'traced_collect.py') $Run $Case" in x)
dll=str(C/'J6OwnedEntry.dll').replace('\\','\\\\')
newLine=''' Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
public static class J6OwnChild { [DllImport("DLL",CharSet=CharSet.Unicode)] public static extern int RunCollector(string root,string mode); }
'@
 $global:LASTEXITCODE=[J6OwnChild]::RunCollector($root,$Case)'''.replace('DLL',dll)
launch=launch.replace(oldLine,newLine)
(C/'traced_launch.ps1').write_text(launch)
original=read(R.parent/'stage6-internal-startup-trace-20260921/followup-build.json')[1]['args'];results=[]
for src,out,dllMode in [('startup_trace.cpp','J6StartupTrace.exe',False),('sink_test.cpp','J6SinkTest.exe',False),('owned_entry.cpp','J6OwnedEntry.dll',True)]:
 args=[a.replace(str(S),str(C)).replace('startup_trace.cpp',src).replace('startup_trace.obj',src.replace('.cpp','.obj')).replace('J6StartupTrace.exe',out) for a in original]
 args.append('bcrypt.lib')
 if dllMode:args.insert(1,'/LD')
 p=subprocess.run(args,cwd=C,capture_output=True,text=True);results.append(dict(args=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (R/'build.json').write_text(json.dumps(results,indent=2))
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
print(json.dumps(dict(code=str(C),builds=[x['returncode'] for x in results])))
