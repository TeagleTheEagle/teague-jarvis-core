import unittest,threading,uuid
from unittest.mock import patch
import bounded_sampler as s
from workspace import new_run,activate_temp,CODE
from lineage import associate
from test_hardening_scope import row,ev
class Boundary(unittest.TestCase):
 def test_truncated_image_remains_unknown(self):
  r=row(7,10,20,'x');r['image']=r'D:\J6ProbeNative.exe';e=ev(7,21,'stop',received=100);e['name']='J6ProbeNative.'
  self.assertTrue(associate([r],[e],{'x'})['unknown'])
 def test_short_helper_is_exact_binary_copy(self):
  self.assertEqual((CODE/'J6Native.exe').read_bytes(),(CODE/'J6ProbeNative.exe').read_bytes())
 def test_missing_required_job_proof_fails_closed(self):
  root=new_run('missing-proof-'+uuid.uuid4().hex);activate_temp(root)
  with patch.object(s.K,'QueryInformationJobObject',return_value=0):v=s.query(root,'normal',0,threading.Event())
  self.assertEqual(v['status'],'CLEANUP_FAILED');self.assertFalse(v['allExited']);self.assertTrue(v['handleClosed']);self.assertEqual(v['handleState'],0)

 def test_delayed_stop_cannot_transfer_to_reused_pid(self):
  a=row(7,10,20,'a');b=row(7,100,120,'b');e=ev(7,121,'stop',received=200)
  v=associate([a,b],[e],{'a','b'});self.assertFalse(v['bound']);self.assertEqual(len(v['unknown']),1)
 def test_delayed_start_cannot_transfer_to_reused_pid(self):
  a=row(7,10,20,'a');b=row(7,100,120,'b');e=ev(7,101,'start',received=200)
  v=associate([a,b],[e],{'a','b'});self.assertFalse(v['bound']);self.assertEqual(len(v['unknown']),1)
