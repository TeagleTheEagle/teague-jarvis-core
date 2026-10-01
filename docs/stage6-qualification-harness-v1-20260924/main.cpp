// One executable, no live trace APIs, no benchmark executed by --selftest.
#define NOMINMAX
#include "api.hpp"
#include "protocol_hash.hpp"
#include <iostream>
#include <vector>
#include <string>
#include <stdexcept>
#include <algorithm>
#include <cstdlib>
#include <new>
unsigned long long allocationCount=0;
void* operator new(size_t n){++allocationCount;if(auto p=malloc(n?n:1))return p;throw std::bad_alloc();}
void operator delete(void*p) noexcept{free(p);}
void operator delete(void*p,size_t) noexcept{free(p);}
using U=unsigned long long;
U ft(FILETIME x){return (U(x.dwHighDateTime)<<32)|x.dwLowDateTime;}
struct CPU{U kernel,user;DWORD tid;};
CPU cpu(){FILETIME a,b,k,u;if(!GetThreadTimes(GetCurrentThread(),&a,&b,&k,&u))throw std::runtime_error("CPU_API_FAILURE");return {ft(k),ft(u),GetCurrentThreadId()};}
long long qpc(){LARGE_INTEGER q;if(!QueryPerformanceCounter(&q))throw std::runtime_error("QPC_API_FAILURE");return q.QuadPart;}
static U frequency=0;static unsigned checks=0;
void check(bool ok,const char*msg){++checks;if(!ok)throw std::runtime_error(msg);}
unsigned expected(unsigned s){switch(s){case 0:case 1:return 0;case 2:return 1;case 3:return 2;case 4:case 5:return 3;case 6:return 4;case 7:return 5;case 8:return 7;case 9:return 6;default:return 7;}}
Outcome runChunk(Arm arm,unsigned ordinal,unsigned n){unsigned s=ordinal%11,ch=(ordinal/11)%2;arm.prepare(s,ch,n);for(unsigned i=0;i<n;i++)arm.dispatch(i);auto o=arm.finish();if(arm.name[0]!='A'){check(o.records==(s==10?0:n),"record count");check(o.overflow==0&&o.handoffErrors==0&&o.timing,"record state");if(o.records)check(o.disposition==expected(s),"disposition");}return o;}
struct Chunk{unsigned scenario,channel,count;CPU begin,end;long long wallBegin,wallEnd;Outcome outcome;};
struct Trial{U callbacks=0,cpuTicks=0,wallTicks=0,digest=0;std::vector<Chunk> chunks;};
Trial measure(Arm arm,unsigned n){Trial t;t.chunks.reserve((n+8191)/8192);DWORD tid=GetCurrentThreadId();unsigned ordinal=0;
 while(t.callbacks<n){unsigned count=unsigned(std::min<U>(8192,n-t.callbacks));unsigned s=ordinal%11,ch=(ordinal/11)%2;
  arm.prepare(s,ch,count);auto a=cpu();auto w0=qpc();for(unsigned i=0;i<count;i++)arm.dispatch(i);auto w1=qpc();auto b=cpu();auto o=arm.finish();
  if(a.tid!=tid||b.tid!=tid||b.kernel<a.kernel||b.user<a.user||w1<w0)throw std::runtime_error("COUNTER_OR_THREAD_IDENTITY");
  if(o.allocations)throw std::runtime_error("CALLBACK_CPP_ALLOCATION");
  if(arm.name[0]!='A'&&(o.records!=(s==10?0:count)||o.overflow||o.handoffErrors||!o.timing||(o.records&&o.disposition!=expected(s))))throw std::runtime_error("RECORD_INTEGRITY");
  t.cpuTicks+=b.kernel-a.kernel+b.user-a.user;t.wallTicks+=U(w1-w0);t.callbacks+=count;t.digest=(t.digest^o.hash)*1099511628211ULL;
  t.chunks.push_back({s,ch,count,a,b,w0,w1,o});++ordinal;
 }return t;
}
void selftest(){Arm arms[]={arm_A(),arm_B(),arm_C()};
 check(arms[0].scopeSize()<arms[2].scopeSize(),"true baseline excludes payload");check(arms[1].scopeSize()==arms[2].scopeSize(),"reference same handoff");
 for(unsigned ordinal=0;ordinal<22;ordinal++){
  auto a=runChunk(arms[0],ordinal,4);auto b=runChunk(arms[1],ordinal,4);auto c=runChunk(arms[2],ordinal,4);
  check(a.hash==b.hash&&a.hash==c.hash,"identical input and selection output");check(a.queries==b.queries&&a.queries==c.queries,"identical decode calls");
  check(a.records==0&&a.attempted==0,"baseline no recorder");check(!a.allocations&&!b.allocations&&!c.allocations,"no counted C++ callback allocation");
  auto old=runChunk(arms[0],ordinal,4);check(old.hash==a.hash,"no cross-arm state leak/reset");
 }
 // Capacity correctness, deliberately repeats a rejection without re-preparing: no map or mutable decision changes.
 arms[2].prepare(2,0,1);for(unsigned i=0;i<16385;i++)arms[2].dispatch(0);auto full=arms[2].finish();check(full.records==16384&&full.attempted==16385&&full.overflow==1,"bounded capacity");
 arms[0].prepare(2,0,1);auto beforeA=arms[0].finish();arms[2].prepare(0,0,1);auto afterA=arms[0].finish();check(beforeA.hash==afterA.hash,"recorder reset cannot change A");
 for(auto arm:arms){auto warm=runChunk(arm,2,3);auto tiny=measure(arm,7);check(warm.queries>0&&tiny.callbacks==7&&tiny.chunks.size()==1,"warmup excluded / measured count");check(tiny.chunks[0].begin.tid==GetCurrentThreadId()&&tiny.chunks[0].end.tid==GetCurrentThreadId(),"measurement thread identity");}
 std::cout<<"{\"schema\":\"j6.qualification.selftest.v1\",\"status\":\"PASS\",\"checks\":"<<checks<<",\"scopeA\":"<<arms[0].scopeSize()<<",\"scopeB\":"<<arms[1].scopeSize()<<",\"scopeC\":"<<arms[2].scopeSize()<<",\"benchmarkExecuted\":false}"<<std::endl;
}
void benchmark(){Arm arms[]={arm_A(),arm_B(),arm_C()};const char*schedule[]={"ABC","BCA","CAB","ACB","CBA","BAC"};FILETIME a,b,k,u;if(!GetProcessTimes(GetCurrentProcess(),&a,&b,&k,&u))throw std::runtime_error("PROCESS_IDENTITY");
 std::cout<<"{\"kind\":\"header\",\"schema\":\"j6.final-overhead.raw.v1\",\"protocolSHA256\":\""<<protocolHash<<"\",\"pid\":"<<GetCurrentProcessId()<<",\"created\":"<<ft(a)<<",\"tid\":"<<GetCurrentThreadId()<<",\"frequency\":"<<frequency<<"}"<<std::endl;
 for(unsigned block=0;block<60;block++){U expectedDigest=0;for(unsigned position=0;position<3;position++){
  unsigned index=unsigned(schedule[block%6][position]-'A');Arm arm=arms[index];unsigned done=0,ordinal=0;
  while(done<20000){unsigned n=std::min(8192U,20000-done);runChunk(arm,ordinal++,n);done+=n;}
  auto t=measure(arm,1000000);if(!t.cpuTicks||!t.wallTicks)throw std::runtime_error("ZERO_PRIMARY_COUNTER");if(position&&t.digest!=expectedDigest)throw std::runtime_error("CROSS_ARM_WORKLOAD_MISMATCH");expectedDigest=t.digest;
  std::cout<<"{\"kind\":\"trial\",\"block\":"<<block<<",\"position\":"<<position<<",\"arm\":\""<<arm.name<<"\",\"warmup\":20000,\"callbacks\":"<<t.callbacks<<",\"cpu100ns\":"<<t.cpuTicks<<",\"wallTicks\":"<<t.wallTicks<<",\"workloadDigest\":"<<t.digest<<",\"chunks\":[";
  for(size_t i=0;i<t.chunks.size();i++){auto&x=t.chunks[i];if(i)std::cout<<',';std::cout<<"["<<x.scenario<<','<<x.channel<<','<<x.count<<','<<x.begin.kernel<<','<<x.begin.user<<','<<x.end.kernel<<','<<x.end.user<<','<<x.begin.tid<<','<<x.end.tid<<','<<x.wallBegin<<','<<x.wallEnd<<','<<x.outcome.hash<<"]";}
  std::cout<<"]}"<<std::endl;
 }}std::cout<<"{\"kind\":\"complete\",\"blocks\":60,\"trials\":180,\"callbacks\":180000000,\"warmup\":3600000}"<<std::endl;
}
int main(int argc,char**argv){try{LARGE_INTEGER f;if(!QueryPerformanceFrequency(&f)||f.QuadPart<=0)throw std::runtime_error("FREQUENCY");frequency=U(f.QuadPart);
 if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}
 if(argc==3&&std::string(argv[1])=="--qualify"&&std::string(argv[2])==protocolHash){benchmark();return 0;}
 std::cerr<<"REJECTED_ARGUMENT_OR_PROTOCOL"<<std::endl;return 90;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 97;}catch(...){std::cerr<<"UNEXPECTED_EXCEPTION"<<std::endl;return 98;}}
