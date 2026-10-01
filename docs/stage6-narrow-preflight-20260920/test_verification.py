import unittest,pathlib,tempfile,json,zipfile
from unittest.mock import patch
import verification as v
class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.r=pathlib.Path(self.tmp.name)
  (self.r/'source.py').write_bytes(b'frozen');(self.r/'calibration.json').write_text('{"bytes": 17}')
  self.rows=[dict(name='source.py',sha256=v.sha_bytes(b'frozen'))]
  data=b'preserved';self.m=dict(files=[dict(name='fixture/evidence.json',source=str(self.r/'inaccessible'/'collector-finished.json'),bytes=len(data),sha256=v.sha_bytes(data))])
  raw=json.dumps(self.m).encode();(self.r/'archive-manifest.json').write_bytes(raw)
  with zipfile.ZipFile(self.r/'evidence.zip','w') as z:z.writestr('fixture/evidence.json',data);z.writestr('archive-manifest.json',raw)
  self.receipt=dict(members=2,zipSHA256=v.sha_bytes((self.r/'evidence.zip').read_bytes()),manifestSHA256=v.sha_bytes(raw))
 def test_01_candidate(self):self.assertEqual(v.verify_candidate(self.r,self.rows),1)
 def test_02_calibration(self):self.assertEqual(v.verify_calibration([(self.r/'calibration.json',v.sha_bytes((self.r/'calibration.json').read_bytes()))])[0]['bytes'],17)
 def test_03_zip_hash(self):self.assertTrue(v.verify_hash(self.r/'evidence.zip',self.receipt['zipSHA256']))
 def test_04_manifest_hash(self):self.assertEqual(json.loads(v.verify_hash(self.r/'archive-manifest.json',self.receipt['manifestSHA256'])),self.m)
 def test_05_members(self):self.assertEqual(v.verify_archive(self.r,self.receipt),self.m)
 def test_06_inaccessible_extracted_file_never_read(self):
  real=pathlib.Path.read_bytes;opens=[]
  def checked(p):
   opens.append(p)
   if 'inaccessible' in p.parts:raise PermissionError('Fixture denied')
   return real(p)
  with patch.object(pathlib.Path,'read_bytes',checked):v.verify_archive(self.r,self.receipt)
  self.assertEqual(set(opens),{self.r/'evidence.zip',self.r/'archive-manifest.json'})
 def test_07_missing_archive(self):
  (self.r/'evidence.zip').unlink()
  with self.assertRaises(FileNotFoundError):v.verify_archive(self.r,self.receipt)
 def test_08_archive_mismatch(self):
  with self.assertRaises(ValueError):v.verify_archive(self.r,dict(self.receipt,zipSHA256='0'*64))
 def test_09_candidate_mismatch(self):
  (self.r/'source.py').write_bytes(b'changed')
  with self.assertRaises(ValueError):v.verify_candidate(self.r,self.rows)
 def test_10_calibration_mismatch(self):
  with self.assertRaises(ValueError):v.verify_calibration([(self.r/'calibration.json','0'*64)])
 def test_11_live_process(self):
  with self.assertRaises(ValueError):v.verify_safety(dict(processes=[{'pid':42}],traces=[],traceExit=0))
 def test_12_live_trace(self):
  with self.assertRaises(ValueError):v.verify_safety(dict(processes=[],traces=['J6Kernel-test'],traceExit=0))
 def test_13_safety_ok(self):self.assertTrue(v.verify_safety(dict(processes=[],traces=[],traceExit=0)))
 def test_14_manifest_mismatch(self):
  with self.assertRaises(ValueError):v.verify_archive(self.r,dict(self.receipt,manifestSHA256='0'*64))
if __name__=='__main__':unittest.main(verbosity=2)
