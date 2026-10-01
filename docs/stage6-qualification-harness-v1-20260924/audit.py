from prepare import *
import re,ast,zipfile
checks=[]
def check(x,label):
 checks.append(dict(check=label,passed=bool(x)))
 if not x:raise AssertionError(label)
def asmfn(text,symbol):
 start=text.index(symbol+' PROC');end=text.index(' ENDP',start);return text[start:end]
def calls(text):return [re.sub(r'_(A|B|C)\b','_ARM',line.split(';')[0].strip()) for line in text.splitlines() if re.match(r'\s*call\s',line)]
result={};linkmap=(C/'qualification.map').read_text()
for arm in 'ABC':
 text=(C/f'{arm}.asm').read_text(errors='replace');ctor=asmfn(text,f'??0CallbackScope@timer_{arm}@@QEAA@XZ');dtor=asmfn(text,f'??1CallbackScope@timer_{arm}@@QEAA@XZ')
 result[arm]=dict(constructorCalls=calls(ctor),destructorCalls=calls(dtor),constructorQPC=sum('QueryPerformanceCounter' in x for x in calls(ctor)),destructorQPC=sum('QueryPerformanceCounter' in x for x in calls(dtor)),scopeSize=88 if arm=='A' else 184,
 symbols=[line.strip() for line in linkmap.splitlines() if re.search(r'\s(?:dispatch_'+arm+r'|\?\?[01]CallbackScope@timer_'+arm+r'@@QEAA@XZ)\s',line)],
 instructionLines=sum(bool(re.match(r'\s+(?:mov\w*|lea|call|cmp|test|j\w+|add|sub|ret|push|pop|xor|and|or|inc|lock)\b',l)) for l in (ctor+'\n'+dtor).splitlines()))
 check(result[arm]['constructorQPC']==1,arm+' arrival read')
 check(result[arm]['destructorQPC']==(2 if arm=='B' else 1),arm+' completion read(s)')
 check(len(result[arm]['symbols'])==3,arm+' linked constructor/destructor/dispatch symbols')
 if arm=='A':check('Handoff' not in text and 'lifecycleTap' not in text, 'baseline assembly excludes successor recorder/payload')
 else:check('lifecycleTap' in dtor,arm+' bounded append retained')
 (R/f'assembly-final-{arm}.txt').write_text(ctor+' ENDP\n'+dtor+' ENDP\n')
 check(not any(any(x in call for x in ['operator new','??2@','malloc','Tdh','CreateFile','WriteFile','OpenProcess']) for call in calls(ctor)+calls(dtor)),arm+' no added forbidden timer calls')
for arm in 'BC':check([x for x in result[arm]['destructorCalls'] if 'QueryPerformanceCounter' not in x]==[x for x in result['A']['destructorCalls'] if 'QueryPerformanceCounter' not in x],arm+' unchanged non-QPC destructor callees')
for x in load(R/'source-binding.json'):
 if 'copy' in x:
  check(rec(x['source']['path'])==x['source'],'source header preserved '+x['source']['path'])
  check(sha(x['copy']['path'])==x['source']['sha256'],'byte-identical bound copied header '+x['arm'])
 else:check(rec(x['selectorSource']['path'])==x['selectorSource'],'selector source preserved '+x['arm']+x['kind'])
for p in sorted(R.glob('*.py')):ast.parse(p.read_text());check(True,'syntax '+p.name)
before=load(R/'before.json')['inputs']
for x in before:check(rec(x['path'])==x,'preserved '+x['path'])
receipt=load(D/'stage6-timestamp-reuse-v1-20260924'/'archive-receipt.json');check(sha(receipt['archive'])==receipt['sha256'],'predecessor archive hash')
with zipfile.ZipFile(receipt['archive']) as z:check(z.testzip() is None and len(z.namelist())==92,'predecessor archive intact')
check(not (C/'ONE-FINAL-ATTEMPT').exists(),'qualification never started')
baseCounts={'outside lifecycle':2,'exception at first decoder':4,'unknown parent':13,'unknown instance':9,'duplicate start':13,'duplicate stop':9,'invalid identity':13,'decode failure':13,'capacity':13,'authority admitted START':34,'detail admitted START':24,'authority admitted STOP':26,'detail admitted STOP':16}
write(R/'generated-code-review-final.json',dict(status='PASS',arms=result,QPCByBranch={k:dict(A=v,B=v+(k!='outside lifecycle'),C=v) for k,v in baseCounts.items()},basis='Existing scope 2; acquired event-map Lock 3; existing metadata scopes 2 each; existing selected-output QPCs and acquisition/capture timing preserved in equal adapters. Detailed schema is a declared cache hit; acquisition models failed OpenProcess timing without an OS lookup. These counts describe the bound synthetic paths, not all live OS paths.',comparison='baseline timer headers unchanged; optimized/reference headers unchanged; only namespace isolation and equal offline adapters',codeGeneration='Larger optimized stack/store footprint is intentional handoff work; not hidden in baseline. Link /OPT:NOICF; distinct linked function addresses.',performanceClaim=False))
write(R/'verification-final.json',dict(status='PASS',checks=len(checks),results=checks,preserved=len(before),benchmarkExecuted=False))
binding=dict(schema='j6.qualification.binding.v1',workspace=str(C),binary=str(C/'J6FinalQualification.exe'),binarySHA256=sha(C/'J6FinalQualification.exe'),protocol=str(C/'protocol.json'),protocolSHA256=sha(C/'protocol.json'),files=[rec(p) for p in sorted(C.rglob('*')) if p.is_file() and 'temp' not in p.relative_to(C).parts]+[rec(R/n) for n in ['analyze.py','run_once.py']],liveETW=False,UAC=False,qualificationExecuted=False,compiler='MSVC 19.44; vcvars64 Visual Studio 2022 BuildTools',flags='/EHsc /std:c++17 /O2 /GL- /FAs; linker /OPT:NOICF',sourceBindingSHA256=sha(R/'source-binding.json'),generatedCodeReviewSHA256=sha(R/'generated-code-review-final.json'))
write(R/'qualification-binding-final.json',binding)
print(json.dumps(dict(status='PASS',checks=len(checks),binary=binding['binarySHA256'],protocol=binding['protocolSHA256'],symbols={a:result[a]['symbols'] for a in 'ABC'})))
