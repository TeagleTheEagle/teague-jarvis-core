"""Future owner-authorized execution only. No import-time execution."""
import pathlib,json,subprocess,time,ctypes,sys
from analyze import verify_binding,load_raw,validate,analyze
def main():
 if sys.argv[1:]!=['--execute-one-final-attempt']:raise SystemExit('Explicit execution argument required; preparation must not invoke it.')
 root=pathlib.Path(__file__).parent;b=json.loads((root/'qualification-binding-final.json').read_text());verify_binding(b)
 run=pathlib.Path(b['workspace'])/'ONE-FINAL-ATTEMPT';run.mkdir(exist_ok=False)
 (run/'started.json').write_text(json.dumps(dict(protocol=b['protocolSHA256'],start=time.time(),retry=False)))
 started=time.monotonic();code=None;timed_out=False
 with (run/'raw.jsonl').open('xb') as out,(run/'stderr.txt').open('xb') as err:
  p=subprocess.Popen([b['binary'],'--qualify',b['protocolSHA256']],cwd=b['workspace'],stdout=out,stderr=err)
  class FT(ctypes.Structure):_fields_=[('low',ctypes.c_uint32),('high',ctypes.c_uint32)]
  a,z,k,u=FT(),FT(),FT(),FT();api=ctypes.WinDLL('kernel32',use_last_error=True).GetProcessTimes;api.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(FT)]*4;api.restype=ctypes.c_int
  if not api(int(p._handle),ctypes.byref(a),ctypes.byref(z),ctypes.byref(k),ctypes.byref(u)):
   p.kill();p.wait(timeout=10);raise RuntimeError('retained process identity unavailable')
  created=(a.high<<32)|a.low
  (run/'process.json').write_text(json.dumps(dict(pid=p.pid,created=created,binary=b['binary'])))
  try:code=p.wait(timeout=max(0,1200-(time.monotonic()-started)))
  except subprocess.TimeoutExpired:timed_out=True;p.kill();code=p.wait(timeout=10)
 (run/'exit.json').write_text(json.dumps(dict(code=code,timedOut=timed_out,seconds=time.monotonic()-started,pid=p.pid,exited=True)))
 verify_binding(b)
 if timed_out:raise RuntimeError('single launcher bound exceeded; preserve partial evidence, no retry')
 rows=load_raw(run/'raw.jsonl');blocks=validate(rows,code,b['protocolSHA256'])
 if rows[0]['pid']!=p.pid or rows[0]['created']!=created:raise RuntimeError('retained process identity contradiction')
 (run/'analysis.json').write_text(json.dumps(analyze(blocks),indent=2))
 print('One attempt ended. Final census, drift review and archival required. Do not retry.')
if __name__=='__main__':main()
