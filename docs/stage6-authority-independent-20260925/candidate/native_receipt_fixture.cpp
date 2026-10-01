// OFFLINE FIXTURE ONLY. Uses constructed row evidence, never starts ETW/observers.
#include <iostream>
#define wmain UNUSED_TRACER_ENTRYPOINT
#include "authority_trace_v3.cpp"
#undef wmain
int wmain(int argc,wchar_t**argv){
 if(argc!=2)return 80;
 try{
  folder=argv[1];if(folder.rfind(L"D:\\JARVIS-STAGE6-LIVE\\7f204e14c90a497a8476be0e9927e074\\code\\offline-native-",0)!=0)return 81;
  session=L"OFFLINE-CONSTRUCTED-EVIDENCE";LARGE_INTEGER f;QueryPerformanceFrequency(&f);auto now=Q();
  FILETIME a,b,c,d;GetProcessTimes(GetCurrentProcess(),&a,&b,&c,&d);
  std::string run=U(folder.substr(folder.find_last_of(L'\\')+1));std::string hash(64,'a');
  std::string declaration="{\"heartbeat\":10.0,\"probe\":13.6,\"run\":"+J(run)+",\"sourceManifestSHA256\":"+J(hash)+"}";
  if(!Write(L"small-declaration-v3.json",declaration)||!Write(L"observer-identities.json","{}"))return 82;
  std::string binding="{\"schema\":\"stage6-terminal-v3\",\"run\":"+J(run)+",\"declarationSHA256\":"+J(terminal_v3::Sha(declaration))+",\"sourceManifestSHA256\":"+J(hash)+",\"kernelSession\":"+J(U(session))+",\"observerSHA256\":"+J(terminal_v3::Sha("{}"))+",\"frequency\":"+std::to_string(f.QuadPart)+"}";
  Row collector;collector.pid=101;collector.created=1000;collector.sequence=400;collector.parent=50;collector.parentSequence=399;collector.handle=reinterpret_cast<HANDLE>(1);collector.handleCreated=1000;collector.handleImage=L"D:\\python.exe";collector.start=now-100;collector.retained=now-90;collector.imageBegin=now-85;collector.imageEnd=now-80;collector.stop=now-20;collector.stopNotified=now-19;collector.signal=now-18;collector.exitFT=2000;collector.exitCode=0;collector.exitCodeKnown=true;
  Row helper=collector;helper.pid=102;helper.created=1001;helper.handleCreated=1001;helper.sequence=401;helper.parent=101;helper.parentSequence=400;helper.handleImage=L"C:\\Windows\\System32\\conhost.exe";helper.stop=now-10;helper.stopNotified=now-9;helper.signal=now-8;
  rows.emplace(std::make_pair(collector.pid,collector.created),collector);rows.emplace(std::make_pair(helper.pid,helper.created),helper);
  std::string ci="{\"pid\":101,\"created\":\"1000\",\"image\":\"D:\\\\python.exe\"}";
  std::string helperJson="{\"pid\":102,\"created\":\"1001\",\"image\":\"C:\\\\Windows\\\\System32\\\\conhost.exe\",\"role\":\"OS_CONSOLE_HELPER\",\"parent\":"+ci+",\"localClosed\":true,\"localCloseQpc\":"+std::to_string(now-50)+"}";
  std::string phase="{\"binding\":"+binding+",\"cleanupEntryQpc\":"+std::to_string(now-60)+",\"deadlineQpc\":"+std::to_string(now-60+20*f.QuadPart)+",\"authorityObserver\":{\"pid\":"+std::to_string(GetCurrentProcessId())+",\"created\":"+J(std::to_string(FT(a)))+"},\"state\":\"LOCAL_EVIDENCE_FINALIZED_PENDING_EXTERNAL_EXIT\",\"localDurable\":true,\"localHandlesClosed\":true,\"trackerStopped\":true,\"admissionsStopped\":true,\"collector\":"+ci+",\"helpers\":["+helperJson+"]}";
  if(!Write(L"phase-a-v3.json",phase))return 83;
  unsigned checks=0;
  auto bad=[&](const std::string&s){try{terminal_v3::Parser(s).parse();throw std::runtime_error("invalid JSON accepted");}catch(const std::exception&e){if(std::string(e.what())=="invalid JSON accepted")throw;checks++;}};
  bad("{");bad("{\"a\":1,\"a\":2}");bad("{\"a\":01}");bad("true trailing");
  auto key=std::make_pair(helper.pid,helper.created);rows[key].stop=0;
  if(terminal_v3::WorkloadReceipt())return 84;checks++;rows[key]=helper;
  rows[key].handleCreated=9999;bool rejected=false;try{terminal_v3::WorkloadReceipt();}catch(...){rejected=true;}if(!rejected)return 85;checks++;rows[key]=helper;
  rows[key].parentSequence=9999;rejected=false;try{terminal_v3::WorkloadReceipt();}catch(...){rejected=true;}if(!rejected)return 86;checks++;rows[key]=helper;
  if(!terminal_v3::WorkloadReceipt())return 87;checks++;
  auto receipt=terminal_v3::Read(folder+L"\\terminal-v3.json");auto parsed=terminal_v3::Parser(receipt).parse();if(parsed.at("rows").arr.size()!=2)return 88;checks++;
  rejected=false;try{terminal_v3::WorkloadReceipt();}catch(...){rejected=true;}if(!rejected||terminal_v3::Read(folder+L"\\terminal-v3.json")!=receipt)return 89;checks++;
  std::cout<<"OFFLINE_NATIVE_RECEIPT_CHECKS "<<checks<<" PASS; constructed rows, no ETW or live qualification\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 90;}
}
