// Non-elevated, own-child-only diagnostic. Fixed unchanged J6Probe.exe.
// A hardware execution breakpoint observes its PE entry; no image bytes patched.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>
#include <vector>
#include <sstream>
#include <thread>
#include <atomic>
#include <climits>
static LONGLONG Q(){LARGE_INTEGER x;QueryPerformanceCounter(&x);return x.QuadPart;}
static ULONGLONG FT(FILETIME x){return (ULONGLONG(x.dwHighDateTime)<<32)|x.dwLowDateTime;}
static std::string U(std::wstring w){int n=WideCharToMultiByte(CP_UTF8,0,w.data(),int(w.size()),0,0,0,0);std::string s(n,0);WideCharToMultiByte(CP_UTF8,0,w.data(),int(w.size()),s.data(),n,0,0);return s;}
static std::string J(std::string s){std::string r="\"";for(unsigned char c:s){if(c=='\\'||c=='"')r+='\\';if(c<32)r+='?';else r+=c;}return r+'"';}
static bool Bounded(std::wstring p){if(p.rfind(L"D:\\JARVIS-STAGE6-LIVE\\",0)||p.find(L"..")!=p.npos)return false;for(size_t i=3;i<=p.size();i++){if(i<p.size()&&p[i]!=L'\\')continue;auto a=GetFileAttributesW(p.substr(0,i).c_str());if(a==INVALID_FILE_ATTRIBUTES||(a&FILE_ATTRIBUTE_REPARSE_POINT))return false;}return true;}
static std::wstring Path(HANDLE h){if(!h)return L"";wchar_t b[32768];DWORD n=GetFinalPathNameByHandleW(h,b,32768,FILE_NAME_NORMALIZED);return n&&n<32768?std::wstring(b,n):L"";}
static bool Write(std::wstring p,std::string s){HANDLE h=CreateFileW(p.c_str(),GENERIC_WRITE,FILE_SHARE_READ,0,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,0);if(h==INVALID_HANDLE_VALUE)return false;DWORD n=0;BOOL ok=WriteFile(h,s.data(),DWORD(s.size()),&n,0);BOOL f=FlushFileBuffers(h);CloseHandle(h);return ok&&f&&n==s.size();}

extern "C" __declspec(dllexport) int TraceOwned(HANDLE ph,HANDLE th,DWORD pid,DWORD tid,const wchar_t* path,LONGLONG launch,BOOL isProbe,LONGLONG cb,LONGLONG ce){
 std::wstring root=path,mode=L"entry";if(!Bounded(root))return 91;
 PROCESS_INFORMATION pi{ph,th,pid,tid};LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);
 std::vector<std::string> events;bool fault=false,deadline=false,entry=false,debug=true;DWORD error=0;
 auto record=[&](std::string name,DWORD t,ULONGLONG address,std::wstring p=L""){if(events.size()>=4096){fault=true;return;}std::ostringstream s;s<<"{\"event\":"<<J(name)<<",\"qpc\":"<<Q()<<",\"tid\":"<<t<<",\"address\":"<<address<<",\"path\":"<<J(U(p))<<"}";events.push_back(s.str());};
 FILETIME created{},exited{},kt{},ut{};if(GetProcessId(ph)!=pid||GetThreadId(th)!=tid||!GetProcessTimes(ph,&created,&exited,&kt,&ut))return 92;
 auto acquired=Q();
 // Direct process identity comes from the creator's handle, before any debug continuation.
 auto imageBegin=Q();wchar_t imageBuffer[32768]{};DWORD imageCount=32768;
 BOOL imageOK=QueryFullProcessImageNameW(ph,0,imageBuffer,&imageCount);
 DWORD imageError=imageOK?0:GetLastError();auto imageEnd=Q();
 DWORD identityWait=WaitForSingleObject(ph,0);auto stateQpc=Q();
 std::wstring fullImage=imageOK?std::wstring(imageBuffer,imageCount):L"";
 bool identityOK=imageOK&&imageCount>0&&imageCount<32768&&identityWait==WAIT_TIMEOUT;
 std::ostringstream early;
 early<<"{\"source\":\"creator-owned-handle\",\"recordId\":"<<J(std::to_string(pid)+"-"+std::to_string(FT(created)))<<",\"creatorPid\":"<<GetCurrentProcessId()<<",\"pid\":"<<pid<<",\"tid\":"<<tid<<",\"handlePid\":"<<GetProcessId(ph)<<",\"handleIdentity\":\""<<reinterpret_cast<ULONG_PTR>(ph)<<"\",\"created\":\""<<FT(created)<<"\",\"handleCreated\":\""<<FT(created)<<"\",\"frequency\":"<<freq.QuadPart<<",\"createBeginQpc\":"<<cb<<",\"createEndQpc\":"<<ce<<",\"handleAcquiredQpc\":"<<acquired<<",\"queryBeginQpc\":"<<imageBegin<<",\"queryEndQpc\":"<<imageEnd<<",\"stateQpc\":"<<stateQpc<<",\"processState\":"<<identityWait<<",\"image\":"<<J(U(fullImage))<<",\"imageError\":"<<imageError<<",\"imageCharacters\":"<<imageCount<<",\"success\":"<<(identityOK?"true":"false")<<"}";
 bool identityWritten=Write(root+L"\\early-image-"+std::to_wstring(pid)+L"-"+std::to_wstring(FT(created))+L".json",early.str());
 auto identityPersisted=identityWritten?Q():0;if(!identityOK||!identityWritten)fault=true;
 HANDLE independent=nullptr;
 std::atomic<DWORD> observed{UINT_MAX};LONGLONG ob=0,oe=0;std::thread observer;
 if(isProbe){if(!DuplicateHandle(GetCurrentProcess(),ph,GetCurrentProcess(),&independent,SYNCHRONIZE|PROCESS_QUERY_LIMITED_INFORMATION,FALSE,0))fault=true;
 if(independent)observer=std::thread([&]{ob=Q();observed=WaitForSingleObject(independent,15000);oe=Q();});}
 bool done=false,armed=false;CONTEXT saved{};HANDLE primary=nullptr;ULONGLONG ep=0;LONGLONG marker=0,hard=0;unsigned pauses=0;LONGLONG pauseTicks=0;
 while(!done){
  auto now=Q();double elapsed=double(now-launch)/freq.QuadPart;if(isProbe&&elapsed>=13.6&&!deadline){deadline=true;hard=now;}
  if(elapsed>=(isProbe?30:1200)){if(debug)DebugActiveProcessStop(pi.dwProcessId);break;} // observation only; never converts deadline failure to pass
  if(!debug){DWORD w=WaitForSingleObject(pi.hProcess,1);if(w==WAIT_OBJECT_0)done=true;else if(w!=WAIT_TIMEOUT){fault=true;break;}continue;}
  DEBUG_EVENT ev{};if(!WaitForDebugEvent(&ev,1)){if(GetLastError()!=ERROR_SEM_TIMEOUT){fault=true;error=GetLastError();break;}continue;}
  auto pause=Q();++pauses;DWORD cont=DBG_CONTINUE;
  if(ev.dwProcessId!=pi.dwProcessId){fault=true;cont=DBG_EXCEPTION_NOT_HANDLED;}
  else switch(ev.dwDebugEventCode){
   case CREATE_PROCESS_DEBUG_EVENT:{
    auto& d=ev.u.CreateProcessInfo;primary=d.hThread;record("create_process_debug",ev.dwThreadId,ULONGLONG(d.lpStartAddress),Path(d.hFile));if(d.hFile)CloseHandle(d.hFile);
    IMAGE_DOS_HEADER dos{};IMAGE_NT_HEADERS64 nt{};SIZE_T got=0;
    bool ok=ReadProcessMemory(pi.hProcess,d.lpBaseOfImage,&dos,sizeof(dos),&got)&&got==sizeof(dos)&&dos.e_magic==IMAGE_DOS_SIGNATURE&&dos.e_lfanew>0&&dos.e_lfanew<1048576;
    ok=ok&&ReadProcessMemory(pi.hProcess,static_cast<BYTE*>(d.lpBaseOfImage)+dos.e_lfanew,&nt,sizeof(nt),&got)&&got==sizeof(nt)&&nt.Signature==IMAGE_NT_SIGNATURE&&nt.OptionalHeader.Magic==IMAGE_NT_OPTIONAL_HDR64_MAGIC&&nt.OptionalHeader.AddressOfEntryPoint<nt.OptionalHeader.SizeOfImage;
    saved.ContextFlags=CONTEXT_DEBUG_REGISTERS;ok=ok&&GetThreadContext(primary,&saved);
    if(ok&&saved.Dr7==0){ep=ULONGLONG(d.lpBaseOfImage)+nt.OptionalHeader.AddressOfEntryPoint;CONTEXT c=saved;c.Dr0=ep;c.Dr7=1;armed=SetThreadContext(primary,&c)!=0;record("entry_breakpoint_armed",ev.dwThreadId,ep);if(!armed)fault=true;}else fault=true;
    break;}
   case CREATE_THREAD_DEBUG_EVENT:record("create_thread_debug",ev.dwThreadId,ULONGLONG(ev.u.CreateThread.lpStartAddress));break;
   case LOAD_DLL_DEBUG_EVENT:record("load_dll_debug",ev.dwThreadId,ULONGLONG(ev.u.LoadDll.lpBaseOfDll),Path(ev.u.LoadDll.hFile));if(ev.u.LoadDll.hFile)CloseHandle(ev.u.LoadDll.hFile);break;
   case UNLOAD_DLL_DEBUG_EVENT:record("unload_dll_debug",ev.dwThreadId,ULONGLONG(ev.u.UnloadDll.lpBaseOfDll));break;
   case EXCEPTION_DEBUG_EVENT:{auto& e=ev.u.Exception.ExceptionRecord;
    if(e.ExceptionCode==EXCEPTION_SINGLE_STEP&&armed&&ev.dwThreadId==pi.dwThreadId&&ULONGLONG(e.ExceptionAddress)==ep){marker=Q();entry=true;record("PE_ENTRY_EXECUTED",ev.dwThreadId,ep);if(!SetThreadContext(primary,&saved))fault=true;armed=false;}
    else if(e.ExceptionCode==EXCEPTION_BREAKPOINT){record("loader_debug_breakpoint",ev.dwThreadId,ULONGLONG(e.ExceptionAddress));}
    else{record("unhandled_exception",ev.dwThreadId,e.ExceptionCode);cont=DBG_EXCEPTION_NOT_HANDLED;}
    break;}
   case EXIT_THREAD_DEBUG_EVENT:record("exit_thread_debug",ev.dwThreadId,ev.u.ExitThread.dwExitCode);break;
   case EXIT_PROCESS_DEBUG_EVENT:record("exit_process_debug",ev.dwThreadId,ev.u.ExitProcess.dwExitCode);done=true;break;
   default:record("other_debug_event",ev.dwThreadId,ev.dwDebugEventCode);break;
  }
  if(!ContinueDebugEvent(ev.dwProcessId,ev.dwThreadId,cont)){fault=true;error=GetLastError();break;}pauseTicks+=Q()-pause;
 }
 DWORD finalWait=WaitForSingleObject(pi.hProcess,0),exitCode=STILL_ACTIVE;auto signal=Q();GetExitCodeProcess(pi.hProcess,&exitCode);GetProcessTimes(pi.hProcess,&created,&exited,&kt,&ut);
 if(debug&&!done){DebugActiveProcessStop(pi.dwProcessId);fault=true;}
 if(isProbe&&FT(exited)&&double(FT(exited)-FT(created))/10000000.0>=13.6){deadline=true;if(!hard)hard=signal;}
 if(observer.joinable())observer.join();else WaitForSingleObject(pi.hProcess,1000);finalWait=WaitForSingleObject(pi.hProcess,0);signal=Q();GetExitCodeProcess(pi.hProcess,&exitCode);GetProcessTimes(pi.hProcess,&created,&exited,&kt,&ut);if(isProbe&&FT(exited)&&double(FT(exited)-FT(created))/10000000.0>=13.6)deadline=true;if(independent)CloseHandle(independent);
 std::ostringstream s;s<<"{\"identityPersistedQpc\":"<<identityPersisted<<",\"mode\":"<<J(U(mode))<<",\"pid\":"<<pi.dwProcessId<<",\"tid\":"<<pi.dwThreadId<<",\"frequency\":"<<freq.QuadPart<<",\"launchQpc\":"<<launch<<",\"createBeginQpc\":"<<cb<<",\"createEndQpc\":"<<ce<<",\"handleAcquiredQpc\":"<<acquired<<",\"created\":\""<<FT(created)<<"\",\"exitFiletime\":\""<<FT(exited)<<"\",\"entryQpc\":"<<marker<<",\"entryAddress\":"<<ep<<",\"hardDeadlineQpc\":"<<hard<<",\"deadlineExceeded\":"<<(deadline?"true":"false")<<",\"signalObservedQpc\":"<<signal<<",\"finalWait\":"<<finalWait<<",\"exitCode\":"<<exitCode<<",\"observerBeginQpc\":"<<ob<<",\"observerEndQpc\":"<<oe<<",\"observerResult\":"<<observed<<",\"fault\":"<<(fault?"true":"false")<<",\"error\":"<<error<<",\"debugPauses\":"<<pauses<<",\"debugHandlingTicks\":"<<pauseTicks<<",\"events\":[";
 for(size_t i=0;i<events.size();i++){if(i)s<<",";s<<events[i];}s<<"]}";

 bool wrote=Write(root+L"\\native-"+std::to_wstring(pid)+L"-"+std::to_wstring(FT(created))+L".json",s.str());return !wrote||fault||deadline||finalWait!=0||!entry?97:0;
}
extern "C" __declspec(dllexport) int RunCollector(const wchar_t* path,const wchar_t* caseName){
 std::wstring root=path,mode=caseName;if(!Bounded(root)||(mode!=L"normal"&&mode!=L"hash-start-failure"))return 91;
 auto code=root.substr(0,root.find_last_of(L'\\'));auto run=root.substr(root.find_last_of(L'\\')+1);
 std::wstring exe=L"C:\\Users\\jonny\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe";
 std::wstring cmd=L"\""+exe+L"\" -B \""+code+L"\\traced_collect.py\" "+run+L" "+mode;
 SECURITY_ATTRIBUTES sa{sizeof(sa),0,TRUE};HANDLE handles[3];
 handles[0]=CreateFileW(L"NUL",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,0,0);
 handles[1]=CreateFileW((root+L"\\work.stdout").c_str(),GENERIC_WRITE,FILE_SHARE_READ,&sa,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,0);
 handles[2]=CreateFileW((root+L"\\work.stderr").c_str(),GENERIC_WRITE,FILE_SHARE_READ,&sa,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,0);
 for(auto h:handles)if(h==INVALID_HANDLE_VALUE){for(auto x:handles)if(x!=INVALID_HANDLE_VALUE)CloseHandle(x);return 93;}
 STARTUPINFOEXW si{};si.StartupInfo.cb=sizeof(si);si.StartupInfo.dwFlags=STARTF_USESTDHANDLES;si.StartupInfo.hStdInput=handles[0];si.StartupInfo.hStdOutput=handles[1];si.StartupInfo.hStdError=handles[2];
 SIZE_T size=0;InitializeProcThreadAttributeList(0,1,0,&size);std::vector<BYTE> attrs(size);si.lpAttributeList=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attrs.data());
 if(!InitializeProcThreadAttributeList(si.lpAttributeList,1,0,&size)||!UpdateProcThreadAttribute(si.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,handles,sizeof(handles),0,0))return 94;
 PROCESS_INFORMATION pi{};auto launch=Q();BOOL ok=CreateProcessW(exe.c_str(),cmd.data(),0,0,TRUE,CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT|DEBUG_ONLY_THIS_PROCESS,0,code.c_str(),&si.StartupInfo,&pi);
 auto createEnd=Q();DeleteProcThreadAttributeList(si.lpAttributeList);for(auto h:handles)CloseHandle(h);if(!ok)return 95;
 if(!DebugSetProcessKillOnExit(FALSE))return 96;
 int trace=TraceOwned(pi.hProcess,pi.hThread,pi.dwProcessId,pi.dwThreadId,path,launch,FALSE,launch,createEnd);DWORD status=STILL_ACTIVE;GetExitCodeProcess(pi.hProcess,&status);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return trace?trace:int(status);
}

extern "C" __declspec(dllexport) int RunQualification(const wchar_t* path){
 std::wstring root=path;if(!Bounded(root))return 91;
 auto code=root.substr(0,root.find_last_of(L'\\'));auto run=root.substr(root.find_last_of(L'\\')+1);
 std::wstring exe=L"C:\\Users\\jonny\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe";
 std::wstring cmd=L"\""+exe+L"\" -B \""+code+L"\\qualified_worker.py\" "+run;
 SECURITY_ATTRIBUTES sa{sizeof(sa),0,TRUE};HANDLE handles[3];
 handles[0]=CreateFileW(L"NUL",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,0,0);
 handles[1]=CreateFileW((root+L"\\worker.stdout").c_str(),GENERIC_WRITE,FILE_SHARE_READ,&sa,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,0);
 handles[2]=CreateFileW((root+L"\\worker.stderr").c_str(),GENERIC_WRITE,FILE_SHARE_READ,&sa,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,0);
 for(auto h:handles)if(h==INVALID_HANDLE_VALUE){for(auto x:handles)if(x!=INVALID_HANDLE_VALUE)CloseHandle(x);return 93;}
 STARTUPINFOEXW si{};si.StartupInfo.cb=sizeof(si);si.StartupInfo.dwFlags=STARTF_USESTDHANDLES|STARTF_USESHOWWINDOW;si.StartupInfo.wShowWindow=SW_HIDE;si.StartupInfo.hStdInput=handles[0];si.StartupInfo.hStdOutput=handles[1];si.StartupInfo.hStdError=handles[2];
 SIZE_T size=0;InitializeProcThreadAttributeList(0,1,0,&size);std::vector<BYTE> attrs(size);si.lpAttributeList=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attrs.data());
 if(!InitializeProcThreadAttributeList(si.lpAttributeList,1,0,&size)||!UpdateProcThreadAttribute(si.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,handles,sizeof(handles),0,0))return 94;
 PROCESS_INFORMATION pi{};auto launch=Q();BOOL ok=CreateProcessW(exe.c_str(),cmd.data(),0,0,TRUE,CREATE_NEW_CONSOLE|EXTENDED_STARTUPINFO_PRESENT|DEBUG_ONLY_THIS_PROCESS,0,code.c_str(),&si.StartupInfo,&pi);
 auto createEnd=Q();DeleteProcThreadAttributeList(si.lpAttributeList);for(auto h:handles)CloseHandle(h);if(!ok)return 95;
 int captureError=DebugSetProcessKillOnExit(FALSE)?0:96;FILETIME a{},b{},c{},d{};wchar_t image[32768];DWORD count=32768;
 if(!GetProcessTimes(pi.hProcess,&a,&b,&c,&d)||!QueryFullProcessImageNameW(pi.hProcess,0,image,&count))captureError=98;
 std::ostringstream ident;ident<<"{\"pid\":"<<pi.dwProcessId<<",\"created\":\""<<FT(a)<<"\",\"image\":"<<J(U(std::wstring(image,count)))<<",\"createBeginQpc\":"<<launch<<",\"createEndQpc\":"<<createEnd<<"}";
 if(captureError==0&&!Write(root+L"\\worker-created.json",ident.str()))captureError=99;
 
 int trace=TraceOwned(pi.hProcess,pi.hThread,pi.dwProcessId,pi.dwThreadId,path,launch,FALSE,launch,createEnd);DWORD status=STILL_ACTIVE;GetExitCodeProcess(pi.hProcess,&status);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return captureError?captureError:(trace?trace:int(status));
}
