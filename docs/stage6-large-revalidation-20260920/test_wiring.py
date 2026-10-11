import unittest,threading,pathlib
from unittest.mock import patch
import secondary_sampling as s
class Ledger:
 def __init__(self):self.errors=[]
 def fail(self,*args):self.errors.append(args)
class Wiring(unittest.TestCase):
 def execute(self,result):
  called=threading.Event();saved={};ledger=Ledger();launches=[]
  def query(root,mode,ordinal,cancel,tracker):
   self.assertEqual(mode,'normal');self.assertEqual(ordinal,0);called.set();return result
  with patch.object(s,'query',query),patch.object(s,'save',lambda p,v:saved.update(v)):
   worker=s.SecondarySampler(pathlib.Path('D:/synthetic-test'),object(),launches,ledger);self.assertTrue(called.wait(2));worker.close()
  self.assertFalse(worker.thread.is_alive());return ledger,saved,launches
 def test_normal(self):
  l,v,a=self.execute(dict(pid=123,created='456',status='AVAILABLE',allExited=True,handleClosed=True));self.assertFalse(l.errors);self.assertEqual(v['missing'],0);self.assertEqual(a[0]['created'],'456')
 def test_optional_timeout_stays_secondary(self):
  l,v,a=self.execute(dict(status='MISSING',reason='QUERY_TIMEOUT',allExited=True,handleClosed=True));self.assertFalse(l.errors);self.assertEqual(v['missing'],1)
 def test_unproven_cleanup_blocks(self):
  l,v,a=self.execute(dict(status='CLEANUP_FAILED',allExited=False,handleClosed=True));self.assertTrue(l.errors)
 def test_core_collector_not_changed(self):
  import baseline_collect
  self.assertNotIn('SecondarySampler',pathlib.Path(baseline_collect.__file__).read_text())
if __name__=='__main__':unittest.main(verbosity=2)
