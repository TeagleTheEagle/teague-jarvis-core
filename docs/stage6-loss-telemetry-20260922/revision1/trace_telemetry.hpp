#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <evntrace.h>
#include <atomic>
#include <mutex>
#include <sstream>
#include <algorithm>

// TEST-only, bounded in-memory instrumentation. No callback filesystem I/O.
namespace j6t {
inline long long now(){LARGE_INTEGER x;QueryPerformanceCounter(&x);return x.QuadPart;}
enum Metric {Callback,GuardWait,GuardHold,Metadata,Admission,Write,Flush,Close,MetricCount};
inline const char* names[]={"callback","guardWait","guardHold","metadata","admission","write","flush","close"};
struct MetricValue {
 std::atomic<unsigned long long> count{0},ticks{0},maximum{0};
 void add(unsigned long long n){++count;ticks+=n;auto old=maximum.load();while(old<n&&!maximum.compare_exchange_weak(old,n)){} }
};
struct Phase {const char* name=nullptr;long long begin=0,end=0;unsigned long status=0;};
struct Snapshot {const char* phase=nullptr;long long begin=0,end=0;ULONG status=0,events=0,real=0,log=0,buffers=0,free=0,written=0;};
class Telemetry {
public:
 static constexpr unsigned phaseLimit=128,snapshotLimit=2048;
 MetricValue metrics[MetricCount];
 std::atomic<unsigned> phaseCount{0},errors{0};
 std::atomic<unsigned long long> callbacks{0},selected{0},rejected{0};
 std::atomic<long long> firstCallback{0};
 Phase phases[phaseLimit];Snapshot snapshots[snapshotLimit];unsigned snapshotCount=0;
 long long lastQuery=0; // main/control thread only
 void phase(const char* name,long long begin,long long end,ULONG status=0){
  auto i=phaseCount.fetch_add(1);if(i>=phaseLimit){++errors;return;}phases[i]={name,begin,end,status};
 }
 template<class F> auto call(const char* name,F f){auto b=now();auto r=f();phase(name,b,now(),static_cast<ULONG>(r));return r;}
 using QueryFn=ULONG (WINAPI *)(TRACEHANDLE,LPCWSTR,PEVENT_TRACE_PROPERTIES,ULONG);
 void query(TRACEHANDLE handle,const wchar_t* session,const char* phaseName,QueryFn fn=ControlTraceW){
  if(snapshotCount>=snapshotLimit){++errors;return;}
  // Query cannot mutate the capture configuration buffer.
  alignas(EVENT_TRACE_PROPERTIES) BYTE storage[sizeof(EVENT_TRACE_PROPERTIES)+2048]{};
  auto p=reinterpret_cast<EVENT_TRACE_PROPERTIES*>(storage);
  p->Wnode.BufferSize=sizeof(storage);p->LoggerNameOffset=sizeof(EVENT_TRACE_PROPERTIES);
  Snapshot s;s.phase=phaseName;s.begin=now();s.status=fn(handle,session,p,EVENT_TRACE_CONTROL_QUERY);s.end=now();
  if(s.status)++errors;else{s.events=p->EventsLost;s.real=p->RealTimeBuffersLost;s.log=p->LogBuffersLost;s.buffers=p->NumberOfBuffers;s.free=p->FreeBuffers;s.written=p->BuffersWritten;}
  snapshots[snapshotCount++]=s;lastQuery=s.end;
 }
 void poll(TRACEHANDLE h,const wchar_t* s,long long frequency){if(now()-lastQuery>=frequency)query(h,s,"periodic");}
 std::string json(){
  LARGE_INTEGER f;QueryPerformanceFrequency(&f);std::ostringstream o;
  o<<"{\"schema\":\"stage6-loss-telemetry-v1\",\"frequency\":"<<f.QuadPart<<",\"errors\":"<<errors<<",\"callbacks\":"<<callbacks<<",\"selected\":"<<selected<<",\"rejected\":"<<rejected<<",\"firstCallbackQpc\":"<<firstCallback<<",\"phaseCapacity\":"<<phaseLimit<<",\"snapshotCapacity\":"<<snapshotLimit<<",\"phases\":[";
  for(unsigned i=0;i<std::min(phaseCount.load(),phaseLimit);++i){auto&s=phases[i];if(i)o<<',';o<<"{\"name\":\""<<s.name<<"\",\"begin\":"<<s.begin<<",\"end\":"<<s.end<<",\"status\":"<<s.status<<'}';}
  o<<"],\"snapshots\":[";for(unsigned i=0;i<snapshotCount;++i){auto&s=snapshots[i];if(i)o<<',';o<<"{\"phase\":\""<<s.phase<<"\",\"begin\":"<<s.begin<<",\"end\":"<<s.end<<",\"status\":"<<s.status<<",\"eventsLost\":"<<s.events<<",\"realtimeBuffersLost\":"<<s.real<<",\"logBuffersLost\":"<<s.log<<",\"numberOfBuffers\":"<<s.buffers<<",\"freeBuffers\":"<<s.free<<",\"buffersWritten\":"<<s.written<<'}';}
  o<<"],\"metrics\":{";for(unsigned i=0;i<MetricCount;++i){if(i)o<<',';auto&m=metrics[i];o<<'"'<<names[i]<<"\":{\"count\":"<<m.count<<",\"totalTicks\":"<<m.ticks<<",\"maxTicks\":"<<m.maximum<<'}';}o<<"}}";return o.str();
 }
};
inline Telemetry telemetry;
struct Scope {Metric metric;long long begin;explicit Scope(Metric m):metric(m),begin(now()){} ~Scope(){telemetry.metrics[metric].add(now()-begin);} };
struct CallbackScope {
 long long begin=now();bool selected=false;
 CallbackScope(){++telemetry.callbacks;long long empty=0;telemetry.firstCallback.compare_exchange_strong(empty,begin);}
 ~CallbackScope(){telemetry.metrics[Callback].add(now()-begin);if(selected)++telemetry.selected;else ++telemetry.rejected;}
};
struct Lock {
 std::unique_lock<std::mutex> lock;long long held;
 explicit Lock(std::mutex&m):lock(m,std::defer_lock){auto b=now();lock.lock();held=now();telemetry.metrics[GuardWait].add(held-b);}
 ~Lock(){telemetry.metrics[GuardHold].add(now()-held);}
};
template<class F> inline auto measure(Metric m,F f){Scope t(m);return f();}
inline BOOL write(HANDLE h,LPCVOID b,DWORD n,LPDWORD done,LPOVERLAPPED o){return measure(Write,[&]{return WriteFile(h,b,n,done,o);});}
inline BOOL flush(HANDLE h){return measure(Flush,[&]{return FlushFileBuffers(h);});}
inline BOOL close(HANDLE h){return measure(Close,[&]{return CloseHandle(h);});}
}
