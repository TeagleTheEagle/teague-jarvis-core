import unittest,threading,time,pathlib
from test_finalization import fixture
from finalize import finalize,accepted,sync_file
class ExtendedFinalization(unittest.TestCase):
 def test_delay_beyond_live_threshold_is_not_early_acceptance(self):
  root=fixture();entered=threading.Event();release=threading.Event();errors=[];first=True
  def sync(p):
   nonlocal first
   if first:first=False;entered.set();release.wait(20)
   sync_file(p)
  def worker():
   try:finalize(root,sync=sync)
   except BaseException as e:errors.append(repr(e))
  t=threading.Thread(target=worker);t.start()
  try:
   self.assertTrue(entered.wait(1));time.sleep(10.2);self.assertTrue(t.is_alive());self.assertFalse(accepted(root,0));self.assertFalse((root/'EVIDENCE-DURABLY-FINALIZED.json').exists())
  finally:release.set();t.join(10)
  self.assertFalse(t.is_alive());self.assertFalse(errors);self.assertTrue(accepted(root,0))
if __name__=='__main__':unittest.main(verbosity=2)
