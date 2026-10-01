import json,copy,importlib.util,hashlib,uuid,shutil
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-durable-kernel-20260921';C=Path(json.loads((R/'preflight.json').read_text())['code']);root=Path(json.loads((R/'run.json').read_text())['path'])
spec=importlib.util.spec_from_file_location('q',P/'qualification.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
original=json.loads((R/'qualification-inputs.json').read_text());results=[]
def lineage(k):
 ready=q.load(root/'etw-ready.json');byseq={r['sequence']:r for r in k['rows']}
 for r in k['rows']:
  if r['parentPid']==ready['rootPid']:q.require(int(r['created'])>=int(ready['rootCreated']),'ROOT_TIME')
  else:
   p=byseq.get(r['parentSequence']);q.require(p and p['pid']==r['parentPid'] and int(p['created'])<=int(r['created'])<=int(p['exitFiletime']),'PARENT_INSTANCE')
def evaluate(d):
 x=q.qualify(**d);lineage(d['kernel']);return x
def case(name,change,expected):
 d=copy.deepcopy(original);change(d)
 try:r=evaluate(d);actual='PASS';reason=None
 except (ValueError,KeyError) as e:actual='FAIL';reason=str(e)
 results.append(dict(case=name,expected=expected,actual=actual,reason=reason,passed=actual==expected,kind='mutated copy of fresh evidence; not a new process run'))
 assert actual==expected,(name,actual,reason)
key=[original['kernel']['session'],original['handles'][0]['pid'],original['handles'][0]['created'],next(r['sequence'] for r in original['kernel']['rows'] if r['pid']==original['handles'][0]['pid'])]
case('kernel complete + verification + synthetic event-bound CIM unique',lambda d:d.update(cim=[dict(result='UNIQUE_CORRELATED',selected=key,independentEventBoundProof=True)]),'PASS')
case('kernel complete + verification + CIM ambiguous',lambda d:d.update(cim=[dict(result='AMBIGUOUS',selected=None)]),'PASS')
case('kernel complete + verification + CIM unmatched',lambda d:d.update(cim=[dict(result='UNMATCHED',selected=None)]),'PASS')
case('missing kernel START',lambda d:d['events'].pop(next(i for i,e in enumerate(d['events']) if e['kind']=='start')),'FAIL')
case('missing kernel STOP',lambda d:d['events'].pop(next(i for i,e in enumerate(d['events']) if e['kind']=='stop')),'FAIL')
case('ETW loss',lambda d:d['kernel'].update(eventsLost=1),'FAIL')
case('duplicate START',lambda d:d['events'].append(copy.deepcopy(next(e for e in d['events'] if e['kind']=='start'))),'FAIL')
case('authoritative identity ambiguity',lambda d:d['events'][0].update(sequence=d['events'][1]['sequence'] if d['events'][1]['sequence']!=d['events'][0]['sequence'] else '1'),'FAIL')
case('retained-handle contradiction',lambda d:d['handles'][0].update(exitCode=999),'FAIL')
case('native-entry contradiction',lambda d:d['natives'][0].update(entryQpc=1),'FAIL')
case('missing native entry',lambda d:d['natives'].pop(0),'FAIL')
case('proven CIM contradiction',lambda d:d['cim'][0].update(provenContradiction=True),'FAIL')
case('forced CIM unique',lambda d:d.update(cim=[dict(result='UNIQUE_CORRELATED',selected=key,independentEventBoundProof=False)]),'FAIL')
case('ambiguous CIM must not select identity',lambda d:d['cim'][0].update(selected=key),'FAIL')
case('parent sequence contradiction',lambda d:d['kernel']['rows'][0].update(parentSequence='0'),'FAIL')
case('kernel handle contradiction',lambda d:next(r for r in d['kernel']['rows'] if r['handleRetained']).update(metadataError=5),'FAIL')
case('trace buffer loss',lambda d:d['kernel'].update(buffersLost=1),'FAIL')

# Two complete lifetimes with the same PID, distinct creation/sequence, in a controlled fixture.
# This tests identity keys, not an actual OS reuse claim.
def reuse(d):
 r=copy.deepcopy(next(r for r in d['kernel']['rows'] if r['pid']==original['handles'][0]['pid']));old=copy.deepcopy(r)
 delta=100000;newseq=str(max(int(v['sequence']) for v in d['kernel']['rows'])+1)
 r.update(created=str(int(r['created'])+delta),sequence=newseq,exitFiletime=str(int(r['exitFiletime'])+delta),startQpc=r['startQpc']+delta,stopQpc=r['stopQpc']+delta,signalObservedQpc=r['signalObservedQpc']+delta,handleAttemptQpc=r['handleAttemptQpc']+delta,handleAttemptBeginQpc=r['handleAttemptBeginQpc']+delta)
 # Place synthetic next lifetime after old exit and still within the real long-lived parent.
 shift=int(old['exitFiletime'])-int(old['created'])+10000
 shiftq=old['stopQpc']-old['startQpc']+10000
 r.update(created=str(int(old['created'])+shift),exitFiletime=str(int(old['exitFiletime'])+shift),startQpc=old['startQpc']+shiftq,stopQpc=old['stopQpc']+shiftq,signalObservedQpc=old['signalObservedQpc']+shiftq,handleAttemptQpc=old['handleAttemptQpc']+shiftq,handleAttemptBeginQpc=old['handleAttemptBeginQpc']+shiftq)
 edges=[copy.deepcopy(e) for e in d['events'] if (e['pid'],e['created'])==(old['pid'],old['created'])]
 for e in edges:
  e.update(created=r['created'],sequence=newseq,eventQpc=r['startQpc'] if e['kind']=='start' else r['stopQpc'],exitFiletime='0' if e['kind']=='start' else r['exitFiletime'])
 d['events'].extend(edges);d['kernel']['rows'].append(r)
case('same PID distinct creation/sequence fixture',reuse,'PASS')
def wrong_reused_stop(d):
 reuse(d);d['events'][-1]['created']=original['handles'][0]['created']
case('reused PID STOP bound to wrong incarnation',wrong_reused_stop,'FAIL')

workspace=C/('fault-fixtures-'+uuid.uuid4().hex);workspace.mkdir()
for name in ('sequence-gap','missing-segment','corrupt-segment','missing-seal'):
 dest=workspace/name;dest.mkdir()
 for p in root.glob('kernel-authority-*'):
  with (dest/p.name).open('xb') as f:f.write(p.read_bytes())
 manifest=q.load(dest/'kernel-authority-manifest.json');first=dest/manifest['segments'][0]['name']
 if name=='missing-segment':first.unlink()
 elif name=='corrupt-segment':
  b=first.read_bytes();first.write_bytes(b'!'+b[1:])
 elif name=='missing-seal':(dest/'kernel-authority-seal.json').unlink()
 else:
  lines=first.read_bytes().splitlines(keepends=True);row=json.loads(lines[0]);row['seq']=999
  lines[0]=(json.dumps(row,separators=(',',':'))+'\n').encode();data=b''.join(lines);first.write_bytes(data)
  old=manifest['segments'][0]['bytes'];manifest['segments'][0].update(bytes=len(data),sha256=q.sha(first));manifest['bytes']+=len(data)-old
  (dest/'kernel-authority-manifest.json').write_text(json.dumps(manifest));seal=q.load(dest/'kernel-authority-seal.json');seal['manifestSHA256']=q.sha(dest/'kernel-authority-manifest.json');(dest/'kernel-authority-seal.json').write_text(json.dumps(seal))
 try:q.stream(dest,'kernel-authority');actual='PASS';reason=None
 except (ValueError,OSError) as e:actual='FAIL';reason=str(e)
 results.append(dict(case=name,expected='FAIL',actual=actual,reason=reason,passed=actual=='FAIL',path=str(dest)));assert actual=='FAIL'
with (R/'contract-tests.json').open('x') as f:json.dump(dict(results=results,passed=sum(r['passed'] for r in results),total=len(results),fixtureRoot=str(workspace),realPIDReuseObserved=False),f,indent=2)
print(json.dumps(dict(passed=len(results),realPIDReuseObserved=False)))
