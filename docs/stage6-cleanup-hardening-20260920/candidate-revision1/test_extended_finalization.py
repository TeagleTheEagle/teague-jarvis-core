import unittest,threading,time,pathlib,json
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
  started=time.perf_counter();t=threading.Thread(target=worker);t.start()
  try:
   self.assertTrue(entered.wait(1));time.sleep(10.2);self.assertTrue(t.is_alive());self.assertFalse(accepted(root,0));self.assertFalse((root/'EVIDENCE-DURABLY-FINALIZED.json').exists())
  finally:
   released=time.perf_counter();release.set();t.join(60)
   (pathlib.Path(__file__).parent/'extended-delay-result.json').write_text(json.dumps({'withheld_seconds':released-started,'finalization_wait_seconds':time.perf_counter()-released,'worker_still_alive':t.is_alive(),'errors':errors,'deadline_seconds':60}))
  self.assertFalse(t.is_alive());self.assertFalse(errors);self.assertTrue(accepted(root,0))
if __name__=='__main__':unittest.main(verbosity=2)
