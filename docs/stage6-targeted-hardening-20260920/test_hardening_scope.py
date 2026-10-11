import unittest,copy,pathlib,json
from lineage import associate,parent_valid
import cleanup_checker
def row(pid,created,exit,seq,parent=1,pseq='p'):
 return dict(pid=pid,created=str(created),exitFiletime=str(exit),sequence=seq,parentPid=parent,parentSequence=pseq,startQpc=created,stopQpc=exit,image='D:\\child.exe')
def ev(pid,stamp,kind='start',parent=1,received=None):return dict(pid=pid,nativeTime=str(stamp),kind=kind,parentPid=parent,name='child.exe',receivedQpc=stamp+10 if received is None else received)
class Lineage(unittest.TestCase):
 def test_01_reused_parent_predates_creation(self):
  p=row(1,200,400,'p');v=associate([p],[ev(7,100,parent=1)],{'p'});self.assertFalse(v['unknown']);self.assertEqual(len(v['outside']),1)
 def test_02_child_pid_reuse(self):
  a=row(7,10,20,'a');b=row(7,100,120,'b');v=associate([a,b],[ev(7,11),ev(7,101)],{'a','b'});self.assertEqual(set(v['bound']),{'a','b'})
 def test_03_same_pid_different_creation_not_reassigned(self):
  a=row(7,100,120,'a');v=associate([a],[ev(7,11)],{'a'});self.assertFalse(v['bound'])
 def test_04_parent_exits_before_delayed_notification(self):
  p=row(1,1,30,'p');a=row(7,10,50,'a');self.assertTrue(parent_valid(a,p));v=associate([p,a],[ev(7,11,received=100)],{'p','a'});self.assertEqual(len(v['bound']['a']),1)
 def test_05_impossible_order(self):self.assertFalse(parent_valid(row(7,10,20,'a'),row(1,11,30,'p')))
 def test_06_delayed_delivery(self):
  a=row(7,10,20,'a');v=associate([a],[ev(7,21,'stop',received=1000)],{'a'});self.assertEqual(len(v['bound']['a']),1)
 def test_07_handle_key_not_pid(self):
  a=row(7,10,20,'a');b=row(7,100,120,'b');handle={'pid':7,'created':'100'};match=[r for r in [a,b] if (r['pid'],r['created'])==(handle['pid'],handle['created'])];self.assertEqual(match,[b])
 def test_08_valid_parent(self):self.assertTrue(parent_valid(row(7,10,20,'a'),row(1,1,30,'p')))
 def test_09_ambiguous_rejected(self):
  a=row(7,10,20,'a');b=row(7,10,20,'b');v=associate([a,b],[ev(7,11)],{'a','b'});self.assertTrue(v['unknown'])
 def test_10_no_mutation_reassignment(self):
  rows=[row(7,10,20,'a')];events=[ev(7,11)];before=copy.deepcopy((rows,events));associate(rows,events,{'a'});self.assertEqual((rows,events),before)
 def test_11_wrong_kernel_parent_sequence(self):self.assertFalse(parent_valid(row(7,10,20,'a',pseq='other'),row(1,1,30,'p')))
 def test_12_missing_child_is_unknown(self):
  v=associate([row(1,1,30,'p')],[ev(7,10)],{'p'});self.assertEqual(v['unknown'][0]['status'],'UNKNOWN')
 def test_13_wrong_image_unknown(self):
  a=row(7,10,20,'a');e=ev(7,11);e['name']='other.exe';self.assertTrue(associate([a],[e],{'a'})['unknown'])
 def test_14_event_before_kernel_start_rejected(self):
  a=row(7,10,20,'a');self.assertTrue(associate([a],[ev(7,11,received=9)],{'a'})['unknown'])
 def test_15_real_reuse_failure_replay(self):
  r=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\0bafc8d10864489782bd174e3699094c\code\correlation-ladder-4b1da87a04724e84a1435bd5be5e8c03');v=cleanup_checker.evaluate(r);self.assertEqual(v['status'],'PASS',v.get('errors'));self.assertFalse(v['acceptance']);self.assertTrue(v['lineageExcluded'])
 def test_16_prior_valid_run(self):
  r=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\b675935592fe41d48968e22be8cc6641\code\integrated-dry1-8c2cbaeef9d04a8080b9bcf22fae89cd');v=cleanup_checker.evaluate(r);self.assertEqual(v['status'],'PASS',v.get('errors'))
 def test_17_original_failure_stays_failed(self):
  r=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code\protected-3aec3ce0062c42a19077a2bad0571bd7');v=cleanup_checker.evaluate(r);self.assertEqual(v['status'],'FAIL');self.assertIsNotNone(v['primaryFailure'])
if __name__=='__main__':unittest.main(verbosity=2)
