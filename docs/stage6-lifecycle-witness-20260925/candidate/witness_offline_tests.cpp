#include <map>
#include <vector>
#include <string>
#include <iostream>
#include <cassert>
#include "lifecycle_witness_v1.hpp"

using DWORD=unsigned long;using ULONGLONG=unsigned long long;using LONGLONG=long long;
#define WINAPI
struct Descriptor{unsigned Id=1,Version=4;};
struct Header{int ProviderId=1;Descriptor EventDescriptor;struct{long long QuadPart=100;}TimeStamp;};
struct EVENT_RECORD{Header EventHeader;std::map<std::wstring,ULONGLONG> fields;bool throwing=false;};
bool IsEqualGUID(int a,int b){return a==b;}constexpr int Provider=1;
namespace j6t{struct CallbackScope{long long begin=99,eventQpc=0;bool selected=false;};struct Lock{explicit Lock(int&){} };}

namespace authority_old {

static unsigned faults=0,discarded=0;static int guard;static long long clockValue=1000;
static std::vector<std::wstring> queries;static std::vector<std::string> captured;
static DWORD rootPid=10;static ULONGLONG rootCreated=1;
static LONGLONG Q(){return ++clockValue;}
static ULONGLONG Number(EVENT_RECORD*e,const wchar_t*n,bool*found=nullptr){queries.push_back(n);auto i=e->fields.find(n);if(found)*found=i!=e->fields.end();return i==e->fields.end()?0:i->second;}
static std::wstring Text(EVENT_RECORD*e,const wchar_t*){if(e->throwing)throw 1;return L"image";}
static std::vector<std::string> Schemas(EVENT_RECORD*){return {"unchanged"};}
struct Row{DWORD pid=0,parent=0;ULONGLONG created=0,sequence=0,parentSequence=0,exitFT=0;DWORD exitCode=0;bool exitCodeKnown=false;std::wstring image;LONGLONG start=0,notified=0,stop=0,stopNotified=0;unsigned version=0,stopVersion=0;std::vector<std::string> schema,stopSchema;};
static std::map<std::pair<DWORD,ULONGLONG>,Row> rows;
static bool ParentKnown(DWORD pid,ULONGLONG childTime,ULONGLONG parentSequence){if(pid==rootPid)return childTime>=rootCreated;for(auto&a:rows){auto&r=a.second;if(r.pid==pid&&r.created<=childTime&&(!r.exitFT||childTime<=r.exitFT)&&(!parentSequence||r.sequence==parentSequence))return true;}return false;}
static void Acquire(Row&){}
static void Capture(const Row&r,bool start){captured.push_back(std::to_string(r.pid)+":"+std::to_string(r.created)+":"+std::to_string(start));}
static std::string snapshot(){std::ostringstream s;s<<faults<<":"<<discarded<<":"<<clockValue;for(auto&a:rows){auto&r=a.second;s<<"|"<<r.pid<<":"<<r.parent<<":"<<r.created<<":"<<r.sequence<<":"<<r.parentSequence<<":"<<r.start<<":"<<r.notified<<":"<<r.stop<<":"<<r.stopNotified<<":"<<r.exitFT<<":"<<r.exitCode<<":"<<r.exitCodeKnown;}for(auto&v:captured)s<<"/"<<v;return s.str();}
static void WINAPI Event(EVENT_RECORD* e){j6t::CallbackScope timing;timing.eventQpc=e->EventHeader.TimeStamp.QuadPart;try{
 if(!IsEqualGUID(e->EventHeader.ProviderId,Provider))return;unsigned id=e->EventHeader.EventDescriptor.Id;if(id!=1&&id!=2)return;
 bool hasPid=false,hasTime=false;DWORD pid=static_cast<DWORD>(Number(e,L"ProcessID",&hasPid));ULONGLONG created=Number(e,L"CreateTime",&hasTime);
 j6t::Lock l(guard);
 if(id==1){DWORD parent=static_cast<DWORD>(Number(e,L"ParentProcessID"));if(!ParentKnown(parent,created,Number(e,L"ParentProcessSequenceNumber"))){++discarded;return;}
  if(!hasPid||!hasTime||!created||rows.size()>=8192){++faults;return;}auto key=std::make_pair(pid,created);if(rows.count(key)){++faults;return;}
  Row r;r.pid=pid;r.parent=parent;r.created=created;r.start=e->EventHeader.TimeStamp.QuadPart;r.notified=Q();r.version=e->EventHeader.EventDescriptor.Version;r.image=Text(e,L"ImageName");r.sequence=Number(e,L"ProcessSequenceNumber");r.parentSequence=Number(e,L"ParentProcessSequenceNumber");r.schema=Schemas(e);timing.selected=true;Capture(r,true);Acquire(r);rows.emplace(key,std::move(r));
 }else{auto it=rows.find(std::make_pair(pid,created));if(it==rows.end()){++discarded;return;}auto&r=it->second;if(r.stop){++faults;return;}if(r.sequence!=Number(e,L"ProcessSequenceNumber"))++faults;r.stop=e->EventHeader.TimeStamp.QuadPart;r.stopNotified=Q();r.stopVersion=e->EventHeader.EventDescriptor.Version;auto exitTime=Number(e,L"ExitTime");bool known=false;auto code=static_cast<DWORD>(Number(e,L"ExitCode",&known));if(r.exitFT&&exitTime!=r.exitFT)++faults;if(r.exitCodeKnown&&(!known||r.exitCode!=code))++faults;r.exitFT=exitTime;r.exitCode=code;r.exitCodeKnown=known;r.stopSchema=Schemas(e);timing.selected=true;Capture(r,false);}
 }catch(...){++faults;}}

}

namespace authority_new {

static unsigned faults=0,discarded=0;static int guard;static long long clockValue=1000;
static std::vector<std::wstring> queries;static std::vector<std::string> captured;
static DWORD rootPid=10;static ULONGLONG rootCreated=1;
static LONGLONG Q(){return ++clockValue;}
static ULONGLONG Number(EVENT_RECORD*e,const wchar_t*n,bool*found=nullptr){queries.push_back(n);auto i=e->fields.find(n);if(found)*found=i!=e->fields.end();return i==e->fields.end()?0:i->second;}
static std::wstring Text(EVENT_RECORD*e,const wchar_t*){if(e->throwing)throw 1;return L"image";}
static std::vector<std::string> Schemas(EVENT_RECORD*){return {"unchanged"};}
struct Row{DWORD pid=0,parent=0;ULONGLONG created=0,sequence=0,parentSequence=0,exitFT=0;DWORD exitCode=0;bool exitCodeKnown=false;std::wstring image;LONGLONG start=0,notified=0,stop=0,stopNotified=0;unsigned version=0,stopVersion=0;std::vector<std::string> schema,stopSchema;};
static std::map<std::pair<DWORD,ULONGLONG>,Row> rows;
static bool ParentKnown(DWORD pid,ULONGLONG childTime,ULONGLONG parentSequence){if(pid==rootPid)return childTime>=rootCreated;for(auto&a:rows){auto&r=a.second;if(r.pid==pid&&r.created<=childTime&&(!r.exitFT||childTime<=r.exitFT)&&(!parentSequence||r.sequence==parentSequence))return true;}return false;}
static void Acquire(Row&){}
static void Capture(const Row&r,bool start){captured.push_back(std::to_string(r.pid)+":"+std::to_string(r.created)+":"+std::to_string(start));}
static std::string snapshot(){std::ostringstream s;s<<faults<<":"<<discarded<<":"<<clockValue;for(auto&a:rows){auto&r=a.second;s<<"|"<<r.pid<<":"<<r.parent<<":"<<r.created<<":"<<r.sequence<<":"<<r.parentSequence<<":"<<r.start<<":"<<r.notified<<":"<<r.stop<<":"<<r.stopNotified<<":"<<r.exitFT<<":"<<r.exitCode<<":"<<r.exitCodeKnown;}for(auto&v:captured)s<<"/"<<v;return s.str();}
static void WINAPI Event(EVENT_RECORD* e){j6t::CallbackScope timing;timing.eventQpc=e->EventHeader.TimeStamp.QuadPart;
 if(!IsEqualGUID(e->EventHeader.ProviderId,Provider))return;unsigned id=e->EventHeader.EventDescriptor.Id;if(id!=1&&id!=2)return;
 j6w::Scope witness(id,e->EventHeader.TimeStamp.QuadPart,timing.begin);
 auto read=[&](const wchar_t* n,j6w::Field f){bool ok=false;auto v=Number(e,n,&ok);return witness.field(v,f,ok);};try{
 bool hasPid=false,hasTime=false;DWORD pid=static_cast<DWORD>(Number(e,L"ProcessID",&hasPid));ULONGLONG created=Number(e,L"CreateTime",&hasTime);
 witness.field(pid,j6w::PID,hasPid);witness.field(created,j6w::CREATION,hasTime);
 j6t::Lock l(guard);
 if(id==1){DWORD parent=static_cast<DWORD>(read(L"ParentProcessID",j6w::PARENT));if(!witness.parent(ParentKnown(parent,created,read(L"ParentProcessSequenceNumber",j6w::PARENT_SEQUENCE)))){witness.result(j6w::UNKNOWN_PARENT,j6w::PARENT_NOT_KNOWN);++discarded;return;}
  if(!hasPid||!hasTime||!created||rows.size()>=8192){witness.result((!hasPid||!hasTime)?j6w::DECODE_FAILURE:!created?j6w::INVALID_IDENTITY:j6w::OTHER_EXPLICIT_REJECTION,(!hasPid||!hasTime)?j6w::FIELD_DECODE_FAILED:!created?j6w::ZERO_CREATION:j6w::ROW_CAPACITY);++faults;return;}auto key=std::make_pair(pid,created);if(rows.count(key)){witness.result(j6w::DUPLICATE_EVENT,j6w::DUPLICATE_START);++faults;return;}
  Row r;r.pid=pid;r.parent=parent;r.created=created;r.start=e->EventHeader.TimeStamp.QuadPart;r.notified=Q();r.version=e->EventHeader.EventDescriptor.Version;r.image=Text(e,L"ImageName");r.sequence=read(L"ProcessSequenceNumber",j6w::SEQUENCE);r.parentSequence=read(L"ParentProcessSequenceNumber",j6w::PARENT_SEQUENCE);r.schema=Schemas(e);timing.selected=true;Capture(r,true);Acquire(r);rows.emplace(key,std::move(r));witness.result(j6w::ADMITTED);
 }else{auto it=rows.find(std::make_pair(pid,created));if(!witness.instance(it!=rows.end())){witness.result(j6w::UNKNOWN_INSTANCE,j6w::INSTANCE_NOT_KNOWN);++discarded;return;}auto&r=it->second;if(r.stop){witness.result(j6w::DUPLICATE_EVENT,j6w::DUPLICATE_STOP);++faults;return;}if(r.sequence!=read(L"ProcessSequenceNumber",j6w::SEQUENCE))++faults;r.stop=e->EventHeader.TimeStamp.QuadPart;r.stopNotified=Q();r.stopVersion=e->EventHeader.EventDescriptor.Version;auto exitTime=Number(e,L"ExitTime");bool known=false;auto code=static_cast<DWORD>(Number(e,L"ExitCode",&known));if(r.exitFT&&exitTime!=r.exitFT)++faults;if(r.exitCodeKnown&&(!known||r.exitCode!=code))++faults;r.exitFT=exitTime;r.exitCode=code;r.exitCodeKnown=known;r.stopSchema=Schemas(e);timing.selected=true;Capture(r,false);witness.result(j6w::ADMITTED);}
 }catch(...){witness.result(j6w::OTHER_EXPLICIT_REJECTION,j6w::EXCEPTION);++faults;}}

}

namespace detailed_old {

static unsigned faults=0,discarded=0;static int guard;static long long clockValue=1000;
static std::vector<std::wstring> queries;static std::vector<std::string> captured;
static DWORD rootPid=10;static ULONGLONG rootCreated=1;
static LONGLONG Q(){return ++clockValue;}
static ULONGLONG Number(EVENT_RECORD*e,const wchar_t*n,bool*found=nullptr){queries.push_back(n);auto i=e->fields.find(n);if(found)*found=i!=e->fields.end();return i==e->fields.end()?0:i->second;}
static std::wstring Text(EVENT_RECORD*e,const wchar_t*){if(e->throwing)throw 1;return L"image";}
static std::vector<std::string> Schemas(EVENT_RECORD*){return {"unchanged"};}
struct Row{DWORD pid=0,parent=0;ULONGLONG created=0,sequence=0,parentSequence=0,exitFT=0;DWORD exitCode=0;bool exitCodeKnown=false;std::wstring image;LONGLONG start=0,notified=0,stop=0,stopNotified=0;unsigned version=0,stopVersion=0;std::vector<std::string> schema,stopSchema;};
static std::map<std::pair<DWORD,ULONGLONG>,Row> rows;
static bool ParentKnown(DWORD pid,ULONGLONG childTime,ULONGLONG parentSequence){if(pid==rootPid)return childTime>=rootCreated;for(auto&a:rows){auto&r=a.second;if(r.pid==pid&&r.created<=childTime&&(!r.exitFT||childTime<=r.exitFT)&&(!parentSequence||r.sequence==parentSequence))return true;}return false;}
static void Acquire(Row&){}
static void Capture(const Row&r,bool start){captured.push_back(std::to_string(r.pid)+":"+std::to_string(r.created)+":"+std::to_string(start));}
static std::string snapshot(){std::ostringstream s;s<<faults<<":"<<discarded<<":"<<clockValue;for(auto&a:rows){auto&r=a.second;s<<"|"<<r.pid<<":"<<r.parent<<":"<<r.created<<":"<<r.sequence<<":"<<r.parentSequence<<":"<<r.start<<":"<<r.notified<<":"<<r.stop<<":"<<r.stopNotified<<":"<<r.exitFT<<":"<<r.exitCode<<":"<<r.exitCodeKnown;}for(auto&v:captured)s<<"/"<<v;return s.str();}
static void LifecycleEvent(EVENT_RECORD* e){try{
 if(!IsEqualGUID(e->EventHeader.ProviderId,Provider))return;unsigned id=e->EventHeader.EventDescriptor.Id;if(id!=1&&id!=2)return;
 bool hasPid=false,hasTime=false;DWORD pid=static_cast<DWORD>(Number(e,L"ProcessID",&hasPid));ULONGLONG created=Number(e,L"CreateTime",&hasTime);
 j6t::Lock l(guard);
 if(id==1){DWORD parent=static_cast<DWORD>(Number(e,L"ParentProcessID"));if(!ParentKnown(parent,created,Number(e,L"ParentProcessSequenceNumber"))){++discarded;return;}
  if(!hasPid||!hasTime||!created||rows.size()>=8192){++faults;return;}auto key=std::make_pair(pid,created);if(rows.count(key)){++faults;return;}
  Row r;r.pid=pid;r.parent=parent;r.created=created;r.start=e->EventHeader.TimeStamp.QuadPart;r.notified=Q();r.version=e->EventHeader.EventDescriptor.Version;r.image=Text(e,L"ImageName");r.sequence=Number(e,L"ProcessSequenceNumber");r.parentSequence=Number(e,L"ParentProcessSequenceNumber");r.schema=Schemas(e);Acquire(r);rows.emplace(key,std::move(r));
 }else{auto it=rows.find(std::make_pair(pid,created));if(it==rows.end()){++discarded;return;}auto&r=it->second;if(r.stop){++faults;return;}if(r.sequence!=Number(e,L"ProcessSequenceNumber"))++faults;r.stop=e->EventHeader.TimeStamp.QuadPart;r.stopNotified=Q();r.stopVersion=e->EventHeader.EventDescriptor.Version;auto exitTime=Number(e,L"ExitTime");bool known=false;auto code=static_cast<DWORD>(Number(e,L"ExitCode",&known));if(r.exitFT&&exitTime!=r.exitFT)++faults;if(r.exitCodeKnown&&(!known||r.exitCode!=code))++faults;r.exitFT=exitTime;r.exitCode=code;r.exitCodeKnown=known;r.stopSchema=Schemas(e);}
 }catch(...){++faults;}}

}

namespace detailed_new {

static unsigned faults=0,discarded=0;static int guard;static long long clockValue=1000;
static std::vector<std::wstring> queries;static std::vector<std::string> captured;
static DWORD rootPid=10;static ULONGLONG rootCreated=1;
static LONGLONG Q(){return ++clockValue;}
static ULONGLONG Number(EVENT_RECORD*e,const wchar_t*n,bool*found=nullptr){queries.push_back(n);auto i=e->fields.find(n);if(found)*found=i!=e->fields.end();return i==e->fields.end()?0:i->second;}
static std::wstring Text(EVENT_RECORD*e,const wchar_t*){if(e->throwing)throw 1;return L"image";}
static std::vector<std::string> Schemas(EVENT_RECORD*){return {"unchanged"};}
struct Row{DWORD pid=0,parent=0;ULONGLONG created=0,sequence=0,parentSequence=0,exitFT=0;DWORD exitCode=0;bool exitCodeKnown=false;std::wstring image;LONGLONG start=0,notified=0,stop=0,stopNotified=0;unsigned version=0,stopVersion=0;std::vector<std::string> schema,stopSchema;};
static std::map<std::pair<DWORD,ULONGLONG>,Row> rows;
static bool ParentKnown(DWORD pid,ULONGLONG childTime,ULONGLONG parentSequence){if(pid==rootPid)return childTime>=rootCreated;for(auto&a:rows){auto&r=a.second;if(r.pid==pid&&r.created<=childTime&&(!r.exitFT||childTime<=r.exitFT)&&(!parentSequence||r.sequence==parentSequence))return true;}return false;}
static void Acquire(Row&){}
static void Capture(const Row&r,bool start){captured.push_back(std::to_string(r.pid)+":"+std::to_string(r.created)+":"+std::to_string(start));}
static std::string snapshot(){std::ostringstream s;s<<faults<<":"<<discarded<<":"<<clockValue;for(auto&a:rows){auto&r=a.second;s<<"|"<<r.pid<<":"<<r.parent<<":"<<r.created<<":"<<r.sequence<<":"<<r.parentSequence<<":"<<r.start<<":"<<r.notified<<":"<<r.stop<<":"<<r.stopNotified<<":"<<r.exitFT<<":"<<r.exitCode<<":"<<r.exitCodeKnown;}for(auto&v:captured)s<<"/"<<v;return s.str();}
static void LifecycleEvent(EVENT_RECORD* e,LONGLONG callbackQpc){
 if(!IsEqualGUID(e->EventHeader.ProviderId,Provider))return;unsigned id=e->EventHeader.EventDescriptor.Id;if(id!=1&&id!=2)return;
 j6w::Scope witness(id,e->EventHeader.TimeStamp.QuadPart,callbackQpc);
 auto read=[&](const wchar_t* n,j6w::Field f){bool ok=false;auto v=Number(e,n,&ok);return witness.field(v,f,ok);};try{
 bool hasPid=false,hasTime=false;DWORD pid=static_cast<DWORD>(Number(e,L"ProcessID",&hasPid));ULONGLONG created=Number(e,L"CreateTime",&hasTime);
 witness.field(pid,j6w::PID,hasPid);witness.field(created,j6w::CREATION,hasTime);
 j6t::Lock l(guard);
 if(id==1){DWORD parent=static_cast<DWORD>(read(L"ParentProcessID",j6w::PARENT));if(!witness.parent(ParentKnown(parent,created,read(L"ParentProcessSequenceNumber",j6w::PARENT_SEQUENCE)))){witness.result(j6w::UNKNOWN_PARENT,j6w::PARENT_NOT_KNOWN);++discarded;return;}
  if(!hasPid||!hasTime||!created||rows.size()>=8192){witness.result((!hasPid||!hasTime)?j6w::DECODE_FAILURE:!created?j6w::INVALID_IDENTITY:j6w::OTHER_EXPLICIT_REJECTION,(!hasPid||!hasTime)?j6w::FIELD_DECODE_FAILED:!created?j6w::ZERO_CREATION:j6w::ROW_CAPACITY);++faults;return;}auto key=std::make_pair(pid,created);if(rows.count(key)){witness.result(j6w::DUPLICATE_EVENT,j6w::DUPLICATE_START);++faults;return;}
  Row r;r.pid=pid;r.parent=parent;r.created=created;r.start=e->EventHeader.TimeStamp.QuadPart;r.notified=Q();r.version=e->EventHeader.EventDescriptor.Version;r.image=Text(e,L"ImageName");r.sequence=read(L"ProcessSequenceNumber",j6w::SEQUENCE);r.parentSequence=read(L"ParentProcessSequenceNumber",j6w::PARENT_SEQUENCE);r.schema=Schemas(e);Acquire(r);rows.emplace(key,std::move(r));witness.result(j6w::ADMITTED);
 }else{auto it=rows.find(std::make_pair(pid,created));if(!witness.instance(it!=rows.end())){witness.result(j6w::UNKNOWN_INSTANCE,j6w::INSTANCE_NOT_KNOWN);++discarded;return;}auto&r=it->second;if(r.stop){witness.result(j6w::DUPLICATE_EVENT,j6w::DUPLICATE_STOP);++faults;return;}if(r.sequence!=read(L"ProcessSequenceNumber",j6w::SEQUENCE))++faults;r.stop=e->EventHeader.TimeStamp.QuadPart;r.stopNotified=Q();r.stopVersion=e->EventHeader.EventDescriptor.Version;auto exitTime=Number(e,L"ExitTime");bool known=false;auto code=static_cast<DWORD>(Number(e,L"ExitCode",&known));if(r.exitFT&&exitTime!=r.exitFT)++faults;if(r.exitCodeKnown&&(!known||r.exitCode!=code))++faults;r.exitFT=exitTime;r.exitCode=code;r.exitCodeKnown=known;r.stopSchema=Schemas(e);witness.result(j6w::ADMITTED);}
 }catch(...){witness.result(j6w::OTHER_EXPLICIT_REJECTION,j6w::EXCEPTION);++faults;}}

}

static int checks=0;void check(bool b){++checks;if(!b){std::cerr<<"failed assertion "<<checks<<"\n";std::exit(1);}}
EVENT_RECORD event(unsigned id,unsigned pid,unsigned created,unsigned parent=10){EVENT_RECORD e;e.EventHeader.EventDescriptor.Id=id;e.fields={{L"ProcessID",pid},{L"CreateTime",created},{L"ParentProcessID",parent},{L"ParentProcessSequenceNumber",0},{L"ProcessSequenceNumber",7},{L"ExitTime",200},{L"ExitCode",0}};return e;}
int main(){
 std::vector<EVENT_RECORD> cases;
 cases.push_back(event(1,20,10)); // admitted
 cases.push_back(event(1,21,11,999)); // unknown parent
 cases.push_back(event(2,20,10)); // admitted STOP
 cases.push_back(event(2,21,11)); // unknown instance
 cases.push_back(event(1,20,10)); // duplicate START
 auto invalid=event(1,22,0);invalid.fields[L"ParentProcessID"]=0;cases.push_back(invalid); // rejected at parent first
 auto zero=event(1,23,0);cases.push_back(zero); // also parent first with existing root rule
 auto decode=event(1,24,15);decode.fields.erase(L"ProcessID");cases.push_back(decode);
 cases.push_back(event(2,20,10)); // duplicate STOP
 auto ex=event(1,25,16);ex.throwing=true;cases.push_back(ex);
 cases.push_back(event(1,26,17,999)); // parent unknown before later arrival
 cases.push_back(event(1,999,16)); // admit that parent later, no reconsideration
 auto seq=event(2,999,16);seq.fields[L"ProcessSequenceNumber"]=8;cases.push_back(seq); // contradiction still faults
 for(auto e:cases){
  authority_old::Event(&e);authority_new::Event(&e);
  check(authority_old::snapshot()==authority_new::snapshot());check(authority_old::queries==authority_new::queries);
  detailed_old::LifecycleEvent(&e);detailed_new::LifecycleEvent(&e,99);
  check(detailed_old::snapshot()==detailed_new::snapshot());check(detailed_old::queries==detailed_new::queries);
 }
 check(j6w::buffer.count==cases.size()*2);
 check(j6w::buffer.records[0].disposition==j6w::ADMITTED);
 check(j6w::buffer.records[2].disposition==j6w::UNKNOWN_PARENT&&!j6w::buffer.records[2].parentKnown);
 check(j6w::buffer.records[4].disposition==j6w::ADMITTED&&j6w::buffer.records[4].instanceKnown);
 check(j6w::buffer.records[6].disposition==j6w::UNKNOWN_INSTANCE&&!j6w::buffer.records[6].instanceKnown);
 check(j6w::buffer.records[8].disposition==j6w::DUPLICATE_EVENT);
 check(j6w::buffer.records[14].disposition==j6w::DECODE_FAILURE);
 check(j6w::buffer.records[18].disposition==j6w::OTHER_EXPLICIT_REJECTION);
 check(j6w::buffer.records[20].parentKnown==0); // snapshot retained after parent admitted
 for(std::size_t i=0;i<j6w::buffer.count;++i){check(j6w::buffer.records[i].complete);check(j6w::buffer.records[i].sequence==i+1);check(j6w::buffer.records[i].callbackQpc==99);}
 // Exercise the existing invalid identity branch without changing its ordering.
 authority_old::rootCreated=0;authority_new::rootCreated=0;auto z=event(1,27,0);
 authority_old::Event(&z);authority_new::Event(&z);check(authority_old::snapshot()==authority_new::snapshot());check(j6w::buffer.records[j6w::buffer.count-1].disposition==j6w::INVALID_IDENTITY);
 // Lifecycle-only scope: provider mismatch and non-lifecycle IDs add no records.
 auto count=j6w::buffer.count;auto unrelated=event(3,99,99);authority_new::Event(&unrelated);detailed_new::LifecycleEvent(&unrelated,99);unrelated.EventHeader.ProviderId=2;unrelated.EventHeader.EventDescriptor.Id=1;authority_new::Event(&unrelated);detailed_new::LifecycleEvent(&unrelated,99);check(count==j6w::buffer.count);
 j6w::Buffer<2> small;auto*r=small.begin(1,100,200);r->pid=42;r->complete=true;small.begin(2,101,201);check(small.begin(1,102,202)==nullptr);check(small.overflow&&small.attempted==3&&small.count==2);check(small.records[0].pid==42&&small.records[0].sequence==1);check(small.begin(1,103,203)==nullptr&&small.attempted==4);
 std::cout<<"{\"checks\":"<<checks<<",\"status\":\"PASS\",\"records\":"<<j6w::recordsJson(j6w::buffer)<<"}\n";
}
