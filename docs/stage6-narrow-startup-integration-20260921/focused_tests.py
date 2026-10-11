import pathlib,json,sys,unittest,uuid,types
from unittest.mock import patch
R=pathlib.Path(__file__).parent
C=pathlib.Path(json.loads((R/'plan.json').read_text())['code']);sys.path.insert(0,str(C))
import traced_collect,large_collect,secondary_sampling,integration_marks
class Integration(unittest.TestCase):
 def setUp(self):
  self.root=C/('unit-'+uuid.uuid4().hex);self.root.mkdir()
 def marks(self):return json.loads(next(self.root.glob('integration-collector-*.json')).read_text())
 def test_success_returns_exact_exit_and_restores(self):
  original=(large_collect.Managed,large_collect.Probe,secondary_sampling.query)
  with patch.object(large_collect,'main',return_value=0):self.assertEqual(traced_collect.main(self.root,'normal'),0)
  self.assertEqual(original,(large_collect.Managed,large_collect.Probe,secondary_sampling.query))
  self.assertEqual(self.marks()[-1]['status'],'RETURNED')
 def test_failure_is_not_converted_to_success(self):
  with patch.object(large_collect,'main',return_value=1):self.assertEqual(traced_collect.main(self.root,'normal'),1)
  self.assertEqual(self.marks()[-1]['status'],'FAILED')
 def test_exception_propagates_and_cleanup_marker_exists(self):
  original=large_collect.Managed
  with patch.object(large_collect,'main',side_effect=ValueError('fixture')):
   with self.assertRaises(ValueError):traced_collect.main(self.root,'normal')
  self.assertIs(large_collect.Managed,original)
  self.assertEqual(self.marks()[-1]['event'],'FINAL_SHUTDOWN')
  self.assertEqual(self.marks()[-2]['exceptionType'],'ValueError')
 def test_managed_delegates_same_timeout_identity_and_result(self):
  calls=[];result=dict(exit=0,handleState=0,other='preserved')
  class Fake:
   def __init__(self,args,root,role,tracker):
    calls.append((args,root,role,tracker));self.role=role;self.p=types.SimpleNamespace(pid=123);self.identity={'created':456}
   def finish(self,seconds):calls.append(seconds);return result
  def body(root):
   x=large_collect.Managed(['python','-B',str(C/'baseline_hash_worker.py'),root.name],root,'hash-worker','tracker')
   self.assertIs(x.finish(15),result);return 0
  with patch.object(large_collect,'Managed',Fake),patch.object(large_collect,'main',body):traced_collect.main(self.root,'normal')
  self.assertEqual(calls[0],(['python','-B',str(C/'traced_hash_worker.py'),self.root.name,'normal'],self.root,'hash-worker','tracker'))
  self.assertEqual(calls[1],15)
 def test_unexpected_hash_command_fails_closed(self):
  def body(root):large_collect.Managed(['python','-B','unapproved.py',root.name],root,'hash-worker')
  with patch.object(large_collect,'main',body):
   with self.assertRaises(AssertionError):traced_collect.main(self.root,'normal')
 def test_markers_have_monotonic_identity(self):
  m=integration_marks.Marks(self.root,'fixture',1);m.add('WORK');m.close('DONE')
  rows=json.loads(next(self.root.glob('integration-fixture-*.json')).read_text())
  self.assertEqual([x['qpc'] for x in rows],sorted(x['qpc'] for x in rows))
  self.assertTrue(all(x['pid']>0 and int(x['created'])>0 and x['frequency']>0 for x in rows))
 def test_marker_budget_is_bounded(self):
  m=integration_marks.Marks(self.root,'fixture',1);m.rows=[{}]*10000
  with self.assertRaises(RuntimeError):m.add('NO')
 def test_existing_evidence_cannot_be_overwritten(self):
  m=integration_marks.Marks(self.root,'fixture',1);m.close('DONE')
  p=next(self.root.glob('integration-fixture-*.json'));before=p.read_bytes()
  with self.assertRaises(FileExistsError):m.close('REWRITE')
  self.assertEqual(p.read_bytes(),before)
if __name__=='__main__':unittest.main(verbosity=2)
