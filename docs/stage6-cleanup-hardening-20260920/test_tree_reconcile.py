import unittest
from tree_reconcile import match_child
class Reconcile(unittest.TestCase):
 def fixture(self):
  start=dict(stage='B-WMI-callback',kind='start',pid=10,parentPid=5,name='conhost.exe',nativeTime='1000')
  stop=dict(start,kind='stop',nativeTime='1100')
  row=dict(pid=10,parentPid=5,image='C:/Windows/System32/conhost.exe',created='10',exitFiletime='20')
  return start,[row],[start,stop]
 def test_late_provider_time_does_not_erase_kernel_proof(self):
  s,r,e=self.fixture();v=match_child(s,r,e);self.assertEqual(v['retainedMatches'],1);self.assertEqual(v['stopMatches'],1)
 def test_missing_handle_remains_unproven(self):
  s,r,e=self.fixture();self.assertEqual(match_child(s,[],e)['retainedMatches'],0)
 def test_pid_reuse_is_ambiguous(self):
  s,r,e=self.fixture();r.append(dict(r[0],created='500'));self.assertEqual(match_child(s,r,e)['retainedMatches'],0)
 def test_duplicate_start_is_ambiguous(self):
  s,r,e=self.fixture();e.append(s);self.assertEqual(match_child(s,r,e)['retainedMatches'],0)
 def test_wrong_parent_is_rejected(self):
  s,r,e=self.fixture();r[0]['parentPid']=6;self.assertEqual(match_child(s,r,e)['retainedMatches'],0)
 def test_wrong_image_is_rejected(self):
  s,r,e=self.fixture();r[0]['image']='C:/Other.exe';self.assertEqual(match_child(s,r,e)['retainedMatches'],0)
 def test_missing_stop_is_not_synthesized(self):
  s,r,e=self.fixture();self.assertEqual(match_child(s,r,[s])['stopMatches'],0)
