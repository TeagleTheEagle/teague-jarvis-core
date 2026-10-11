from prepare import *
for root,label in [(C,'reuse'),(C.parent/'reference','reference')]:
 p=root/'trace_telemetry.hpp';s=p.read_text();shutil.copy2(p,R/f'build-attempt-1-{label}-header.hpp')
 assert s.count(' CallbackScope(){')==1 and 'j6m::Handoff lifecycle;' not in s
 s=s.replace(' CallbackScope(){',' j6m::Handoff lifecycle;\n CallbackScope(){');p.write_text(s)
print('Restored missing payload declaration after original timer members; failed headers retained')
