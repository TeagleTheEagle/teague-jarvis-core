#pragma once
#include <cstdint>
#include <cstddef>
#include <sstream>

// TEST diagnostic only. One ProcessTrace consumer owns this buffer. Export only
// after that consumer joins. No atomics, locks, allocation, clocks or I/O here.
namespace j6w {
enum Disposition : unsigned {ADMITTED, UNKNOWN_PARENT, UNKNOWN_INSTANCE,
 DUPLICATE_EVENT, INVALID_IDENTITY, DECODE_FAILURE, OTHER_EXPLICIT_REJECTION};
enum Reason : unsigned {NONE, PARENT_NOT_KNOWN, INSTANCE_NOT_KNOWN,
 DUPLICATE_START, DUPLICATE_STOP, ZERO_CREATION, FIELD_DECODE_FAILED,
 ROW_CAPACITY, EXCEPTION, SELECTOR_FAULT};
enum Field : unsigned {PID=1, CREATION=2, PARENT=4, SEQUENCE=8, PARENT_SEQUENCE=16};
struct Record {
 std::uint64_t sequence=0,processSequence=0,parentSequence=0;
 std::int64_t eventQpc=0,callbackQpc=0;
 std::uint32_t pid=0,parentPid=0,valid=0,decoded=0;
 unsigned kind=0,disposition=DECODE_FAILURE,reason=FIELD_DECODE_FAILED;
 // -1 means this decision was not evaluated; never infer false after the fact.
 int parentKnown=-1,instanceKnown=-1;
 bool admitted=false,complete=false;
};
template<std::size_t Capacity> struct Buffer {
 Record records[Capacity]{};
 std::uint64_t attempted=0;std::size_t count=0;bool overflow=false;
 Record* begin(unsigned kind,std::int64_t event,std::int64_t callback) noexcept {
  ++attempted;if(count==Capacity){overflow=true;return nullptr;}
  auto* r=&records[count++];r->sequence=attempted;r->kind=kind;
  r->eventQpc=event;r->callbackQpc=callback;return r;
 }
};
constexpr std::size_t capacity=65536;
inline Buffer<capacity> buffer;
struct Scope {
 Record* r;
 Scope(unsigned kind,std::int64_t event,std::int64_t callback) noexcept
  :r(buffer.begin(kind,event,callback)){}
 ~Scope() noexcept {if(r)r->complete=true;}
 std::uint64_t field(std::uint64_t value,Field f,bool ok) noexcept {
  if(r){r->decoded|=f;if(ok)r->valid|=f;else r->valid&=~unsigned(f);
   if(f==PID)r->pid=static_cast<std::uint32_t>(value);
   if(f==PARENT)r->parentPid=static_cast<std::uint32_t>(value);
   if(f==SEQUENCE)r->processSequence=value;
   if(f==PARENT_SEQUENCE)r->parentSequence=value;}
  return value;
 }
 bool parent(bool known) noexcept {if(r)r->parentKnown=known;return known;}
 bool instance(bool known) noexcept {if(r)r->instanceKnown=known;return known;}
 void result(Disposition d,Reason reason=NONE) noexcept {
  if(r){r->disposition=d;r->reason=reason;r->admitted=d==ADMITTED;}
 }
};
inline const char* disposition(unsigned x){static const char* a[]={"ADMITTED","UNKNOWN_PARENT","UNKNOWN_INSTANCE","DUPLICATE","INVALID_IDENTITY","DECODE_FAILURE","OTHER_EXPLICIT_REJECTION"};return x<7?a[x]:"INVALID";}
inline const char* reason(unsigned x){static const char* a[]={"NONE","PARENT_NOT_KNOWN","INSTANCE_NOT_KNOWN","DUPLICATE_START","DUPLICATE_STOP","ZERO_CREATION","FIELD_DECODE_FAILED","ROW_CAPACITY","EXCEPTION","SELECTOR_FAULT"};return x<10?a[x]:"INVALID";}
// Serialization is deliberately separate from Scope and only used post-join.
template<std::size_t N> std::string recordsJson(const Buffer<N>& b){
 std::ostringstream o;o<<'[';
 for(std::size_t i=0;i<b.count;++i){const auto&r=b.records[i];if(i)o<<',';
  o<<"{\"sequence\":"<<r.sequence<<",\"kind\":\""<<(r.kind==1?"START":"STOP")
   <<"\",\"eventQpc\":"<<r.eventQpc<<",\"callbackQpc\":"<<r.callbackQpc
   <<",\"pid\":"<<r.pid<<",\"parentPid\":"<<r.parentPid
   <<",\"processSequence\":\""<<r.processSequence<<"\",\"parentSequence\":\""<<r.parentSequence
   <<"\",\"decodedFields\":"<<r.decoded<<",\"validFields\":"<<r.valid
   <<",\"parentKnown\":"<<(r.parentKnown<0?"null":r.parentKnown?"true":"false")
   <<",\"instanceKnown\":"<<(r.instanceKnown<0?"null":r.instanceKnown?"true":"false")
   <<",\"admitted\":"<<(r.admitted?"true":"false")<<",\"complete\":"<<(r.complete?"true":"false")
   <<",\"disposition\":\""<<disposition(r.disposition)<<"\",\"reason\":\""<<reason(r.reason)<<"\"}";
 }o<<']';return o.str();
}
}
