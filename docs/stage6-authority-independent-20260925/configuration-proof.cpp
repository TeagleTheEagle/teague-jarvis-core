#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <evntrace.h>
constexpr ULONG oldMode=EVENT_TRACE_REAL_TIME_MODE;
constexpr ULONG newMode=EVENT_TRACE_REAL_TIME_MODE|EVENT_TRACE_INDEPENDENT_SESSION_MODE;
constexpr ULONG detailMode=EVENT_TRACE_REAL_TIME_MODE|EVENT_TRACE_SYSTEM_LOGGER_MODE;
static_assert(oldMode==0x100);
static_assert(newMode==0x08000100);
static_assert((oldMode^newMode)==EVENT_TRACE_INDEPENDENT_SESSION_MODE);
static_assert((detailMode&EVENT_TRACE_INDEPENDENT_SESSION_MODE)==0);
struct Counters {ULONG EventsLost; ULONG RealTimeBuffersLost;};
constexpr int authority(ULONG lost){Counters c{lost,0};auto p=&c;bool wrote=true,requested=true;ULONG stop=0,faults=0;return !wrote||!requested||stop||faults||p->EventsLost||p->RealTimeBuffersLost?95:0;}
static_assert(authority(0)==0);
static_assert(authority(1)==95);
static_assert(authority(16)==95);
static_assert(authority(136196)==95);
constexpr int detailed(ULONG lost){Counters c{lost,0};auto p=&c;bool wrote=true,requested=true;ULONG stop=0,faults=0;return !wrote||!requested||stop||faults||p->EventsLost||p->RealTimeBuffersLost?95:0;}
static_assert(detailed(0)==0);
static_assert(detailed(1)==95);
static_assert(detailed(16)==95);
static_assert(detailed(136196)==95);
