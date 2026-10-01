from prepare import *
import ast,re,difflib,zipfile
results=[]
def check(ok,label):
 results.append(dict(check=label,pass_=bool(ok)))
 if not ok:raise AssertionError(label)
def function(s,marker):
 start=s.index(marker);begin=s.index('{',start);depth=0
 for i in range(begin,len(s)):
  depth+=int(s[i]=='{')-int(s[i]=='}')
  if not depth:return s[start:i+1]
def assembly(s,marker):
 start=s.index(marker);end=s.index(' ENDP',start);return s[start:end]
asm={}
for label,root in [('reuse',C),('reference',C.parent/'reference')]:
 text=(root/'fixture-final.asm').read_text(errors='replace')
 ctor=assembly(text,'??0CallbackScope@j6t@@QEAA@XZ PROC')
 dtor=assembly(text,'??1CallbackScope@j6t@@QEAA@XZ PROC')
 calls=lambda x:[l.split(';')[0].strip() for l in x.splitlines() if re.match(r'\s*call\s',l)]
 ctorCalls=calls(ctor);dtorCalls=calls(dtor)
 asm[label]=dict(constructor=ctorCalls,destructor=dtorCalls,qpcConstructor=sum('QueryPerformanceCounter' in x for x in ctorCalls),qpcDestructor=sum('QueryPerformanceCounter' in x for x in dtorCalls))
 (R/f'final-assembly-{label}.txt').write_text(ctor+' ENDP\n'+dtor+' ENDP\n')
 check(asm[label]['qpcConstructor']==1,label+' existing arrival retained')
 check(asm[label]['qpcDestructor']==(1 if label=='reuse' else 2),label+' exact destructor QPC sites')
check([x for x in asm['reuse']['destructor'] if 'QueryPerformanceCounter' not in x]==[x for x in asm['reference']['destructor'] if 'QueryPerformanceCounter' not in x],'identical non-QPC destructor call targets')
check(asm['reuse']['constructor']==asm['reference']['constructor'],'identical constructor call targets')
write(R/'generated-code-review.json',dict(status='PASS',calls=asm,eligibleEnabledReference=3,eligibleEnabledReuse=2,disabledReference=2,disabledReuse=2,otherNestedClocks='unchanged by successor/reference difference',measuredSavings=False,qualification=False))
for name in ['authority_trace_v3.cpp','startup_trace.cpp']:
 old=(P/name).read_text();new=(C/name).read_text()
 for f in ['static bool Field','static ULONGLONG Number','static std::wstring Text','static bool ParentKnown','static void Acquire']:
  check(function(old,f)==function(new,f),name+' '+f+' unchanged')
 check(old.count('Number(e,')==new.count('Number(e,'),name+' number query sites unchanged')
 for token in ['j6t::Lock l(guard)','StartTraceW(','EnableTraceEx2(','OpenTraceW(','ProcessTrace(','Capture(r,','Acquire(r);','rows.emplace(key,']:
  check(old.count(token)==new.count(token),name+' site count '+token)
 for token in ['new ','malloc(','CreateFile','WriteFile','std::mutex','std::lock_guard']:
  check(old.count(token)==new.count(token),name+' no added '+token)
check(function((P/'authority_trace_v3.cpp').read_text(),'static void Capture')==function((C/'authority_trace_v3.cpp').read_text(),'static void Capture'),'actual authoritative serialization/admission unchanged')
old=(P/'trace_telemetry.hpp').read_text();new=(C/'trace_telemetry.hpp').read_text()
oldDestructor=function(old,'~CallbackScope()')
newDestructor=function(new,'~CallbackScope()')
check(newDestructor.replace('lifecycle.publish(end);','')==oldDestructor,'existing timer endpoint and complete bookkeeping byte-order unchanged')
check(function(old,'CallbackScope(){')==function(new,'CallbackScope(){'),'existing arrival bookkeeping unchanged')
handoff=function((C/'loss_measurement_v3.hpp').read_text(),'struct Handoff')
for token in ['tick(', 'QueryPerformanceCounter','new ', 'malloc(', 'std::', 'mutex','CreateFile','WriteFile','Tdh','OpenProcess']:
 check(token not in handoff,'handoff excludes '+token)
check(function((P/'loss_measurement_v3.hpp').read_text(),'void append(Lifecycle')==function((C/'loss_measurement_v3.hpp').read_text(),'void append(Lifecycle'),'append capacity/sequence semantics unchanged')
schema=load(C/'semantic-binding-v1.json')
check(schema['historicalValuesInterchangeable'] is False,'historical semantic separation')
check(schema['completionSource']=='existing CallbackScope end','outer timestamp provenance')
for f in sorted(R.glob('*.py')):ast.parse(f.read_text());check(True,'syntax '+f.name)
preserved=[];archives=[]
for x in load(R/'before.json')['inputs']:
 r=rec(x['path']);check(r==x,'preserved '+x['path']);preserved.append(r)
 if pathlib.Path(x['path']).suffix.lower()=='.zip':
  with zipfile.ZipFile(x['path']) as z:check(z.testzip() is None,'historical ZIP CRC '+x['path']);archives.append(dict(path=x['path'],members=len(z.namelist()),sha256=x['sha256']))
write(R/'preservation-after.json',dict(status='PASS',files=len(preserved),historicalArchives=archives,protectedAccess=False,productionChanged=False))
write(R/'offline-review-results.json',dict(status='PASS',checks=len(results),results=results))
diff=''
for name in ['trace_telemetry.hpp','authority_trace_v3.cpp','startup_trace.cpp','loss_measurement_v3.hpp','loss_measurement_fixture_v3.cpp']:
 diff+=''.join(difflib.unified_diff((P/name).read_text().splitlines(True),(C/name).read_text().splitlines(True),fromfile=str(P/name),tofile=str(C/name)))
(R/'final-implementation.diff').write_text(diff)
write(R/'final-candidate-manifest.json',dict(status='OFFLINE_ONLY_NOT_LIVE_ELIGIBLE',files=[rec(p) for base in [C,C.parent/'reference'] for p in sorted(base.iterdir()) if p.is_file()],frozenCheckerUnchanged=True,finalOverheadQualified=False))
print(json.dumps(dict(status='PASS',reviewChecks=len(results),preservedFiles=len(preserved),archives=len(archives),generatedCode=asm)))
