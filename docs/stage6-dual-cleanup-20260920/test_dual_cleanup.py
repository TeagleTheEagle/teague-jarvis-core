"""Mutate copies of real independent evidence, never the original records."""
import copy,hashlib,json,pathlib,unittest
import cleanup_checker as c
ROOT=pathlib.Path(__file__).resolve().parent
FRESH=ROOT/'dual-9aa6b84f76074c83956a1cb4fad811bc'
OLD=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\991e246fb08b45a3904e4cadfa8f4e99\code\etw-stress-0ecaea118aec42c9b0afcaf56c8686d5')
HISTORY=pathlib.Path(r'C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-dual-cleanup-20260920\historical-classification.json')
def hashes(root):return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
class DualEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.original=c.load(FRESH);cls.before=hashes(FRESH)
 @classmethod
 def tearDownClass(cls):assert hashes(FRESH)==cls.before,'Tests altered original evidence'
 def setUp(self):
  self.d=copy.deepcopy(self.original)
  result=c.check(self.d);self.assertEqual(result['status'],'PASS')
  self.post=next(x for x in self.d['kernel']['rows'] if any(a['pid']==x['pid'] and a['classification']==c.KERNEL for a in result['identities']))
  self.h=self.d['handles']['rows'][0]
  self.k=next(x for x in self.d['kernel']['rows'] if (x['pid'],x['created'])==(self.h['pid'],self.h['created']))
 def bad(self):self.assertEqual(c.check(self.d)['status'],'FAIL')
 def test_01_retained_complete(self):
  r=c.check(self.d);self.assertEqual((r['total'],r['handleConfirmed'],r['kernelPostExit'],r['insufficient']),(97,91,6,0))
 def test_02_missing_application_stop(self):
  self.d['events']=[x for x in self.d['events'] if not(x['pid']==self.h['pid'] and x['kind']=='stop')];self.bad()
 def test_03_missing_kernel_exit(self):self.k['stopQpc']=0;self.bad()
 def test_04_post_exit_complete(self):self.assertEqual(c.check(self.d)['kernelPostExit'],6)
 def test_05_acquisition_begins_before_exit(self):self.post['handleAttemptBeginQpc']=self.post['stopQpc']-1;self.bad()
 def test_06_kernel_only(self):self.d['events']=[];self.bad()
 def test_07_application_only(self):self.d['kernel']['rows']=[];self.bad()
 def test_08_pid_reuse(self):
  v=copy.deepcopy(self.post);v['sequence']='999999';v['created']=str(int(v['exitFiletime'])+1);self.d['kernel']['rows'].append(v);self.bad()
 def test_09_missing_child(self):self.d['kernel']['rows'].remove(self.post);self.bad()
 def test_10_conflicting_creation(self):self.h['created']=str(int(self.h['created'])+1);self.bad()
 def test_11_already_gone_requires_complete(self):
  self.assertEqual(self.post['openError'],87);self.assertGreater(self.post['handleAttemptBeginQpc'],self.post['stopQpc']);self.assertEqual(c.check(self.d)['status'],'PASS')
  self.d['events']=[x for x in self.d['events'] if x['pid']!=self.post['pid']];self.bad()
 def test_12_primary_failure_preserved(self):
  self.d['producer'].update(status='FAILED',primary_failure='HARD_DEADLINE: preserved')
  r=c.check(self.d);self.assertEqual(r['status'],'PASS');self.assertEqual(r['primaryFailure'],'HARD_DEADLINE: preserved');self.assertEqual(r['producerStatus'],'FAILED');self.assertFalse(r['acceptance'])
 def test_13_external_eventidentifier_collisions(self):
  for x in self.d['events']:x['eventIdentifier']=7
  r=c.check(self.d);self.assertEqual(r['status'],'PASS');self.assertEqual(r['externalEventIdentifierCollisions'],len(self.d['events'])-1)
 def test_14_historical_kernel_only_not_upgraded(self):
  before=hashes(OLD);self.assertFalse((OLD/'app-events.jsonl').exists());self.assertEqual(c.evaluate(OLD)['status'],'FAIL');self.assertEqual(hashes(OLD),before)
 def test_15_historical_87_unknown(self):
  h=json.loads(HISTORY.read_text());self.assertEqual(h['historical87'],'UNKNOWN');self.assertFalse(h['eligibleForDualEvidence']);self.assertEqual(h['APPLICATION_START_STOP_EVIDENCE'],'NOT CAPTURED')
 def test_16_bound_image_query_loss_preserved(self):
  self.assertEqual(len(self.d['handles']['errors']),2);self.assertEqual(c.check(self.d)['status'],'PASS')
 def test_17_unbound_image_error(self):self.d['handles']['errors']=[];self.bad()
 def test_18_generic_handle_error(self):self.d['handles']['errors'].append(dict(stage='open',pid=123,error='Access denied'));self.bad()
 def test_19_known_image_conflict(self):self.h['image']='D:\\unrelated.exe';self.bad()
 def test_20_access_denied_is_not_gone(self):self.post['openError']=5;self.bad()
 def test_21_equal_acquisition_and_exit(self):self.post['handleAttemptBeginQpc']=self.post['stopQpc'];self.bad()
 def test_22_callback_missing(self):self.d['tap'].pop();self.bad()
 def test_23_persistence_receipt_missing(self):self.d['receipts'].pop();self.bad()
 def test_24_queue_residue(self):self.d['app']['queue']['remaining']=1;self.bad()
 def test_25_kernel_loss(self):self.d['kernel']['eventsLost']=1;self.bad()
 def test_26_heartbeat_at_threshold(self):self.d['heartbeat'][0]['interval']=10;self.bad()
 def test_27_observer_still_live(self):self.d['appExit']['exited']=False;self.bad()
 def test_28_unsignaled_handle(self):self.h['signalObservedQpc']=0;self.bad()
 def test_29_unclosed_handle(self):self.h['closed']=False;self.bad()
 def test_30_kernel_sequence_collision(self):self.d['kernel']['rows'].append(copy.deepcopy(self.post));self.bad()
 def test_31_application_queue_id_collision(self):self.d['events'][1]['queueSequence']=self.d['events'][0]['queueSequence'];self.bad()
 def test_32_wrong_parent(self):self.k['parentPid']+=1;self.bad()
 def test_33_missing_app_start(self):self.d['events']=[x for x in self.d['events'] if not(x['pid']==self.post['pid'] and x['kind']=='start')];self.bad()
 def test_34_handle_creation_conflict(self):self.h['startFiletime']='1';self.bad()
 def test_35_image_error_other_identity(self):self.d['handles']['errors'][0]['created']='1';self.bad()
 def test_36_no_instrumented_child_finish(self):self.d['internal'][0].pop();self.bad()
 def test_37_primary_failure_no_laundering_on_cleanup_failure(self):
  self.d['producer'].update(status='FAILED',primary_failure='original');self.post['stopQpc']=0
  r=c.check(self.d);self.assertEqual(r['status'],'FAIL');self.assertEqual(r['primaryFailure'],'original')
 def test_38_retained_exit_code_conflict(self):self.h['exitCode']=99;self.bad()
 def test_39_durable_finalization_failed(self):self.d['app']['durableFinalization']=False;self.bad()
 def test_40_unknown_image_no_error(self):self.h['image']='UNKNOWN';self.bad()
if __name__=='__main__':unittest.main(verbosity=2)
