import unittest,pathlib,tempfile,subprocess,time,json,ctypes as c,ctypes.wintypes as w
from finalize import finalize,accepted
from journal import PublisherWatch
R=pathlib.Path(__file__).resolve().parent
PWSH=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
class FailedCampaigns(unittest.TestCase):
 def test_queue_consumer_death_is_explicit_campaign_failure(self):
  root=pathlib.Path(tempfile.mkdtemp(prefix='queue-crash-',dir=R))
  p=subprocess.Popen([PWSH,'-NoProfile','-File',str(R/'queue_crash_fixture.ps1'),'-OutputDirectory',str(root)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=0x08000000)
  try:
   end=time.monotonic()+10
   while not (root/'ready.json').exists():
    if p.poll() is not None or time.monotonic()>end:raise AssertionError('Sacrificial fixture readiness failed')
    time.sleep(.02)
   info=json.loads((root/'ready.json').read_text(encoding='utf-8-sig'));self.assertEqual(info['identity']['pid'],p.pid)
   k=c.WinDLL('kernel32',use_last_error=True);k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4
   times=[w.FILETIME() for _ in range(4)];self.assertTrue(k.GetProcessTimes(int(p._handle),*[c.byref(v) for v in times]))
   created=str((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime);self.assertEqual(created,info['identity']['created'])
   self.assertEqual(info['queue']['enqueued'],8);self.assertEqual(info['queue']['persisted'],0)
   p.kill();_,err=p.communicate(timeout=5)
   failure={'status':'FAILED_CLOSED','injected':'selected queue consumer termination','pid':p.pid,'created':created,'exit':p.returncode,'retained_handle_cleanup':True,'unpersisted_entries':8,'stderr':err.decode(errors='replace')}
   (root/'collector-failure.json').write_text(json.dumps(failure,indent=2))
   with self.assertRaisesRegex(RuntimeError,'Preserved failure'):finalize(root)
   self.assertFalse(accepted(root,0));self.assertNotEqual(p.returncode,0)
  finally:
   if p.poll() is None:p.kill();p.communicate(timeout=5)
if __name__=='__main__':unittest.main(verbosity=2)
