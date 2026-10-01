// Bounded, real-time ETW diagnostic consumer. No driver, ETL, command-line capture,
// security changes, termination, or unrelated process evidence output.
#define WIN32_LEAN_AND_MEAN
#include "trace_telemetry.hpp"
#define NOMINMAX
#include "durable_sink.hpp"
#include <windows.h>
#include <evntrace.h>
#include <evntcons.h>
#include <tdh.h>
#include <objbase.h>
#include <climits>
#include <string>
#include <vector>
#include <map>
#include <mutex>
#include <thread>
#include <sstream>
#include <fstream>
#include <atomic>
#include <algorithm>

static const GUID Provider={0x22fb2cd6,0x0e7b,0x422b,{0xa0,0xc7,0x2f,0xad,0x1f,0xd0,0xe7,0x16}};
static std::wstring folder,session;static DWORD rootPid;static ULONGLONG rootCreated;
static std::mutex guard;static std::atomic<unsigned> faults{0};static unsigned discarded=0;
static LONGLONG Q(){LARGE_INTEGER x;QueryPerformanceCounter(&x);return x.QuadPart;}
static ULONGLONG FT(FILETIME x){return (static_cast<ULONGLONG>(x.dwHighDateTime)<<32)|x.dwLowDateTime;}
static std::string U(const std::wstring& w){if(w.empty())return "";int n=WideCharToMultiByte(CP_UTF8,0,w.data(),static_cast<int>(w.size()),nullptr,0,nullptr,nullptr);std::string s(n,0);WideCharToMultiByte(CP_UTF8,0,w.data(),static_cast<int>(w.size()),s.data(),n,nullptr,nullptr);return s;}
static std::string J(const std::string& s){std::string o="\"";for(unsigned char c:s){if(c=='"'||c=='\\'){o+='\\';o+=c;}else if(c<32){o+='?';}else o+=c;}return o+'"';}
static bool Write(const wchar_t* name,const std::string& s){std::wstring p=folder+L"\\"+name;HANDLE f=CreateFileW(p.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);if(f==INVALID_HANDLE_VALUE)return false;DWORD n=0;BOOL ok=WriteFile(f,s.data(),static_cast<DWORD>(s.size()),&n,nullptr);BOOL flush=FlushFileBuffers(f);CloseHandle(f);return ok&&flush&&n==s.size();}
static bool Field(EVENT_RECORD* e,const wchar_t* name,std::vector<BYTE>& v){j6t::Scope timing(j6t::Metadata);PROPERTY_DATA_DESCRIPTOR p{};p.PropertyName=reinterpret_cast<ULONGLONG>(name);p.ArrayIndex=ULONG_MAX;ULONG n=0;ULONG r=TdhGetPropertySize(e,0,nullptr,1,&p,&n);if(r||n>65536)return false;v.resize(n);return TdhGetProperty(e,0,nullptr,1,&p,n,v.data())==0;}
static ULONGLONG Number(EVENT_RECORD* e,const wchar_t* name,bool* found=nullptr){std::vector<BYTE> v;bool ok=Field(e,name,v)&&(v.size()==4||v.size()==8);if(found)*found=ok;if(!ok)return 0;ULONGLONG n=0;memcpy(&n,v.data(),v.size());return n;}
static std::wstring Text(EVENT_RECORD* e,const wchar_t* name){std::vector<BYTE> v;if(!Field(e,name,v)||v.size()<2)return L"";const wchar_t* w=reinterpret_cast<const wchar_t*>(v.data());size_t n=v.size()/2;size_t end=0;while(end<n&&w[end])++end;return std::wstring(w,end);}
static std::vector<std::string> Schemas(EVENT_RECORD* e){j6t::Scope timing(j6t::Metadata);ULONG n=0;std::vector<std::string> names;if(TdhGetEventInformation(e,0,nullptr,nullptr,&n)!=ERROR_INSUFFICIENT_BUFFER||n>262144)return names;std::vector<BYTE> v(n);auto p=reinterpret_cast<TRACE_EVENT_INFO*>(v.data());if(TdhGetEventInformation(e,0,nullptr,p,&n))return names;for(ULONG i=0;i<p->TopLevelPropertyCount;i++){ULONG off=p->EventPropertyInfoArray[i].NameOffset;if(off<n)names.push_back(U(reinterpret_cast<wchar_t*>(v.data()+off)));}return names;}
struct Row{DWORD pid=0,parent=0;ULONGLONG created=0,sequence=0,parentSequence=0,exitFT=0;DWORD exitCode=0;bool exitCodeKnown=false;std::wstring image,handleImage;ULONGLONG handleCreated=0;DWORD imageError=0;LONGLONG imageBegin=0,imageEnd=0;LONGLONG start=0,notified=0,stop=0,stopNotified=0,retained=0,attemptBegin=0,signal=0;HANDLE handle=nullptr;DWORD openError=0,metadataError=0;std::string reason;bool closed=false;unsigned version=0,stopVersion=0;std::vector<std::string> schema,stopSchema;};
static std::map<std::pair<DWORD,ULONGLONG>,Row> rows;
static bool ParentKnown(DWORD pid,ULONGLONG childTime,ULONGLONG parentSequence){if(pid==rootPid)return childTime>=rootCreated;for(auto& a:rows){auto&r=a.second;if(r.pid==pid&&r.created<=childTime&&(!r.exitFT||childTime<=r.exitFT)&&(!parentSequence||r.sequence==parentSequence))return true;}return false;}
static void Acquire(Row& r){r.attemptBegin=Q();r.handle=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,FALSE,r.pid);DWORD openError=r.handle?0:GetLastError();r.retained=Q();if(!r.handle){r.openError=openError;r.reason="OPEN_PROCESS_FAILED";return;}FILETIME a,b,c,d;if(!GetProcessTimes(r.handle,&a,&b,&c,&d)){r.metadataError=GetLastError();r.reason="KERNEL_IDENTITY_QUERY_FAILED";return;}if(FT(a)!=r.created){r.reason="PID_REUSED_KERNEL_CREATION_MISMATCH";CloseHandle(r.handle);r.handle=nullptr;return;}r.handleCreated=FT(a);r.imageBegin=Q();wchar_t image[32768];DWORD count=32768;if(QueryFullProcessImageNameW(r.handle,0,image,&count))r.handleImage.assign(image,count);else r.imageError=GetLastError();r.imageEnd=Q();r.reason="RETAINED_MATCHING_KERNEL_CREATION";}

static std::unique_ptr<DurableSink> lifecycleSink;
static unsigned long long lifecycleCaptured=0;
static void Capture(const Row&r,bool start){
 std::ostringstream o;o<<"{\"source\":\"Microsoft-Windows-Kernel-Process\",\"scope\":"<<J(U(session))<<",\"kind\":"<<J(start?"start":"stop")<<",\"pid\":"<<r.pid<<",\"created\":\""<<r.created<<"\",\"sequence\":\""<<r.sequence<<"\",\"parentPid\":"<<r.parent<<",\"parentSequence\":\""<<r.parentSequence<<"\",\"image\":"<<J(U(r.image))<<",\"eventQpc\":"<<(start?r.start:r.stop)<<",\"callbackQpc\":"<<(start?r.notified:r.stopNotified)<<",\"exitFiletime\":\""<<(start?0:r.exitFT)<<"\",\"exitCode\":"<<r.exitCode<<",\"version\":"<<(start?r.version:r.stopVersion)<<"}";
 if(!j6t::measure(j6t::Admission,[&]{return lifecycleSink->add(o.str());}))++faults;else ++lifecycleCaptured;
}

static void WINAPI Event(EVENT_RECORD* e){j6t::CallbackScope timing;try{
 if(!IsEqualGUID(e->EventHeader.ProviderId,Provider))return;unsigned id=e->EventHeader.EventDescriptor.Id;if(id!=1&&id!=2)return;
 bool hasPid=false,hasTime=false;DWORD pid=static_cast<DWORD>(Number(e,L"ProcessID",&hasPid));ULONGLONG created=Number(e,L"CreateTime",&hasTime);
 j6t::Lock l(guard);
 if(id==1){DWORD parent=static_cast<DWORD>(Number(e,L"ParentProcessID"));if(!ParentKnown(parent,created,Number(e,L"ParentProcessSequenceNumber"))){++discarded;return;}
  if(!hasPid||!hasTime||!created||rows.size()>=8192){++faults;return;}auto key=std::make_pair(pid,created);if(rows.count(key)){++faults;return;}
  Row r;r.pid=pid;r.parent=parent;r.created=created;r.start=e->EventHeader.TimeStamp.QuadPart;r.notified=Q();r.version=e->EventHeader.EventDescriptor.Version;r.image=Text(e,L"ImageName");r.sequence=Number(e,L"ProcessSequenceNumber");r.parentSequence=Number(e,L"ParentProcessSequenceNumber");r.schema=Schemas(e);timing.selected=true;Capture(r,true);Acquire(r);rows.emplace(key,std::move(r));
 }else{auto it=rows.find(std::make_pair(pid,created));if(it==rows.end()){++discarded;return;}auto&r=it->second;if(r.stop){++faults;return;}if(r.sequence!=Number(e,L"ProcessSequenceNumber"))++faults;r.stop=e->EventHeader.TimeStamp.QuadPart;r.stopNotified=Q();r.stopVersion=e->EventHeader.EventDescriptor.Version;auto exitTime=Number(e,L"ExitTime");bool known=false;auto code=static_cast<DWORD>(Number(e,L"ExitCode",&known));if(r.exitFT&&exitTime!=r.exitFT)++faults;if(r.exitCodeKnown&&(!known||r.exitCode!=code))++faults;r.exitFT=exitTime;r.exitCode=code;r.exitCodeKnown=known;r.stopSchema=Schemas(e);timing.selected=true;Capture(r,false);}
 }catch(...){++faults;}}
static void Sample(){j6t::Lock l(guard);for(auto& a:rows){auto&r=a.second;if(r.handle&&!r.signal){DWORD s=WaitForSingleObject(r.handle,0);if(s==WAIT_OBJECT_0){r.signal=Q();FILETIME a,b,c,d;DWORD exit=0;if(GetProcessTimes(r.handle,&a,&b,&c,&d)&&GetExitCodeProcess(r.handle,&exit)){if(FT(a)!=r.created)++faults;if(r.exitFT&&r.exitFT!=FT(b))++faults;if(r.exitCodeKnown&&r.exitCode!=exit)++faults;r.exitFT=FT(b);r.exitCode=exit;r.exitCodeKnown=true;}else{r.metadataError=GetLastError();++faults;}}else if(s!=WAIT_TIMEOUT){++faults;}}}}
static std::string List(const std::vector<std::string>& names){std::string s="[";bool first=true;for(auto&n:names){if(!first)s+=",";first=false;s+=J(n);}return s+"]";}
int wmain(int argc,wchar_t**argv){
 if(argc!=4)return 90;folder=argv[1];rootPid=wcstoul(argv[2],nullptr,10);rootCreated=_wcstoui64(argv[3],nullptr,10);
 if(folder.rfind(L"D:\\JARVIS-STAGE6-LIVE\\",0)!=0||folder.find(L"..")!=std::wstring::npos)return 91;
 HANDLE root=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,FALSE,rootPid);FILETIME ra,rb,rc,rd;
 if(!root||!GetProcessTimes(root,&ra,&rb,&rc,&rd)||FT(ra)!=rootCreated){if(root)CloseHandle(root);return 92;}
 GUID guid;CoCreateGuid(&guid);wchar_t guidText[64];StringFromGUID2(guid,guidText,64);session=L"J6Kernel-"+std::wstring(guidText);
 lifecycleSink=std::make_unique<DurableSink>(folder,"kernel-authority",8192);
 std::vector<BYTE> buffer(sizeof(EVENT_TRACE_PROPERTIES)+1024);auto p=reinterpret_cast<EVENT_TRACE_PROPERTIES*>(buffer.data());p->Wnode.BufferSize=static_cast<ULONG>(buffer.size());p->Wnode.Flags=WNODE_FLAG_TRACED_GUID;p->Wnode.ClientContext=1;p->Wnode.Guid=guid;p->BufferSize=64;p->MinimumBuffers=4;p->MaximumBuffers=64;p->FlushTimer=1;p->LogFileMode=EVENT_TRACE_REAL_TIME_MODE;p->LoggerNameOffset=sizeof(EVENT_TRACE_PROPERTIES);
 TRACEHANDLE sessionHandle=0;ULONG start=j6t::telemetry.call("StartTrace",[&]{return StartTraceW(&sessionHandle,session.c_str(),p);});if(start){Write(L"etw-failure.json","{\"stage\":\"StartTrace\",\"code\":"+std::to_string(start)+"}");CloseHandle(root);return 93;}
 EVENT_TRACE_LOGFILEW log{};log.LoggerName=const_cast<wchar_t*>(session.c_str());log.ProcessTraceMode=PROCESS_TRACE_MODE_REAL_TIME|PROCESS_TRACE_MODE_EVENT_RECORD|PROCESS_TRACE_MODE_RAW_TIMESTAMP;log.EventRecordCallback=Event;
 j6t::telemetry.query(sessionHandle,session.c_str(),"afterStartTrace");auto openBegin=j6t::now();TRACEHANDLE consumer=OpenTraceW(&log);ULONG openError=consumer==INVALID_PROCESSTRACE_HANDLE?GetLastError():0;j6t::telemetry.phase("OpenTrace",openBegin,j6t::now(),openError);ULONG enable=openError?openError:j6t::telemetry.call("EnableProviderProcess",[&]{return EnableTraceEx2(sessionHandle,&Provider,EVENT_CONTROL_CODE_ENABLE_PROVIDER,TRACE_LEVEL_INFORMATION,0x10,0,0,nullptr);});
 if(enable){ControlTraceW(sessionHandle,session.c_str(),p,EVENT_TRACE_CONTROL_STOP);if(!openError)CloseTrace(consumer);Write(L"etw-failure.json","{\"stage\":\"OpenTrace/Enable\",\"code\":"+std::to_string(enable)+"}");CloseHandle(root);return 94;}
 j6t::telemetry.query(sessionHandle,session.c_str(),"afterEnable");std::atomic<ULONG> consumed{ULONG_MAX};std::thread thread([&]{auto b=j6t::now();j6t::telemetry.phase("ProcessTraceEntry",b,b);consumed=ProcessTrace(&consumer,1,nullptr,nullptr);j6t::telemetry.phase("ProcessTraceReturn",b,j6t::now(),consumed);});
 LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);bool ready=Write(L"etw-ready.json","{\"pid\":"+std::to_string(GetCurrentProcessId())+",\"rootPid\":"+std::to_string(rootPid)+",\"rootCreated\":\""+std::to_string(rootCreated)+"\",\"session\":"+J(U(session))+",\"frequency\":"+std::to_string(freq.QuadPart)+",\"qpc\":"+std::to_string(Q())+"}");
 j6t::telemetry.phase("ReadyPublished",Q(),Q(),ready?0:1);j6t::telemetry.query(sessionHandle,session.c_str(),"ready");LONGLONG begin=Q();bool requested=false;while(ready&&(Q()-begin)/static_cast<double>(freq.QuadPart)<180){j6t::telemetry.poll(sessionHandle,session.c_str(),freq.QuadPart);Sample();if(GetFileAttributesW((folder+L"\\etw-stop").c_str())!=INVALID_FILE_ATTRIBUTES){requested=true;break;}if(consumed!=ULONG_MAX)break;Sleep(10);}
 j6t::telemetry.phase("StopRequestedOrLoopEnded",Q(),Q(),requested?0:1);j6t::telemetry.query(sessionHandle,session.c_str(),"beforeFlush");ULONG flush=j6t::telemetry.call("FlushTrace",[&]{return ControlTraceW(sessionHandle,session.c_str(),p,EVENT_TRACE_CONTROL_FLUSH);});Sleep(1100);Sample();j6t::telemetry.query(sessionHandle,session.c_str(),"beforeStop");ULONG stop=j6t::telemetry.call("StopTrace",[&]{return ControlTraceW(sessionHandle,session.c_str(),p,EVENT_TRACE_CONTROL_STOP);});thread.join();CloseTrace(consumer);Sample();CloseHandle(root);
 lifecycleSink->finish();if(lifecycleSink->fault())++faults;
 std::ostringstream out;out<<"{\"requestedStop\":"<<(requested?"true":"false")<<",\"session\":"<<J(U(session))<<",\"flushResult\":"<<flush<<",\"stopResult\":"<<stop<<",\"consumerResult\":"<<consumed<<",\"eventsLost\":"<<p->EventsLost<<",\"realtimeBuffersLost\":"<<p->RealTimeBuffersLost<<",\"buffersLost\":"<<p->LogBuffersLost<<",\"faults\":"<<faults<<",\"discardedUnrelated\":"<<discarded<<",\"rows\":[";bool first=true;
 for(auto&a:rows){auto&r=a.second;if(!first)out<<",";first=false;bool closed=true;if(r.handle){closed=CloseHandle(r.handle)!=0;r.closed=closed;}out<<"{\"pid\":"<<r.pid<<",\"parentPid\":"<<r.parent<<",\"created\":\""<<r.created<<"\",\"sequence\":\""<<r.sequence<<"\",\"parentSequence\":\""<<r.parentSequence<<"\",\"image\":"<<J(U(r.image))<<",\"handleImage\":"<<J(U(r.handleImage))<<",\"handleCreated\":\""<<r.handleCreated<<"\",\"imageError\":"<<r.imageError<<",\"imageBeginQpc\":"<<r.imageBegin<<",\"imageEndQpc\":"<<r.imageEnd<<",\"startQpc\":"<<r.start<<",\"startCallbackQpc\":"<<r.notified<<",\"handleAttemptBeginQpc\":"<<r.attemptBegin<<",\"handleAttemptQpc\":"<<r.retained<<",\"handleRetained\":"<<(r.handle?"true":"false")<<",\"handleIdentity\":\""<<reinterpret_cast<ULONG_PTR>(r.handle)<<"\",\"reason\":"<<J(r.reason)<<",\"openError\":"<<r.openError<<",\"metadataError\":"<<r.metadataError<<",\"stopQpc\":"<<r.stop<<",\"stopCallbackQpc\":"<<r.stopNotified<<",\"signalObservedQpc\":"<<r.signal<<",\"exitFiletime\":\""<<r.exitFT<<"\",\"exitCode\":"<<r.exitCode<<",\"exitCodeKnown\":"<<(r.exitCodeKnown?"true":"false")<<",\"handleClosed\":"<<(closed?"true":"false")<<",\"startVersion\":"<<r.version<<",\"stopVersion\":"<<r.stopVersion<<",\"startSchema\":"<<List(r.schema)<<",\"stopSchema\":"<<List(r.stopSchema)<<"}";}
 out<<"]}";if(!Write(L"loss-telemetry.json",j6t::telemetry.json())||j6t::telemetry.errors.load())++faults;bool wrote=Write(L"etw-result.json",out.str());return !wrote||!requested||stop||faults||p->EventsLost||p->RealTimeBuffersLost?95:0;
}
