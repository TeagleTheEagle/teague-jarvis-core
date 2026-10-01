#pragma once
// Bounded TEST evidence parsing/publication only. No command dispatch or process control.
#include <stdexcept>
#include <cctype>
#include <set>
namespace terminal_v3 {
struct Json {
 char type='n';std::string text;std::map<std::string,Json> obj;std::vector<Json> arr;
 const Json& at(const std::string& k)const{auto i=obj.find(k);if(type!='o'||i==obj.end())throw std::runtime_error("missing JSON field");return i->second;}
 unsigned long long number()const{if(type!='i'||text.empty()||text[0]=='-')throw std::runtime_error("integer required");size_t end;auto n=std::stoull(text,&end);if(end!=text.size())throw std::runtime_error("integer suffix");return n;}
 std::string str()const{if(type!='s')throw std::runtime_error("string required");return text;}
 bool yes()const{return type=='b'&&text=="true";}
 std::string dump()const{if(type=='s')return J(text);if(type=='i'||type=='d'||type=='b'||type=='n')return text;std::string s=type=='o'?"{":"[";bool first=true;if(type=='o'){for(auto&x:obj){if(!first)s+=",";first=false;s+=J(x.first)+":"+x.second.dump();}}else{for(auto&x:arr){if(!first)s+=",";first=false;s+=x.dump();}}return s+(type=='o'?"}":"]");}
};
class Parser{
 const std::string&s;size_t p=0,nodes=0;
 void ws(){while(p<s.size()&&(s[p]==' '||s[p]=='\r'||s[p]=='\n'||s[p]=='\t'))p++;}
 char take(){if(p>=s.size())throw std::runtime_error("partial JSON");return s[p++];}
 std::string string(){if(take()!='"')throw std::runtime_error("JSON string");std::string out;for(;;){char c=take();if(c=='"')return out;if(static_cast<unsigned char>(c)<32)throw std::runtime_error("JSON control");if(c=='\\'){c=take();if(c=='"'||c=='\\'||c=='/')out+=c;else if(c=='n')out+='\n';else if(c=='r')out+='\r';else if(c=='t')out+='\t';else if(c=='u'){unsigned v=0;for(int i=0;i<4;i++){char h=take();v=v*16+(h>='0'&&h<='9'?h-'0':h>='a'&&h<='f'?h-'a'+10:h>='A'&&h<='F'?h-'A'+10:throw std::runtime_error("JSON escape"));}if(v>127)throw std::runtime_error("non-ASCII contract field");out+=char(v);}else throw std::runtime_error("JSON escape");}else out+=c;if(out.size()>32768)throw std::runtime_error("string bound");}}
 Json value(unsigned depth){if(depth>24||++nodes>100000)throw std::runtime_error("JSON bound");ws();if(p==s.size())throw std::runtime_error("partial JSON");Json v;char c=s[p];if(c=='"'){v.type='s';v.text=string();return v;}if(c=='{'||c=='['){p++;v.type=c=='{'?'o':'a';ws();if(p<s.size()&&s[p]==(c=='{'?'}':']')){p++;return v;}for(;;){ws();if(c=='{'){auto key=string();ws();if(take()!=':')throw std::runtime_error("colon");if(v.obj.count(key))throw std::runtime_error("duplicate JSON key");v.obj.emplace(key,value(depth+1));}else v.arr.push_back(value(depth+1));ws();char sep=take();if(sep==(c=='{'?'}':']'))return v;if(sep!=',')throw std::runtime_error("separator");}}if(c=='t'||c=='f'||c=='n'){std::string w=c=='t'?"true":c=='f'?"false":"null";if(s.compare(p,w.size(),w))throw std::runtime_error("literal");p+=w.size();v.type=c=='n'?'n':'b';v.text=w;return v;}v.type='i';if(c=='-')v.text+=take();size_t begin=p;while(p<s.size()&&std::isdigit(static_cast<unsigned char>(s[p])))v.text+=take();if(p==begin||(p-begin>1&&s[begin]=='0'))throw std::runtime_error("integer");if(p<s.size()&&s[p]=='.'){v.type='d';v.text+=take();size_t part=p;while(p<s.size()&&std::isdigit(static_cast<unsigned char>(s[p])))v.text+=take();if(part==p)throw std::runtime_error("fraction");}if(p<s.size()&&(s[p]=='e'||s[p]=='E')){v.type='d';v.text+=take();if(p<s.size()&&(s[p]=='+'||s[p]=='-'))v.text+=take();size_t part=p;while(p<s.size()&&std::isdigit(static_cast<unsigned char>(s[p])))v.text+=take();if(part==p)throw std::runtime_error("exponent");}return v;}
 public:explicit Parser(const std::string&raw):s(raw){if(raw.empty()||raw.size()>1048576)throw std::runtime_error("JSON size");}Json parse(){auto v=value(0);ws();if(p!=s.size())throw std::runtime_error("trailing JSON");return v;}
};
static std::string Read(const std::wstring&p){HANDLE h=CreateFileW(p.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);if(h==INVALID_HANDLE_VALUE)throw std::runtime_error("evidence read");BY_HANDLE_FILE_INFORMATION info{};LARGE_INTEGER size{};if(!GetFileInformationByHandle(h,&info)||(info.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)||!GetFileSizeEx(h,&size)||size.QuadPart<=0||size.QuadPart>1048576){CloseHandle(h);throw std::runtime_error("evidence path/size");}std::string b(size_t(size.QuadPart),'\0');DWORD n=0;bool ok=ReadFile(h,b.data(),DWORD(b.size()),&n,nullptr)&&n==b.size();CloseHandle(h);if(!ok)throw std::runtime_error("partial evidence");return b;}
static std::string Sha(const std::string&b){BCRYPT_ALG_HANDLE a=nullptr;BCRYPT_HASH_HANDLE h=nullptr;BYTE out[32];auto code=BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0);if(code<0)throw std::runtime_error("hash algorithm");code=BCryptCreateHash(a,&h,nullptr,0,nullptr,0,0);if(code>=0)code=BCryptHashData(h,(PUCHAR)b.data(),ULONG(b.size()),0);if(code>=0)code=BCryptFinishHash(h,out,32,0);if(h)BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);if(code<0)throw std::runtime_error("hash");std::ostringstream s;for(auto x:out)s<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(x);return s.str();}
static std::string lower(std::string s){for(char&c:s){if(c=='/')c='\\';else c=char(std::tolower(static_cast<unsigned char>(c)));}return s;}
static void Require(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
static std::string RowJson(const Row&r){std::ostringstream s;s<<"{\"pid\":"<<r.pid<<",\"created\":"<<J(std::to_string(r.created))<<",\"sequence\":"<<J(std::to_string(r.sequence))<<",\"parentPid\":"<<r.parent<<",\"parentSequence\":"<<J(std::to_string(r.parentSequence))<<",\"handleImage\":"<<J(U(r.handleImage))<<",\"handleCreated\":"<<J(std::to_string(r.handleCreated))<<",\"handleRetained\":true,\"imageError\":"<<r.imageError<<",\"metadataError\":"<<r.metadataError<<",\"startQpc\":"<<r.start<<",\"handleAttemptQpc\":"<<r.retained<<",\"imageBeginQpc\":"<<r.imageBegin<<",\"imageEndQpc\":"<<r.imageEnd<<",\"stopQpc\":"<<r.stop<<",\"stopCallbackQpc\":"<<r.stopNotified<<",\"signalObservedQpc\":"<<r.signal<<",\"exitFiletime\":"<<J(std::to_string(r.exitFT))<<",\"exitCode\":"<<r.exitCode<<",\"kernelExitFiletime\":"<<J(std::to_string(r.exitFT))<<",\"kernelExitCode\":"<<r.exitCode<<"}";return s.str();}
static bool WorkloadReceipt(){
 const auto phasePath=folder+L"\\phase-a-v3.json";
 if(GetFileAttributesW(phasePath.c_str())==INVALID_FILE_ATTRIBUTES)return false;
 auto raw=Read(phasePath);auto p=Parser(raw).parse();auto b=p.at("binding");
 Require(b.at("schema").str()=="stage6-terminal-v3","schema");
 Require(b.at("kernelSession").str()==U(session),"session");
 LARGE_INTEGER f;QueryPerformanceFrequency(&f);auto start=p.at("cleanupEntryQpc").number(),end=p.at("deadlineQpc").number();
 Require(b.at("frequency").number()==static_cast<unsigned long long>(f.QuadPart)&&end==start+20*f.QuadPart&&static_cast<unsigned long long>(Q())<end,"absolute deadline");
 auto declRaw=Read(folder+L"\\small-declaration-v3.json");auto decl=Parser(declRaw).parse();
 Require(Sha(declRaw)==b.at("declarationSHA256").str()&&decl.at("sourceManifestSHA256").str()==b.at("sourceManifestSHA256").str(),"declaration");
 auto run=folder.substr(folder.find_last_of(L"\\/")+1);Require(U(run)==b.at("run").str()&&decl.at("run").str()==U(run),"run");
 Require(Sha(Read(folder+L"\\observer-identities.json"))==b.at("observerSHA256").str(),"observer binding");
 Require(p.at("authorityObserver").at("pid").number()==GetCurrentProcessId(),"observer PID");
 FILETIME a,c,d,e;Require(GetProcessTimes(GetCurrentProcess(),&a,&c,&d,&e)!=0,"observer identity");Require(p.at("authorityObserver").at("created").str()==std::to_string(FT(a)),"observer creation");
 Require(p.at("state").str()=="LOCAL_EVIDENCE_FINALIZED_PENDING_EXTERNAL_EXIT"&&p.at("localDurable").yes()&&p.at("localHandlesClosed").yes()&&p.at("trackerStopped").yes()&&p.at("admissionsStopped").yes(),"phase A");
 auto collector=p.at("collector");auto helpers=p.at("helpers");Require(helpers.type=='a'&&helpers.arr.size()<=8192,"helper bound");
 std::vector<Json>wanted{collector};for(auto&h:helpers.arr)wanted.push_back(h);
 std::vector<Row> snapshot;{
  std::lock_guard<std::mutex>l(guard);Require(faults==0,"authority faults");
  std::set<std::pair<DWORD,ULONGLONG>> seen;Row parent;
  for(size_t i=0;i<wanted.size();i++){
   auto&w=wanted[i];auto pid=w.at("pid").number(),created=std::stoull(w.at("created").str());Require(pid<=MAXDWORD,"pid bound");auto key=std::make_pair(DWORD(pid),created);Require(seen.insert(key).second,"duplicate instance");auto it=rows.find(key);if(it==rows.end())return false;auto&r=it->second;
   if(!r.stop||!r.signal)return false;
   Require(r.handle&&r.handleCreated==r.created&&r.sequence&&r.imageError==0&&r.metadataError==0&&r.exitCodeKnown,"terminal handle");
   Require(r.start<=r.retained&&r.retained<=r.signal&&r.imageBegin<=r.imageEnd&&r.imageEnd<r.stop&&static_cast<unsigned long long>(r.stop)<end&&static_cast<unsigned long long>(r.signal)<end,"terminal timing");
   Require(lower(U(r.handleImage))==lower(w.at("image").str()),"image mismatch");
   if(i==0){parent=r;Require(r.exitCode==0,"collector failure");}else{Require(w.at("role").str()=="OS_CONSOLE_HELPER"&&lower(w.at("image").str())=="c:\\windows\\system32\\conhost.exe","class");Require(r.parent==parent.pid&&r.parentSequence==parent.sequence,"parent");Require(w.at("parent").at("pid").number()==parent.pid&&w.at("parent").at("created").str()==std::to_string(parent.created),"parent creation");Require(w.at("localClosed").yes()&&static_cast<unsigned long long>(r.retained)<w.at("localCloseQpc").number()&&static_cast<unsigned long long>(r.imageBegin)<w.at("localCloseQpc").number(),"handoff");}
   snapshot.push_back(r);
  }
 }
 std::ostringstream out;out<<"{\"schema\":\"stage6-terminal-v3\",\"kind\":\"workload-terminal\",\"sequence\":1,\"binding\":"<<b.dump()<<",\"phaseASHA256\":"<<J(Sha(raw))<<",\"observer\":"<<p.at("authorityObserver").dump()<<",\"cleanupEntryQpc\":"<<start<<",\"deadlineQpc\":"<<end<<",\"capturedQpc\":"<<Q()<<",\"coordinationOnly\":true,\"acceptance\":false,\"faults\":0,\"eventsLost\":0,\"buffersLost\":0,\"rows\":[";
 for(size_t i=0;i<snapshot.size();i++){if(i)out<<",";out<<RowJson(snapshot[i]);}out<<"]}";
 Require(Write(L"terminal-v3.json.pending",out.str()),"receipt durable write");
 Require(static_cast<unsigned long long>(Q())<end,"receipt publication late");
 Require(MoveFileExW((folder+L"\\terminal-v3.json.pending").c_str(),(folder+L"\\terminal-v3.json").c_str(),MOVEFILE_WRITE_THROUGH)!=0,"receipt exclusive publication");return true;
}
static bool TailReceipt(){
 if(GetFileAttributesW((folder+L"\\observer-tail-request-v3.json").c_str())==INVALID_FILE_ATTRIBUTES)return false;
 auto phaseRaw=Read(folder+L"\\phase-a-v3.json");auto p=Parser(phaseRaw).parse();auto req=Parser(Read(folder+L"\\observer-tail-request-v3.json")).parse();
 Require(req.at("phaseASHA256").str()==Sha(phaseRaw)&&req.at("binding").dump()==p.at("binding").dump(),"tail binding");
 auto end=p.at("deadlineQpc").number();Require(static_cast<unsigned long long>(Q())<end,"tail deadline");
 std::vector<Row> snapshot;{std::lock_guard<std::mutex>l(guard);Require(!faults,"tail faults");
  for(auto&item:rows){auto&r=item.second;if(!r.stop)return false;
   if(r.handle){if(!r.signal)return false;Require(r.handleCreated==r.created&&r.metadataError==0,"tail identity");}
   else {
    auto img=lower(U(r.image));wchar_t device[32768];if(QueryDosDeviceW(L"C:",device,32768)){auto prefix=lower(U(device));if(img.rfind(prefix+"\\",0)==0)img="c:"+img.substr(prefix.size());}
    Require(r.openError==87&&r.stop<r.attemptBegin&&r.sequence&&r.created&&img=="c:\\windows\\system32\\conhost.exe"&&ParentKnown(r.parent,r.created,r.parentSequence),"unqualified missing tail handle");
   }
   Require(static_cast<unsigned long long>(r.stop)<end&&static_cast<unsigned long long>(r.signal)<end,"tail late");snapshot.push_back(r);
  }
 }
 std::ostringstream out;out<<"{\"schema\":\"stage6-terminal-v3\",\"kind\":\"observer-tail\",\"sequence\":2,\"binding\":"<<p.at("binding").dump()<<",\"phaseASHA256\":"<<J(Sha(phaseRaw))<<",\"capturedQpc\":"<<Q()<<",\"coordinationOnly\":true,\"rows\":[";
 for(size_t i=0;i<snapshot.size();i++){if(i)out<<",";out<<"{\"pid\":"<<snapshot[i].pid<<",\"created\":"<<J(std::to_string(snapshot[i].created))<<",\"sequence\":"<<J(std::to_string(snapshot[i].sequence))<<",\"stopQpc\":"<<snapshot[i].stop<<",\"signalObservedQpc\":"<<snapshot[i].signal<<"}";}out<<"]}";
 Require(Write(L"observer-tail-v3.json.pending",out.str()),"tail persistence");Require(static_cast<unsigned long long>(Q())<end,"tail publication late");
 Require(MoveFileExW((folder+L"\\observer-tail-v3.json.pending").c_str(),(folder+L"\\observer-tail-v3.json").c_str(),MOVEFILE_WRITE_THROUGH)!=0,"tail publication");return true;
}
}
