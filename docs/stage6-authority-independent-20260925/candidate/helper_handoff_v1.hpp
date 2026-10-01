#pragma once
// TEST pre-release receipt; no command dispatch, process transfer or termination.
namespace handoff_v1 {
using namespace terminal_v3;
static std::string Image(const std::wstring&w){auto s=lower(U(w));wchar_t dev[32768];if(QueryDosDeviceW(L"C:",dev,32768)){auto d=lower(U(dev));if(s.rfind(d+"\\",0)==0)s="c:"+s.substr(d.size());}return s;}
static void SafeRoot(){
 std::wstring p=folder;for(;;){DWORD a=GetFileAttributesW(p.c_str());Require(a!=INVALID_FILE_ATTRIBUTES&&!(a&FILE_ATTRIBUTE_REPARSE_POINT),"handoff reparse/root");auto k=p.find_last_of(L"\\/");if(k==std::wstring::npos||k<3)break;p.resize(k);}
}
static bool HandoffReceipt(){
 const auto path=folder+L"\\helper-handoff-obligations-v1.json";
 if(GetFileAttributesW(path.c_str())==INVALID_FILE_ATTRIBUTES)return false;
 SafeRoot();auto raw=Read(path);auto o=Parser(raw).parse();auto b=o.at("binding");
 Require(o.at("schema").str()=="stage6-helper-handoff-v1"&&o.at("kind").str()=="HELPER_OBLIGATIONS","handoff schema");
 Require(o.at("coordinationOnly").yes()&&!o.at("cleanupPass").yes()&&!o.at("acceptance").yes(),"handoff premature acceptance");
 auto run=U(folder.substr(folder.find_last_of(L"\\/")+1));auto candidate=folder.substr(0,folder.find_last_of(L"\\/"));
 LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);auto f=static_cast<unsigned long long>(frequency.QuadPart);
 auto start=o.at("cleanupEntryQpc").number(),end=o.at("deadlineQpc").number();
 Require(start&&end==start+20*f&&static_cast<unsigned long long>(Q())>=start&&static_cast<unsigned long long>(Q())<end,"handoff deadline");
 Require(b.at("run").str()==run&&b.at("kernelSession").str()==U(session)&&b.at("frequency").number()==f,"handoff run/session");
 auto originRaw=Read(folder+L"\\cleanup-origin-v3.json");auto origin=Parser(originRaw).parse();
 Require(Sha(originRaw)==b.at("cleanupOriginSHA256").str()&&origin.at("cleanupEntryQpc").number()==start&&origin.at("deadlineQpc").number()==end&&origin.at("frequency").number()==f,"handoff origin");
 auto declarationRaw=Read(folder+L"\\small-declaration-v3.json");auto declaration=Parser(declarationRaw).parse();
 auto workspaceRaw=Read(folder+L"\\workspace-binding-v4.json");auto workspace=Parser(workspaceRaw).parse();
 Require(Sha(declarationRaw)==b.at("declarationSHA256").str()&&Sha(workspaceRaw)==b.at("workspaceBindingSHA256").str(),"handoff binding hashes");
 Require(declaration.at("run").str()==run&&declaration.at("sourceManifestSHA256").str()==b.at("sourceManifestSHA256").str()&&lower(declaration.at("code").str())==lower(U(candidate)),"handoff declaration");
 Require(workspace.at("run").str()==run&&lower(workspace.at("candidateRoot").str())==lower(U(candidate))&&lower(workspace.at("evidenceRoot").str())==lower(U(folder))&&workspace.at("candidateManifestSHA256").str()==b.at("sourceManifestSHA256").str()&&workspace.at("smallDeclarationSHA256").str()==Sha(declarationRaw),"handoff workspace");
 Require(Sha(Read(candidate+L"\\small-source-v3.json"))==b.at("sourceManifestSHA256").str(),"handoff source manifest");
 auto obsRaw=Read(folder+L"\\observer-identities.json");auto obs=Parser(obsRaw).parse().at("etw");
 Require(Sha(obsRaw)==b.at("observerSHA256").str()&&obs.dump()==o.at("authorityObserver").dump(),"handoff observer binding");
 FILETIME ca,cb,cc,cd;Require(GetProcessTimes(GetCurrentProcess(),&ca,&cb,&cc,&cd)!=0,"handoff own creation");
 wchar_t own[32768];DWORD ownN=32768;Require(QueryFullProcessImageNameW(GetCurrentProcess(),0,own,&ownN)!=0,"handoff own image");
 Require(obs.at("pid").number()==GetCurrentProcessId()&&obs.at("created").str()==std::to_string(FT(ca))&&lower(obs.at("image").str())==lower(U(std::wstring(own,ownN))),"handoff wrong observer");
 auto collector=o.at("collector"),hs=o.at("helpers");Require(hs.type=='a'&&!hs.arr.empty()&&hs.arr.size()<=8192,"handoff helper bound");
 Require(Sha(hs.dump())==o.at("obligationSetId").str(),"handoff set hash");
 std::vector<Row> copy;Row parent;std::set<std::pair<DWORD,ULONGLONG>> instances;std::set<std::string> obligations,sequences;
 {std::lock_guard<std::mutex>lock(guard);Require(faults==0,"handoff observer fault");
 auto it=rows.find({DWORD(collector.at("pid").number()),std::stoull(collector.at("created").str())});if(it==rows.end())return false;parent=it->second;
 Require(parent.sequence&&parent.handle&&parent.handleCreated==parent.created&&parent.handlePid==parent.pid&&parent.imageError==0&&parent.metadataError==0&&Image(parent.handleImage)==lower(collector.at("image").str()),"handoff collector identity");
 for(auto&h:hs.arr){auto pid=h.at("pid").number();auto created=std::stoull(h.at("created").str());Require(pid&&pid<=MAXDWORD&&created,"handoff identity");auto key=std::make_pair(DWORD(pid),created);auto id=h.at("obligationId").str();
 Require(instances.insert(key).second&&obligations.insert(id).second&&id==std::to_string(pid)+"-"+std::to_string(created),"handoff duplicate");
 Require(h.at("localRetained").yes()&&h.at("publicationState").str()=="SEALED_CLAIM"&&h.at("parent").dump()==collector.dump()&&lower(h.at("image").str())=="c:\\windows\\system32\\conhost.exe","handoff local claims");
 auto pos=rows.find(key);if(pos==rows.end())return false;auto&r=pos->second;
 Require(r.handle&&r.handlePid==r.pid&&r.handleCreated==r.created&&r.imageError==0&&r.metadataError==0&&r.sequence&&sequences.insert(std::to_string(r.sequence)).second,"handoff missing independent handle");
 Require(r.imageStateBefore==WAIT_TIMEOUT&&r.imageStateAfter==WAIT_TIMEOUT,"handoff image not captured live");
 Require(r.parent==parent.pid&&r.parentSequence==parent.sequence&&r.sequence!=parent.sequence,"handoff parent instance");
 Require(h.at("expectedSequence").type=='n'||h.at("expectedSequence").str()==std::to_string(r.sequence),"handoff sequence");
 Require(Image(r.image)==lower(h.at("image").str())&&Image(r.handleImage)==lower(h.at("image").str()),"handoff image");
 Require(r.start<=r.attemptBegin&&r.attemptBegin<=r.retained&&r.retained<=r.creationVerified&&r.creationVerified<=r.imageBegin&&r.imageBegin<=r.imageEnd&&(!r.stop||r.imageEnd<r.stop),"handoff live acquisition timing");
 DWORD state=WaitForSingleObject(r.handle,0);Require(state==WAIT_OBJECT_0||state==WAIT_TIMEOUT,"handoff handle state");
 FILETIME a,c,d,e;Require(GetProcessId(r.handle)==r.pid&&GetProcessTimes(r.handle,&a,&c,&d,&e)&&FT(a)==r.created,"handoff retained identity");
 copy.push_back(r);
 }} // No receipt I/O occurs with the event-map lock held.
 auto verified=Q();Require(static_cast<unsigned long long>(verified)<end,"handoff verification late");
 std::ostringstream s;s<<"{\"schema\":\"stage6-helper-handoff-v1\",\"kind\":\"HANDOFF_ACQUIRED\",\"receiptSequence\":1,\"binding\":"<<b.dump()<<",\"obligationsSHA256\":"<<J(Sha(raw))<<",\"cleanupEntryQpc\":"<<start<<",\"deadlineQpc\":"<<end<<",\"collector\":"<<collector.dump()<<",\"authorityObserver\":"<<obs.dump()<<",\"preparedQpc\":"<<Q()<<",\"coordinationOnly\":true,\"cleanupPass\":false,\"acceptance\":false,\"helpers\":[";
 for(size_t i=0;i<copy.size();i++){auto&r=copy[i];if(i)s<<",";
 s<<"{\"obligationId\":"<<hs.arr[i].at("obligationId").dump()<<",\"pid\":"<<r.pid<<",\"created\":"<<J(std::to_string(r.created))<<",\"sequence\":"<<J(std::to_string(r.sequence))<<",\"kernelSession\":"<<J(U(session))<<",\"parent\":{\"pid\":"<<parent.pid<<",\"created\":"<<J(std::to_string(parent.created))<<",\"sequence\":"<<J(std::to_string(parent.sequence))<<",\"image\":"<<J(U(parent.handleImage))<<"},\"kernelImage\":"<<J(U(r.image))<<",\"handleImage\":"<<J(U(r.handleImage))<<",\"method\":\"OpenProcess\",\"accessMask\":1052672,\"handlePid\":"<<r.handlePid<<",\"handleCreated\":"<<J(std::to_string(r.handleCreated))<<",\"handleIdentity\":"<<J(std::to_string(reinterpret_cast<ULONG_PTR>(r.handle)))<<",\"retained\":true,\"acquisitionBeginQpc\":"<<r.attemptBegin<<",\"acquisitionReturnQpc\":"<<r.retained<<",\"creationVerifiedQpc\":"<<r.creationVerified<<",\"imageBeginQpc\":"<<r.imageBegin<<",\"imageEndQpc\":"<<r.imageEnd<<",\"verificationQpc\":"<<verified<<"}";
 }s<<"]}";
 Require(static_cast<unsigned long long>(Q())<end,"handoff publication expired");
 Require(Write(L"helper-handoff-acquired-v1.json.pending",s.str()),"handoff write");
 Require(static_cast<unsigned long long>(Q())<end,"handoff flush late");
 Require(MoveFileExW((folder+L"\\helper-handoff-acquired-v1.json.pending").c_str(),(folder+L"\\helper-handoff-acquired-v1.json").c_str(),MOVEFILE_WRITE_THROUGH)!=0,"handoff publication");
 Require(static_cast<unsigned long long>(Q())<end,"handoff publish late");return true;
}
}
