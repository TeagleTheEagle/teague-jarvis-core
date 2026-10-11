"""Offline handoff tests: API seams/constructed evidence, no observers or ETW."""
import unittest,unittest.mock as m,json,pathlib,uuid,copy,hashlib,itertools,threading,subprocess
import helper_handoff_v1 as h
from coordination_v3 import canonical,digest,write_once
from workspace import CODE
def fixture(root=None):
 root=root or CODE/('protected-'+uuid.uuid4().hex)
 c=dict(pid=101,created='1000',image=r'D:\python.exe');obs=dict(pid=201,created='900',image=r'D:\observer.exe')
 b=dict(run=root.name,declarationSHA256='a'*64,sourceManifestSHA256='b'*64,kernelSession='OFFLINE-HANDOFF',frequency=100,observerSHA256='c'*64,workspaceBindingSHA256='d'*64,cleanupOriginSHA256='e'*64)
 helper=dict(obligationId='102-1001',pid=102,created='1001',expectedSequence=None,parent=c,image=r'C:\Windows\System32\conhost.exe',localHandleIdentity='33',localRetained=True,localRetainedQpc=50,localVerifiedQpc=60,publicationState='SEALED_CLAIM')
 o=dict(schema=h.SCHEMA,kind='HELPER_OBLIGATIONS',binding=b,obligationSetId=hashlib.sha256(canonical([helper])).hexdigest(),cleanupEntryQpc=100,deadlineQpc=2100,collector=c,authorityObserver=obs,helpers=[helper],preparedQpc=101,coordinationOnly=True,cleanupPass=False,acceptance=False)
 r=dict(obligationId='102-1001',pid=102,created='1001',sequence='401',kernelSession=b['kernelSession'],parent=dict(c,sequence='400'),kernelImage=r'\Device\HarddiskVolume6\Windows\System32\conhost.exe',handleImage=helper['image'],method='OpenProcess',accessMask=0x101000,handlePid=102,handleCreated='1001',handleIdentity='44',retained=True,acquisitionBeginQpc=70,acquisitionReturnQpc=71,creationVerifiedQpc=72,imageBeginQpc=73,imageEndQpc=74,verificationQpc=102)
 a=dict(schema=h.SCHEMA,kind='HANDOFF_ACQUIRED',receiptSequence=1,binding=copy.deepcopy(b),obligationsSHA256=hashlib.sha256(canonical(o)).hexdigest(),cleanupEntryQpc=100,deadlineQpc=2100,collector=c,authorityObserver=obs,helpers=[r],preparedQpc=103,coordinationOnly=True,cleanupPass=False,acceptance=False)
 return root,o,a
class Receipt(unittest.TestCase):
 def test_normal_independent_acquisition(self):
  _,o,a=fixture();self.assertIs(h.validate_receipt(o,a,a['obligationsSHA256'],104),a)
 def test_multiple_exact_helpers(self):
  _,o,a=fixture();x=copy.deepcopy(o['helpers'][0]);x.update(pid=103,created='1002',obligationId='103-1002');o['helpers'].append(x);o['obligationSetId']=hashlib.sha256(canonical(o['helpers'])).hexdigest()
  r=copy.deepcopy(a['helpers'][0]);r.update(pid=103,created='1002',obligationId='103-1002',sequence='402',handlePid=103,handleCreated='1002');a['helpers'].append(r);a['obligationsSHA256']=hashlib.sha256(canonical(o)).hexdigest();h.validate_receipt(o,a,a['obligationsSHA256'],104)
 def test_no_stop_or_exit_requirement(self):
  _,o,a=fixture();h.validate_receipt(o,a,a['obligationsSHA256'],104);self.assertNotIn('stopQpc',a['helpers'][0]);self.assertNotIn('exitCode',a['collector'])
 def test_duplicate_obligation(self):
  _,o,a=fixture();o['helpers'].append(copy.deepcopy(o['helpers'][0]));o['obligationSetId']=hashlib.sha256(canonical(o['helpers'])).hexdigest()
  with self.assertRaises(ValueError):h.validate_obligations(o)
 def test_duplicate_instance_different_obligation(self):
  _,o,a=fixture();r=copy.deepcopy(o['helpers'][0]);r['obligationId']='different';o['helpers'].append(r)
  with self.assertRaises(ValueError):h.validate_obligations(o)
 def test_unretained_local_claim(self):
  _,o,a=fixture();o['helpers'][0]['localRetained']=False
  with self.assertRaises(ValueError):h.validate_obligations(o)
 def test_duplicate_json_keys(self):
  root,_,_=fixture();root.mkdir();p=root/h.NAMES[1];p.write_text('{"schema":1,"schema":2}')
  with self.assertRaises(ValueError):h.load(p)
 def test_malformed_and_partial_json(self):
  for raw in ('{','null','{"x":'):
   with self.subTest(raw=raw):
    root,_,_=fixture();root.mkdir();p=root/h.NAMES[1];p.write_text(raw)
    with self.assertRaises((ValueError,TypeError)):h.validate_receipt(fixture()[1],h.load(p),'0'*64,104)
 def test_partial_publication_not_final(self):
  root,o,a=fixture();root.mkdir();(root/(h.NAMES[1]+'.pending')).write_text('{');self.assertFalse(h.safe(root,h.NAMES[1]).exists())
 def test_duplicate_exclusive_publication(self):
  root,o,_=fixture();root.mkdir();h.publish(root,h.NAMES[0],o);before=(root/h.NAMES[0]).read_bytes()
  with self.assertRaises(ValueError):h.publish(root,h.NAMES[0],o)
  self.assertEqual(before,(root/h.NAMES[0]).read_bytes())
 def test_traversal_and_external_root(self):
  root,_,_=fixture();root.mkdir()
  for r,n in ((root,'../escape'),(CODE.parent,h.NAMES[0]),(CODE/'protected-x'/'..'/'protected-y',h.NAMES[0])):
   with self.assertRaises(ValueError):h.safe(r,n)
 def test_reparse_rejection(self):
  root,_,_=fixture();root.mkdir();real=root.lstat()
  with m.patch.object(pathlib.Path,'lstat',return_value=type('S',(),{'st_file_attributes':real.st_file_attributes|0x400})()),self.assertRaises(ValueError):h.safe(root,h.NAMES[0])
def rejection(name,path,value):
 def test(self):
  _,o,a=fixture();x=a
  for k in path[:-1]:x=x[k]
  x[path[-1]]=value
  with self.assertRaises((ValueError,KeyError,TypeError)):h.validate_receipt(o,a,hashlib.sha256(canonical(o)).hexdigest(),104)
 setattr(Receipt,'test_reject_'+name,test)
for name,path,value in [
 ('schema',['schema'],'old'),('run',['binding','run'],'old'),('candidate',['binding','sourceManifestSHA256'],'0'*64),('workspace',['binding','workspaceBindingSHA256'],'0'*64),('declaration',['binding','declarationSHA256'],'0'*64),('session',['binding','kernelSession'],'old'),('observer',['authorityObserver'],dict(pid=222,created='8',image=r'D:\wrong.exe')),('obligation_hash',['obligationsSHA256'],'0'*64),('origin',['cleanupEntryQpc'],101),('deadline',['deadlineQpc'],2101),('expired',['preparedQpc'],2100),('future',['preparedQpc'],105),('retained_false',['helpers',0,'retained'],False),('creation',['helpers',0,'handleCreated'],'1002'),('pid_reuse',['helpers',0,'created'],'1002'),('handle_pid',['helpers',0,'handlePid'],999),('image',['helpers',0,'handleImage'],r'D:\other.exe'),('parent',['helpers',0,'parent'],dict(pid=1,created='1000',sequence='400',image=r'D:\python.exe')),('kernel_sequence',['helpers',0,'sequence'],'0'),('wrong_kernel_session',['helpers',0,'kernelSession'],'old'),('missing_helper',['helpers'],[]),('duplicate_helper',['helpers'],[fixture()[2]['helpers'][0]]*2),('late_verification',['helpers',0,'verificationQpc'],2100),('bad_creation_timing',['helpers',0,'creationVerifiedQpc'],75),('transfer',['helpers',0,'method'],'DuplicateHandle'),('access',['helpers',0,'accessMask'],0x1fffff),('acceptance',['acceptance'],True),('empty_image',['helpers',0,'kernelImage'],''),('handle_missing',['helpers',0,'handleIdentity'],'0')]:rejection(name,path,value)
class Wait(unittest.TestCase):
 def setup_wait(self):
  root,o,a=fixture();root.mkdir();write_once(root/'cleanup-origin-v3.json',dict(cleanupEntryQpc=100,deadlineQpc=2100,frequency=100));write_once(root/'workspace-binding-v4.json',{});write_once(root/'observer-identities.json',dict(etw=o['authorityObserver']))
  r=dict(pid=102,created='1001',image=o['helpers'][0]['image'],closed=False,handleIdentity='33',handleRetainedQpc=50,imageCapture=dict(stateAfterQpc=60))
  t=m.Mock();t.anchor=dict(o['collector'],capture=dict(image=o['collector']['image']));t.handles={(102,'1001'):33};t.snapshot.return_value=[r];t.eligible.return_value=True
  b=dict(o['binding']);b.pop('workspaceBindingSHA256');b.pop('cleanupOriginSHA256');b['producer']=o['collector'];return root,o,a,t,b
 def deliver(self,root,a):
  o=h.load(root/h.NAMES[0]);a=copy.deepcopy(a);a.update(binding=o['binding'],obligationsSHA256=digest(root/h.NAMES[0]),preparedQpc=110);a['helpers'][0]['verificationQpc']=109;h.publish(root,h.NAMES[1],a)
 def test_obligation_first_then_independent_receipt(self):
  root,o,a,t,b=self.setup_wait();clock=itertools.count(105)
  with m.patch('tracker_adapter_v3.binding',return_value=b):
   result=h.perform(root,t,100,2100,clock=lambda:next(clock),pause=lambda _:self.deliver(root,a))
  self.assertEqual(result['kind'],'HANDOFF_OBSERVED');self.assertFalse(t.snapshot()[0]['closed']);self.assertTrue((root/h.NAMES[2]).exists())
 def test_never_observed_deadline_no_reset(self):
  root,o,a,t,b=self.setup_wait();clock=iter([101,102,103,2099,2100,2101])
  with m.patch('tracker_adapter_v3.binding',return_value=b),self.assertRaises(ValueError):h.perform(root,t,100,2100,clock=lambda:next(clock),pause=lambda _:None)
  self.assertFalse((root/h.NAMES[2]).exists());self.assertFalse(t.snapshot()[0]['closed'])
 def test_late_write_rejected(self):
  root,o,a,t,b=self.setup_wait();clock=iter([101,2101])
  with m.patch('tracker_adapter_v3.binding',return_value=b),self.assertRaises(ValueError):h.perform(root,t,100,2100,clock=lambda:next(clock))
 def test_observer_crash_rejected(self):
  root,o,a,t,b=self.setup_wait()
  def dead():raise ValueError('observer dead')
  with m.patch('tracker_adapter_v3.binding',return_value=b),self.assertRaises(ValueError):h.perform(root,t,100,2100,clock=lambda:105,health=dead)
 def test_collector_exception_no_observed_record(self):
  root,o,a,t,b=self.setup_wait()
  with m.patch('tracker_adapter_v3.binding',return_value=b),m.patch.object(h,'publish',side_effect=OSError('write failure')),self.assertRaises(OSError):h.perform(root,t,100,2100,clock=lambda:105)
  self.assertFalse((root/h.NAMES[2]).exists())
 def test_stale_prior_artifact_fails(self):
  root,o,a,t,b=self.setup_wait();h.publish(root,h.NAMES[1],a)
  with self.assertRaises(ValueError):h.perform(root,t,100,2100,clock=lambda:105)
class FinalEvidence(unittest.TestCase):
 def setup_final(self):
  root,o,a=fixture();root.mkdir();write_once(root/'workspace-binding-v4.json',{});write_once(root/'cleanup-origin-v3.json',dict(cleanupEntryQpc=100,deadlineQpc=2100,frequency=100))
  o['binding'].update(workspaceBindingSHA256=digest(root/'workspace-binding-v4.json'),cleanupOriginSHA256=digest(root/'cleanup-origin-v3.json'));a['binding']=copy.deepcopy(o['binding'])
  h.publish(root,h.NAMES[0],o);a['obligationsSHA256']=digest(root/h.NAMES[0]);h.publish(root,h.NAMES[1],a)
  v=dict(schema=h.SCHEMA,kind='HANDOFF_OBSERVED',binding=o['binding'],obligationsSHA256=digest(root/h.NAMES[0]),acquiredSHA256=digest(root/h.NAMES[1]),collector=o['collector'],cleanupEntryQpc=100,deadlineQpc=2100,observedQpc=104,helpers=[dict(obligationId='102-1001',pid=102,created='1001')],coordinationOnly=True,cleanupPass=False,acceptance=False)
  h.publish(root,h.NAMES[2],v)
  b=copy.deepcopy(o['binding']);b.pop('workspaceBindingSHA256');b.pop('cleanupOriginSHA256');b['schema']='stage6-terminal-v3'
  write_once(root/'phase-a-v3.json',dict(binding=b,collector=o['collector'],authorityObserver=o['authorityObserver'],cleanupEntryQpc=100,deadlineQpc=2100))
  r=a['helpers'][0];x=dict(pid=102,created='1001',sequence='401',parentPid=101,parentSequence='400',image=r['kernelImage'],handleImage=r['handleImage'],handleRetained=True,handleClosed=True,handlePid=102,handleCreated='1001',handleIdentity='44',handleAttemptBeginQpc=70,handleAttemptQpc=71,creationVerifiedQpc=72,imageBeginQpc=73,imageEndQpc=74,imageError=0,metadataError=0,signalObservedQpc=110,stopQpc=109)
  x.update(imageStateBefore=258,imageStateAfter=258)
  k=dict(session=b['kernelSession'],faults=0,eventsLost=0,buffersLost=0,realtimeBuffersLost=0,rows=[dict(pid=101,created='1000',sequence='400'),x]);write_once(root/'etw-result.json',k)
  tree=dict(rows=[dict(pid=102,created='1001',closed=True,localCloseQpc=105,localCloseReturnedQpc=106)]);write_once(root/'tree-handles.json',tree);return root,k,tree
 def change(self,root,name,value):
  # Only mutable constructed test evidence, never historical/acceptance artifacts.
  (root/name).write_text(json.dumps(value))
 def test_final_independent_reconciliation(self):
  root,_,_=self.setup_final();self.assertEqual(h.verify_final(root)['obligations'],1)
 def test_later_authority_failure_rejects(self):
  root,k,_=self.setup_final();k['faults']=1;self.change(root,'etw-result.json',k)
  with self.assertRaises(ValueError):h.verify_final(root)
 def test_kernel_handle_contradiction(self):
  root,k,_=self.setup_final();k['rows'][1]['creationVerifiedQpc']=999;self.change(root,'etw-result.json',k)
  with self.assertRaises(ValueError):h.verify_final(root)
 def test_receipt_after_local_release(self):
  root,_,t=self.setup_final();t['rows'][0]['localCloseQpc']=103;self.change(root,'tree-handles.json',t)
  with self.assertRaises(ValueError):h.verify_final(root)
 def test_close_returns_after_deadline(self):
  root,_,t=self.setup_final();t['rows'][0]['localCloseReturnedQpc']=2100;self.change(root,'tree-handles.json',t)
  with self.assertRaises(ValueError):h.verify_final(root)
 def test_claim_cannot_replace_missing_authority(self):
  root,k,_=self.setup_final();k['rows'].pop();self.change(root,'etw-result.json',k)
  with self.assertRaises((ValueError,KeyError)):h.verify_final(root)
 def test_later_reused_pid_cannot_replace_original(self):
  root,k,_=self.setup_final();k['rows'][1]['created']='1002';self.change(root,'etw-result.json',k)
  with self.assertRaises((ValueError,KeyError)):h.verify_final(root)
 def test_helper_exited_before_acquisition_rejected(self):
  root,k,_=self.setup_final();k['rows'][1]['stopQpc']=69;self.change(root,'etw-result.json',k)
  with self.assertRaises(ValueError):h.verify_final(root)
class Release(unittest.TestCase):
 def setup_tracker(self):
  import evidence_support_v3 as tr
  t=tr.TreeTracker.__new__(tr.TreeTracker);t.anchor=dict(pid=101,created='1000',capture=dict(image=r'D:\python.exe'));t.anchorHandle=1;t.rows={};t.handles={};t.errors=[];t.lock=threading.RLock();t.stop=threading.Event();t.thread=m.Mock();t.thread.is_alive.return_value=False;t.scans=1;t.maxScan=0;t.capacity=8192;t.scan=lambda:None
  r=dict(pid=102,created='1001',parentPid=101,role='descendant:conhost.exe',image=r'C:\Windows\System32\conhost.exe',imageCapture=dict(valid=True,image=r'C:\Windows\System32\conhost.exe'),closed=False,exitFiletime=None,exitCode=None,signalObservedQpc=None)
  t.rows[(102,'1001')]=r;t.handles[(102,'1001')]=2;root=CODE/('protected-'+uuid.uuid4().hex);root.mkdir();write_once(root/'observer-identities.json',dict(etw=dict(pid=201,created='900')));return tr,t,r,root
 def run_tracker(self,fail=False):
  tr,t,r,root=self.setup_tracker();clock=itertools.count(100);seen=[]
  def ack(*args,**kwargs):
   self.assertFalse(r['closed']);self.assertTrue(t.stop.is_set());t.thread.join.assert_called_once();seen.append('ack')
   if fail:raise ValueError('injected receipt failure')
   return dict(observedQpc=101)
  def close(x):
   if x==2:
    if fail:self.assertTrue((root/'rejected-v3.json').exists())
    else:self.assertIn('ack',seen)
    seen.append('close')
   return True
  with m.patch.object(tr,'ticks',side_effect=lambda:next(clock)),m.patch.object(tr,'frequency',return_value=100),m.patch.object(tr.K,'OpenProcess',return_value=3),m.patch.object(tr,'times',return_value=('900',None)),m.patch.object(tr.K,'WaitForSingleObject',return_value=258),m.patch.object(tr.K,'CloseHandle',side_effect=close),m.patch.object(h,'perform',side_effect=ack),m.patch('tracker_adapter_v3.binding',return_value={}):
   if fail:
    with self.assertRaises(ValueError):t.finish(root,20)
   else:
    out=t.finish(root,20);self.assertEqual(out['deadlineQpc']-out['cleanupEntryQpc'],2000);self.assertGreaterEqual(r['localCloseReturnedQpc'],r['localCloseQpc'])
  self.assertEqual(seen,['ack','close'])
 def test_actual_tracker_ack_precedes_close(self):self.run_tracker()
 def test_actual_tracker_failure_cleanup_is_rejected(self):self.run_tracker(True)
class Native(unittest.TestCase):
 def test_actual_cpp_producer(self):
  for mode in ('normal','missing-row','exit-after-acquire','no-handle','creation','image','kernel-image','parent','pid-reuse','post-exit-acquire','sequence','image-error','already-signaled','exit-during-image','fault','expected-sequence','duplicate','wrong-run','wrong-observer','wrong-workspace','deadline','duplicate-publish'):
   with self.subTest(mode=mode):
    root,o,a=fixture();root.mkdir();b=o['binding'];b['sourceManifestSHA256']=digest(CODE/'small-source-v3.json')
    declaration=dict(run=root.name,code=str(CODE),sourceManifestSHA256=b['sourceManifestSHA256']);write_once(root/'small-declaration-v3.json',declaration);b['declarationSHA256']=digest(root/'small-declaration-v3.json')
    workspace=dict(run=root.name,candidateRoot=str(CODE),evidenceRoot=str(root),candidateManifestSHA256=b['sourceManifestSHA256'],smallDeclarationSHA256=b['declarationSHA256']);write_once(root/'workspace-binding-v4.json',workspace);b['workspaceBindingSHA256']=digest(root/'workspace-binding-v4.json');write_once(root/'input.json',o)
    p=subprocess.run([str(CODE/'J6HandoffFixture.exe'),str(root),mode],capture_output=True,text=True,timeout=10)
    write_once(root/'offline-native-result.json',dict(mode=mode,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,constructed=True))
    self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    if mode in ('normal','missing-row','exit-after-acquire'):
     actual_o=h.load(root/h.NAMES[0]);actual_a=h.load(root/h.NAMES[1]);h.validate_receipt(actual_o,actual_a,digest(root/h.NAMES[0]),h.ticks())
if __name__=='__main__':unittest.main(verbosity=2)
