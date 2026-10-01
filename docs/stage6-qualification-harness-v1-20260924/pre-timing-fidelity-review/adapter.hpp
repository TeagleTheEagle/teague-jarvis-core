// Same bounded offline dependencies in all three arms; no live OS event source or metadata query.
#include <evntcons.h>
#include <utility>
#include <stdexcept>
#include <cwchar>
#include "api.hpp"
namespace fixture {
using U=unsigned long long;
static const GUID Provider={1},FileProvider={2},RegProvider={3},ClassicReg={4},ThreadProvider={5};
struct Image{};struct Schema{};
struct Row{DWORD pid=0,parent=0;U created=0,sequence=0,parentSequence=0,exitFT=0;DWORD exitCode=0;bool exitCodeKnown=false;long long start=0,notified=0,stop=0,stopNotified=0;unsigned version=0,stopVersion=0;Image image;Schema schema,stopSchema;};
struct Rows {
 struct Entry{std::pair<DWORD,U> first;Row second;};Entry data[8192];bool occupied[8192]{};size_t count_=0;
 size_t size() const noexcept{return count_;}
 Entry* end() noexcept{return nullptr;}
 Entry* find(std::pair<DWORD,U> key) noexcept {size_t i=key.first-10000;if(i>=8192||!occupied[i]||data[i].first!=key)return nullptr;return &data[i];}
 size_t count(std::pair<DWORD,U> key) noexcept {return find(key)?1:0;}
 void emplace(std::pair<DWORD,U> key,Row&&r) noexcept{size_t i=key.first-10000;if(i<8192&&!occupied[i]){occupied[i]=true;data[i]={key,r};++count_;}}
 void reset() noexcept{for(size_t i=0;i<8192;i++)occupied[i]=false;count_=0;}
} rows;
std::mutex guard;unsigned faults=0,discarded=0;unsigned scenario=0,channel=0,current=0;U queries=0,captures=0,acquires=0;EVENT_RECORD events[8192]{};
U Number(EVENT_RECORD*,const wchar_t*name,bool*ok=nullptr){
 ++queries;if(scenario==9)throw 7;bool valid=true;U v=0;
 if(!wcscmp(name,L"ProcessID")){v=10000+((scenario==4||scenario==5)?0:current);valid=scenario!=7;}
 else if(!wcscmp(name,L"CreateTime"))v=scenario==6?0:23;
 else if(!wcscmp(name,L"ParentProcessID"))v=7;
 else if(!wcscmp(name,L"ParentProcessSequenceNumber"))v=11;
 else if(!wcscmp(name,L"ProcessSequenceNumber"))v=13;
 else if(!wcscmp(name,L"ExitTime"))v=71;
 else if(!wcscmp(name,L"ExitCode"))v=0;
 else throw 8;
 if(ok)*ok=valid;return valid?v:0;
}
bool ParentKnown(DWORD,U,U) noexcept{return scenario!=2;}
Image Text(EVENT_RECORD*,const wchar_t*) noexcept{return {};}
Schema Schemas(EVENT_RECORD*) noexcept{return {};}
long long Q() noexcept{return 100;} // deterministic existing selected-output timestamp double; same for all arms
void Capture(const Row&,bool) noexcept{++captures;}
void Acquire(Row&) noexcept{++acquires;}
void setup(unsigned sc,unsigned ch,unsigned n){
 scenario=sc;channel=ch;queries=captures=acquires=0;faults=discarded=0;rows.reset();
 for(unsigned i=0;i<8192;i++){
  if((sc==1&&i<n)||((sc==4||sc==5)&&i==0)||sc==8){Row r;r.pid=10000+i;r.created=23;r.sequence=13;r.stop=sc==5?50:0;rows.emplace({r.pid,r.created},std::move(r));}
  if(i<n){events[i]={};auto&e=events[i];e.EventHeader.ProviderId=Provider;e.EventHeader.EventDescriptor.Id=(sc==1||sc==3||sc==5)?2:sc==10?0:1;e.EventHeader.EventDescriptor.Version=4;e.EventHeader.ThreadId=81;e.EventHeader.TimeStamp.QuadPart=1;}
 }
}
U digest() noexcept {
 U h=1469598103934665603ULL;auto add=[&](U v){h=(h^v)*1099511628211ULL;};
 add(rows.size());add(queries);add(captures);add(acquires);add(faults);add(discarded);
 for(unsigned i=0;i<8192;i++)if(rows.occupied[i]){auto&r=rows.data[i].second;add(i);add(r.pid);add(r.parent);add(r.created);add(r.sequence);add(r.parentSequence);add(r.start);add(r.stop);add(r.exitFT);add(r.exitCode);add(r.exitCodeKnown);}
 return h;
}
}
