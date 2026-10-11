import copy,hashlib,json,os,subprocess,sys,uuid
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-checker-integration-20260922'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
pre=load(R/'preflight.json');C=Path(pre['code']);K=Path(pre['checker']);old=Path(pre['originalChecker']);root=Path(pre['root'])
V=C/'validation';V.mkdir();(C/'fixtures').mkdir()
for name in ('positive-fixture.json','binding.json','frozen_reference.py'):(V/name).write_bytes((old/name).read_bytes())
driver=(old/'test_candidate.py').read_text(encoding='utf8');driver=driver.replace('import checker_v2 as c',f"import sys;sys.path.insert(0,{str(old)!r})\nimport checker_v2 as c")
(V/'legacy_tests.py').write_text(driver,encoding='utf8')
r=subprocess.run([sys.executable,'-B',str(V/'legacy_tests.py')],capture_output=True,text=True,timeout=60)
save(R/'legacy-83-execution.json',dict(command=r.args,exit=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0
review=(P/'review_tests.py').read_text(encoding='utf8')
begin=review.index('R=Path(__file__).parent;');end=review.index('base=c.load',begin)
review=review[:begin]+f"R=Path(__file__).parent;C=Path({str(old)!r});sys.path.insert(0,str(C));import checker_v2 as c\n"+review[end:]
review=review.replace("hist=R.parent/'stage6-identity-capacity-recalibration-20260921/identity-summary.json'",f"hist=Path({str(R.parent/'stage6-identity-capacity-recalibration-20260921/identity-summary.json')!r})")
(V/'legacy_review.py').write_text(review,encoding='utf8');r=subprocess.run([sys.executable,'-B',str(V/'legacy_review.py')],capture_output=True,text=True,timeout=60)
save(R/'legacy-31-execution.json',dict(command=r.args,exit=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0
sys.path[:0]=[str(K),str(C)];import checker_medium as m;import fresh_binding as fb
base=load(old/'positive-fixture.json');b=base['bundle'];decl=load(C/'medium-declaration.json')
# Synthetic checker fixture only: 48 additional explicit direct instances, no processes launched.
key=lambda x:(x['pid'],x['created'])
template=next(x for x in b['coverage']['expected'] if x['role']=='DIRECT_PROBE');oldkey=key(template);oldseq=template['sequence']
def clone(obj,pid,created,seq):
 if isinstance(obj,dict):return {k:clone(v,pid,created,seq) for k,v in obj.items()}
 if isinstance(obj,list):return [clone(v,pid,created,seq) for v in obj]
 if type(obj) is int and obj==oldkey[0]:return pid
 if type(obj) is str and obj==oldkey[1]:return created
 if type(obj) is str and obj==oldseq:return seq
 return obj
for i in range(48):
 pid=100000+i;created=str(int(oldkey[1])+i+1);seq=str(1000000+i)
 for container in (b['kernel']['rows'],b['coverage']['expected'],b['coverage']['handles'],b['coverage']['natives'],b['structural']['handles'],b['structural']['natives']):
  original=next(x for x in container if key(x)==oldkey);container.append(clone(original,pid,created,seq))
 for event in [x for x in list(b['events']) if key(x)==oldkey]:b['events'].append(clone(event,pid,created,seq))
b['structural'].update(events=copy.deepcopy(b['events']),kernel=copy.deepcopy(b['kernel']));b['coverage']['events']=copy.deepcopy(b['events'])
b['qualification']['realNativeCount']=65
F=C/'fixtures'/('medium-positive-'+uuid.uuid4().hex);F.mkdir();segments=[];totalbytes=0
for number,start in enumerate(range(0,len(b['events']),18)):
 group=b['events'][start:start+18];data=b''.join((json.dumps(dict(seq=start+j+1,raw=x),separators=(',',':'))+'\n').encode() for j,x in enumerate(group));name=f'kernel-authority-{number}.jsonl';(F/name).write_bytes(data);totalbytes+=len(data)
 segments.append(dict(number=number,name=name,first=start+1,last=start+len(group),records=len(group),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),states=[0,1,2,3,4]))
b['manifest'].update(accepted=len(b['events']),bytes=totalbytes,segments=segments);b['writer'].update(attempted=len(b['events']),accepted=len(b['events']),written=len(b['events']),segments=[dict(s,states=[0,1,2,3,4,5]) for s in segments])
save(F/'kernel-authority-manifest.json',b['manifest']);save(F/'kernel-authority-result.json',b['writer']);save(F/'kernel-authority-seal.json',dict(manifestSHA256=fb.sha(F/'kernel-authority-manifest.json'),accepted=len(b['events']),segments=len(segments)))
base.update(schema=m.VERSION,adapter='stage6-medium-combined-v1');base['payload']=m.adapter.validate(b,declaration=decl)
save(V/'medium-positive-fixture.json',base)
tests=[]
def test(name,fn,want='REJECT'):
 try:fn();actual='PASS';reason=None
 except (ValueError,KeyError,TypeError,OSError) as e:actual='REJECT';reason=str(e)
 tests.append(dict(name=name,expected=want,actual=actual,passed=want==actual,reason=reason))
 if want!=actual:
  save(R/'preparation-test-failure.json',dict(tests=tests));raise RuntimeError('PREPARATION_TEST_FAILURE:'+name)
test('medium 64 probe complete synthetic rules',lambda:m.rules(base,declaration=decl),'PASS')
test('medium fixture segment persistence',lambda:m.adapter.q.stream(F,'kernel-authority'),'PASS')
test('exact medium declaration',lambda:fb.validate_declaration(decl,C,root),'PASS')
for key,value in [('directProbes',16),('directWorkers',0),('minimumSegments',2),('heartbeatSeconds',11),('hardDeadlineSeconds',14),('observerSeconds',16),('collectionSeconds',61),('queueItems',65537),('pendingSegments',3),('runId','identity-'+'0'*32),('evidenceRoot',str(root.parent)),('schema','unknown')]:
 bad=copy.deepcopy(decl);bad[key]=value;test('declaration rejects '+key,lambda bad=bad:fb.validate_declaration(bad,C,root))
for field in list(decl):
 bad=copy.deepcopy(decl);del bad[field];test('missing declaration '+field,lambda bad=bad:fb.validate_declaration(bad,C,root))
for label,mut in [('missing direct probe',lambda b:b['coverage']['expected'].pop()),('missing handle',lambda b:b['coverage']['handles'].pop()),('missing native',lambda b:b['coverage']['natives'].pop()),('missing segment',lambda b:b['manifest']['segments'].pop()),('unknown helper',lambda b:b['coverage']['expected'][0].update(role='OTHER_HELPER')),('heartbeat',lambda b:b['hb'][0].update(interval=10.0)),('deadline',lambda b:b['qualification'].update(deadlineViolations=1)),('cleanup',lambda b:b['host'].update(matchingProcessCount=1))]:
 bad=copy.deepcopy(base);mut(bad['bundle']);test(label,lambda bad=bad:m.rules(bad,compare_payload=False,declaration=decl))
bad=copy.deepcopy(base);bad['schema']='stage6-checker-input-v2';test('reject small version',lambda:m.rules(bad,declaration=decl))
test('small 16 probes cannot satisfy medium',lambda:m.rules(dict(load(old/'positive-fixture.json'),schema=m.VERSION,adapter='stage6-medium-combined-v1'),declaration=decl))
test('empty medium evidence',lambda:m.rules({},declaration=decl))
test('no source freeze means no fresh acceptance',lambda:m.evaluate())
save(R/'preparation-tests.json',dict(status='PASS',total=len(tests),passed=len(tests),failed=0,tests=tests,fixture=str(F),syntheticNotLive=True))
print(json.dumps(dict(status='PREPARATION_TESTS_PASS',legacy=114,medium=len(tests),syntheticRecords=len(b['events']),syntheticSegments=len(segments),noLiveRun=True)))
