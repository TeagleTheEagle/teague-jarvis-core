from pathlib import Path
import json
R=Path(__file__).parent
with (R/'analysis-failure.json').open('x') as f:json.dump(dict(status='FAIL',stage='InstanceTable construction',reason='HANDLE_CREATION_CONFLICT',cause='16 failed post-exit handle acquisitions serialized unavailable handleCreated as string zero; existing checker rejects a supplied mismatching creation time',runtimeRunRepeated=False),f,indent=2)
s=(R/'analyze.py').read_text()
s=s.replace("def save(name,v):\n with (R/name).open('x')", "O=R/'analysis-v2';O.mkdir()\ndef save(name,v):\n with (O/name).open('x')")
old="table=InstanceTable(kernel['rows'],kernel['session']);"
new='''
# Explicit format adapter for supporting CIM correlation ONLY. Raw kernel records remain
# unchanged and are independently subjected to strict acquisition/coverage checks below.
import copy
correlationRows=copy.deepcopy(kernel['rows']);adapted=[]
for row in correlationRows:
 if row.get('handleCreated')=='0':
  q.require(not row['handleRetained'] and row['reason']=='OPEN_PROCESS_FAILED' and row['openError']==87 and row['stopQpc']<row['handleAttemptBeginQpc']<=row['handleAttemptQpc'] and norm(row['image'])=='c:\\\\windows\\\\system32\\\\conhost.exe','INVALID_ABSENT_HANDLE_SENTINEL')
  adapted.append(dict(pid=row['pid'],created=row['created'],field='handleCreated',rawValue='0',adapterValue=None,reason='explicit unavailable handle-query sentinel; strictly qualified post-exit console helper'))
  row['handleCreated']=None
save('format-adaptation.json',adapted)
table=InstanceTable(correlationRows,kernel['session']);'''
assert old in s;s=s.replace(old,new)
with (R/'analyze_v2.py').open('x') as f:f.write(s)
