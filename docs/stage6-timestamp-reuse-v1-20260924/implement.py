"""One bounded TEST successor; never edits predecessor."""
from prepare import *
import difflib
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b)
h=(P/'loss_measurement_v3.hpp').read_text()
h=replace(h,'enum Valid:unsigned', 'enum Valid:unsigned')
insert=r'''
// Prospective callback-body endpoint, not historical fixture completion.
enum Reason:unsigned { PID_DECODE=1,TIME_DECODE=2,ZERO_CREATION=4,CAPACITY=8,
 DUP_START=16,DUP_STOP=32,SEQUENCE_CONTRADICTION=64,EXIT_TIME_CONTRADICTION=128,
 EXIT_CODE_CONTRADICTION=256,AUTHORITATIVE_ATTEMPT=512,AUTHORITATIVE_RETURNED=1024,
 HANDLE_ATTEMPT=2048,HANDLE_RETURNED=4096,MAP_COMMITTED=8192,
 PARENT_DECODE=16384,SEQUENCE_DECODE=32768,PARENT_SEQUENCE_DECODE=65536 };
inline LifecycleTap lifecycleTap; // default disabled; offline candidate only
inline U handoffErrors=0;
struct Handoff {
 Lifecycle value{};bool eligible=false,finalized=false;
 void start(long long arrival,long long event,unsigned id,unsigned version,unsigned thread) noexcept {
  eligible=true;value.arrivalQpc=arrival;value.eventQpc=event;value.eventId=id;value.version=version;value.thread=thread;
 }
 void pid(U v,bool ok) noexcept {value.pid=unsigned(v);if(ok)value.valid|=PID_VALID;else value.reserved|=PID_DECODE;}
 void created(U v,bool ok) noexcept {value.created=v;if(ok)value.valid|=CREATED_VALID;else value.reserved|=TIME_DECODE;}
 void parent(U v,bool ok) noexcept {value.parentPid=unsigned(v);if(ok)value.valid|=PARENT_VALID;else value.reserved|=PARENT_DECODE;}
 void sequence(U v,bool ok) noexcept {value.sequence=v;if(ok)value.valid|=SEQUENCE_VALID;else value.reserved|=SEQUENCE_DECODE;}
 void parentSequence(U v,bool ok) noexcept {value.parentSequence=v;if(ok)value.valid|=PARENT_SEQUENCE_VALID;else value.reserved|=PARENT_SEQUENCE_DECODE;}
 void finish(Disposition d,unsigned reason=0) noexcept {value.disposition=d;value.reserved|=reason;finalized=true;}
 void exception() noexcept {if(eligible)finish(Disposition::ExceptionCaught);}
 void publish(long long end) noexcept {
  if(!lifecycleTap.enabled||!eligible)return;
  if(!finalized||end<value.arrivalQpc){++handoffErrors;return;}
  value.completionQpc=end;lifecycleTap.append(value);
 }
};
static_assert(std::is_trivially_copyable_v<Handoff>);
static_assert(sizeof(Handoff)<=96,"fixed scope payload");
inline bool lifecycleComplete() noexcept {return !handoffErrors&&lifecycleTap.complete();}
'''
h=replace(h,'enum class Operation:unsigned',insert+'\nenum class Operation:unsigned')
(C/'loss_measurement_v3.hpp').write_text(h)
t=(P/'trace_telemetry.hpp').read_text()
t=replace(t,'#include "loss_diagnostic_v2.hpp"','#include "loss_diagnostic_v2.hpp"\n#include "loss_measurement_v3.hpp"')
t=replace(t,'struct CallbackScope {','struct CallbackScope {\n  j6m::Handoff lifecycle;')
t=replace(t,'j6d::diagnostic.span(j6d::Callback,begin,end,before,previous);}', 'j6d::diagnostic.span(j6d::Callback,begin,end,before,previous);lifecycle.publish(end);}')
(C/'trace_telemetry.hpp').write_text(t)
for name in ['authority_trace_v3.cpp','startup_trace.cpp']:
 s=(P/name).read_text();detail=name=='startup_trace.cpp'
 if detail:
  s=replace(s,'static void LifecycleEvent(EVENT_RECORD* e){try{','static void LifecycleEvent(EVENT_RECORD* e,j6t::CallbackScope& timing){try{')
  s=replace(s,' LifecycleEvent(e);',' LifecycleEvent(e,timing);')
 begin=s.index('static void LifecycleEvent' if detail else 'static void WINAPI Event')
 end=s.index('\n }catch(...){++faults;}}',begin)+len('\n }catch(...){++faults;}}')
 b=s[begin:end]
 b=replace(b,'if(id!=1&&id!=2)return;', 'if(id!=1&&id!=2)return;\n timing.lifecycle.start(timing.begin,e->EventHeader.TimeStamp.QuadPart,id,e->EventHeader.EventDescriptor.Version,e->EventHeader.ThreadId);')
 b=replace(b,'ULONGLONG created=Number(e,L"CreateTime",&hasTime);', 'timing.lifecycle.pid(pid,hasPid);ULONGLONG created=Number(e,L"CreateTime",&hasTime);timing.lifecycle.created(created,hasTime);')
 b=replace(b,'DWORD parent=static_cast<DWORD>(Number(e,L"ParentProcessID"));if(!ParentKnown(parent,created,Number(e,L"ParentProcessSequenceNumber"))){++discarded;return;}', 'bool parentOk=false,parentSequenceOk=false;DWORD parent=static_cast<DWORD>(Number(e,L"ParentProcessID",&parentOk));timing.lifecycle.parent(parent,parentOk);auto parentSequence=Number(e,L"ParentProcessSequenceNumber",&parentSequenceOk);timing.lifecycle.parentSequence(parentSequence,parentSequenceOk);if(!ParentKnown(parent,created,parentSequence)){++discarded;timing.lifecycle.finish(j6m::Disposition::UNKNOWN_PARENT);return;}')
 b=replace(b,'if(!hasPid||!hasTime||!created||rows.size()>=8192){++faults;return;}', 'if(!hasPid||!hasTime){++faults;timing.lifecycle.finish(j6m::Disposition::DECODE_FAILURE);return;}if(!created){++faults;timing.lifecycle.finish(j6m::Disposition::INVALID_IDENTITY,j6m::ZERO_CREATION);return;}if(rows.size()>=8192){++faults;timing.lifecycle.finish(j6m::Disposition::OTHER_EXPLICIT_REJECTION,j6m::CAPACITY);return;}')
 b=replace(b,'if(rows.count(key)){++faults;return;}','if(rows.count(key)){++faults;timing.lifecycle.finish(j6m::Disposition::DuplicateRecord,j6m::DUP_START);return;}')
 b=replace(b,'r.sequence=Number(e,L"ProcessSequenceNumber");r.parentSequence=Number(e,L"ParentProcessSequenceNumber");','bool sequenceOk=false,secondParentSequenceOk=false;r.sequence=Number(e,L"ProcessSequenceNumber",&sequenceOk);timing.lifecycle.sequence(r.sequence,sequenceOk);r.parentSequence=Number(e,L"ParentProcessSequenceNumber",&secondParentSequenceOk);')
 # Preserve the first parent-sequence value used for selection, not a later decode overwrite.
 b=replace(b,'Acquire(r);rows.emplace(key,std::move(r));','timing.lifecycle.value.reserved|=j6m::HANDLE_ATTEMPT;Acquire(r);timing.lifecycle.value.reserved|=j6m::HANDLE_RETURNED;rows.emplace(key,std::move(r));timing.lifecycle.value.reserved|=j6m::MAP_COMMITTED;timing.lifecycle.finish(j6m::Disposition::ADMITTED);')
 if not detail:
  b=replace(b,'Capture(r,true);','timing.lifecycle.value.reserved|=j6m::AUTHORITATIVE_ATTEMPT;Capture(r,true);timing.lifecycle.value.reserved|=j6m::AUTHORITATIVE_RETURNED;')
 b=replace(b,'if(it==rows.end()){++discarded;return;}','if(it==rows.end()){++discarded;timing.lifecycle.finish(j6m::Disposition::UNKNOWN_PROCESS_INSTANCE);return;}')
 b=replace(b,'if(r.stop){++faults;return;}','if(r.stop){++faults;timing.lifecycle.finish(j6m::Disposition::DuplicateRecord,j6m::DUP_STOP);return;}')
 b=replace(b,'if(r.sequence!=Number(e,L"ProcessSequenceNumber"))++faults;', 'bool stopSequenceOk=false;auto stopSequence=Number(e,L"ProcessSequenceNumber",&stopSequenceOk);timing.lifecycle.sequence(stopSequence,stopSequenceOk);if(r.sequence!=stopSequence){++faults;timing.lifecycle.value.reserved|=j6m::SEQUENCE_CONTRADICTION;}')
 b=replace(b,'if(r.exitFT&&exitTime!=r.exitFT)++faults;', 'if(r.exitFT&&exitTime!=r.exitFT){++faults;timing.lifecycle.value.reserved|=j6m::EXIT_TIME_CONTRADICTION;}')
 b=replace(b,'if(r.exitCodeKnown&&(!known||r.exitCode!=code))++faults;', 'if(r.exitCodeKnown&&(!known||r.exitCode!=code)){++faults;timing.lifecycle.value.reserved|=j6m::EXIT_CODE_CONTRADICTION;}')
 if not detail:
  b=replace(b,'Capture(r,false);','timing.lifecycle.value.reserved|=j6m::AUTHORITATIVE_ATTEMPT;Capture(r,false);timing.lifecycle.value.reserved|=j6m::AUTHORITATIVE_RETURNED;timing.lifecycle.finish(j6m::Disposition::ADMITTED);')
 else:b=replace(b,'r.stopSchema=Schemas(e);}', 'r.stopSchema=Schemas(e);timing.lifecycle.finish(j6m::Disposition::ADMITTED);}')
 b=replace(b,'catch(...){++faults;}', 'catch(...){++faults;timing.lifecycle.exception();}')
 s=s[:begin]+b+s[end:]
 # Outer exception must finalize a lifecycle payload if one exists; never classify non-lifecycle as lifecycle.
 if detail:s=replace(s,' }catch(...){++faults;}\n}', ' }catch(...){++faults;timing.lifecycle.exception();}\n}')
 (C/name).write_text(s)
diff=''
for name in ['loss_measurement_v3.hpp','trace_telemetry.hpp','authority_trace_v3.cpp','startup_trace.cpp']:
 diff+=''.join(difflib.unified_diff((P/name).read_text().splitlines(True),(C/name).read_text().splitlines(True),fromfile=str(P/name),tofile=str(C/name)))
(R/'implementation.diff').write_text(diff)
write(R/'implementation-files.json',[rec(C/n) for n in ['loss_measurement_v3.hpp','trace_telemetry.hpp','authority_trace_v3.cpp','startup_trace.cpp']])
print('Four successor components written; predecessor unchanged; no live run')
