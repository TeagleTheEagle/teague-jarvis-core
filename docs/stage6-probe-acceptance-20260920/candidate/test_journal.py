import unittest,tempfile,pathlib,json,threading,time,io,errno,os
from unittest.mock import patch
from journal import Reader,Unhealthy,append,encode,MAX_BYTES
ROOT=pathlib.Path(__file__).parent
class Tests(unittest.TestCase):
 def setUp(self):
  self.root=pathlib.Path(tempfile.mkdtemp(prefix='fixture-',dir=ROOT));self.p=self.root/'heartbeat.jsonl';self.p.touch()
  self.now=100000;self.ident={'run':'TEST','pid':123,'created':'456','frequency':1000};self.seq=0
 def row(self,**changes):
  self.seq+=1;r=dict(self.ident,seq=self.seq,ticks=self.now,pump=self.seq,utc='synthetic',state='ACTIVE',violations=0);r.update(changes);return r
 def put(self,row):
  with self.p.open('ab') as f:append(f,row)
 def reader(self):return Reader(self.p,self.ident,lambda:self.now)
 def reject(self,reader):
  with self.assertRaises((Unhealthy,OSError,ValueError)):reader.poll()
 def test_sequential(self):
  self.put(self.row());r=self.reader()
  try:
   for _ in range(20):self.put(self.row());self.assertEqual(r.poll()['sequence'],self.seq)
  finally:r.close()
 def test_continuous_reader_concurrent_append(self):
  self.put(self.row());r=self.reader();errors=[]
  def writer():
   try:
    for _ in range(100):self.put(self.row());time.sleep(.001)
   except Exception as e:errors.append(str(e))
  t=threading.Thread(target=writer);t.start()
  try:
   while t.is_alive():r.poll();time.sleep(.001)
   t.join();self.assertEqual(r.poll()['sequence'],101);self.assertFalse(errors)
  finally:r.close()
 def test_partial_line_does_not_renew(self):
  self.put(self.row());r=self.reader()
  try:
   r.poll();data=encode(self.row())
   with self.p.open('ab') as f:f.write(data[:12])
   self.assertEqual(r.poll()['sequence'],1)
   self.now+=10001;self.reject(r)
  finally:r.close()
 def test_partial_then_complete(self):
  self.put(self.row());r=self.reader();data=encode(self.row())
  try:
   with self.p.open('ab') as f:f.write(data[:12]);f.flush();self.assertEqual(r.poll()['sequence'],1);f.write(data[12:]);f.flush()
   self.assertEqual(r.poll()['sequence'],2)
  finally:r.close()
 def test_malformed(self):
  self.put(self.row())
  with self.p.open('ab') as f:f.write(b'not-json\n')
  r=self.reader()
  try:self.reject(r)
  finally:r.close()
 def test_stale(self):
  self.put(self.row());r=self.reader();self.now+=10001
  try:self.reject(r)
  finally:r.close()
 def test_exact_ten_seconds(self):
  self.put(self.row());r=self.reader();self.now+=10000
  try:self.assertEqual(r.poll()['age'],10);self.now+=1;self.reject(r)
  finally:r.close()
 def test_duplicate(self):
  row=self.row();self.put(row);self.put(row);r=self.reader()
  try:self.reject(r)
  finally:r.close()
 def test_skipped(self):
  self.put(self.row(seq=2));r=self.reader()
  try:self.reject(r)
  finally:r.close()
 def test_publisher_restart(self):
  self.put(self.row());self.put(self.row(pid=124));r=self.reader()
  try:self.reject(r)
  finally:r.close()
 def test_wrong_run(self):
  self.put(self.row(run='OTHER'));r=self.reader()
  try:self.reject(r)
  finally:r.close()
 def test_reader_restart_revalidates(self):
  self.put(self.row());r=self.reader();r.poll();r.close();self.now+=10001;r=self.reader()
  try:self.reject(r)
  finally:r.close()
 def test_rotation_fails_closed(self):
  self.put(self.row());r=self.reader();r.poll()
  try:
   # A changed path identity, even if an old read handle remains valid.
   old=self.p.stat()
   class S:st_dev=old.st_dev;st_ino=old.st_ino+1;st_size=old.st_size
   with patch.object(pathlib.Path,'stat',return_value=S()):self.reject(r)
  finally:r.close()
 def test_truncation(self):
  self.put(self.row());r=self.reader();r.poll();self.p.write_bytes(b'')
  try:self.reject(r)
  finally:r.close()
 def test_access_denied_latches(self):
  self.put(self.row());r=self.reader()
  try:
   with patch.object(pathlib.Path,'stat',side_effect=PermissionError(errno.EACCES,'simulated')):self.reject(r)
   self.reject(r)
  finally:r.close()
 def test_disk_full(self):
  class Full(io.BytesIO):
   def write(self,b):raise OSError(errno.ENOSPC,'simulated disk full')
  with self.assertRaises(OSError):append(Full(),self.row())
 def test_short_write(self):
  class Short(io.BytesIO):
   def write(self,b):return 1
  with self.assertRaises(Unhealthy):append(Short(),self.row())
 def test_bound(self):
  f=io.BytesIO();f.seek(MAX_BYTES)
  with self.assertRaises(Unhealthy):append(f,self.row())
 def test_dead_publisher(self):
  self.put(self.row())
  def dead():raise Unhealthy('publisher exited')
  r=Reader(self.p,self.ident,lambda:self.now,dead)
  try:self.reject(r)
  finally:r.close()
 def test_failed_pump(self):
  self.put(self.row(pump=0));r=self.reader()
  try:self.reject(r)
  finally:r.close()
 def test_time_regression(self):
  self.put(self.row());self.put(self.row(ticks=self.now-1));r=self.reader()
  try:self.reject(r)
  finally:r.close()
 def test_future(self):
  self.put(self.row(ticks=self.now+1));r=self.reader()
  try:self.reject(r)
  finally:r.close()
if __name__=='__main__':unittest.main(verbosity=2)
