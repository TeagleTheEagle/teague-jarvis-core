from pathlib import Path
import json
R=Path(__file__).parent; C=R/'candidate'
def edit(name,pairs):
 p=C/name;s=p.read_text()
 for a,b in pairs:
  assert a in s,(name,a)
  s=s.replace(a,b)
 p.write_text(s)
edit('trace_telemetry.hpp',[
 ('#include <algorithm>','#include <algorithm>\n#include "loss_diagnostic_v2.hpp"'),
 ('auto i=phaseCount.fetch_add(1);','j6d::diagnostic.phase(name,begin);auto i=phaseCount.fetch_add(1);'),
 ('Metric metric;long long begin;','Metric metric;long long begin;j6d::Span diagnosticSpan;'),
 ('metric(m),begin(now()){}','metric(m),begin(now()),diagnosticSpan(m==Metadata?j6d::Metadata:m==Admission?j6d::Admission:m==Write?j6d::Write:m==Flush?j6d::Flush:m==Close?j6d::Close:j6d::Other){}'),
 ('long long begin=now();bool selected=false;','long long begin=now();bool selected=false;long long eventQpc=0;j6d::Span diagnosticSpan{j6d::Callback};'),
 ('~CallbackScope(){telemetry.metrics','~CallbackScope(){j6d::diagnostic.callback(begin,now(),selected,eventQpc);telemetry.metrics'),
 ('auto b=now();lock.lock();','auto b=now();j6d::Queue state=j6d::diagnostic.queue();auto sample=j6d::diagnostic.sampleSequence.load();lock.lock();j6d::diagnostic.span(j6d::GuardWait,b,now(),state,sample);'),
 ])
for name,channel in [('authority_trace_v3.cpp','authority'),('startup_trace.cpp','detail')]:
 edit(name,[
 ('j6t::CallbackScope timing;','j6t::CallbackScope timing;timing.eventQpc=e->EventHeader.TimeStamp.QuadPart;'),
 ('static void Acquire(Row& r){','static void Acquire(Row& r){j6d::Span diagnosticProcessImage(j6d::ProcessImage);'),
 ('j6t::telemetry.query(sessionHandle,session.c_str(),"afterEnable");','j6d::bind(folder,session,"'+channel+'",*p);j6t::telemetry.query(sessionHandle,session.c_str(),"afterEnable");'),
 ('LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);bool ready=','j6d::diagnostic.start(sessionHandle,thread.native_handle());LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);bool ready='),
 ('thread.join();CloseTrace(consumer);','thread.join();j6d::diagnostic.stop();CloseTrace(consumer);'),
 ('out<<"]}";if(!Write(L"loss-telemetry.json",','out<<"]}";Write(L"loss-diagnostic-v2.json",j6d::diagnostic.json());if(!Write(L"loss-telemetry.json",'),
 ])
edit('authority_trace_v3.cpp',[('static void Capture(const Row&r,bool start){','static void Capture(const Row&r,bool start){j6d::Span diagnosticSerialization(j6d::Serialization);')])
edit('startup_trace.cpp',[('std::ostringstream out;out<<','j6d::Span diagnosticSerialization(j6d::Serialization);std::ostringstream out;out<<')])
edit('durable_sink.hpp',[
 ('void snapshot(U kind,U id=0,U raw=0){','void snapshot(U kind,U id=0,U raw=0){\n  j6d::diagnostic.queueState(inflightItems,queueBytes,pending);j6d::diagnostic.admitted=accepted;'),
 ('void transfer(std::unique_ptr<Segment>&s){','void transfer(std::unique_ptr<Segment>&s){j6d::Span diagnosticRotation(j6d::Rotation);'),
 ('auto serial=q();std::string row=','j6d::Span diagnosticSerialization(j6d::Serialization);auto serial=q();std::string row='),
 ('s->advance(DURABLY_COMMITTED);','s->advance(DURABLY_COMMITTED);j6d::diagnostic.persisted+=s->count;j6d::diagnostic.persistedBytes+=s->bytes;'),
 ('done.push_back(std::move(s));snapshot(6,id);','done.push_back(std::move(s));++j6d::diagnostic.finalizations;snapshot(6,id);'),
 ])
edit('trace_sink.hpp',[
 ('bool closeSegment(){','bool closeSegment(){j6d::Span diagnosticRotation(j6d::Rotation);'),
 ('if(ok)persisted+=segments.back().records;','if(ok){persisted+=segments.back().records;j6d::diagnostic.persisted+=segments.back().records;j6d::diagnostic.persistedBytes+=segments.back().bytes;++j6d::diagnostic.finalizations;}'),
 ('queued-=row.size();','queued-=row.size();j6d::diagnostic.queueState(queue.size(),queued,0);'),
 ('queue.push_back(std::move(row));wake.notify_one();','queue.push_back(std::move(row));j6d::diagnostic.queueState(queue.size(),queued,0);j6d::diagnostic.admitted=accepted;wake.notify_one();'),
 ])
print('Separate candidate telemetry hooks applied. Originals unchanged.')
