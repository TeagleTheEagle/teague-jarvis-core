import unittest,json,copy,uuid,sys
from unittest.mock import patch,MagicMock
import small_binding as b
import dry_health as h
from workspace import CODE,new_run
class Binding(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=b.make('normal');cls.v=json.loads((cls.root/'small-declaration.json').read_text())
 def test_valid(self):self.assertEqual(b.validate(self.root,self.v),self.v)
 def test_mutations(self):
  changes={'schema':'medium','run':'old','code':'C:/wrong','source':'D:/outside','sourceManifestSHA256':'0'*64,'case':'large','files':11,'bytes':59665402098,'heartbeat':11,'probe':14,'observer':16,'campaign':1080,'kernelCapture':1200,'channels':['kernel-authority'],'classes':['DIRECT_WORKER']}
  for key,value in changes.items():
   with self.subTest(key=key):
    v=copy.deepcopy(self.v);v[key]=value
    with self.assertRaises(ValueError):b.validate(self.root,v)
 def test_extra(self):
  with self.assertRaises(ValueError):b.validate(self.root,dict(self.v,realProtectedAccess=True))
 def test_false_synthetic(self):
  real=b.load(self.root);real['synthetic']=False
  with patch.object(b,'load',return_value=real),self.assertRaises(ValueError):b.validate(self.root,self.v)
class Observer(unittest.TestCase):
 def setUp(self):
  self.root=new_run('health-fixture-'+uuid.uuid4().hex)
  self.ids={r:dict(pid=i,created=str(i)) for i,r in enumerate(('etw','detail','app'),1)}
  self.opened=[];self.closed=[];self.bad=None
  self.fake=MagicMock();self.fake.OpenProcess.side_effect=lambda rights,inherit,pid:pid
  self.fake.WaitForSingleObject.side_effect=lambda handle,wait:0 if handle==self.bad else 258
  self.fake.CloseHandle.side_effect=self.closed.append
  self.reader=MagicMock();self.reader.poll.return_value={'age':.2}
  def read(path):return self.ids if path.name=='observer-identities.json' else dict(pid=3,created='3',frequency=10000000)
  self.patches=[patch.object(h,'K',self.fake),patch.object(h,'times',side_effect=lambda handle:[str(handle)]),patch.object(h,'read',side_effect=read),patch.object(h,'HealthReader',return_value=self.reader)]
  for p in self.patches:p.start()
 def tearDown(self):
  for p in self.patches:p.stop()
 def test_all_live(self):
  x=h.Health(self.root);self.assertEqual(len(x.handles),3);x.check();x.close();self.assertEqual(sorted(self.closed),[1,2,3]);self.reader.close.assert_called_once()
 def test_each_observer_exit(self):
  for pid in (1,2,3):
   self.bad=None;x=h.Health(self.root);self.bad=pid
   with self.assertRaises(RuntimeError):x.check()
   self.bad=None
   with self.assertRaises(RuntimeError):x.check()
   x.close()
 def test_missing_channel(self):
  del self.ids['detail']
  with self.assertRaises(ValueError):h.Health(self.root)
 def test_stale_or_malformed_journal(self):
  x=h.Health(self.root);self.reader.poll.side_effect=ValueError('bad journal')
  with self.assertRaises(ValueError):x.check()
  self.reader.poll.side_effect=None
  with self.assertRaises(RuntimeError):x.check()
  x.close()
 def test_creation_mismatch(self):
  with patch.object(h,'times',return_value=['wrong']),self.assertRaises(RuntimeError):h.Health(self.root)
  self.assertEqual(self.closed,[1])
 def test_premature_detail_finalization(self):
  x=h.Health(self.root);(self.root/'detail').mkdir();(self.root/'detail'/'etw-result.json').write_text('{}')
  with self.assertRaises(RuntimeError):x.check()
  x.close()
if __name__=='__main__':unittest.main(verbosity=2)
