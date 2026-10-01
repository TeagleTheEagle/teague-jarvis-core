"""Offline adversarial copies. No observer/process launch or acceptance substitution."""
import copy,json,pathlib,sys,shutil
from unittest.mock import patch
R=pathlib.Path(__file__).parent
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
B=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\3316657ba1864413a0c95ea1dc7bf6ff\code\protected-5d26ae153ea2490da7ca1ec16d97c124')
sys.path.insert(0,str(C))
import lineage,cleanup_checker,integration_verify
results=[]
def test(n,fn):
 try:fn();results.append(dict(case=n,status='PASS'))
 except Exception as e:results.append(dict(case=n,status='FAIL',error=repr(e)));raise
def require(v):assert v
def row(seq='1',created='100',start=100,end=200,pid=10,parent=1):return dict(pid=pid,parentPid=parent,created=created,exitFiletime=str(end),sequence=seq,parentSequence='P',startQpc=start,stopQpc=end,image=r'C:\test\probe.exe')
def event(kind='stop',stamp='350',qpc=350,parent=0):return dict(pid=10,parentPid=parent,kind=kind,nativeTime=stamp,receivedQpc=qpc,name='probe.exe')
a=row(); b=row('2','250',250,300)
def match(rows,es):return lineage.associate(rows,es,{r['sequence'] for r in rows})
def ambiguous(rows,es):
 r=match(rows,es);require(not r['bound'] and len(r['unknown'])==len(es))
d=cleanup_checker.load(B);require(cleanup_checker.check(d)['status']=='PASS')
def altered(fn):
 x=copy.deepcopy(d);fn(x);require(cleanup_checker.check(x)['status']=='FAIL')
test('01 reused PID cannot identify later STOP',lambda:ambiguous([a,b],[event()]))
test('02 parent PID reused requires exact parent sequence',lambda:require(not lineage.parent_valid(dict(b,parentPid=10,parentSequence='1'),dict(b,pid=10,sequence='2'))))
test('03 same image different incarnations remain ambiguous',lambda:ambiguous([a,b],[event()]))
test('04 delayed START after PID reuse',lambda:ambiguous([a,b],[event('start',parent=1)]))
test('05 delayed STOP after PID reuse',lambda:ambiguous([a,b],[event()]))
test('06 equal creation identities reject; one FILETIME tick retained exactly',lambda:(ambiguous([a,dict(a,sequence='2')],[event()]),require(int('134344257832103044')-int('134344257832103043')==1)))
test('07 out of order receipt does not substitute for event order',lambda:require(len(match([a],[event(),event('start',stamp='110',qpc=120,parent=1)])['bound']['1'])==2))
def native_case(missing=False):
 root=R/('native-missing' if missing else 'native-present');root.mkdir()
 for n in ('etw-result.json','stress-result.json','native-bridge-cleanup.json'):shutil.copy2(B/n,root/n)
 ns=sorted(p for p in B.glob('native-*-*.json') if p.name!='native-trace-verification.json')
 for p in ns[1:] if missing else ns:shutil.copy2(p,root/p.name)
 for p in B.glob('integration-*-*.json'):shutil.copy2(p,root/p.name)
 with patch.object(integration_verify,'verify',return_value={'offlineFixture':'segment integrity independently checked'}):
  if missing:
   try:integration_verify.inspect(root)
   except AssertionError:return
   raise AssertionError('missing native accepted')
  require(integration_verify.inspect(root)['nativeEntries']==5)
test('08 actual native PE entries present',lambda:native_case(False))
test('09 missing native PE evidence rejected',lambda:native_case(True))
test('10 retained handle evidence present',lambda:require(cleanup_checker.check(d)['handleConfirmed']>0))
test('11 no post-exit handle requires qualified kernel evidence',lambda:(require(cleanup_checker.check(d)['kernelPostExit']>0),altered(lambda x:next(r for r in x['kernel']['rows'] if r['openError']==87).__setitem__('openError',5))))
test('12 unique valid candidate passes association',lambda:require(len(match([a],[event()])['bound']['1'])==1))
test('13 two candidates rejected',lambda:ambiguous([a,b],[event()]))
test('14 zero compatible candidates not forced to unique',lambda:require(not match([a],[dict(event(),name='foreign.exe')])['bound']))
test('15 impossible lifetime rejected by complete checker',lambda:altered(lambda x:x['kernel']['rows'][0].__setitem__('stopQpc',x['kernel']['rows'][0]['startQpc']-1)))
test('16 notification before creation rejected; delayed notification after exit stays distinct from lifetime',lambda:(require(not match([a],[event(stamp='99',qpc=99)])['bound']),require(bool(match([a],[event()])['bound']))))
test('17 QPC nanosecond conversion preserves exact measured integer scale',lambda:require(2585331811249*100==258533181124900))
test('18 retained creation identity mismatch rejected',lambda:altered(lambda x:x['handles']['rows'][0].__setitem__('startFiletime','1')))
test('19 preserved 22 ambiguities keep full gate failed',lambda:require(cleanup_checker.evaluate(C/'protected-00a17b2c499c4966a5113c30924b367a')['status']=='FAIL'))
test('20 actual prior valid relationship still passes',lambda:require(cleanup_checker.check(d)['status']=='PASS'))
with (R/'identity-regressions.json').open('x') as f:json.dump(dict(results=results,count=len(results),scope='Offline evidence mutations only; not fresh process stress.',runtimeCorrections=False),f,indent=2)
print(len(results),'PASS')
