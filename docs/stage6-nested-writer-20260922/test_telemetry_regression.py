import copy,json,sys,uuid
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code']);sys.path.insert(0,str(C/'medium-checker'));import telemetry as t
source=next(Path('D:\\JARVIS-STAGE6-LIVE\\929ba9ea1c724c46b549d1dff12b517d\\code').glob('telemetry-tests-*/case-2-0'));m=t.load(source/'durable-manifest.json');w=t.load(source/'durable-result.json');v=t.load(source/'durable-telemetry.json');checks=[]
def test(name,fn,reject=False):
 try:fn();actual='PASS'
 except (ValueError,KeyError,TypeError,IndexError,OSError) as e:actual='REJECT'
 expected='REJECT' if reject else 'PASS';checks.append(dict(case=name,expected=expected,actual=actual));assert actual==expected,name
test('full native telemetry and hash binding',lambda:t.verify(source,'durable'))
test('known nearest rank',lambda:t.need(t.stats(list(range(1,21)),1)==dict(count=20,meanSeconds=10.5,maxSeconds=20,p95Seconds=19),'STATS'))
test('15 sample nearest rank is max',lambda:t.need(t.stats(list(range(15)),1)['p95Seconds']==14,'STATS'))
test('one sample',lambda:t.need(t.stats([2],2)['meanSeconds']==1,'STATS'))
for name,x,f in [('empty',[],1),('negative',[-1],1),('bool',[True],1),('frequency zero',[1],0),('frequency bool',[1],True),('frequency negative',[1],-2)]:test('stats '+name,lambda x=x,f=f:t.stats(x,f),True)
mutations=[
 ('unknown version',lambda v,m,w:v.update(schema='unknown')),
 ('frequency zero',lambda v,m,w:v.update(frequency=0)),
 ('frequency bool',lambda v,m,w:v.update(frequency=True)),
 ('overflow',lambda v,m,w:v.update(overflow=True)),
 ('expanded telemetry bound',lambda v,m,w:v.update(capacity=65537)),
 ('wrong bytes',lambda v,m,w:v.update(allocatedBytes=1)),
 ('missing snapshots',lambda v,m,w:v.update(snapshots=[])),
 ('missing initial',lambda v,m,w:v['snapshots'].pop(0)),
 ('missing final',lambda v,m,w:v['snapshots'].pop()),
 ('duplicate transition',lambda v,m,w:v['snapshots'].insert(1,copy.deepcopy(v['snapshots'][1]))),
 ('gap transition',lambda v,m,w:v['snapshots'].pop(1)),
 ('false queue depth',lambda v,m,w:v['snapshots'][1].__setitem__(4,60000)),
 ('unknown transition',lambda v,m,w:v['snapshots'][1].__setitem__(1,90)),
 ('backward ticks',lambda v,m,w:v['snapshots'][1].__setitem__(0,0)),
 ('float ticks',lambda v,m,w:v['snapshots'][1].__setitem__(0,1.5)),
 ('false wait count',lambda v,m,w:v['backpressure'].update(started=999)),
 ('interrupted wait',lambda v,m,w:v['backpressure'].update(interrupted=1)),
 ('false lag',lambda v,m,w:v['lag'].update(maxCompletionTicks=0)),
 ('false peak',lambda v,m,w:w.update(peakQueueItems=0)),
 ('missing timing',lambda v,m,w:m['segments'][0].pop('timing')),
 ('missing segment',lambda v,m,w:m['segments'].pop()),
 ('manifest conflict',lambda v,m,w:w['segments'][0]['timing'].update(flushEnd=0)),
 ('false flush aggregate',lambda v,m,w:w.update(flushSeconds=100000)),
 ('nonfinite hash',lambda v,m,w:w.update(hashSeconds=float('nan'))),
 ('false window',lambda v,m,w:v['windows'].update(lastFinal=0)),
 ('failed writer',lambda v,m,w:w.update(fault=1)),
]
for name,change in mutations:
 def run(change=change):
  a,b,c=copy.deepcopy((v,m,w));change(a,b,c);t.validate(a,b,c)
 test(name,run,True)
for name,key in [('flush order','flushEnd'),('hash order','hashEnd'),('enqueue order','enqueued')]:
 def run(key=key):
  a,b,c=copy.deepcopy((v,m,w));b['segments'][0]['timing'][key]=0;c['segments'][0]['timing'][key]=0;t.validate(a,b,c)
 test(name,run,True)
test('duplicate JSON key',lambda:t.json.loads('{"a":1,"a":2}',object_pairs_hook=t.pairs),True)
with (R/('telemetry-checks-'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(dict(status='PASS',passed=len(checks),checks=checks,fixture=str(source)),f,indent=2)
print(json.dumps(dict(status='PASS',checks=len(checks))))
