"""Failure-injection component tests; live dual evidence is validated separately."""
import unittest,pathlib,json,uuid,copy,os
from unittest.mock import patch
import dry_contract as c,dry_hash_worker as w,dry_finalize as f
from workspace import CODE,check_path,activate_temp
class Health:
 def __init__(self):self.samples=[]
 def check(self):self.samples.append(1)
class Integration(unittest.TestCase):
 def setUp(self):
  self.root=c.prepare('miniature');activate_temp(self.root);self.v=c.load(self.root)
 def go(self,target):
  while c.state(self.root)['phase']!=target:
   p=c.state(self.root)['phase'];c.advance(self.root,p,c.PHASES[c.PHASES.index(p)+1])
 def test_01_contract(self):self.assertEqual(self.v['scenario'],'miniature');self.assertEqual(len(self.v['inventory']),12)
 def test_02_legacy_mode_rejected(self):
  self.v['mode']='dry'
  with self.assertRaises(ValueError):c.validate(self.root,self.v)
 def test_03_legacy_phase_rejected(self):
  self.v['phase']='E'
  with self.assertRaises(ValueError):c.validate(self.root,self.v)
 def test_04_pass1(self):self.assertEqual(len(w.snapshot(self.root,self.v,Health(),1)),12)
 def test_05_two_independent_hashes(self):
  a=w.snapshot(self.root,self.v,Health(),1);b=w.snapshot(self.root,self.v,Health(),2);self.assertEqual(a,b)
 def test_06_metadata_mismatch(self):
  with (pathlib.Path(self.v['source'])/'00.bin').open('ab') as out:out.write(b'x')
  with self.assertRaises(ValueError):c.load(self.root)
 def test_07_hash_checks_heartbeat(self):
  h=Health();w.snapshot(self.root,self.v,h,1);self.assertGreaterEqual(len(h.samples),24)
 def test_08_hash_health_failure(self):
  h=Health();h.check=lambda:(_ for _ in ()).throw(RuntimeError('stale heartbeat'))
  with self.assertRaises(RuntimeError):w.snapshot(self.root,self.v,h,1)
  self.assertFalse((self.root/'hash-pass-1.json').exists())
 def test_09_finalize_before_closure_rejected(self):
  with self.assertRaises(RuntimeError):f.require_ready(self.root)
 def test_10_primary_failure_blocks(self):
  self.go('OBSERVERS_CLOSED');c.save(self.root/'primary-failure.json',{'error':'original'})
  with self.assertRaises(RuntimeError):f.finalize(self.root)
  self.assertFalse((self.root/'baseline-manifest.json').exists())
 def test_11_hash_failure_blocks(self):
  self.go('OBSERVERS_CLOSED');c.save(self.root/'hash-failure.json',{'error':'hash'})
  with self.assertRaises(RuntimeError):f.finalize(self.root)
  self.assertFalse((self.root/'evidence.zip').exists())
 def test_12_missing_lifecycle_blocks_manifest(self):
  self.go('OBSERVERS_CLOSED')
  with self.assertRaises((OSError,RuntimeError)):f.finalize(self.root)
  self.assertFalse((self.root/'baseline-manifest.json').exists())
 def test_13_protected_source_rejected_without_access(self):
  self.v['source']=r'C:\Users\jonny\VirtualBox VMs\JARVIS-CLEAN-WIN11'
  with patch.object(c,'inventory',side_effect=AssertionError('must not open')):
   with self.assertRaises(ValueError):c.validate(self.root,self.v)
 def test_14_unrelated_source_rejected_without_access(self):
  self.v['source']=str(CODE.parent)
  with patch.object(c,'inventory',side_effect=AssertionError('must not open')):
   with self.assertRaises(ValueError):c.validate(self.root,self.v)
 def test_15_c_live_fallback_rejected(self):
  with self.assertRaises(ValueError):check_path(pathlib.Path('C:/temp/heartbeat.json'))
 def test_16_traversal_rejected(self):
  with self.assertRaises(ValueError):check_path(self.root/'..'/'escape')
 def test_17_order_rejected(self):
  with self.assertRaises(ValueError):c.advance(self.root,'PREPARED','HASH2_COMPLETE')
 def test_18_stale_transition_rejected(self):
  c.advance(self.root,'PREPARED','OBSERVERS_READY')
  with self.assertRaises(ValueError):c.advance(self.root,'PREPARED','OBSERVERS_READY')
 def test_19_deadline_changes_rejected(self):
  self.v['thresholds']['probe']=20
  with self.assertRaises(ValueError):c.validate(self.root,self.v)
 def test_20_cancelled_hash_no_result(self):
  (self.root/'workload-stop').touch()
  with self.assertRaises(RuntimeError):w.snapshot(self.root,self.v,Health(),1)
 def test_21_unique_runs(self):self.assertNotEqual(self.root,c.prepare('miniature'))
 def test_22_contract_identity_mismatch(self):
  self.v['run']='stale'
  with self.assertRaises(ValueError):c.validate(self.root,self.v)
 def test_23_finalization_order(self):
  self.go('FINALIZED');c.advance(self.root,'FINALIZED','MANIFESTED');self.assertEqual(c.state(self.root)['sequence'],10)
 def test_24_unknown_phase_rejected(self):
  with self.assertRaises(ValueError):c.advance(self.root,'PREPARED','UNKNOWN')
 def test_25_historical_hashes_not_changed_by_tests(self):
  self.assertTrue((CODE/'cleanup_checker.py').exists());self.assertEqual(c.inventory(pathlib.Path(self.v['source'])),self.v['inventory'])
 def test_26_failed_checker_blocks_manifest(self):
  self.go('OBSERVERS_CLOSED');c.save(self.root/'stress-result.json',dict(status='DIAGNOSTIC_COMPLETE',primary_failure=None));c.save(self.root/'launcher-result.json',dict(workExit=0))
  with patch.object(f,'evaluate',return_value=dict(status='FAIL',errors=['missing STOP'])):
   with self.assertRaises(RuntimeError):f.finalize(self.root)
  self.assertFalse((self.root/'baseline-manifest.json').exists())
 def test_27_archive_failure_cannot_pass(self):
  self.go('OBSERVERS_CLOSED');c.save(self.root/'source-hashes.json',[]);c.save(self.root/'hash-pass-2.json',dict(files={}))
  with patch.object(f,'require_ready',return_value=dict(status='PASS')),patch.object(f.zipfile,'ZipFile',side_effect=OSError('injected archive failure')):
   with self.assertRaises(OSError):f.finalize(self.root)
  self.assertEqual(c.state(self.root)['phase'],'MANIFESTED');self.assertFalse((self.root/'integration-result.json').exists())
 def test_28_durable_failure_blocks_manifest(self):
  self.go('OBSERVERS_CLOSED');c.save(self.root/'source-hashes.json',[])
  with patch.object(f,'require_ready',return_value=dict(status='PASS')),patch.object(f.os,'fsync',side_effect=OSError('injected flush failure')):
   with self.assertRaises(OSError):f.finalize(self.root)
  self.assertFalse((self.root/'baseline-manifest.json').exists())
 def test_29_false_producer_success_rejected(self):
  self.go('OBSERVERS_CLOSED');c.save(self.root/'stress-result.json',dict(status='FAILED',primary_failure='original'))
  with self.assertRaises(RuntimeError):f.require_ready(self.root)
 def test_30_unknown_scenario_never_prepares(self):
  with self.assertRaises(ValueError):c.prepare('production')
if __name__=='__main__':unittest.main(verbosity=2)
