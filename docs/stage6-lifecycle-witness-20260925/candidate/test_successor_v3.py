"""Offline tests of actual successor binding, tracker and completed-evidence adapters."""
import unittest,json,pathlib,uuid,copy,itertools,threading
from unittest.mock import patch,Mock
from workspace import CODE,new_run
import small_binding_v3 as binding
import evidence_support_v3 as tracker
import support_verifier_v3 as support
import completed_v3
from coordination_v3 import Rejected
from fixture_support import fixture as support_fixture
ROOT=new_run('v3-successor-focused-'+uuid.uuid4().hex)

class Binding(unittest.TestCase):
 def test_actual_fresh_binding(self):
  root=binding.make('normal');doc=json.loads((root/'small-declaration-v3.json').read_text());self.assertEqual(binding.validate(root,doc),doc)
 def test_declaration_rejections(self):
  root=binding.make('normal');doc=json.loads((root/'small-declaration-v3.json').read_text())
  for field,value in [('run','previous'),('cleanup',21.0),('coordination','v2'),('sourceManifestSHA256','0'*64),('files',13),('bytes',59665402098),('heartbeat',11),('probe',14)]:
   with self.subTest(field=field),self.assertRaises(ValueError):binding.validate(root,dict(doc,**{field:value}))
 def test_failed_run_is_not_completed_evidence(self):
  root=ROOT/uuid.uuid4().hex;root.mkdir();(root/'primary-failure.json').write_text('{"historical":true}')
  with self.assertRaises(Rejected):completed_v3.verify_complete(root)
 def test_no_missing_phase_fallback(self):
  root=ROOT/uuid.uuid4().hex;root.mkdir()
  with self.assertRaises(FileNotFoundError):completed_v3.verify_complete(root)

class LocalEvidence(unittest.TestCase):
 def doc(self):
  d=support_fixture()[0];d['schema']='stage6-independent-tree-support-v3';r=d['descendants'][0]
  r.update(eligibleConsoleHelper=True,localCloseQpc=80,stateAtClose=258,exitFiletime=None,exitCode=None)
  r['capture']['image']=r'C:\Windows\System32\conhost.exe';return d
 def test_pending_is_not_exit(self):
  d=self.doc();support.structural(d);self.assertIsNone(d['descendants'][0]['exitFiletime'])
 def test_direct_process_cannot_pend(self):
  d=self.doc();d['descendants'][0]['eligibleConsoleHelper']=False
  with self.assertRaises(ValueError):support.structural(d)
 def test_wrong_parent_cannot_pend(self):
  d=self.doc();d['descendants'][0]['parentPid']=999
  with self.assertRaises(ValueError):support.structural(d)
 def test_non_console_cannot_pend(self):
  d=self.doc();d['descendants'][0]['capture']['image']=r'D:\other.exe'
  with self.assertRaises(ValueError):support.structural(d)
 def test_open_handle_fails(self):
  d=self.doc();d['descendants'][0]['closed']=False
  with self.assertRaises(ValueError):support.structural(d)

class Tracker(unittest.TestCase):
 def build(self):
  t=tracker.TreeTracker.__new__(tracker.TreeTracker);t.anchor={'pid':10,'created':'1000','capture':{'image':r'D:\python.exe'}};t.anchorHandle=1;t.rows={};t.handles={};t.errors=[];t.lock=threading.RLock();t.stop=threading.Event();t.thread=Mock();t.thread.is_alive.return_value=False;t.scans=1;t.maxScan=0;t.capacity=8192
  r=dict(pid=11,created='1001',parentPid=10,role='descendant:conhost.exe',image=r'C:\Windows\System32\conhost.exe',imageCapture={'valid':True,'image':r'C:\Windows\System32\conhost.exe'},closed=False,exitFiletime=None,exitCode=None,signalObservedQpc=None)
  t.rows[(11,'1001')]=r;t.handles[(11,'1001')]=2;t.scan=lambda:None
  return t,r
 def test_pending_closes_local_handle_without_exit_claim(self):
  t,r=self.build();root=ROOT/uuid.uuid4().hex;root.mkdir();(root/'observer-identities.json').write_text(json.dumps({'etw':{'pid':99,'created':'900'}}));clock=itertools.count(1000)
  with patch.object(tracker,'ticks',side_effect=lambda:next(clock)),patch.object(tracker,'frequency',return_value=100),patch.object(tracker.K,'OpenProcess',return_value=3),patch.object(tracker,'times',return_value=('900',None)),patch('helper_handoff_v1.perform',return_value={'observedQpc':999}),patch.object(tracker.K,'WaitForSingleObject',return_value=258),patch.object(tracker.K,'CloseHandle',return_value=True),patch('tracker_adapter_v3.binding',return_value={'synthetic':True}):v=t.finish(root,20)
  self.assertTrue(v['localFinalized']);self.assertTrue(v['allHandlesClosed']);self.assertFalse(v['allExited']);self.assertIsNone(v['rows'][0]['exitFiletime'])
  self.assertEqual(v['deadlineQpc']-v['cleanupEntryQpc'],2000)
 def test_handle_close_failure_is_not_pending_success(self):
  t,r=self.build();root=ROOT/uuid.uuid4().hex;root.mkdir();(root/'observer-identities.json').write_text(json.dumps({'etw':{'pid':99,'created':'900'}}));clock=itertools.count(1000)
  with patch.object(tracker,'ticks',side_effect=lambda:next(clock)),patch.object(tracker,'frequency',return_value=100),patch.object(tracker.K,'OpenProcess',return_value=3),patch.object(tracker,'times',return_value=('900',None)),patch('helper_handoff_v1.perform',return_value={'observedQpc':999}),patch.object(tracker.K,'WaitForSingleObject',return_value=258),patch.object(tracker.K,'CloseHandle',return_value=False),self.assertRaises(Rejected):t.finish(root,20)
 def test_other_class_is_not_eligible(self):
  t,r=self.build();r['role']='lifecycle-probe';self.assertFalse(t.eligible(r))
if __name__=='__main__':unittest.main(verbosity=2)
