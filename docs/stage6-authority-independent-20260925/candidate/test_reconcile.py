import pathlib,tempfile,shutil,json,unittest,sys
from reconcile import reconcile
BASE=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\991e246fb08b45a3904e4cadfa8f4e99\code')
SOURCE=BASE/'etw-stress-b5fc727e71ad49f0b0e528934d0efee9'
class Reconciliation(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='reconcile-test-',dir=BASE);self.root=pathlib.Path(self.temp.name)
  for p in SOURCE.glob('*.json'):shutil.copyfile(p,self.root/p.name)
 def tearDown(self):self.temp.cleanup()
 def mutate(self,fn):
  p=self.root/'etw-result.json';x=json.loads(p.read_text());fn(x);p.write_text(json.dumps(x));return reconcile(self.root)
 def test_complete(self):self.assertEqual(reconcile(self.root)['status'],'PASS')
 def test_loss(self):self.assertEqual(self.mutate(lambda x:x.update(eventsLost=1))['status'],'FAIL')
 def test_missing_exit(self):self.assertEqual(self.mutate(lambda x:x['rows'][0].update(stopQpc=0))['status'],'FAIL')
 def test_wrong_creation(self):self.assertEqual(self.mutate(lambda x:x['rows'][0].update(created='1'))['status'],'FAIL')
 def test_duplicate(self):self.assertEqual(self.mutate(lambda x:x['rows'].append(x['rows'][0].copy()))['status'],'FAIL')
 def test_parent_sequence(self):
  def f(x):
   row=next(r for r in x['rows'] if r['parentSequence'] in {a['sequence'] for a in x['rows']});row['parentSequence']='99999999999'
  self.assertEqual(self.mutate(f)['status'],'FAIL')
 def test_exit_mismatch(self):self.assertEqual(self.mutate(lambda x:x['rows'][0].update(exitCode=100))['status'],'FAIL')
 def test_open_before_exit_is_unexplained(self):
  def f(x):
   rows=json.loads((self.root/'tree-handles.json').read_text())['rows'];keys={(r['pid'],r['created']) for r in rows}
   row=next(r for r in x['rows'] if not r['handleRetained'] and (r['pid'],r['created']) not in keys);row['handleAttemptQpc']=row['startQpc']
  self.assertEqual(self.mutate(f)['status'],'FAIL')
 def test_open_access_denied_is_unexplained(self):
  def f(x):
   keys={(r['pid'],r['created']) for r in json.loads((self.root/'tree-handles.json').read_text())['rows']}
   row=next(r for r in x['rows'] if not r['handleRetained'] and (r['pid'],r['created']) not in keys);row['openError']=5
  self.assertEqual(self.mutate(f)['status'],'FAIL')
 def test_missing_expected_process(self):self.assertEqual(self.mutate(lambda x:x['rows'].pop())['status'],'FAIL')
 def test_unclosed_handle(self):self.assertEqual(self.mutate(lambda x:x['rows'][0].update(handleClosed=False))['status'],'FAIL')
 def test_producer_failure_is_not_erased(self):
  p=self.root/'launcher-result.json';x=json.loads(p.read_text());x['workExit']=1;p.write_text(json.dumps(x));r=reconcile(self.root)
  self.assertEqual(r['status'],'PASS');self.assertEqual(r['producerStatus'],'FAILED_PRESERVED')
if __name__=='__main__':unittest.main()
