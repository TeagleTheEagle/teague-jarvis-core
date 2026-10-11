import pathlib,sys,json,copy
from evidence_io import create_json
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'active-workspace.json').read_text())['code']);sys.path.insert(0,str(C))
from process_instances import InstanceTable
base=dict(pid=100,created='100',sequence='1',parentPid=50,parentSequence='0',image=r'D:\fixture\same.exe',startQpc=100,stopQpc=200,exitFiletime='200')
other=dict(base,created='210',sequence='2',startQpc=210,stopQpc=300,exitFiletime='300')
event=dict(pid=100,parentPid=0,name='same.exe',kind='stop',nativeTime='400',receivedQpc=400)
cases=[
('normal unique process',[base],event,'AMBIGUOUS'),
('PID reuse',[base,other],event,'AMBIGUOUS'),
('rapid PID reuse',[base,dict(other,created='201',startQpc=201)],event,'AMBIGUOUS'),
('parent PID reused with wrong sequence',[dict(base,parentRequired=True)],event,'REJECTED'),
('identical names',[base,other],event,'AMBIGUOUS'),
('identical paths',[base,other],event,'AMBIGUOUS'),
('concurrent identical helpers',[base,dict(base,pid=101,sequence='2')],event,'AMBIGUOUS'),
('delayed START',[base,other],dict(event,kind='start',parentPid=50),'AMBIGUOUS'),
('delayed STOP',[base],dict(event,nativeTime='999',receivedQpc=999),'AMBIGUOUS'),
('STOP after PID reuse',[base,other],event,'AMBIGUOUS'),
('exit before correlation',[base],event,'AMBIGUOUS'),
('matching retained handle',[dict(base,handleCreated='100')],event,'AMBIGUOUS'),
('no retained handle',[base],event,'AMBIGUOUS'),
('native entry available',[dict(base,nativeEntryQpc=150)],event,'AMBIGUOUS'),
('native entry delayed',[base],event,'AMBIGUOUS'),
('equal timestamp resolution',[base,dict(base,sequence='2')],event,'REJECTED'),
('out of order early STOP',[base],dict(event,receivedQpc=150),'UNMATCHED'),
('impossible lifetime',[dict(base,exitFiletime='99')],event,'REJECTED'),
('one compatible candidate',[base],event,'AMBIGUOUS'),
('two compatible candidates',[base,other],event,'AMBIGUOUS'),
('zero compatible candidates',[base],dict(event,pid=999),'UNMATCHED'),
('handle creation mismatch',[dict(base,handleCreated='101')],event,'REJECTED'),
('forged event key rejected',[base,other],dict(event,created='210',sequence='2'),'AMBIGUOUS'),
('known kernel identity alone cannot bind CIM',[dict(base,handleCreated='100',nativeEntryQpc=150)],event,'AMBIGUOUS')]
results=[]
for name,rows,raw,wanted in cases:
 before=copy.deepcopy(raw)
 try:v=InstanceTable(rows,'test-boot').correlate(raw);actual=v['result']
 except ValueError as ex:v=dict(error=str(ex));actual='REJECTED'
 assert actual==wanted,(name,actual,wanted)
 assert raw==before
 results.append(dict(case=name,safety='PASS',result=actual,evidence=v,actualWindowsPIDReuse=False))
create_json(R/'identity-matrix.json',dict(safetyChecks=len(results),safetyPassed=len(results),falseUniqueMatches=0,scope='Synthetic adversarial contract fixtures, NOT real process/ETW stress',positiveUniqueCIMAcceptance='NOT SATISFIED: no independently event-bound creation discriminator',currentSourceCapability='IDENTITY_INTEGRATION_STILL_DEFECTIVE',cases=results))
print(json.dumps(dict(safetyChecks=len(results),safetyPassed=len(results),falseUniqueMatches=0,positiveUniqueCIMAcceptance='NOT SATISFIED')))
