// OFFLINE constructed identities/API seams. Never starts tracing or a collector.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <map>
static std::map<ULONG_PTR,std::pair<DWORD,ULONGLONG>> fake;
static DWORD FixturePid(HANDLE h){auto i=fake.find((ULONG_PTR)h);return i==fake.end()?GetProcessId(h):i->second.first;}
static BOOL FixtureTimes(HANDLE h,LPFILETIME a,LPFILETIME b,LPFILETIME c,LPFILETIME d){auto i=fake.find((ULONG_PTR)h);if(i==fake.end())return GetProcessTimes(h,a,b,c,d);a->dwLowDateTime=DWORD(i->second.second);a->dwHighDateTime=DWORD(i->second.second>>32);*b=*c=*d={};return TRUE;}
static DWORD FixtureWait(HANDLE h,DWORD t){return fake.count((ULONG_PTR)h)?WAIT_TIMEOUT:WaitForSingleObject(h,t);}
#define GetProcessId FixturePid
#define GetProcessTimes FixtureTimes
#define WaitForSingleObject FixtureWait
#define wmain UNUSED_AUTHORITY_ENTRY
#include "authority_trace_v3.cpp"
#undef wmain
#undef GetProcessId
#undef GetProcessTimes
#undef WaitForSingleObject
#include <iostream>
int wmain(int argc,wchar_t**argv){
 if(argc!=3)return 81;folder=argv[1];std::string mode=U(argv[2]);session=L"OFFLINE-HANDOFF";
 try{
 auto o=terminal_v3::Parser(terminal_v3::Read(folder+L"\\input.json")).parse();auto&b=o.obj["binding"];
 auto json=[](std::string s){return terminal_v3::Parser(s).parse();};auto num=[&](ULONGLONG x){return json(std::to_string(x));};auto str=[&](std::string s){return json(J(s));};
 auto now=Q();LARGE_INTEGER f;QueryPerformanceFrequency(&f);auto start=now-1000,end=start+20*f.QuadPart;
 if(mode=="deadline")end=start;
 o.obj["cleanupEntryQpc"]=num(start);o.obj["deadlineQpc"]=num(end);o.obj["preparedQpc"]=num(now);
 b.obj["frequency"]=num(f.QuadPart);b.obj["kernelSession"]=str(U(session));
 auto origin="{\"cleanupEntryQpc\":"+std::to_string(start)+",\"deadlineQpc\":"+std::to_string(end)+",\"frequency\":"+std::to_string(f.QuadPart)+"}";Write(L"cleanup-origin-v3.json",origin);b.obj["cleanupOriginSHA256"]=str(terminal_v3::Sha(origin));
 FILETIME a,bb,c,d;GetProcessTimes(GetCurrentProcess(),&a,&bb,&c,&d);wchar_t image[32768];DWORD n=32768;QueryFullProcessImageNameW(GetCurrentProcess(),0,image,&n);
 auto obs="{\"pid\":"+std::to_string(GetCurrentProcessId())+",\"created\":"+J(std::to_string(FT(a)))+",\"image\":"+J(U(std::wstring(image,n)))+"}";
 auto obsRaw="{\"etw\":"+obs+"}";Write(L"observer-identities.json",obsRaw);o.obj["authorityObserver"]=json(obs);b.obj["observerSHA256"]=str(terminal_v3::Sha(obsRaw));
 Row parent;parent.pid=101;parent.created=1000;parent.sequence=400;parent.handle=(HANDLE)123;parent.handlePid=101;parent.handleCreated=1000;parent.handleImage=L"D:\\python.exe";parent.start=now-100;parent.retained=now-90;parent.creationVerified=now-85;parent.imageBegin=now-80;parent.imageEnd=now-70;
 rows[{101,1000}]=parent;fake[123]={101,1000};
 Row helper=parent;helper.pid=102;helper.created=1001;helper.sequence=401;helper.parent=101;helper.parentSequence=400;helper.handle=(HANDLE)124;helper.handlePid=102;helper.handleCreated=1001;helper.image=helper.handleImage=L"C:\\Windows\\System32\\conhost.exe";helper.attemptBegin=now-95;
 fake[124]={102,1001};helper.imageStateBefore=helper.imageStateAfter=WAIT_TIMEOUT;
 if(mode=="no-handle")helper.handle=nullptr;
 if(mode=="creation")helper.handleCreated=999;
 if(mode=="image")helper.handleImage=L"D:\\wrong.exe";
 if(mode=="kernel-image")helper.image=L"D:\\wrong.exe";
 if(mode=="parent")helper.parentSequence=399;
 if(mode=="pid-reuse")fake[124]={102,999};
 if(mode=="post-exit-acquire")helper.stop=helper.attemptBegin-1;
 if(mode=="exit-after-acquire")helper.stop=now-60;
 if(mode=="sequence")helper.sequence=0;
 if(mode=="image-error")helper.imageError=5;
 if(mode=="already-signaled")helper.imageStateBefore=WAIT_OBJECT_0;
 if(mode=="exit-during-image")helper.imageStateAfter=WAIT_OBJECT_0;
 if(mode=="fault")faults=1;
 if(mode!="missing-row")rows[{102,1001}]=helper;
 auto&h=o.obj["helpers"].arr[0];h.obj["localRetainedQpc"]=num(now-120);h.obj["localVerifiedQpc"]=num(now-110);
 if(mode=="expected-sequence")h.obj["expectedSequence"]=str("999");
 if(mode=="duplicate")o.obj["helpers"].arr.push_back(h);
 if(mode=="wrong-run")b.obj["run"]=str("old-run");
 if(mode=="wrong-observer")o.obj["authorityObserver"].obj["created"]=str("2");
 if(mode=="wrong-workspace")b.obj["workspaceBindingSHA256"]=str(std::string(64,'0'));
 o.obj["obligationSetId"]=str(terminal_v3::Sha(o.at("helpers").dump()));
 Write(L"helper-handoff-obligations-v1.json",o.dump());
 bool passed=handoff_v1::HandoffReceipt();
 if(mode=="missing-row"){if(passed)return 88;rows[{102,1001}]=helper;passed=handoff_v1::HandoffReceipt();}
 if(mode=="duplicate-publish"){if(!passed)return 89;handoff_v1::HandoffReceipt();return 90;}
 bool expected=mode=="normal"||mode=="missing-row"||mode=="exit-after-acquire";
 if(passed!=expected)return 91;
 std::cout<<"PASS "<<mode<<"\n";return 0;
 }catch(const std::exception&e){bool expected=mode!="normal"&&mode!="missing-row"&&mode!="exit-after-acquire";std::cout<<(expected?"PASS rejected ":"FAIL ")<<mode<<" "<<e.what()<<"\n";return expected?0:92;}
}
