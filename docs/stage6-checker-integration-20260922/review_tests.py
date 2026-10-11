import collections,contextlib,copy,hashlib,io,json,sys
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'preflight.json').read_text(encoding='utf8'));C=Path(pre['candidate']);sys.path.insert(0,str(C));import checker_v2 as c
base=c.load(C/'positive-fixture.json');rows=[]
def case(name,call,want='REJECT'):
 try:call();actual='PASS';reason=None
 except (ValueError,KeyError,OSError,TypeError) as e:actual='REJECT';reason=str(e)
 rows.append(dict(name=name,expected=want,actual=actual,reason=reason,passed=actual==want))
 if actual!=want:raise RuntimeError('UNEXPLAINED_REVIEW_FAILURE:'+name)
def mutation(name,fn):
 e=copy.deepcopy(base);fn(e['bundle']);case(name,lambda:c.rules(e,compare_payload=False))
for field in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult'):
 def change(b,field=field):b['kernel'][field]=1;b['structural']['kernel']=copy.deepcopy(b['kernel'])
 mutation('kernel rejects '+field,change)
for kind in ('start','stop'):
 def remove(b,kind=kind):
  b['events'].pop(next(i for i,x in enumerate(b['events']) if x['kind']==kind));b['structural']['events']=copy.deepcopy(b['events']);b['coverage']['events']=copy.deepcopy(b['events'])
  total=len(b['events']);b['manifest']['accepted']=total;b['writer'].update(attempted=total,accepted=total,written=total)
 mutation('missing '+kind+' even with adjusted aggregate counts',remove)
mutation('ETW stop not requested',lambda b:(b['kernel'].update(requestedStop=False),b['structural']['kernel'].update(requestedStop=False)))
mutation('native explicit fault',lambda b:b['coverage']['natives'][0].update(fault=True))
mutation('native deadline exceeded',lambda b:b['coverage']['natives'][0].update(deadlineExceeded=True))
mutation('observer unhealthy',lambda b:b['app'].update(success=False))
mutation('secondary queue residue',lambda b:b['app']['queue'].update(remaining=1))
mutation('secondary collector errors',lambda b:b['app'].update(tapErrors=1))
mutation('finalizer limit exceeded',lambda b:b['writer'].update(peakPending=3))
mutation('writer capacity exceeded',lambda b:b['writer'].update(peakQueueItems=65537))
mutation('heartbeat age stale',lambda b:b['health'][0].update(age=10.0))
mutation('early capture not before entry',lambda b:next(h for h in b['coverage']['handles'] if h['source']=='creator-owned-handle').update(identityPersistedQpc=9223372036854775807))
mutation('postexit generic access denied not eligible',lambda b:next(h for h in b['coverage']['handles'] if not h['retained']).update(openError=5))
mutation('tracer retained handle not signaled',lambda b:next(h for h in b['coverage']['handles'] if h['source']=='tracer-opened-handle' and h['retained']).update(exited=False))
mutation('creator handle not closed',lambda b:next(h for h in b['coverage']['handles'] if h['source']=='creator-owned-handle').update(closed=False))
for attr,value in [('verificationStatus','FAIL'),('schema','stage6-small-combined-v999'),('acceptanceSealed',True)]:
 e=copy.deepcopy(base);e['payload'][attr]=value;case('payload '+attr+' substitution',lambda e=e:c.rules(e))
for text in ('{"x":Infinity}','{"x":-Infinity}','{"x":true,"x":false}'):
 case('strict JSON '+text,lambda text=text:c.decode(text))
for args in ([],['--legacy'],['--replay-validated-small','--ignore-errors']):
 old=sys.argv;sys.argv=['checker_v2.py']+args
 try:
  output=io.StringIO()
  with contextlib.redirect_stdout(output):rc=c.main()
  case('explicit dispatch '+str(args),lambda rc=rc:c.need(rc==1,'BAD_CLI_DISPATCH'),'PASS')
 finally:sys.argv=old
hist=R.parent/'stage6-identity-capacity-recalibration-20260921/identity-summary.json';h=c.load(hist)
with (R/'historical-identity-preservation.json').open('x',encoding='utf8') as f:json.dump(dict(path=str(hist),sha256=c.sha(hist),evidence=h),f,indent=2)
with (R/'review-tests.json').open('x',encoding='utf8') as f:json.dump(dict(total=len(rows),passed=sum(x['passed'] for x in rows),failed=sum(not x['passed'] for x in rows),skipped=0,tests=rows),f,indent=2)
replay=c.replay()
with (R/'replay.json').open('x',encoding='utf8') as f:json.dump(replay,f,indent=2)
print(json.dumps(dict(total=len(rows),passed=sum(x['passed'] for x in rows),failed=sum(not x['passed'] for x in rows),replay=replay['status'],classes=replay['rules']['counts'])))
