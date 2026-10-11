import unittest,pathlib,sys,json,time,hashlib,uuid,subprocess
from workspace import CODE,new_run,activate_temp
from evidence_support import Ledger,Managed,TreeTracker,put
from probe_timing import Probe,K,process_times
class Hardening(unittest.TestCase):
 def setUp(self):self.r=new_run('harden-test-'+uuid.uuid4().hex);activate_temp(self.r)
 def helper(self,mode,tree=None):return Managed([sys._base_executable,'-B',str(CODE/'trace_fixture.py'),str(self.r),mode],self.r,'fixture',tree)
 def test_primary_survives_cleanup_failure(self):
  l=Ledger(self.r);l.fail('probe','original');before=(self.r/'primary-failure.json').read_bytes();l.fail('cleanup','second');self.assertEqual(before,(self.r/'primary-failure.json').read_bytes());self.assertEqual(l.result()['status'],'FAILED')
 def test_primary_survives_archive_failure(self):
  l=Ledger(self.r);l.fail('probe','original');l.fail('archive',OSError('copy failed'));self.assertEqual(l.primary['error'],'original');self.assertEqual(len(l.secondary),1)
 def test_output_nonzero_and_large_both_streams(self):
  m=self.helper('nonzero');r=m.finish();self.assertEqual(r['exit'],7)
  for n in ('stdout','stderr'):self.assertEqual(r[n]['totalBytes'],2097152);self.assertEqual(r[n]['storedBytes'],65536);self.assertTrue(r[n]['truncated']);self.assertTrue(r[n]['eof']);self.assertFalse(r[n]['threadAlive'])
 def treecase(self,mode):
  t=TreeTracker();m=self.helper(mode,t);r=m.finish();before=t.snapshot();v=t.finish(self.r)
  self.assertEqual(r['exit'],0);self.assertTrue(v['allExited']);self.assertTrue(v['allHandlesClosed']);self.assertFalse(v['errors'])
  child=[x for x in v['rows'] if x['parentPid']==m.p.pid and x['image'].lower().endswith('python.exe')];self.assertEqual(len(child),1)
  main=next(x for x in v['rows'] if x['pid']==m.p.pid);self.assertNotEqual(main['handleIdentity'],child[0]['handleIdentity']);self.assertTrue(int(child[0]['created'])>=int(main['created']))
  return main,child[0],before
 def test_child_exits_before_parent(self):
  m,ch,_=self.treecase('child-first');self.assertLess(int(ch['exitFiletime']),int(m['exitFiletime']))
 def test_parent_exits_before_child(self):
  m,ch,_=self.treecase('parent-first');self.assertLess(int(m['exitFiletime']),int(ch['exitFiletime']))
 def test_cleanup_catches_live_orphan(self):
  m,ch,before=self.treecase('orphan');self.assertTrue(any(x['parentPid']==m['pid'] and x['signalObservedQpc'] is None for x in before));self.assertLess(int(m['exitFiletime']),int(ch['exitFiletime']))
 def test_console_helper_handle(self):
  t=TreeTracker();m=self.helper('child-first',t);m.finish();v=t.finish(self.r)
  self.assertTrue(any(x['role'].startswith('descendant:') and pathlib.Path(x['image']).name.lower() in ('conhost.exe','openconsole.exe') for x in v['rows']));self.assertTrue(v['allExited'])
 def test_internal_markers(self):
  m=self.helper('trace');m.finish();v=[json.loads(x) for x in (self.r/('internal-'+str(m.p.pid)+'.jsonl')).read_text().splitlines()];stages=[x['stage'] for x in v]
  for n in ('entry','initialization.end','work.begin','identity.begin','identity.end','filesystem.begin','filesystem.end','cleanup.begin','stdout.close.end','stderr.close.end','cleanup.end','return-main'):self.assertIn(n,stages)
  self.assertEqual([x['monotonicNs'] for x in v],sorted(x['monotonicNs'] for x in v))
 def test_timeout_then_later_exit_output_preserved(self):
  # Real fixed 13.6/15s observer exercised once using explicitly delayed synthetic helper.
  p=Probe(sys._base_executable,['-B',str(CODE/'trace_fixture.py'),str(self.r),'late'])
  origin=time.perf_counter();failure=None
  try:p.wait_approved(lambda:None,lambda v:None,time.perf_counter()+30)
  except Exception as e:failure=str(e)
  self.assertIn('HARD_DEADLINE',failure);self.assertTrue(p.row['hardDeadlineFailure'])
  p.process.wait(timeout=10);p.finish_observation();self.assertEqual(p.row['observerResult'],258);self.assertEqual(p.row['finalHandleState'],0);self.assertEqual(p.row['actualExitCode'],0);self.assertTrue(p.row['hardDeadlineFailure']);put(self.r/'late-observer.json',p.row);p.process._handle.Close()
 def test_output_preserved_when_parent_scope_fails(self):
  l=Ledger(self.r);m=self.helper('output')
  try:raise RuntimeError('injected collector exception')
  except Exception:l.fail('parent')
  v=m.finish();self.assertEqual(l.result()['status'],'FAILED');self.assertEqual(v['stdout']['totalBytes'],2097152);self.assertEqual(v['stderr']['totalBytes'],2097152)
 def test_timeout_partial_output_receipt_is_not_success(self):
  m=self.helper('parent-first');state=K.WaitForSingleObject(int(m.p._handle),0);self.assertEqual(state,258);r=m.finish();self.assertEqual(r['handleState'],0)
 def test_hash_source_and_evidence(self):
  p=CODE/'evidence_support.py';a=hashlib.sha256(p.read_bytes()).hexdigest();l=Ledger(self.r);l.fail('probe','synthetic');b=hashlib.sha256((self.r/'primary-failure.json').read_bytes()).hexdigest();l.fail('cleanup','synthetic');self.assertEqual(b,hashlib.sha256((self.r/'primary-failure.json').read_bytes()).hexdigest());self.assertEqual(a,hashlib.sha256(p.read_bytes()).hexdigest())
 def test_archive_new_process_keeps_primary(self):
  l=Ledger(self.r);l.fail('probe','first');later=Ledger(self.r);later.fail('archive','second');self.assertEqual(later.primary['error'],'first');self.assertEqual(len(later.secondary),1)
 def test_both_output_streams_survive_real_timeout(self):
  m=self.helper('late');state=K.WaitForSingleObject(int(m.p._handle),13600);self.assertEqual(state,258)
  self.assertGreater((self.r/'fixture-stdout.bin').stat().st_size,0);self.assertGreater((self.r/'fixture-stderr.bin').stat().st_size,0)
  l=Ledger(self.r);l.fail('deadline','intentional delayed fixture, not rare failure');v=m.finish();self.assertEqual(v['exit'],0);self.assertTrue(v['stdout']['truncated']);self.assertTrue(v['stderr']['truncated']);self.assertEqual(l.result()['status'],'FAILED')
 def test_pending_child_never_proven_by_parent_exit(self):
  t=TreeTracker();m=self.helper('orphan',t);m.finish();rows=t.snapshot();self.assertTrue(any(r['parentPid']==m.p.pid and r['signalObservedQpc'] is None for r in rows));v=t.finish(self.r);self.assertTrue(v['allExited'])
 def test_known_nonzero_stays_nonzero(self):
  t=TreeTracker();m=self.helper('nonzero',t);v=m.finish();r=t.finish(self.r);self.assertEqual(v['exit'],7);self.assertTrue(any(x['exitCode']==7 for x in r['rows']));self.assertTrue(r['allExited'])
if __name__=='__main__':unittest.main(verbosity=2)
