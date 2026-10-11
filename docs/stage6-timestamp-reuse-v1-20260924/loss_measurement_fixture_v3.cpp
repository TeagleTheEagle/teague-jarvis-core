// Offline source-derived branch equivalence only. No tracing/session creation.
#define NOMINMAX
#include "trace_telemetry.hpp"
#include <evntcons.h>
#include <map>
#include <vector>
#include <string>
#include <iostream>
#include <stdexcept>
#include <cstdlib>
#include <new>
static unsigned long long allocations=0;
void* operator new(size_t n){++allocations;if(auto p=malloc(n?n:1))return p;throw std::bad_alloc();}
void operator delete(void*p) noexcept {free(p);}
void operator delete(void*p,size_t) noexcept {free(p);}
namespace fixture {
using U=unsigned long long;
static const GUID Provider={1},FileProvider={2},RegProvider={3},ClassicReg={4},ThreadProvider={5};
struct Row{DWORD pid=0,parent=0;U created=0,sequence=0,parentSequence=0,exitFT=0;DWORD exitCode=0;bool exitCodeKnown=false;long long start=0,notified=0,stop=0,stopNotified=0;unsigned version=0,stopVersion=0;std::wstring image;std::vector<int> schema,stopSchema;};
std::map<std::pair<DWORD,U>,Row> rows;
std::mutex guard;
unsigned faults=0,discarded=0;int calls=0,throwAt=0,captures=0,acquires=0;
bool parentKnown=true;
std::map<std::wstring,std::pair<U,bool>> fields;
std::vector<std::string> operations;
void step(const std::string&x){operations.push_back(x);if(++calls==throwAt)throw std::runtime_error("controlled dependency failure");}
U Number(EVENT_RECORD*,const wchar_t* n,bool*ok=nullptr){std::wstring w(n);step("number:"+std::string(w.begin(),w.end()));auto v=fields.at(w);if(ok)*ok=v.second;return v.second?v.first:0;}
bool ParentKnown(DWORD,U,U){step("parent");return parentKnown;}
std::wstring Text(EVENT_RECORD*,const wchar_t*){step("text");return L"synthetic";}
std::vector<int> Schemas(EVENT_RECORD*){step("schema");return {1,2};}
long long Q(){return 100;}
void Capture(const Row&,bool start){step(start?"capture-start":"capture-stop");++captures;}
void Acquire(Row&){step("acquire");++acquires;}
void reset(int scenario,int fail){
 rows.clear();faults=discarded=0;calls=captures=acquires=0;throwAt=fail;parentKnown=true;operations.clear();
 fields={{L"ProcessID",{19,true}},{L"CreateTime",{23,true}},{L"ParentProcessID",{7,true}},{L"ParentProcessSequenceNumber",{11,true}},{L"ProcessSequenceNumber",{13,true}},{L"ExitTime",{71,true}},{L"ExitCode",{0,true}}};
 if(scenario==1||scenario==9)parentKnown=false;
 if(scenario==4)fields[L"CreateTime"]={0,true};
 if(scenario==5||scenario==9)fields[L"ProcessID"]={0,false};
 if(scenario==10)fields[L"ParentProcessID"]={0,false};
 if(scenario==3||scenario==7||scenario==8||scenario==11){Row r;r.pid=19;r.created=23;r.sequence=13;if(scenario==7)r.stop=9;if(scenario==8){r.sequence=99;r.exitFT=99;r.exitCodeKnown=true;r.exitCode=3;}rows[{19,23}]=r;}
 if(scenario==6)for(unsigned i=0;i<8192;i++)rows[{1000+i,23}]=Row{};
 j6m::lifecycleTap.count=0;j6m::lifecycleTap.attempted=0;j6m::lifecycleTap.overflow=0;j6m::handoffErrors=0;j6m::lifecycleTap.enabled=true;
}
std::string state(){std::ostringstream s;s<<faults<<','<<discarded<<','<<captures<<','<<acquires<<','<<rows.size();for(auto&a:rows){auto&r=a.second;s<<';'<<a.first.first<<','<<a.first.second<<','<<r.pid<<','<<r.parent<<','<<r.created<<','<<r.sequence<<','<<r.parentSequence<<','<<r.start<<','<<r.stop<<','<<r.exitFT<<','<<r.exitCode<<','<<r.exitCodeKnown<<','<<r.schema.size()<<','<<r.stopSchema.size();}return s.str();}
}
#include "callback-bodies.inc"
static unsigned checks=0,cases=0;
static void check(bool ok,const char*why){++checks;if(!ok)throw std::runtime_error(why);}
using Callback=void(WINAPI*)(EVENT_RECORD*);
static void compare(Callback oldFn,Callback newFn,int scenario,int fail){
 EVENT_RECORD e{};e.EventHeader.ProviderId=fixture::Provider;e.EventHeader.EventDescriptor.Id=(scenario==2||scenario==7||scenario==8||scenario==11)?2:1;e.EventHeader.EventDescriptor.Version=4;e.EventHeader.ThreadId=81;e.EventHeader.TimeStamp.QuadPart=1;
 fixture::reset(scenario,fail);oldFn(&e);auto state=fixture::state();auto ops=fixture::operations;
 fixture::reset(scenario,fail);newFn(&e);++cases;
 check(state==fixture::state(),"selector / authority state differs");check(ops==fixture::operations,"existing dependency ordering/query differs");
 check(j6m::lifecycleTap.count==1,"one eligible record");check(j6m::lifecycleComplete(),"handoff complete");
 auto&r=j6m::lifecycleTap.records[0];check(r.arrivalQpc<=r.completionQpc,"monotonic completion");check(r.eventQpc==1&&r.thread==81&&r.version==4,"event identity");check(r.completionQpc-r.arrivalQpc>=0,"body duration");check(r.arrivalQpc-r.eventQpc>=0,"delivery lag");
 if(fail&&fail<=fixture::calls){check(r.disposition==j6m::Disposition::ExceptionCaught,"exception disposition");if(fail==1)check(r.valid==0,"exception before decode");if(fail==2)check(r.valid==j6m::PID_VALID,"exception after pid");if(!fixture::operations.empty()&&fixture::operations.back().find("capture-")==0)check((r.reserved&j6m::AUTHORITATIVE_ATTEMPT)&&!(r.reserved&j6m::AUTHORITATIVE_RETURNED),"partial authoritative attempt retained");if(!fixture::operations.empty()&&fixture::operations.back()=="acquire")check((r.reserved&j6m::HANDLE_ATTEMPT)&&!(r.reserved&j6m::HANDLE_RETURNED),"partial handle attempt retained");return;}
 j6m::Disposition expected=j6m::Disposition::ADMITTED;
 switch(scenario){case 1:case 9:expected=j6m::Disposition::UNKNOWN_PARENT;break;case 2:expected=j6m::Disposition::UNKNOWN_PROCESS_INSTANCE;break;case 3:case 7:expected=j6m::Disposition::DuplicateRecord;break;case 4:expected=j6m::Disposition::INVALID_IDENTITY;break;case 5:expected=j6m::Disposition::DECODE_FAILURE;break;case 6:expected=j6m::Disposition::OTHER_EXPLICIT_REJECTION;break;}
 check(r.disposition==expected,"exact disposition");
 check(r.pid==(scenario==5||scenario==9?0:19)&&r.created==(scenario==4?0:23),"identity values");
 if(scenario==9)check(!(r.valid&j6m::PID_VALID)&&(r.reserved&j6m::PID_DECODE),"unknown parent precedence with invalid pid");
 if(scenario==10)check(!(r.valid&j6m::PARENT_VALID)&&(r.reserved&j6m::PARENT_DECODE),"no inferred parent validity");
 if(scenario==6)check(r.reserved&j6m::CAPACITY,"capacity reason");
 if(scenario==8)check((r.reserved&(j6m::SEQUENCE_CONTRADICTION|j6m::EXIT_TIME_CONTRADICTION|j6m::EXIT_CODE_CONTRADICTION))==(j6m::SEQUENCE_CONTRADICTION|j6m::EXIT_TIME_CONTRADICTION|j6m::EXIT_CODE_CONTRADICTION),"fault and continue facts");
 if(scenario==0||scenario==11)check(r.sequence==13&&(r.valid&j6m::SEQUENCE_VALID),"process sequence");
}
extern "C" __declspec(noinline) void clock_path(unsigned disposition){
 j6t::CallbackScope timing;timing.lifecycle.start(timing.begin,1,1,4,81);timing.lifecycle.finish(static_cast<j6m::Disposition>(disposition));
}
int main(){try{
 for(auto pair:{std::make_pair(old_authority::Event,new_authority::Event),std::make_pair(old_detail::Event,new_detail::Event)}){
  for(int scenario=0;scenario<12;scenario++)compare(pair.first,pair.second,scenario,0);
  for(int scenario:{0,11}){fixture::reset(scenario,0);EVENT_RECORD e{};e.EventHeader.ProviderId=fixture::Provider;e.EventHeader.EventDescriptor.Id=scenario==11?2:1;pair.first(&e);int n=fixture::calls;for(int fail=1;fail<=n;fail++)compare(pair.first,pair.second,scenario,fail);}
  for(int id:{0,3,9}){fixture::reset(0,0);EVENT_RECORD e{};e.EventHeader.ProviderId=fixture::Provider;e.EventHeader.EventDescriptor.Id=USHORT(id);pair.second(&e);check(j6m::lifecycleTap.count==0,"nonlifecycle not fabricated");}
  fixture::reset(0,0);EVENT_RECORD wrong{};pair.second(&wrong);check(j6m::lifecycleTap.count==0,"wrong provider");
 }
 fixture::reset(0,0);auto a=allocations;for(unsigned i=0;i<8;i++)clock_path(i);check(allocations==a,"handoff allocates");check(j6m::lifecycleTap.count==8,"all explicit dispositions");
 for(size_t i=0;i<8;i++)check(j6m::lifecycleTap.records[i].localSequence==i+1,"sequence continuity");
 auto first=j6m::lifecycleTap.records[0];for(size_t i=8;i<j6m::LifecycleTap::capacity+1;i++)clock_path(0);
 check(j6m::lifecycleTap.count==j6m::LifecycleTap::capacity&&j6m::lifecycleTap.overflow==1,"capacity overflow");check(j6m::lifecycleTap.records[0].completionQpc==first.completionQpc,"no overwrite");check(!j6m::lifecycleComplete(),"overflow fails closed");
 j6m::lifecycleTap.enabled=false;auto n=j6m::lifecycleTap.attempted;clock_path(0);check(j6m::lifecycleTap.attempted==n,"disabled recorder");
 fixture::reset(0,0);{j6t::CallbackScope t;t.lifecycle.start(t.begin,1,1,4,1);}check(j6m::handoffErrors==1&&j6m::lifecycleTap.count==0,"unfinalized fails closed");
 fixture::reset(0,0);j6m::Handoff invalid;invalid.start(10,1,1,4,1);invalid.finish(j6m::Disposition::ADMITTED);invalid.publish(9);check(j6m::handoffErrors==1,"reversed time fails closed");
 fixture::reset(0,0);j6d::diagnostic.enabled=true;long long cleanupQpc=0,arrival=0;
 auto metricBefore=j6t::telemetry.metrics[j6t::Callback].ticks.load();
 {j6t::CallbackScope t;arrival=t.begin;t.lifecycle.start(t.begin,1,1,4,81);struct Cleanup{long long& q;~Cleanup(){q=j6m::tick();}} cleanup{cleanupQpc};t.lifecycle.finish(j6m::Disposition::ADMITTED);}
 auto record=j6m::lifecycleTap.records[0];check(record.completionQpc>=cleanupQpc,"body local cleanup included");check(record.arrivalQpc==arrival,"existing arrival reused");
#ifndef J6_REFERENCE_TEST
 check(record.completionQpc==j6d::diagnostic.lastCallback.load(),"same existing completion reused");check(j6t::telemetry.metrics[j6t::Callback].ticks.load()-metricBefore==static_cast<unsigned long long>(record.completionQpc-record.arrivalQpc),"duration equals existing callback metric");
#endif
 check(j6d::diagnostic.activeCallback.load()==0,"existing bookkeeping completed before inspection");j6d::diagnostic.enabled=false;
 fixture::reset(0,0);j6m::Handoff zeros;zeros.start(1,0,1,4,1);zeros.pid(0,true);zeros.created(0,true);zeros.parent(0,true);zeros.sequence(0,true);zeros.parentSequence(0,true);zeros.finish(j6m::Disposition::ADMITTED);zeros.publish(2);check(j6m::lifecycleTap.records[0].valid==31,"zero decoded fields remain valid");
 fixture::reset(0,0);SetLastError(54321);j6m::Handoff absent;absent.start(1,0,1,4,1);absent.finish(j6m::Disposition::UNKNOWN_PROCESS_INSTANCE);absent.publish(2);check(GetLastError()==54321,"handoff LastError preservation");check(j6m::lifecycleTap.records[0].valid==0,"unavailable fields explicit");
 std::cout<<"{\"status\":\"PASS\",\"checks\":"<<checks<<",\"sourceDerivedCases\":"<<cases<<",\"liveETW\":false,\"handoffBytes\":"<<sizeof(j6m::Handoff)<<"}"<<std::endl;return 0;
 }catch(const std::exception&e){std::cerr<<"{\"status\":\"FAIL\",\"checks\":"<<checks<<",\"error\":\""<<e.what()<<"\"}"<<std::endl;return 97;}}
