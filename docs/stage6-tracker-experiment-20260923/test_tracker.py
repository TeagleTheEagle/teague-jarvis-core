import unittest,pathlib,json,sys,os,time,subprocess,uuid,copy
from unittest.mock import patch,MagicMock
import evidence_support as e
from workspace import CODE

ROOT=CODE/('tracker-focused-'+uuid.uuid4().hex);ROOT.mkdir();(ROOT/'temp').mkdir();os.environ['TEMP']=str(ROOT/'temp');os.environ['TMP']=str(ROOT/'temp')
class Capture(unittest.TestCase):
 def capture(self,states=(258,258),handlepid=123,creation=('100','100'),err=False):
  tracker=e.TreeTracker.__new__(e.TreeTracker);clock=iter(range(10,100))
  k=MagicMock();k.GetProcessId.return_value=handlepid;k.WaitForSingleObject.side_effect=states
  with patch.object(e,'K',k),patch.object(e,'times',side_effect=[[x] for x in creation]),patch.object(e,'ticks',side_effect=lambda:next(clock)),patch.object(e,'image',side_effect=OSError(31,'failed') if err else None,return_value='C:\\Windows\\System32\\conhost.exe'):
   return tracker.capture_image(99,123,'100')
 def test_live_capture(self):self.assertTrue(self.capture()['valid'])
 def test_postexit(self):self.assertFalse(self.capture(states=(0,0))['valid'])
 def test_exit_during_query(self):self.assertFalse(self.capture(states=(258,0))['valid'])
 def test_identity_mismatch(self):self.assertFalse(self.capture(handlepid=999)['valid'])
 def test_creation_mismatch(self):self.assertFalse(self.capture(creation=('101','101'))['valid'])
 def test_creation_changes(self):self.assertFalse(self.capture(creation=('100','101'))['valid'])
 def test_query_error(self):self.assertFalse(self.capture(err=True)['valid'])
 def test_wait_error(self):self.assertFalse(self.capture(states=(0xffffffff,258))['valid'])
 def test_init_failure_starts_no_thread(self):
  with patch.object(e.TreeTracker,'capture_image',return_value={'valid':False}),patch.object(e.threading.Thread,'start') as start:
   with self.assertRaises(RuntimeError):e.TreeTracker(collector_anchor=True)
   start.assert_not_called()
 def test_thread_start_failure_closes_anchor(self):
  original=e.K.CloseHandle;closed=[]
  def close(h):closed.append(h);return original(h)
  with patch.object(e.K,'CloseHandle',side_effect=close),patch.object(e.threading.Thread,'start',side_effect=RuntimeError('injected')):
   with self.assertRaises(RuntimeError):e.TreeTracker(collector_anchor=True)
  self.assertEqual(len(closed),1)

class Actual(unittest.TestCase):
 def setUp(self):self.folder=ROOT/uuid.uuid4().hex;self.folder.mkdir();self.children=[];self.tree=None
 def tearDown(self):
  for p in self.children:
   p.wait(timeout=5)
   if hasattr(p,'_handle'):p._handle.Close()
  if self.tree and self.tree.thread.is_alive():
   self.tree.stop.set();self.tree.thread.join(2)
  if self.tree and self.tree.anchorHandle:e.K.CloseHandle(self.tree.anchorHandle);self.tree.anchorHandle=None
  if self.tree:
   for key,h in self.tree.handles.items():
    if not self.tree.rows[key]['closed']:e.K.CloseHandle(h);self.tree.rows[key]['closed']=True
 def child(self):
  p=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(0.7)'],creationflags=0x08000000,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);self.children.append(p);return p
 def test_anchor_discovers_unregistered_child_and_does_not_wait_for_self(self):
  self.tree=e.TreeTracker(collector_anchor=True);p=self.child();p.wait(timeout=5)
  result=self.tree.finish(self.folder,2);support=json.loads((self.folder/'tree-image-support.json').read_text())
  self.assertTrue(result['allExited']);self.assertTrue(result['allHandlesClosed']);self.assertTrue(result['supportingEvidenceValid'])
  self.assertEqual(support['anchor']['stateAtClose'],258);self.assertTrue(support['anchor']['closed']);self.assertTrue(support['anchor']['scopeOnly'])
  self.assertNotIn(os.getpid(),[x['pid'] for x in result['rows']]);self.assertIn(p.pid,[x['pid'] for x in result['rows']])
 def test_default_no_anchor_and_registered_child(self):
  self.tree=e.TreeTracker();p=self.child();self.tree.register(p,'fixture');p.wait(timeout=5);result=self.tree.finish(self.folder,2)
  self.assertTrue(result['allExited']);self.assertNotIn('supportingEvidenceValid',result);self.assertFalse((self.folder/'tree-image-support.json').exists())
 def test_evidence_failure_remains_failure_with_cleanup(self):
  self.tree=e.TreeTracker(collector_anchor=True)
  with patch.object(e,'image',side_effect=OSError(31,'injected')):
   p=self.child();self.tree.register(p,'fixture')
  p.wait(timeout=5);result=self.tree.finish(self.folder,2)
  self.assertTrue(result['allExited']);self.assertFalse(result['supportingEvidenceValid'])
 def test_durable_output_collision_fails(self):
  self.tree=e.TreeTracker(collector_anchor=True);p=self.child();p.wait(timeout=5)
  (self.folder/'tree-image-support.json').write_text('preserve')
  with self.assertRaises(FileExistsError):self.tree.finish(self.folder,2)
  self.assertEqual((self.folder/'tree-image-support.json').read_text(),'preserve');self.assertIsNone(self.tree.anchorHandle)
 def test_capacity_fails_closed(self):
  self.tree=e.TreeTracker(collector_anchor=True);self.tree.capacity=0;p=self.child();p.wait(timeout=5)
  result=self.tree.finish(self.folder,2);self.assertFalse(result['supportingEvidenceValid']);self.assertTrue(self.tree.errors)
 def test_register_failure_closes_unowned_duplicate(self):
  self.tree=e.TreeTracker(collector_anchor=True);self.tree.stop.set();self.tree.thread.join(2)
  self.tree.capacity=0;p=self.child();original=e.K.CloseHandle;closed=[]
  def close(h):closed.append(h);return original(h)
  with patch.object(e.K,'CloseHandle',side_effect=close):
   with self.assertRaises(RuntimeError):self.tree.register(p,'fixture')
  self.assertEqual(len(closed),1);self.assertEqual(self.tree.handles,{})
 def test_worker_descendant_is_discovered(self):
  self.tree=e.TreeTracker(collector_anchor=True)
  script="import subprocess,sys; p=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(0.7)'],creationflags=0x08000000);p.wait();p._handle.Close()"
  p=subprocess.Popen([sys.executable,'-B','-c',script],creationflags=0x08000000,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);self.children.append(p)
  self.tree.register(p,'worker');p.wait(timeout=5);result=self.tree.finish(self.folder,2)
  self.assertTrue(result['supportingEvidenceValid']);self.assertTrue(any(r['parentPid']==p.pid for r in result['rows']))
 def test_no_descendants_cannot_pass_vacuously(self):
  self.tree=e.TreeTracker(collector_anchor=True);result=self.tree.finish(self.folder,0)
  self.assertFalse(result['supportingEvidenceValid']);self.assertIsNone(self.tree.anchorHandle)

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]);result=unittest.TextTestRunner(verbosity=2).run(suite)
 (ROOT/'result.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),run=str(ROOT)),indent=2))
 print('EVIDENCE '+str(ROOT));sys.exit(not result.wasSuccessful())
