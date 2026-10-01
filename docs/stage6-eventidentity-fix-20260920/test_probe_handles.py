import unittest,subprocess,pathlib,ctypes as c,ctypes.wintypes as w,json
R=pathlib.Path(__file__).parent
class ProbeHandles(unittest.TestCase):
 def test_fifty_retained_process_identities_remain_distinct(self):
  k=c.WinDLL('kernel32',use_last_error=True);k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4;k.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)]
  handles=[];rows=[]
  for _ in range(50):
   p=subprocess.Popen([str(R/'J6Probe.exe')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);handles.append(p);self.assertEqual(p.wait(timeout=5),0)
   values=[w.FILETIME() for _ in range(4)];self.assertTrue(k.GetProcessTimes(int(p._handle),*[c.byref(v) for v in values]))
   rows.append({'pid':p.pid,'created':str((values[0].dwHighDateTime<<32)|values[0].dwLowDateTime)})
  self.assertEqual(len({r['pid'] for r in rows}),50)
  for p in handles:
   code=w.DWORD();self.assertTrue(k.GetExitCodeProcess(int(p._handle),c.byref(code)));self.assertEqual(code.value,0)
  (R/'probe-handle-regression.json').write_text(json.dumps({'status':'PASS','identities':rows,'handles_retained':50},indent=2))
if __name__=='__main__':unittest.main(verbosity=2)
