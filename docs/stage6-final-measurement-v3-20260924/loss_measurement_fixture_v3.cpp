// OFFLINE ONLY: TDH manifest decoding + synthetic callback replay. Never starts an ETW session.
#define NOMINMAX
#include "loss_measurement_v3.hpp"
#include <evntcons.h>
#include <tdh.h>
#include <psapi.h>
#include <iostream>
#include <vector>
#include <algorithm>
#include <mutex>
#include <memory>
#include <cmath>
#include <atomic>
#include <cstdlib>
#include <new>
static std::atomic<unsigned long long> allocations{0};
void* operator new(size_t n){++allocations;if(auto p=malloc(n?n:1))return p;throw std::bad_alloc();}
void operator delete(void* p) noexcept {free(p);}
void operator delete(void* p,size_t) noexcept {free(p);}
using U=unsigned long long;
static const GUID provider={0x22fb2cd6,0x0e7b,0x422b,{0xa0,0xc7,0x2f,0xad,0x1f,0xd0,0xe7,0x16}};
static U ft(FILETIME x){return (U(x.dwHighDateTime)<<32)|x.dwLowDateTime;}
static U cpu(bool thread){FILETIME a,b,k,u;BOOL ok=thread?GetThreadTimes(GetCurrentThread(),&a,&b,&k,&u):GetProcessTimes(GetCurrentProcess(),&a,&b,&k,&u);if(!ok)throw std::runtime_error("CPU query");return ft(k)+ft(u);}
// Same TDH property calls and allocation form as the inspected observer's Field/Number.
static U number(EVENT_RECORD* e,const wchar_t* name){PROPERTY_DATA_DESCRIPTOR p{};p.PropertyName=reinterpret_cast<ULONGLONG>(name);p.ArrayIndex=ULONG_MAX;ULONG n=0;auto r=TdhGetPropertySize(e,0,nullptr,1,&p,&n);if(r||n>65536||(n!=4&&n!=8))throw std::runtime_error("Offline manifest decode unavailable");std::vector<BYTE> v(n);if(TdhGetProperty(e,0,nullptr,1,&p,n,v.data()))throw std::runtime_error("Offline property read");U value=0;memcpy(&value,v.data(),n);return value;}
static volatile U observable=0;
static std::mutex mapGuard;
static void dispatch(EVENT_RECORD* e,j6m::LifecycleTap& tap){
 auto arrival=j6m::tick();
 auto pid=number(e,L"ProcessID");auto created=number(e,L"CreateTime");
 auto wait=j6m::tick();mapGuard.lock();auto held=j6m::tick();
 auto parent=number(e,L"ParentProcessID");auto ps=number(e,L"ParentProcessSequenceNumber");
 // Replay the real unknown-parent branch, with no OpenProcess or selected-output filesystem access.
 observable=pid^created^parent^ps^U(wait)^U(held);
 mapGuard.unlock();
 if(tap.enabled){j6m::Lifecycle v;v.eventQpc=e->EventHeader.TimeStamp.QuadPart;v.arrivalQpc=arrival;v.completionQpc=j6m::tick();v.pid=unsigned(pid);v.created=created;v.parentPid=unsigned(parent);v.parentSequence=ps;v.eventId=1;v.version=4;v.valid=j6m::PID_VALID|j6m::CREATED_VALID|j6m::PARENT_VALID|j6m::PARENT_SEQUENCE_VALID;v.disposition=j6m::Disposition::UNKNOWN_PARENT;tap.append(v);}
 // Existing observer bookkeeping has its own completion clock; retained in both modes.
 observable^=U(j6m::tick());
}
static void check(bool b,const char* m,unsigned& checks){if(!b)throw std::runtime_error(m);++checks;}
static unsigned tests(){
 unsigned checks=0;auto tap=std::make_unique<j6m::LifecycleTap>();j6m::Lifecycle v;v.pid=19;v.created=23;
 auto before=allocations.load();tap->append(v);check(tap->count==0,"disabled",checks);tap->enabled=true;
 for(size_t i=0;i<tap->capacity;i++)tap->append(v);
 check(tap->count==tap->capacity,"capacity",checks);check(tap->complete(),"complete",checks);
 auto first=tap->records[0];tap->append(v);check(tap->overflow==1&&!tap->complete(),"overflow explicit",checks);
 check(tap->records[0].localSequence==first.localSequence&&tap->records[0].pid==19,"no overwrite",checks);
 check(allocations.load()==before,"no tap allocations",checks);
 check(tap->records.back().localSequence==tap->capacity,"recorder sequence",checks);
 check(tap->records[0].valid==0,"optional not decoded",checks);
 SetLastError(12345);tap->append(v);check(GetLastError()==12345,"append preserves LastError",checks);
 auto c=std::make_unique<j6m::Coordination>();c->enabled=true;c->frequency=10000000;
 c->append(j6m::Operation::Attributes,0,10000,1,0,0,true);check(c->count==0,"strict over 1ms",checks);
 c->append(j6m::Operation::Attributes,0,10001,1,0,5,false);check(c->count==1,"slow captured",checks);
 auto t=c->totals[size_t(j6m::Operation::Attributes)];check(t.count==2&&t.success==1&&t.failure==1&&t.total==20001,"counts",checks);
 c->append(j6m::Operation::Attributes,2,1,1,0,0,true);check(c->overflow==1,"invalid time explicit",checks);
 return checks;
}
struct Trial{bool enabled;U count,threadTicks,processTicks,allocated;double wall;long long p50,p95,p99,maximum;SIZE_T peakWorkingSet;};
static Trial trial(EVENT_RECORD& e,j6m::LifecycleTap& tap,bool enabled,U n,long long frequency){
 tap.enabled=enabled;tap.count=0;tap.attempted=0;tap.overflow=0;std::array<long long,4096> latency{};size_t samples=0;
 auto alloc=allocations.load();auto pc=cpu(false);auto tc=cpu(true);auto begin=j6m::tick();long long maximum=0;
 for(U i=0;i<n;++i){
  if(tap.count==8192){observable^=tap.records[0].localSequence^tap.records[8191].localSequence;tap.count=0;tap.attempted=0;}
  // Sparse timing sample is identical in both modes; not a live-recorder reset policy.
  if(i%128==0&&samples<latency.size()){auto b=j6m::tick();dispatch(&e,tap);auto dt=j6m::tick()-b;latency[samples++]=dt;if(dt>maximum)maximum=dt;}else dispatch(&e,tap);
 }
 auto end=j6m::tick();auto thread=cpu(true)-tc;auto process=cpu(false)-pc;auto added=allocations.load()-alloc;
 std::sort(latency.begin(),latency.begin()+samples);PROCESS_MEMORY_COUNTERS pm{};GetProcessMemoryInfo(GetCurrentProcess(),&pm,sizeof(pm));
 auto q=[&](double x){return samples?latency[size_t((samples-1)*x)]:0;};
 return {enabled,n,thread,process,added,double(end-begin)/frequency,q(.5),q(.95),q(.99),maximum,pm.PeakWorkingSetSize};
}
int main(int argc,char**argv){try{
 if(argc!=2)return 90;std::string mode=argv[1];
 if(mode=="tests"){auto n=tests();std::cout<<"{\"status\":\"PASS\",\"checks\":"<<n<<",\"lifecycleBytes\":"<<sizeof(j6m::LifecycleTap)<<",\"coordinationBytes\":"<<sizeof(j6m::Coordination)<<",\"liveETW\":false}"<<std::endl;return 0;}
 if(mode!="benchmark")return 90;
 EVENT_RECORD e{};std::array<BYTE,1024> payload{};e.EventHeader.Size=sizeof(EVENT_HEADER);e.EventHeader.ProviderId=provider;e.EventHeader.EventDescriptor.Id=1;e.EventHeader.EventDescriptor.Version=4;e.EventHeader.EventDescriptor.Opcode=1;e.EventHeader.EventDescriptor.Level=4;e.EventHeader.EventDescriptor.Keyword=0x10;e.EventHeader.Flags=EVENT_HEADER_FLAG_64_BIT_HEADER;e.UserData=payload.data();e.UserDataLength=USHORT(payload.size());
 auto tap=std::make_unique<j6m::LifecycleTap>();LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);
 // Decoding must really succeed. No synthetic sleep/spin to inflate the baseline.
 for(int i=0;i<100;i++)dispatch(&e,*tap);
 auto pilot=trial(e,*tap,false,20000,freq.QuadPart);
 U n=std::max<U>(20000,std::min<U>(1000000,U(std::ceil(30000000.0/double(std::max<U>(pilot.threadTicks,1))*20000))));
 std::cout<<"{\"kind\":\"protocol\",\"fixture\":\"actual TDH property APIs; unknown-parent lifecycle decode branch\",\"sameBinary\":true,\"pairs\":8,\"iterationsPerTrial\":"<<n<<",\"pilotCpu100ns\":"<<pilot.threadTicks<<",\"screenPercent\":1,\"liveETW\":false}"<<std::endl;
 for(int pair=0;pair<8;++pair)for(int order=0;order<2;++order){bool on=(pair%2==0)?order==1:order==0;auto r=trial(e,*tap,on,n,freq.QuadPart);
 std::cout<<"{\"kind\":\"trial\",\"pair\":"<<pair<<",\"enabled\":"<<(on?"true":"false")<<",\"callbacks\":"<<r.count<<",\"dispatcherCpu100ns\":"<<r.threadTicks<<",\"processCpu100ns\":"<<r.processTicks<<",\"wallSeconds\":"<<r.wall<<",\"allocations\":"<<r.allocated<<",\"sampledLatencyTicks\":{\"p50\":"<<r.p50<<",\"p95\":"<<r.p95<<",\"p99\":"<<r.p99<<",\"max\":"<<r.maximum<<"},\"frequency\":"<<freq.QuadPart<<",\"peakWorkingSetBytes\":"<<r.peakWorkingSet<<"}"<<std::endl;
 }
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 97;}}
