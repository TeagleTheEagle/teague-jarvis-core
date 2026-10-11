#include "trace_telemetry.hpp"
#include <thread>
#include <vector>
#include <iostream>
#include <memory>
static unsigned checks=0;
#define CHECK(x) do{++checks;if(!(x)){std::cerr<<"FAIL "<<__LINE__<<"\n";return 1;}}while(0)
ULONG WINAPI fake(TRACEHANDLE,LPCWSTR,PEVENT_TRACE_PROPERTIES p,ULONG action){
 if(action!=EVENT_TRACE_CONTROL_QUERY||p->Wnode.BufferSize<sizeof(*p)||p->BufferSize||p->MinimumBuffers||p->MaximumBuffers)return ERROR_INVALID_PARAMETER;
 p->EventsLost=4;p->RealTimeBuffersLost=3;p->LogBuffersLost=2;p->NumberOfBuffers=64;p->FreeBuffers=7;p->BuffersWritten=91;return 0;
}
ULONG WINAPI denied(TRACEHANDLE,LPCWSTR,PEVENT_TRACE_PROPERTIES,ULONG){return ERROR_ACCESS_DENIED;}
int main(){
 auto t=std::make_unique<j6t::Telemetry>();t->query(0,L"synthetic","test",fake);
 CHECK(t->snapshotCount==1);CHECK(t->errors==0);CHECK(t->snapshots[0].events==4);CHECK(t->snapshots[0].real==3);CHECK(t->snapshots[0].log==2);CHECK(t->snapshots[0].buffers==64);CHECK(t->snapshots[0].free==7);CHECK(t->snapshots[0].written==91);CHECK(t->snapshots[0].end>=t->snapshots[0].begin);
 t->query(0,L"synthetic","denied",denied);CHECK(t->errors==1);CHECK(t->snapshots[1].status==ERROR_ACCESS_DENIED);CHECK(t->snapshots[1].events==0);
 for(unsigned i=2;i<t->snapshotLimit;++i)t->query(0,L"synthetic","bound",fake);
 t->query(0,L"synthetic","overflow",fake);CHECK(t->snapshotCount==t->snapshotLimit);CHECK(t->errors==2);
 for(unsigned i=0;i<t->phaseLimit+1;++i)t->phase("bound",1,2);CHECK(t->phaseCount==t->phaseLimit+1);CHECK(t->errors==3);
 std::vector<std::thread> threads;std::mutex guard;
 for(int i=0;i<4;++i)threads.emplace_back([&]{for(int n=0;n<2500;++n){j6t::CallbackScope c;c.selected=n%2==0;j6t::Lock l(guard);j6t::Scope m(j6t::Metadata);}});
 for(auto&th:threads)th.join();
 CHECK(j6t::telemetry.callbacks==10000);CHECK(j6t::telemetry.selected==5000);CHECK(j6t::telemetry.rejected==5000);CHECK(j6t::telemetry.firstCallback>0);CHECK(j6t::telemetry.metrics[j6t::Callback].count==10000);CHECK(j6t::telemetry.metrics[j6t::GuardWait].count==10000);CHECK(j6t::telemetry.metrics[j6t::GuardHold].count==10000);CHECK(j6t::telemetry.metrics[j6t::Metadata].count==10000);
 CHECK(j6t::measure(j6t::Admission,[]{return 42;})==42);CHECK(j6t::telemetry.metrics[j6t::Admission].count==1);
 auto text=t->json();CHECK(text.find("stage6-loss-telemetry-v1")!=text.npos);CHECK(text.find("\"errors\":3")!=text.npos);
 std::cout<<"{\"checks\":"<<checks<<",\"status\":\"PASS\",\"concurrentCallbacks\":10000}";return 0;
}
