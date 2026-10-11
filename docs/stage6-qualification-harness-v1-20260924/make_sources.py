from prepare import *
for file in ['api.hpp','adapter.hpp']:shutil.copy2(R/file,C/file)
for arm in 'ABC':
 root=C/arm
 text=f'''#define NOMINMAX
#define j6t timer_{arm}
#define j6d diag_{arm}
#define j6m recorder_{arm}
#define fixture fixture_{arm}
#include "trace_telemetry.hpp"
#include "../adapter.hpp"
namespace authority {{using namespace fixture;
#include "authority.inc"
}}
namespace detail {{using namespace fixture;
#include "detail.inc"
}}
static unsigned count_=0;static unsigned long long allocBefore=0;
static void prepare_(unsigned scenario,unsigned channel,unsigned n){{fixture::setup(scenario,channel,n);count_=n;
'''
 if arm!='A':text+='j6m::lifecycleTap.count=0;j6m::lifecycleTap.attempted=0;j6m::lifecycleTap.overflow=0;j6m::handoffErrors=0;j6m::lifecycleTap.enabled=true;\n'
 text+='allocBefore=allocationCount;}\n'
 text+=f'''extern "C" __declspec(noinline) void dispatch_{arm}(unsigned i){{fixture::current=i;if(fixture::channel==0)authority::Event(&fixture::events[i]);else detail::Event(&fixture::events[i]);}}
static Outcome finish_(){{Outcome o;o.hash=fixture::digest();o.queries=fixture::queries;o.captures=fixture::captures;o.acquires=fixture::acquires;o.faults=fixture::faults;o.discarded=fixture::discarded;o.allocations=allocationCount-allocBefore;
'''
 if arm!='A':text+='''o.records=j6m::lifecycleTap.count;o.attempted=j6m::lifecycleTap.attempted;o.overflow=j6m::lifecycleTap.overflow;o.handoffErrors=j6m::handoffErrors;
if(o.records){o.disposition=unsigned(j6m::lifecycleTap.records[0].disposition);o.valid=j6m::lifecycleTap.records[0].valid;for(size_t i=0;i<o.records;i++){auto&r=j6m::lifecycleTap.records[i];if(r.localSequence!=i+1||r.completionQpc<r.arrivalQpc)o.timing=false;}}
'''
 text+=f'''return o;}}
static unsigned scopeSize_(){{return sizeof(j6t::CallbackScope);}}
extern "C" __declspec(noinline) void endpoint_{arm}(){{j6t::CallbackScope scope;'''
 if arm!='A':text+='scope.lifecycle.start(scope.begin,1,1,4,81);scope.lifecycle.finish(j6m::Disposition::ADMITTED);'
 text+=f'''}}
extern "C" Arm arm_{arm}(){{return {{"{arm}",prepare_,dispatch_{arm},finish_,scopeSize_}};}}
'''
 (root/'arm.cpp').write_text(text)
print('Generated three isolated translation units using unmodified bound timer headers')
