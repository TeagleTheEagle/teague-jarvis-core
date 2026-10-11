import unittest,tempfile,pathlib,subprocess,sys,time,json,os
from journal import Reader,PublisherWatch,Unhealthy,encode,ticks
R=pathlib.Path(__file__).parent
class Processes(unittest.TestCase):
 def setUp(self):
  self.r=pathlib.Path(tempfile.mkdtemp(prefix='process-',dir=R));self.children=[];self.readers=[];self.watches=[]
 def launch(self,mode):
  p=subprocess.Popen([sys._base_executable,'-B',str(R/'process_fixture.py'),str(self.r),mode]);self.children.append(p);return p
 def waitfile(self,name):
  end=time.monotonic()+5
  while not (self.r/name).exists():
   if time.monotonic()>end:raise AssertionError('fixture readiness timeout')
   time.sleep(.01)
 def ready(self):
  p=self.launch('publisher');self.waitfile('ready.json');self.ident=json.loads((self.r/'ready.json').read_text())
  self.assertEqual(p.pid,self.ident['pid'])
  (self.r/'process-evidence.json').write_text(json.dumps({'launched_pid':p.pid,'publisher_identity':self.ident,'executable':sys._base_executable}))
  watch=PublisherWatch(self.ident);self.watches.append(watch);reader=Reader(self.r/'journal',self.ident,liveness=watch.check);self.readers.append(reader);return p,reader
 def tearDown(self):
  (self.r/'stop').touch()
  for p in self.children:
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:p.kill();p.wait()
  for r in self.readers:r.close()
  for w in self.watches:w.close()
 def test_continuous_reader_and_publisher(self):
  p,r=self.ready();a=r.poll()['sequence'];time.sleep(.3);self.assertGreater(r.poll()['sequence'],a)
 def test_killed_publisher_immediate_failure(self):
  p,r=self.ready();r.poll();p.kill();p.wait()
  with self.assertRaises(Unhealthy):r.poll()
 def test_delayed_writer_expires_ten_seconds(self):
  p,r=self.ready();r.poll();(self.r/'pause').touch();time.sleep(10.25)
  with self.assertRaises(Unhealthy):r.poll()
 def test_reader_killed_restarted(self):
  p,r=self.ready();q=self.launch('reader');self.waitfile('reader-ready');q.kill();q.wait();a=r.poll()['sequence'];time.sleep(.15)
  fresh=Reader(self.r/'journal',self.ident);self.readers.append(fresh);self.assertGreater(fresh.poll()['sequence'],a)
 def test_publisher_restart_old_authority_rejected(self):
  p,r=self.ready();r.poll();p.kill();p.wait();q=self.launch('publisher');time.sleep(.2)
  with self.assertRaises(Unhealthy):r.poll()
  fresh=Reader(self.r/'journal',self.ident);self.readers.append(fresh)
  with self.assertRaises(Unhealthy):fresh.poll()
 def test_rotation_under_active_reader(self):
  p,r=self.ready();r.poll();replacement=self.r/'replacement';replacement.write_bytes((self.r/'journal').read_bytes())
  try:os.replace(replacement,self.r/'journal')
  except PermissionError:self.assertTrue(replacement.exists());r.poll()
  else:
   with self.assertRaises(Unhealthy):r.poll()
 def test_malformed_append(self):
  p,r=self.ready();r.poll();(self.r/'pause').touch();time.sleep(.1)
  with (self.r/'journal').open('ab') as f:f.write(b'broken\n')
  with self.assertRaises(ValueError):r.poll()
 def test_partial_append_not_healthy_record(self):
  p,r=self.ready();(self.r/'pause').touch();time.sleep(.1);a=r.poll()['sequence']
  with (self.r/'journal').open('ab') as f:f.write(b'{"seq":')
  self.assertEqual(r.poll()['sequence'],a)
 def test_hashing_child_crash_cannot_complete(self):
  p,r=self.ready();q=self.launch('hasher');self.waitfile('hasher-ready');q.kill();q.wait();r.poll()
  self.assertNotEqual(q.returncode,0);self.assertFalse((self.r/'baseline-manifest.json').exists())
if __name__=='__main__':unittest.main(verbosity=2)
