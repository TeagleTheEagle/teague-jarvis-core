#include "trace_telemetry.hpp"
#include <iostream>
#include <fstream>
#include <cassert>
static std::atomic<ULONG> lost{0},status{0};
static ULONG WINAPI fake(TRACEHANDLE,LPCWSTR,PEVENT_TRACE_PROPERTIES p,ULONG code){assert(code==EVENT_TRACE_CONTROL_QUERY);p->EventsLost=lost;p->RealTimeBuffersLost=0;p->LogBuffersLost=0;p->NumberOfBuffers=32;p->FreeBuffers=31;p->BuffersWritten=4;return status;}
int main(int argc,char**argv){
 if(argc!=2)return 90;LARGE_INTEGER hz;QueryPerformanceFrequency(&hz);auto&d=j6d::diagnostic;
 d.bind(L"synthetic-telemetry-v2",L"J6SyntheticAuthority","authority",hz.QuadPart,"{}");d.consumer=GetCurrentThread();
 d.sample(0,fake);lost=3;d.enter(100);d.callback(100,110,true,90);d.enter(200);d.callback(200,230,false,0);d.queueState(7,1200,1);d.admitted=1;d.sample(0,fake);lost=13;d.sample(0,fake);
 assert(d.samples[0].lost==0&&d.samples[1].lost==3&&d.samples[2].lost==13);
 assert(d.samples[1].delta==2&&d.samples[1].durations.count==2&&d.samples[1].durations.total==40&&d.samples[1].selected==1);
 assert(d.samples[1].lag.count==1&&d.samples[1].lag.max==10);assert(d.queueHighItems==7&&d.queueHighBytes==1200);
 auto b=j6d::tick();d.span(j6d::Metadata,b,b+hz.QuadPart/100,d.queue(),d.sampleSequence);d.span(j6d::GuardWait,b,b+hz.QuadPart/50,d.queue(),d.sampleSequence);
 assert(d.slow.size()==2&&d.slow[0].op==j6d::Metadata&&d.slow[1].op==j6d::GuardWait);
 // Synthetic callback benchmark: same existing wrapper, enabled versus disabled. No ETW sessions.
 constexpr unsigned n=300000;double enabled[3]{},disabled[3]{};long long maxCall=0;
 for(int trial=0;trial<3;trial++){
  d.enabled=false;auto start=j6d::tick();for(unsigned i=0;i<n;i++){j6t::CallbackScope scope;scope.selected=true;}disabled[trial]=double(j6d::tick()-start)/hz.QuadPart;
  d.enabled=true;start=j6d::tick();for(unsigned i=0;i<n;i++){auto call=j6d::tick();{j6t::CallbackScope scope;scope.selected=true;scope.eventQpc=call;}maxCall=std::max(maxCall,j6d::tick()-call);}enabled[trial]=double(j6d::tick()-start)/hz.QuadPart;
 }
 d.sample(0,fake);std::ofstream normal(std::string(argv[1])+"/normal.json");normal<<d.json();normal.close();
 // Query failure remains null loss, not a fabricated zero. Never emits acceptance PASS.
 status=5;d.sample(0,fake);assert(d.errors>0);std::ofstream failure(std::string(argv[1])+"/query-failure.json");failure<<d.json();failure.close();
 for(unsigned i=0;i<j6d::Diagnostic::slowCap+1;i++)d.span(j6d::ProcessImage,b,b+hz.QuadPart,d.queue(),0);
 assert(d.slow.size()==j6d::Diagnostic::slowCap&&d.overflow>0);
 d.samples.resize(j6d::Diagnostic::sampleCap);auto count=d.samples.size();d.sample(0,fake);assert(d.samples.size()==count&&d.overflow>1);
 d.consumer=nullptr; // GetCurrentThread pseudo-handle was never owned.
 status=0;lost=0;
 {j6d::Diagnostic concurrent;concurrent.bind(L"synthetic-telemetry-v2",L"J6SyntheticDetail","detail",hz.QuadPart,"{}");concurrent.start(0,GetCurrentThread(),fake);
  auto until=j6d::tick()+hz.QuadPart/2;while(j6d::tick()<until){auto q=j6d::tick();concurrent.enter(q);concurrent.callback(q,j6d::tick(),true,q);}
  concurrent.stop();assert(!concurrent.sampler.joinable()&&!concurrent.consumer&&concurrent.errors==0&&concurrent.samples.size()>=4);
  std::ofstream output(std::string(argv[1])+"/concurrent.json");output<<concurrent.json();
 }
 std::cout<<"{\"assertions\":12,\"callbacksPerTrial\":"<<n<<",\"trials\":3,\"disabledSeconds\":["<<disabled[0]<<','<<disabled[1]<<','<<disabled[2]<<"],\"enabledSeconds\":["<<enabled[0]<<','<<enabled[1]<<','<<enabled[2]<<"],\"maxInstrumentedCallSeconds\":"<<double(maxCall)/hz.QuadPart<<",\"allocatedBytes\":"<<(j6d::Diagnostic::sampleCap*sizeof(j6d::Sample)+j6d::Diagnostic::slowCap*sizeof(j6d::Slow))<<"}";
}
