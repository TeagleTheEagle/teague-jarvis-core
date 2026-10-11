import json,copy,uuid,hashlib
from pathlib import Path
import combined as c
R=Path(__file__).parent;P=R.parent/'stage6-creator-image-20260922';C=Path(json.loads((R/'preflight.json').read_text())['code'])
oldroot=Path(json.loads((P/'run.json').read_text())['path']);oldhost=P/'final'/json.loads((P/'preservation-after.json').read_text())['hostRun']/'final-host-state.json'
base=c.read_bundle(oldroot,P/'analysis',oldhost);tests=[]
def case(name,mutate,want='FAIL'):
 b=copy.deepcopy(base);mutate(b)
 try:r=c.validate(b);actual='PASS';reason=None
 except (ValueError,KeyError) as e:actual='FAIL';reason=str(e)
 tests.append(dict(case=name,expected=want,actual=actual,reason=reason,passed=actual==want,kind='mutated copy of preserved evidence; not current acceptance'))
case('complete preserved control',lambda b:None,'PASS')
case('missing kernel START',lambda b:b['events'].pop(next(i for i,x in enumerate(b['events']) if x['kind']=='start')))
case('missing kernel STOP',lambda b:b['events'].pop(next(i for i,x in enumerate(b['events']) if x['kind']=='stop')))
case('durability failure',lambda b:b['writer'].update(fault=207))
case('empty required handles',lambda b:b['coverage'].update(handles=[]))
case('empty required images',lambda b:[h.update(image='') for h in b['coverage']['handles']])
case('empty native entries',lambda b:b['coverage'].update(natives=[]))
case('identity ambiguity',lambda b:b['kernel']['rows'].append(copy.deepcopy(b['kernel']['rows'][0])))
case('retained exit contradiction',lambda b:next(h for h in b['coverage']['handles'] if h['retained']).update(exitCode=999))
case('helper contradiction',lambda b:next(h for h in b['coverage']['handles'] if h['source']=='tracer-opened-handle' and h['retained']).update(handleCreated='1'))
case('backlog exceeds hard limit',lambda b:b['writer'].update(peakPending=3))
case('backlog fault',lambda b:b['writer'].update(fault=109))
case('incomplete manifest',lambda b:b['manifest']['segments'].pop())
case('result segment altered',lambda b:b['writer']['segments'][0].update(sha256='0'*64))
case('state skipped',lambda b:b['writer']['segments'][0].update(states=[0,1,2,4,5]))
case('cleanup failure',lambda b:b['launch'].update(workerExited=False))
case('host process remains',lambda b:b['host'].update(matchingProcessCount=1))
case('trace remains',lambda b:b['host'].update(diagnosticTraceCount=1))
case('queue not drained',lambda b:b['writer'].update(remaining=1))
case('secondary queue not drained',lambda b:b['app']['queue'].update(remaining=1))
case('heartbeat stale',lambda b:b['hb'][0].update(interval=10))
case('deadline violation',lambda b:b['qualification'].update(deadlineViolations=1))
case('unclassified helper',lambda b:b['coverage']['expected'][0].update(role='OTHER_INDIRECT_HELPER'))
case('inventory omission',lambda b:b['coverage']['expected'].pop())
case('forced CIM match',lambda b:b['cim'][0].update(result='UNIQUE_CORRELATED',selected=None,independentEventBoundProof=False))
fixture=C/('combined-faults-'+uuid.uuid4().hex);fixture.mkdir()
for name in ('sequence-gap','duplicate-sequence','missing-segment','corrupt-segment','extra-segment','missing-seal'):
 dest=fixture/name;dest.mkdir()
 for p in oldroot.glob('kernel-authority-*'):
  with (dest/p.name).open('xb') as f:f.write(p.read_bytes())
 m=c.q.load(dest/'kernel-authority-manifest.json');first=dest/m['segments'][0]['name']
 if name=='missing-segment':first.unlink()
 elif name=='corrupt-segment':first.write_bytes(b'!'+first.read_bytes()[1:])
 elif name=='extra-segment':(dest/'kernel-authority-999.jsonl').write_bytes(b'{}\n')
 elif name=='missing-seal':(dest/'kernel-authority-seal.json').unlink()
 else:
  lines=first.read_bytes().splitlines(True);idx=0 if name=='sequence-gap' else 1;row=json.loads(lines[idx]);row['seq']=999 if idx==0 else 1;lines[idx]=(json.dumps(row,separators=(',',':'))+'\n').encode();data=b''.join(lines);first.write_bytes(data)
  oldsize=m['segments'][0]['bytes'];m['segments'][0].update(bytes=len(data),sha256=c.q.sha(first));m['bytes']+=len(data)-oldsize
  (dest/'kernel-authority-manifest.json').write_text(json.dumps(m));seal=c.q.load(dest/'kernel-authority-seal.json');seal['manifestSHA256']=c.q.sha(dest/'kernel-authority-manifest.json');(dest/'kernel-authority-seal.json').write_text(json.dumps(seal))
 try:c.read_bundle(dest,P/'analysis',oldhost);actual='PASS';reason=None
 except (ValueError,OSError,KeyError) as e:actual='FAIL';reason=str(e)
 tests.append(dict(case=name,expected='FAIL',actual=actual,reason=reason,passed=actual=='FAIL',fixture=str(dest)))
with (R/'combined-tests-v2.json').open('x') as f:json.dump(dict(total=len(tests),passed=sum(x['passed'] for x in tests),tests=tests,fixtureRoot=str(fixture)),f,indent=2)
print(json.dumps(dict(total=len(tests),passed=sum(x['passed'] for x in tests),failures=[x for x in tests if not x['passed']])))
assert all(x['passed'] for x in tests)
