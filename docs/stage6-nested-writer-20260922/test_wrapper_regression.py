import copy,hashlib,json,sys,uuid
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code']);sys.path[:0]=[str(C/'medium-checker'),str(C)]
import checker_telemetry as ct
import telemetry as tv
base=json.loads((C/'validation-v2/medium-positive-fixture.json').read_text());b=copy.deepcopy(base['bundle']);d=json.loads((C/'medium-declaration.json').read_text());m=b['manifest'];w=b['writer'];tick=1000;rows=[];n=0;allsize=[];firstWrite=lastWrite=firstFinal=lastFinal=0
def snap(kind,id=0,raw=0,depth=0,count=0,size=0,queued=0,pending=0,pb=0):
 global tick
 tick+=1;rows.append([tick,kind,id,raw,depth,count,size,queued,pending,pb]);return tick
snap(0)
for s in m['segments']:
 for j in range(s['records']):
  n+=1;raw=100+n;allsize.append(raw);snap(1,n,raw,1,1,raw);start=snap(2,n,raw,0,1,raw);lastWrite=snap(3,n,raw)
  if not firstWrite:firstWrite=start
 enq=snap(4,s['number'],queued=1,pending=1,pb=s['bytes']);deq=snap(5,s['number'],pending=1,pb=s['bytes']);tick+=4
 end=snap(6,s['number']);s['timing']=dict(enqueued=enq,dequeued=deq,completed=end,flushBegin=deq+1,flushEnd=deq+2,hashBegin=deq+3,hashEnd=deq+4,waitBegin=0,waitEnd=0)
 if not firstFinal:firstFinal=deq
 lastFinal=end
snap(7);f=1000000
t=dict(schema=tv.SCHEMA,frequency=f,capacity=65536,snapshotBytes=80,allocatedBytes=5242880,overflow=False,backpressure=dict(started=0,completed=0,interrupted=0,ticks=0),lag=dict(dequeued=n,completed=n,dequeueTicks=n,maxDequeueTicks=1,completionTicks=2*n,maxCompletionTicks=2),windows=dict(firstWrite=firstWrite,lastWrite=lastWrite,firstFinal=firstFinal,lastFinal=lastFinal),snapshots=rows)
ref=dict(schema=tv.SCHEMA,name='kernel-authority-telemetry.json',sha256=hashlib.sha256(json.dumps(t).encode()).hexdigest());m['telemetry']=ref
w.update(telemetry=copy.deepcopy(ref),segments=[dict(copy.deepcopy(s),states=[0,1,2,3,4,5]) for s in m['segments']],peakQueueItems=1,peakQueueBytes=max(allsize),peakPending=1,peakPendingBytes=max(s['bytes'] for s in m['segments']),flushSeconds=len(m['segments'])/f,maxFlushSeconds=1/f,hashSeconds=len(m['segments'])/f)
# Synthetic fixture must include the full analyzer duplicate introduced in the live evidence.
b['qualification']['writer']=copy.deepcopy(w)
checks=[]
def test(name,fn,reject=False):
 try:fn();actual='PASS'
 except (ValueError,KeyError,TypeError,OSError,IndexError) as e:actual='REJECT'
 expected='REJECT' if reject else 'PASS';checks.append(dict(case=name,actual=actual,expected=expected));assert actual==expected,name
test('new wrapper preserves all lifecycle rules plus telemetry',lambda:ct.rules(b,t,d))
mutations=[('missing creator handle',lambda b,t:b['coverage']['handles'].pop()),('missing native entry',lambda b,t:b['coverage']['natives'].pop()),('missing kernel start',lambda b,t:b['events'].pop()),('heartbeat at limit',lambda b,t:b['hb'][0].update(interval=10)),('deadline violation',lambda b,t:b['qualification'].update(deadlineViolations=1)),('unknown helper class',lambda b,t:b['coverage']['expected'][0].update(role='OTHER_HELPER')),('cleanup not proved',lambda b,t:b['host'].update(matchingProcessCount=1)),('missing required measurement',lambda b,t:t.pop('lag')),('forged backpressure',lambda b,t:t['backpressure'].update(started=10)),('missing queue history',lambda b,t:t.update(snapshots=[])),('missing segment timing',lambda b,t:b['manifest']['segments'][0].pop('timing')),('kernel loss',lambda b,t:b['kernel'].update(eventsLost=1)),('forced CIM matching',lambda b,t:b['cim'][0].update(selected=['forced'])),('telemetry unknown version',lambda b,t:t.update(schema='old'))]
for name,mut in mutations:
 def run(mut=mut):
  x,y=copy.deepcopy((b,t));mut(x,y);ct.rules(x,y,d)
 test(name,run,True)
test('unsealed fresh run rejected',ct.evaluate,True)
test('compatibility view preserves original bundle',lambda:tv.need(b['manifest'].get('telemetry')==ref and 'timing' in b['manifest']['segments'][0],'MUTATED'))
# Independent disk hash mutations use fresh disposable copies, never the original run.
src=next(Path('D:\\JARVIS-STAGE6-LIVE\\929ba9ea1c724c46b549d1dff12b517d\\code').glob('telemetry-tests-*/case-0-0'));F=C/('binding-fixtures-'+uuid.uuid4().hex);F.mkdir()
for name in ('changed telemetry','missing telemetry','manifest reference','result conflict'):
 dest=F/name.replace(' ','-');dest.mkdir()
 for p in src.glob('durable-*.json'):(dest/p.name).write_bytes(p.read_bytes())
 if name=='changed telemetry':(dest/'durable-telemetry.json').write_text('{}')
 elif name=='missing telemetry':(dest/'durable-telemetry.json').rename(dest/'deliberately-absent.json')
 elif name=='manifest reference':
  x=tv.load(dest/'durable-manifest.json');x['telemetry']['name']='../escape';(dest/'durable-manifest.json').write_text(json.dumps(x))
 else:
  x=tv.load(dest/'durable-result.json');x['telemetry']['sha256']='0'*64;(dest/'durable-result.json').write_text(json.dumps(x))
 test(name,lambda dest=dest:tv.verify(dest,'durable'),True)
with (F/'synthetic-composition.json').open('x') as out:json.dump(dict(notLiveEvidence=True,bundle=b,telemetry=t,declaration=d),out)
with (R/('wrapper-checks-'+uuid.uuid4().hex+'.json')).open('x') as out:json.dump(dict(status='PASS',passed=len(checks),checks=checks,fixture=str(F)),out,indent=2)
print(json.dumps(dict(status='PASS',checks=len(checks))))
