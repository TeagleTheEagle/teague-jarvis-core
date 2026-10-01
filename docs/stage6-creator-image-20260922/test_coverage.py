import copy,json
from pathlib import Path
from coverage import coverage
R=Path(__file__).parent
expected=[];handles=[];native=[];events=[]
for i,role in enumerate(('DIRECT_PROBE','DIRECT_WORKER','OS_CONSOLE_HELPER'),1):
 x=dict(pid=i,created=str(100+i),sequence=str(i),role=role,image='D:\\test\\'+role+'.exe',startQpc=10,stopQpc=50,exitFiletime=str(200+i),exitCode=0,parentPid=500,parentVerified=True);expected.append(x)
 handles.append(dict(pid=i,created=x['created'],handleCreated=x['created'],image=x['image'],imageError=0,source='tracer-opened-handle' if role=='OS_CONSOLE_HELPER' else 'creator-owned-handle',handlePid=i,creatorPid=500,processState=258,success=True,handleIdentity='123',handleAcquiredQpc=11,queryBeginQpc=12,queryEndQpc=13,identityPersistedQpc=14,retained=True,exited=True,closed=True,exitFiletime=x['exitFiletime'],exitCode=0))
 if role!='OS_CONSOLE_HELPER':native.append(dict(pid=i,created=x['created'],entryQpc=20,exitFiletime=x['exitFiletime'],exitCode=0,fault=False,deadlineExceeded=False,finalWait=0,events=[dict(event='PE_ENTRY_EXECUTED')]))
 for kind in ('start','stop'):events.append(dict(pid=i,created=x['created'],sequence=str(i),kind=kind))
base=dict(expected=expected,events=events,handles=handles,natives=native,mapping={});results=[]
def case(name,mutate,want,reason=None):
 d=copy.deepcopy(base);mutate(d);r=coverage(**d);ok=r['status']==want and (not reason or reason in r['errors']);results.append(dict(name=name,expected=want,actual=r['status'],errors=r['errors'],passed=ok,coverage=r))
def noop(d):pass
case('empty handles',lambda d:d.update(handles=[]),'FAIL','MISSING_REQUIRED_HANDLE_EVIDENCE')
case('empty native',lambda d:d.update(natives=[]),'FAIL','MISSING_REQUIRED_NATIVE_EVIDENCE')
case('empty images',lambda d:[h.update(image='') for h in d['handles']],'FAIL','MISSING_REQUIRED_IMAGE_EVIDENCE')
case('missing start',lambda d:d['events'].pop(0),'FAIL','MISSING_REQUIRED_START_EVIDENCE')
case('missing stop',lambda d:d['events'].pop(1),'FAIL','MISSING_REQUIRED_STOP_EVIDENCE')
case('optional annotation absent',noop,'PASS')
case('console native not applicable',noop,'PASS')
case('required valid',noop,'PASS')
case('contradictory exit',lambda d:d['handles'][0].update(exitCode=1),'FAIL','CONTRADICTORY_EXIT_EVIDENCE')
case('partial set',lambda d:d['handles'].pop(1),'FAIL')
case('worker missing image',lambda d:d['handles'][1].update(image=''),'FAIL')
case('helper missing handle',lambda d:d['handles'].pop(2),'FAIL')
case('exact complete coverage',noop,'PASS')
case('PID reused later handle',lambda d:d['handles'][0].update(created='999',handleCreated='999'),'FAIL')
case('helper exits before query',lambda d:d['handles'][2].update(image='',imageError=87),'FAIL')
case('worker exits before handle query',lambda d:d['handles'][1].update(handleCreated=''),'FAIL')
case('retained handle valid after exit',noop,'PASS')
case('all verification empty',lambda d:d.update(handles=[],natives=[]),'FAIL')
case('empty requirements',lambda d:d.update(expected=[],handles=[],natives=[],events=[]),'FAIL')
case('same basename wrong directory',lambda d:d['handles'][0].update(image='C:\\untrusted\\DIRECT_PROBE.exe'),'FAIL')
case('native contradicts entry',lambda d:d['natives'][0].update(entryQpc=99),'FAIL')
case('duplicate handle',lambda d:d['handles'].append(copy.deepcopy(d['handles'][0])),'FAIL')
case('parent not verified',lambda d:d['expected'][0].update(parentVerified=False),'FAIL')
case('qualified helper after exit',lambda d:d['handles'][2].update(qualifiedPostExit=True,reason='OPEN_PROCESS_FAILED',openError=87,attemptBegin=51,attemptEnd=52,handleCreated='',image='',retained=False),'PASS')
case('unqualified helper timing',lambda d:d['handles'][2].update(qualifiedPostExit=True,reason='OPEN_PROCESS_FAILED',openError=87,attemptBegin=49,attemptEnd=52,handleCreated='',image='',retained=False),'FAIL')
case('worker cannot claim helper exception',lambda d:d['handles'][1].update(qualifiedPostExit=True,reason='OPEN_PROCESS_FAILED',openError=87,attemptBegin=51,attemptEnd=52,handleCreated='',image='',retained=False),'FAIL')

for label,error in [('access denied',5),('invalid handle',6),('already exited',31),('insufficient buffer',122),('unexpected error',999)]:
 case(label,lambda d,e=error:d['handles'][0].update(image='',imageError=e,success=False),'FAIL')
case('malformed relative path',lambda d:d['handles'][0].update(image='DIRECT_PROBE.exe'),'FAIL')
case('NUL image',lambda d:d['handles'][0].update(image='D:\\test\\x\x00.exe'),'FAIL')
case('query after exit',lambda d:d['handles'][0].update(queryBeginQpc=51,queryEndQpc=52),'FAIL')
case('persist after native entry',lambda d:d['handles'][0].update(identityPersistedQpc=21),'FAIL')
case('direct source cannot be tracer',lambda d:d['handles'][0].update(source='tracer-opened-handle'),'FAIL')
case('helper tracer source missing',lambda d:d['handles'][2].update(source=''),'FAIL')
case('helper image absent is not NA',lambda d:d['handles'][2].update(image=''),'FAIL')
case('helper live image query after exit',lambda d:d['handles'][2].update(queryBeginQpc=51,queryEndQpc=52),'FAIL')
case('other helper not implicitly console',lambda d:d['expected'][2].update(role='OTHER_INDIRECT_HELPER'),'FAIL')
case('creator PID differs',lambda d:d['handles'][0].update(creatorPid=999),'FAIL')
case('handle PID differs',lambda d:d['handles'][0].update(handlePid=999),'FAIL')
case('creation mismatches',lambda d:d['handles'][0].update(handleCreated='999'),'FAIL')
case('probe already signaled at capture',lambda d:d['handles'][0].update(processState=0),'FAIL')

with (R/'coverage-tests.json').open('x') as f:json.dump(dict(total=len(results),passed=sum(x['passed'] for x in results),results=results,kind='deterministic fixtures, not real process reuse'),f,indent=2)
print(json.dumps(dict(total=len(results),passed=sum(x['passed'] for x in results))))
assert all(x['passed'] for x in results)
