"""Offline fixtures only. No monitor/workload launch; originals never mutated."""
import copy,json,os,shutil,uuid
from pathlib import Path
import checker_v2 as c
R=Path(__file__).parent;F=R.parent/'fixtures'/uuid.uuid4().hex;F.mkdir()
base=c.load(R/'positive-fixture.json');results=[]
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
def test(name,fn,want='REJECT',category='negative'):
 try:
  value=fn();actual='PASS';reason=None
 except (ValueError,KeyError,OSError,TypeError) as e:actual='REJECT';reason=type(e).__name__+': '+str(e)
 except Exception as e:actual='ERROR';reason=type(e).__name__+': '+str(e)
 row=dict(name=name,expected=want,actual=actual,passed=actual==want,reason=reason,category=category);results.append(row)
 if not row['passed']:
  save(F/'failure-results.json',dict(tests=results));raise RuntimeError('UNEXPLAINED_TEST_FAILURE: '+name+' '+str(row))
def fixture(name,mut,compare=False,category='negative'):
 b=copy.deepcopy(base);mut(b)
 save(F/(str(len(results)).zfill(3)+'-'+name.replace(' ','-')+'.json'),b)
 test(name,lambda:c.rules(b,compare_payload=compare),category=category)
def change(name,mut,category='negative'):fixture(name,lambda e:mut(e['bundle']),category=category)
def synchronize(b):
 b['structural']['events']=copy.deepcopy(b['events']);b['structural']['kernel']=copy.deepcopy(b['kernel']);b['structural']['cim']=copy.deepcopy(b['cim']);b['coverage']['events']=copy.deepcopy(b['events'])
def event_remove(b,kind):
 b['events'].pop(next(i for i,x in enumerate(b['events']) if x['kind']==kind));synchronize(b)
def helper(b,retained=True):return next(h for h in b['coverage']['handles'] if h['source']=='tracer-opened-handle' and h['retained']==retained)
def direct(b):return next(h for h in b['coverage']['handles'] if h['source']=='creator-owned-handle')
def os_helper(b):
 ids={(x['pid'],x['created']) for x in b['coverage']['expected'] if x['role']=='OS_CONSOLE_HELPER'}
 return next(h for h in b['coverage']['handles'] if (h['pid'],h['created']) in ids and h['retained'])
test('positive 72 records 4 segments 36 identities',lambda:c.rules(copy.deepcopy(base)),'PASS','positive')
positive=c.rules(copy.deepcopy(base));save(F/'positive-result.json',positive)
for name,role,kind,count in [('direct probe class','DIRECT_PROBE','DIRECT_CREATOR_CAPTURE',16),('direct worker class','DIRECT_WORKER','DIRECT_CREATOR_CAPTURE',1),('tracer helper class','OS_CONSOLE_HELPER','TRACER_HELPER_VERIFIED',2),('post exit helper class','OS_CONSOLE_HELPER','QUALIFIED_POST_EXIT_HELPER',16)]:
 test(name,lambda role=role,kind=kind,count=count:c.need(sum(x['role']==role and x['evidenceClass']==kind for x in positive['identities'])==count,'CLASS_COUNT'),'PASS','helper-positive')
change('missing durable commit state',lambda b:b['manifest']['segments'][0].update(states=[0,1,2,4]))
change('manifest incomplete',lambda b:b['manifest']['segments'].pop())
change('finalizer queue not drained',lambda b:b['writer'].update(remaining=1))
change('authoritative queue not drained',lambda b:b['writer'].update(attempted=b['writer']['attempted']+1))
change('writer fault',lambda b:b['writer'].update(fault=109))
change('threads not exited',lambda b:b['writer'].update(threadsExited=False))
change('missing kernel START',lambda b:event_remove(b,'start'))
change('missing kernel STOP',lambda b:event_remove(b,'stop'))
def collision(b):
 b['kernel']['rows'].append(copy.deepcopy(b['kernel']['rows'][0]));synchronize(b)
change('authoritative identity ambiguity',collision)
def false_identity(b):
 b['events'][1]['sequence']=b['events'][0]['sequence'];synchronize(b)
change('false identity collision',false_identity)
change('required handle missing',lambda b:b['coverage']['handles'].pop())
change('required image missing',lambda b:direct(b).update(image=''))
change('required native entry missing',lambda b:b['coverage']['natives'].pop())
change('helper verification missing',lambda b:b['coverage']['handles'].remove(os_helper(b)),'helper-negative')
change('helper evidence source mislabeled',lambda b:os_helper(b).update(source='creator-owned-handle'),'helper-negative')
change('postexit falsely creator capture',lambda b:helper(b,False).update(source='creator-owned-handle'),'helper-negative')
change('direct probe falsely postexit',lambda b:direct(b).update(source='tracer-opened-handle'),'helper-negative')
change('kernel handle creation contradiction',lambda b:direct(b).update(handleCreated='1'))
change('retained exit contradiction',lambda b:direct(b).update(exitCode=999))
change('heartbeat threshold violation',lambda b:b['hb'][0].update(interval=10.0))
change('deadline violation',lambda b:b['qualification'].update(deadlineViolations=1))
change('cleanup failure',lambda b:b['launch'].update(workerExited=False))
change('host process remains',lambda b:b['host'].update(matchingProcessCount=1))
change('trace session remains',lambda b:b['host'].update(diagnosticTraceCount=1))
change('unknown process class',lambda b:b['coverage']['expected'][0].update(role='OTHER_INDIRECT_HELPER'),'helper-negative')
for name,key in [('identities','expected'),('handles','handles'),('native entries','natives')]:change('empty required '+name,lambda b,key=key:b['coverage'].update({key:[]}),'nonvacuous')
change('empty image collection',lambda b:[h.update(image='') for h in b['coverage']['handles']],'nonvacuous')
change('empty segment set',lambda b:b['manifest'].update(segments=[]),'nonvacuous')
change('empty START set',lambda b:(b.update(events=[x for x in b['events'] if x['kind']!='start']),synchronize(b)),'nonvacuous')
change('empty STOP set',lambda b:(b.update(events=[x for x in b['events'] if x['kind']!='stop']),synchronize(b)),'nonvacuous')
change('empty CIM collection',lambda b:(b.update(cim=[]),synchronize(b)),'nonvacuous')
fixture('unknown evidence schema',lambda e:e.update(schema='stage6-checker-input-v99'),category='malformed')
fixture('missing schema',lambda e:e.pop('schema'),category='malformed')
fixture('numeric schema',lambda e:e.update(schema=2),category='malformed')
fixture('legacy contract cannot fallback',lambda e:e.update(contract='legacy'),category='malformed')
fixture('missing required field',lambda e:e['bundle'].pop('host'),category='malformed')
fixture('unknown extra field',lambda e:e.update(forcePass=True),category='malformed')
fixture('bool integer coercion',lambda e:e['bundle']['writer'].update(fault=False),category='malformed')
fixture('string boolean coercion',lambda e:e['bundle']['writer'].update(threadsExited='true'),category='malformed')
fixture('forged adapter PASS',lambda e:e['payload']['verification'].update(creatorImages=33),True,'tamper')
fixture('collapsed postexit class',lambda e:e['payload']['verification'].update(qualifiedPostExitHelpers=0,creatorImages=33),True,'tamper')
fixture('wrong run identity',lambda e:e.update(runId='identity-'+'0'*32),category='tamper')
for text in ('{','[]','null','{"schema":1,"schema":2}','{"a":NaN}'):
 test('malformed text '+text,lambda text=text:c.rules(c.decode(text)),category='malformed')
canonical={(e['scope'],e['pid'],e['created'],e['sequence']) for e in base['bundle']['events']};key=list(sorted(canonical))[0]
for status in ('AMBIGUOUS','UNMATCHED'):
 record=copy.deepcopy(next(x for x in base['bundle']['cim'] if x['result']==status))
 test('CIM '+status+' valid secondary',lambda record=record:c.secondary_policy(record,canonical),'PASS','cim')
unique=dict(result='UNIQUE_CORRELATED',selected=list(key),independentEventBoundProof=True)
test('CIM conditional unique independently proven policy only',lambda:c.secondary_policy(unique,canonical),'PASS','cim-policy-only')
test('CIM unique without independent proof',lambda:c.secondary_policy(dict(unique,independentEventBoundProof=False),canonical),category='cim')
test('CIM positive contradiction',lambda:c.secondary_policy(dict(unique,provenContradiction=True),canonical),category='cim')
test('CIM forced ambiguous selection',lambda:c.secondary_policy(dict(result='AMBIGUOUS',selected=list(key)),canonical),category='cim')
def force_match(b):
 b['cim'][0].update(unique);synchronize(b)
change('CIM forced match public evidence',force_match,'cim')
for name,mut in [('process creation identity',lambda b:direct(b).update(created='1')),('image identity',lambda b:direct(b).update(image=r'D:\wrong.exe')),('helper class',lambda b:next(x for x in b['coverage']['expected'] if x['role']=='OS_CONSOLE_HELPER').update(role='DIRECT_PROBE')),('native entry state',lambda b:b['coverage']['natives'][0].update(entryQpc=0)),('cleanup state',lambda b:b['bridge'].update(allThreadsExited=False))]:change('tamper '+name,mut,'tamper')
source=Path(base['evidenceRoot'])
for mode in ('missing-segment','corrupt-segment-bytes','corrupt-segment-hash','sequence-gap','duplicate-sequence','overlap','manifest-content','missing-seal','extra-segment','segment-traversal'):
 dest=F/mode;dest.mkdir()
 for p in source.glob('kernel-authority-*'):
  if p.is_file():shutil.copyfile(p,dest/p.name)
 m=c.load(dest/'kernel-authority-manifest.json');p=dest/m['segments'][0]['name']
 if mode=='missing-segment':p.unlink()
 elif mode=='corrupt-segment-bytes':p.write_bytes(b'!'+p.read_bytes()[1:])
 elif mode=='missing-seal':(dest/'kernel-authority-seal.json').unlink()
 elif mode=='extra-segment':(dest/'kernel-authority-999.jsonl').write_bytes(b'{}\n')
 else:
  if mode=='corrupt-segment-hash':m['segments'][0]['sha256']='0'*64
  elif mode in ('sequence-gap','duplicate-sequence'):
   lines=p.read_bytes().splitlines();i=0 if mode=='sequence-gap' else 1;line=c.decode(lines[i]);line['seq']=999 if i==0 else 1;lines[i]=json.dumps(line).encode();data=b'\n'.join(lines)+b'\n';p.write_bytes(data)
   old=m['segments'][0]['bytes'];m['segments'][0].update(sha256=c.sha(p),bytes=len(data));m['bytes']+=len(data)-old
  elif mode=='overlap':m['segments'][1]['first']=m['segments'][0]['last']
  elif mode=='manifest-content':m['accepted']+=1
  elif mode=='segment-traversal':m['segments'][0]['name']='../outside.jsonl'
  (dest/'kernel-authority-manifest.json').write_text(json.dumps(m),encoding='utf8');seal=c.load(dest/'kernel-authority-seal.json');seal['manifestSHA256']=c.sha(dest/'kernel-authority-manifest.json');(dest/'kernel-authority-seal.json').write_text(json.dumps(seal),encoding='utf8')
 test(mode,lambda dest=dest:c.adapter.read_bundle(dest,Path(c.load(R/'binding.json')['analysis']),Path(c.load(R/'binding.json')['host'])),category='disk-tamper')
config=c.load(R/'binding.json');folder=F/'archive-mismatch';folder.mkdir()
for name in ('evidence.zip','manifest.json'):shutil.copyfile(Path(config['archive']['archive']).parent/name,folder/name)
bad=copy.deepcopy(config);bad['archive']['archive']=str(folder/'evidence.zip');mp=folder/'manifest.json';mp.write_bytes(mp.read_bytes()+b' ')
test('archive manifest mismatch',lambda:c.archive_verify(bad),category='disk-tamper')
test('path escape rejected',lambda:c.safe_path(F/'..'/'escape',[F]),category='path')
test('alternate stream rejected',lambda:c.safe_path(str(F/'a')+':stream',[F]),category='path')
test('unsupported evidence root rejected',lambda:c.safe_path(Path(r'C:\Windows\not-read'),[F]),category='path')
test('frozen checker hash preserved',lambda:c.need(c.sha(config['reference'])==config['referenceSHA256']==c.sha(R/'frozen_reference.py'),'REFERENCE_DRIFT'),'PASS','preservation')
test('candidate self hashes preserved',c.self_verify,'PASS','preservation')
test('actual archived combined replay',c.replay,'PASS','replay')
summary=dict(total=len(results),passed=sum(x['passed'] for x in results),failed=sum(not x['passed'] for x in results),skipped=0,positive=sum(x['expected']=='PASS' for x in results),rejections=sum(x['expected']=='REJECT' for x in results),categories=dict(__import__('collections').Counter(x['category'] for x in results)),tests=results,fixtureRoot=str(F))
save(F/'results.json',summary);save(R.parent/'test-results-location.json',dict(path=str(F/'results.json')))
print(json.dumps({k:v for k,v in summary.items() if k!='tests'}))
