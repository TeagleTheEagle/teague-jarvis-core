#pragma once
// TEST diagnostic sidecar only. Never supplies authoritative process evidence.
#include <windows.h>
#include <evntrace.h>
#include <atomic>
#include <array>
#include <vector>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <sstream>
#include <filesystem>
#include <chrono>
#include <algorithm>
namespace j6d {
using U=unsigned long long;
inline long long tick(){LARGE_INTEGER q;QueryPerformanceCounter(&q);return q.QuadPart;}
inline void maximum(std::atomic<U>& a,U v){auto x=a.load(std::memory_order_relaxed);while(x<v&&!a.compare_exchange_weak(x,v,std::memory_order_relaxed)){} }
enum Op{Callback,Metadata,ProcessImage,GuardWait,GuardHold,Serialization,Admission,Rotation,Write,Flush,Close,Other};
inline const char* opNames[]={"callback","metadata","processImage","guardWait","guardHold","serialization","admission","rotation","write","flush","close","other"};
struct Queue{U items=0,bytes=0,pending=0,admitted=0,persisted=0,persistedBytes=0,finalizations=0;};
struct Histogram{
 std::atomic<U> bins[64]{},count{0},total{0},max{0};
 static unsigned bucket(U n){unsigned i=0;while(n&&i<63){++i;n>>=1;}return i;}
 void add(U n){bins[bucket(n)].fetch_add(1,std::memory_order_relaxed);count.fetch_add(1,std::memory_order_relaxed);total.fetch_add(n,std::memory_order_relaxed);maximum(max,n);}
};
struct Distribution{U count=0,total=0,max=0;std::array<U,64> bins{};};
inline Distribution drain(Histogram& h){Distribution d;for(unsigned i=0;i<64;i++){d.bins[i]=h.bins[i].exchange(0);d.count+=d.bins[i];}d.total=h.total.exchange(0);d.max=h.max.exchange(0);h.count.exchange(0);return d;}
inline std::string hist(const Distribution& d){std::ostringstream o;o<<"{\"count\":"<<d.count<<",\"totalTicks\":"<<d.total<<",\"maxTicks\":"<<d.max<<",\"bins\":[";for(unsigned i=0;i<64;i++){if(i)o<<',';o<<d.bins[i];}return o.str()+"]}";}
struct Slow{long long begin=0,end=0;Op op=Other;DWORD thread=0;Queue before,after;U previousSample=0,latestSample=0;};
struct Sample{long long begin=0,end=0;ULONG status=0,lost=0,real=0,log=0,buffers=0,free=0,written=0;DWORD alive=0,cpuError=0;U cpu100ns=0,callbacks=0,delta=0,selected=0,received=0,receivedDelta=0;long long lastCallback=0,lastReceipt=0,activeCallback=0;Queue queue;Distribution durations,lag;};
class Diagnostic{
public:
 static constexpr unsigned sampleCap=16384,slowCap=4096,intervalMs=100;
 std::atomic<bool> enabled{false},stopping{false};std::atomic<U> errors{0},overflow{0},sampleSequence{0},callbackCount{0},selectedCount{0},queueItems{0},queueBytes{0},pending{0},admitted{0},persisted{0},persistedBytes{0},finalizations{0},queueHighItems{0},queueHighBytes{0};
 std::atomic<long long> lastCallback{0},sessionStart{0},ready{0},stopBegin{0};
 Histogram duration,lag;std::mutex histLock,slowLock,waitLock;std::condition_variable wake;
 std::atomic<U> receivedCount{0};std::atomic<long long> lastReceipt{0},activeCallback{0};U previousReceived=0;
 std::vector<Sample> samples;std::vector<Slow> slow;std::thread sampler;std::wstring session,run;std::string channel,config;long long frequency=0,origin=0;U previousCallbacks=0;HANDLE consumer=nullptr;
 using Query=ULONG(WINAPI*)(TRACEHANDLE,LPCWSTR,PEVENT_TRACE_PROPERTIES,ULONG);
 Queue queue()const{return {queueItems.load(),queueBytes.load(),pending.load(),admitted.load(),persisted.load(),persistedBytes.load(),finalizations.load()};}
 void queueState(U items,U bytes,U pend){queueItems=items;queueBytes=bytes;pending=pend;maximum(queueHighItems,items);maximum(queueHighBytes,bytes);}
 void phase(const char* name,long long q){if(!strcmp(name,"StartTrace"))sessionStart=q;if(!strcmp(name,"ReadyPublished"))ready=q;if(!strcmp(name,"StopTrace"))stopBegin=q;}
 void bind(std::wstring r,std::wstring s,std::string ch,long long hz,std::string cfg){
  if(enabled||r.empty()||s.empty()||hz<=0||(ch!="authority"&&ch!="detail"))throw std::runtime_error("diagnostic binding");
  run=std::move(r);session=std::move(s);channel=std::move(ch);frequency=hz;config=std::move(cfg);origin=tick();samples.reserve(sampleCap);slow.reserve(slowCap);enabled=true;
 }
 void span(Op op,long long begin,long long end,Queue before,U previous){
  if(!enabled||end-begin<frequency/200)return; // 5ms diagnostic threshold, not acceptance limit
  std::unique_lock<std::mutex> l(slowLock,std::try_to_lock);
  if(!l.owns_lock()||slow.size()==slowCap){++errors;++overflow;return;}
  slow.push_back({begin,end,op,GetCurrentThreadId(),before,queue(),previous,sampleSequence.load()});
 }
 void enter(long long begin){if(enabled){++receivedCount;lastReceipt=begin;activeCallback=begin;}}
 void callback(long long begin,long long end,bool selected,long long eventQpc){
  if(!enabled)return;
  // Constant-size in-memory critical section; no OS query or filesystem operation under this lock.
  std::lock_guard<std::mutex> l(histLock);callbackCount.fetch_add(1,std::memory_order_relaxed);lastCallback=end;if(selected)++selectedCount;
  duration.add(U(end-begin));if(selected&&eventQpc){if(eventQpc>begin){++errors;}else lag.add(U(begin-eventQpc));}activeCallback=0;
 }
 void sample(TRACEHANDLE handle,Query query=ControlTraceW){
  if(samples.size()==sampleCap){++errors;++overflow;return;}
  alignas(EVENT_TRACE_PROPERTIES) BYTE storage[sizeof(EVENT_TRACE_PROPERTIES)+2048]{};auto p=reinterpret_cast<EVENT_TRACE_PROPERTIES*>(storage);p->Wnode.BufferSize=sizeof(storage);p->LoggerNameOffset=sizeof(EVENT_TRACE_PROPERTIES);
  Sample s;s.begin=tick();s.status=query(handle,session.c_str(),p,EVENT_TRACE_CONTROL_QUERY);s.end=tick();
  if(!s.status){s.lost=p->EventsLost;s.real=p->RealTimeBuffersLost;s.log=p->LogBuffersLost;s.buffers=p->NumberOfBuffers;s.free=p->FreeBuffers;s.written=p->BuffersWritten;}
  else if(!stopBegin||s.begin<stopBegin)++errors;
  s.queue=queue();s.received=receivedCount;s.receivedDelta=s.received-previousReceived;previousReceived=s.received;s.lastReceipt=lastReceipt;s.activeCallback=activeCallback;
  {std::lock_guard<std::mutex> l(histLock);s.callbacks=callbackCount;s.delta=s.callbacks-previousCallbacks;previousCallbacks=s.callbacks;s.selected=selectedCount;s.lastCallback=lastCallback;s.durations=drain(duration);s.lag=drain(lag);}
  if(consumer){s.alive=WaitForSingleObject(consumer,0);FILETIME a,b,k,u;if(GetThreadTimes(consumer,&a,&b,&k,&u))s.cpu100ns=(U(k.dwHighDateTime)<<32)+k.dwLowDateTime+(U(u.dwHighDateTime)<<32)+u.dwLowDateTime;else{s.cpuError=GetLastError();++errors;}}
  else{s.alive=WAIT_FAILED;s.cpuError=ERROR_INVALID_HANDLE;}
  samples.push_back(s);sampleSequence=samples.size();
 }
 void start(TRACEHANDLE handle,HANDLE thread,Query query=ControlTraceW){if(!DuplicateHandle(GetCurrentProcess(),thread,GetCurrentProcess(),&consumer,0,FALSE,DUPLICATE_SAME_ACCESS)){++errors;return;}sampler=std::thread([this,handle,query]{
  try{while(!stopping){sample(handle,query);std::unique_lock<std::mutex> l(waitLock);wake.wait_for(l,std::chrono::milliseconds(intervalMs),[this]{return stopping.load();});}}catch(...){++errors;}
 });}
 void stop(){stopping=true;wake.notify_all();if(sampler.joinable())sampler.join();if(consumer){CloseHandle(consumer);consumer=nullptr;}}
 static std::string ascii(const std::wstring& s){std::string o;for(auto c:s){if(c<32||c>126||c=='"'||c=='\\')throw std::runtime_error("diagnostic identity encoding");o+=char(c);}return o;}
 static void queueJson(std::ostringstream&o,const Queue&q){o<<"["<<q.items<<','<<q.bytes<<','<<q.pending<<','<<q.admitted<<','<<q.persisted<<','<<q.persistedBytes<<','<<q.finalizations<<"]";}
 std::string json(){
  if(sampler.joinable())throw std::runtime_error("diagnostic still live");std::ostringstream o;
  o<<"{\"schema\":\"stage6-loss-diagnostic-v2\",\"diagnosticOnly\":true,\"acceptanceSealed\":false,\"run\":\""<<ascii(run)<<"\",\"session\":\""<<ascii(session)<<"\",\"channel\":\""<<channel<<"\",\"frequency\":"<<frequency<<",\"originQpc\":"<<origin<<",\"sessionStartQpc\":"<<sessionStart<<",\"readyQpc\":"<<ready<<",\"stopBeginQpc\":"<<stopBegin<<",\"cleanupEntryQpc\":null,\"cleanupBinding\":\"external cleanup-origin-v3.json; offline hash binding required\",\"intervalMs\":100,\"slowThresholdMs\":5,\"sampleCapacity\":"<<sampleCap<<",\"slowCapacity\":"<<slowCap<<",\"allocatedBytes\":"<<(sampleCap*sizeof(Sample)+slowCap*sizeof(Slow))<<",\"errors\":"<<errors<<",\"overflow\":"<<overflow<<",\"queueHighItems\":"<<queueHighItems<<",\"queueHighBytes\":"<<queueHighBytes<<",\"configuration\":"<<config<<",\"histogramSemantics\":\"power-of-two tick bounds; interval approximate quantiles; not exact samples\",\"samples\":[";
  for(size_t i=0;i<samples.size();i++){auto&s=samples[i];if(i)o<<',';o<<"{\"sequence\":"<<i+1<<",\"beginQpc\":"<<s.begin<<",\"endQpc\":"<<s.end<<",\"status\":"<<s.status<<",\"eventsLost\":";if(s.status)o<<"null";else o<<s.lost;o<<",\"realtimeBuffersLost\":"<<s.real<<",\"logBuffersLost\":"<<s.log<<",\"numberOfBuffers\":"<<s.buffers<<",\"freeBuffers\":"<<s.free<<",\"buffersWritten\":"<<s.written<<",\"consumerWaitState\":"<<s.alive<<",\"cpu100ns\":"<<s.cpu100ns<<",\"cpuError\":"<<s.cpuError<<",\"callbacks\":"<<s.callbacks<<",\"callbackDelta\":"<<s.delta<<",\"selected\":"<<s.selected<<",\"lastCallbackQpc\":"<<s.lastCallback<<",\"queue\":";queueJson(o,s.queue);o<<",\"received\":"<<s.received<<",\"receivedDelta\":"<<s.receivedDelta<<",\"lastReceiptQpc\":"<<s.lastReceipt<<",\"activeCallbackQpc\":"<<s.activeCallback<<",\"duration\":"<<hist(s.durations)<<",\"deliveryLag\":"<<hist(s.lag)<<'}';}
  o<<"],\"finalQueue\":";queueJson(o,queue());o<<",\"slowSpans\":[";for(size_t i=0;i<slow.size();i++){auto&s=slow[i];if(i)o<<',';o<<"{\"beginQpc\":"<<s.begin<<",\"endQpc\":"<<s.end<<",\"operation\":\""<<opNames[s.op]<<"\",\"threadId\":"<<s.thread<<",\"beforeSample\":"<<s.previousSample<<",\"latestSample\":"<<s.latestSample<<",\"queueBefore\":";queueJson(o,s.before);o<<",\"queueAfter\":";queueJson(o,s.after);o<<'}';}return o.str()+"]}";
 }
 ~Diagnostic(){stop();}
};
inline Diagnostic diagnostic;
inline void bind(const std::wstring& folder,const std::wstring& session,const char* channel,const EVENT_TRACE_PROPERTIES& p){
 auto path=std::filesystem::path(folder);if(std::string(channel)=="detail")path=path.parent_path();LARGE_INTEGER hz;QueryPerformanceFrequency(&hz);
 std::ostringstream c;c<<"{\"requestedBufferKiB\":64,\"requestedMin\":4,\"requestedMax\":64,\"bufferKiB\":"<<p.BufferSize<<",\"minimumBuffers\":"<<p.MinimumBuffers<<",\"maximumBuffers\":"<<p.MaximumBuffers<<",\"flushSeconds\":"<<p.FlushTimer<<",\"mode\":"<<p.LogFileMode<<",\"kernelFlags\":"<<p.EnableFlags<<",\"clock\":1,\"perProcessor\":true,\"fileMode\":false,\"stackwalk\":false,\"explicitRundown\":false,\"processKeyword\":\""<<(std::string(channel)=="detail"?"0x70":"0x10")<<"\",\"fileKeyword\":\""<<(std::string(channel)=="detail"?"0x1f0":"disabled")<<"\",\"registryKeyword\":\""<<(std::string(channel)=="detail"?"0x400000000000ac33":"disabled")<<"\"}";
 diagnostic.bind(path.filename().wstring(),session,channel,hz.QuadPart,c.str());
}
struct Span{Op op;long long begin;Queue before;U previous;explicit Span(Op o):op(o),begin(tick()),before(diagnostic.queue()),previous(diagnostic.sampleSequence){}~Span(){diagnostic.span(op,begin,tick(),before,previous);}};
}
