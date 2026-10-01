#pragma once
// TEST diagnostic only: never lifecycle authority or an acceptance input.
#include <windows.h>
#include <array>
#include <cstdint>
#include <type_traits>
namespace j6m {
using U=unsigned long long;
inline long long tick() noexcept { LARGE_INTEGER q; QueryPerformanceCounter(&q); return q.QuadPart; }
// DuplicateRecord serializes as DUPLICATE; Windows nb30.h defines DUPLICATE=0x06.
// ExceptionCaught is the C++ spelling for the EXCEPTION disposition.
enum class Disposition:unsigned { ADMITTED,UNKNOWN_PARENT,UNKNOWN_PROCESS_INSTANCE,DuplicateRecord,INVALID_IDENTITY,DECODE_FAILURE,ExceptionCaught,OTHER_EXPLICIT_REJECTION };
enum Valid:unsigned { PID_VALID=1,CREATED_VALID=2,PARENT_VALID=4,SEQUENCE_VALID=8,PARENT_SEQUENCE_VALID=16 };
struct Lifecycle {
 U localSequence=0; long long eventQpc=0,arrivalQpc=0,completionQpc=0;
 U created=0,sequence=0,parentSequence=0;
 unsigned pid=0,parentPid=0,eventId=0,version=0,thread=0,valid=0;
 Disposition disposition=Disposition::OTHER_EXPLICIT_REJECTION;
 unsigned reserved=0;
};
static_assert(std::is_trivially_copyable_v<Lifecycle>);
// Exactly one callback producer. Read/export only after that producer has joined.
// Run/session/source binding belongs to the immutable outer document, not each record.
class LifecycleTap {
public:
 static constexpr size_t capacity=16384;
 std::array<Lifecycle,capacity> records{};
 size_t count=0; U attempted=0,overflow=0; bool enabled=false;
 void append(Lifecycle value) noexcept {
  if(!enabled)return;
  value.localSequence=++attempted;
  if(count==capacity){++overflow;return;}
  records[count++]=value;
 }
 bool complete() const noexcept {return overflow==0&&attempted==count;}
};
static_assert(sizeof(LifecycleTap)<=2*1024*1024,"Lifecycle sidecar exceeds reviewed fixed cap");
enum class Operation:unsigned { Loop,Sample,Handoff,Attributes,Read,Hash,LockWait,LockHold,Write,Flush,Publish,Terminal,Count };
struct Totals {U count=0,total=0,maximum=0,success=0,failure=0;};
struct Slow {long long begin=0,end=0;unsigned thread=0,phase=0;Operation operation{};unsigned result=0;};
class Coordination {
public:
 static constexpr size_t capacity=32768;
 std::array<Slow,capacity> records{};
 std::array<Totals,static_cast<size_t>(Operation::Count)> totals{};
 size_t count=0;U overflow=0;long long frequency=0;bool enabled=false;
 // Control-thread single producer. Caller must append after event-map unlock.
 void append(Operation operation,long long begin,long long end,unsigned thread,unsigned phase,unsigned result,bool success) noexcept {
  if(!enabled)return;
  if(end<begin||frequency<=0){++overflow;return;}
  auto &t=totals[static_cast<size_t>(operation)];U duration=U(end-begin);
  ++t.count;t.total+=duration;if(duration>t.maximum)t.maximum=duration;
  if(success)++t.success;else ++t.failure;
  if(duration<=U(frequency/1000))return;
  if(count==capacity){++overflow;return;}
  records[count++]={begin,end,thread,phase,operation,result};
 }
};
static_assert(sizeof(Coordination)<=2*1024*1024,"Coordination sidecar exceeds reviewed fixed cap");
static_assert(2*sizeof(LifecycleTap)+sizeof(Coordination)+65536<=size_t(6.1*1024*1024));
}
