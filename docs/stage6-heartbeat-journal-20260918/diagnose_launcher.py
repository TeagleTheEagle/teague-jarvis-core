import pathlib,tempfile,subprocess,sys,json,time
from journal import PublisherWatch
r=pathlib.Path(__file__).parent
pdir=pathlib.Path(tempfile.mkdtemp(prefix='process-launcher-',dir=r))
p=subprocess.Popen([sys.executable,'-B',str(r/'process_fixture.py'),str(pdir),'publisher'])
try:
 end=time.monotonic()+5
 while not (pdir/'ready.json').exists():
  if time.monotonic()>end:raise RuntimeError('readiness timeout')
  time.sleep(.01)
 ident=json.loads((pdir/'ready.json').read_text());watch=PublisherWatch(ident)
 p.kill();p.wait();watch.check()
 result={'launcher_pid':p.pid,'publisher_identity':ident,'launcher_exit':p.returncode,'publisher_alive_after_launcher_exit':True,'executable':sys.executable,'base_executable':sys._base_executable}
 (r/'launcher-diagnosis.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 (pdir/'stop').touch()
 if p.poll() is None:p.wait(timeout=5)
 time.sleep(.2)
 try:watch.check();raise RuntimeError('publisher failed to exit')
 except Exception as e:
  from journal import Unhealthy
  if not isinstance(e,Unhealthy):raise
 finally:watch.close()
