from prepare import *
import difflib
# Keep arrival acquisition as the first member initialization; payload follows original timer members.
p=C/'trace_telemetry.hpp';s=p.read_text();s=s.replace('  j6m::Handoff lifecycle;\n','').replace(' j6m::Handoff lifecycle;\n','');assert s.count(' CallbackScope(){')==1;s=s.replace(' CallbackScope(){',' j6m::Handoff lifecycle;\n CallbackScope(){');p.write_text(s)
def extract(src,marker):
 start=src.index(marker);brace=src.index('{',start);depth=0
 for i in range(brace,len(src)):
  if src[i]=='{':depth+=1
  if src[i]=='}':
   depth-=1
   if not depth:return src[start:i+1]
 raise AssertionError(marker)
parts=['// Generated from exact predecessor/successor callback bodies. Dependencies are offline controlled doubles.\n']
for variant,base in [('old',P),('new',C)]:
 for kind,name in [('authority','authority_trace_v3.cpp'),('detail','startup_trace.cpp')]:
  text=(base/name).read_text()
  parts.append(f'namespace {variant}_{kind} {{\nusing namespace fixture;\n')
  if kind=='detail':
   parts.append(extract(text,'static void LifecycleEvent')+'\n')
   # Real outer callback needs many unrelated metadata providers. Preserve actual lifecycle call/filter prefix only,
   # and validate the complete outer translation unit independently by compilation and diff.
   outer=extract(text,'static void WINAPI Event')
   prefix=outer[:outer.index('  if(sched&&op!=36&&op!=50)return;')]
   parts.append(prefix+'   return; }catch(...){++faults;'+('timing.lifecycle.exception();' if variant=='new' else '')+'}\n}\n')
  else:parts.append(extract(text,'static void WINAPI Event')+'\n')
  parts.append('}\n')
(C/'callback-bodies.inc').write_text(''.join(parts))
ref=C.parent/'reference';ref.mkdir(exist_ok=False)
for f in C.glob('*.hpp'):shutil.copy2(f,ref/f.name)
t=(ref/'trace_telemetry.hpp').read_text()
t=t.replace('~CallbackScope(){auto end=now();','~CallbackScope(){long long diagnosticEnd=0;if(lifecycle.eligible&&j6m::lifecycleTap.enabled)diagnosticEnd=now();auto end=now();')
t=t.replace('lifecycle.publish(end);','lifecycle.publish(lifecycle.eligible&&j6m::lifecycleTap.enabled?diagnosticEnd:end);')
(ref/'trace_telemetry.hpp').write_text(t)
write(R/'reference-binding.json',dict(purpose='Fully instrumented separate-clock reference, not historical/live observer',difference='one eligible-enabled diagnostic QPC immediately before existing completion QPC',referenceHeader=rec(ref/'trace_telemetry.hpp'),successorHeader=rec(C/'trace_telemetry.hpp')))
print('Exact callback bodies extracted; separate-clock reference prepared')
