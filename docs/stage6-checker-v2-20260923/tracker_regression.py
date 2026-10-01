import unittest,json
from unittest.mock import patch
import test_tracker as t

def acquisition(self):
 self.tree=t.e.TreeTracker(collector_anchor=True);p=self.child();self.tree.register(p,'fixture');p.wait(timeout=5)
 r=self.tree.finish(self.folder,2);self.assertTrue(r['supportingEvidenceValid'])
 d=json.loads((self.folder/'tree-image-support.json').read_text())
 for row in [d['anchor']]+d['descendants']:
  c=row['capture'];self.assertLessEqual(c['acquisitionBeginQpc'],c['acquisitionReturnedQpc']);self.assertLessEqual(c['acquisitionReturnedQpc'],c['captureEntryQpc'])
def join_failure(self):
 self.tree=t.e.TreeTracker(collector_anchor=True);self.tree.stop.set();self.tree.thread.join(2)
 with patch.object(self.tree.thread,'is_alive',return_value=True),self.assertRaises(RuntimeError):self.tree.finish(self.folder,0)
 self.assertFalse((self.folder/'tree-image-support.json').exists())
def anchor_close_failure(self):
 self.tree=t.e.TreeTracker(collector_anchor=True);p=self.child();p.wait(timeout=5);anchor=self.tree.anchorHandle;original=t.e.K.CloseHandle
 with patch.object(t.e.K,'CloseHandle',side_effect=lambda h:False if h==anchor else original(h)):
  r=self.tree.finish(self.folder,2)
 self.assertFalse(r['supportingEvidenceValid']);self.assertEqual(self.tree.anchorHandle,anchor)
t.Actual.test_actual_acquisition_timing=acquisition
t.Actual.test_join_failure_failclosed=join_failure
t.Actual.test_anchor_close_failure_failclosed=anchor_close_failure
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromModule(t);r=unittest.TextTestRunner(verbosity=2).run(suite)
 print('TRACKER_EVIDENCE '+str(t.ROOT));raise SystemExit(not r.wasSuccessful())
