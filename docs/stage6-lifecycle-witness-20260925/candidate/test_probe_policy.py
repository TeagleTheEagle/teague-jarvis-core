import unittest,json,shutil,copy
from probe_policy import wait_tracked,validate_lifecycle,ProbeFailure,HardDeadline
from test_finalization import fixture
from finalize import finalize,accepted

class ClockProbe:
 def __init__(self,exit_at,initial=0):self.now=initial;self.exit_at=exit_at;self.warnings=[];self.checks=[];self.failure=None
 def health(self):
  self.checks.append(self.now)
  if self.failure in ('heartbeat','subscriber','queue') and self.now>=2:raise RuntimeError(self.failure)
 def identity(self):
  if self.failure=='identity' and self.now>=2:raise RuntimeError('identity')
 def wait(self,ms):
  if self.failure=='handle' and self.now>=2:return 0xffffffff
  if ms:self.now=min(self.now+ms/1000,self.exit_at) if self.exit_at>self.now else self.now
  return 0 if self.now>=self.exit_at else 258
 def run(self,campaign=175):return wait_tracked(clock=lambda:self.now,origin=0,campaign_deadline=campaign,wait=self.wait,identity=self.identity,health=self.health,warning=self.warnings.append,exit_elapsed=lambda:self.exit_at)

def completed(seconds=6):
 c=ClockProbe(seconds);policy=c.run()
 row=dict(pid=1,policy=policy,finalKernelTimes=['100','200','0','0'],actualExitCode=0,finalHandleState=0,timedOut=False,hardDeadlineFailure=False)
 events=[dict(pid=1,kind=k) for k in ('start','stop')];handles=[dict(pid=1,times=['100','200','0','0'],exit=0)]
 return [row],events,handles

class ProbePolicyTests(unittest.TestCase):
 def test_exit_4_9_normal(self):
  c=ClockProbe(4.9);r=c.run();self.assertFalse(r['warning']);self.assertFalse(c.warnings)
 def test_exit_just_over_five_warns(self):
  c=ClockProbe(5.0001);r=c.run();self.assertTrue(r['warning']);self.assertEqual(len(c.warnings),1)
 def test_exit_six_warns_and_health_continues(self):
  c=ClockProbe(6);r=c.run();self.assertTrue(r['warning']);self.assertTrue(any(x>5 for x in c.checks));self.assertLessEqual(max(b-a for a,b in zip(c.checks,c.checks[1:])),.051)
 def test_exit_below_deadline(self):
  self.assertEqual(ClockProbe(13.599).run()['status'],'ELIGIBLE_PENDING_LIFECYCLE')
 def test_exact_deadline_fails(self):
  with self.assertRaises(HardDeadline):ClockProbe(13.6).run()
 def test_exceeded_deadline_fails(self):
  with self.assertRaises(HardDeadline):ClockProbe(14).run()
 def test_never_exits_fails_bounded(self):
  c=ClockProbe(float('inf'))
  with self.assertRaises(HardDeadline):c.run()
  self.assertLess(c.now,13.602)
 def test_creation_delay_included(self):
  with self.assertRaises(HardDeadline):ClockProbe(4.9,initial=13.7).run()
 def test_campaign_deadline_not_extended(self):
  with self.assertRaises(HardDeadline):ClockProbe(6).run(campaign=5.5)
 def test_heartbeat_fails_before_exit(self):
  c=ClockProbe(6);c.failure='heartbeat'
  with self.assertRaisesRegex(RuntimeError,'heartbeat'):c.run()
 def test_subscriber_failure(self):
  c=ClockProbe(6);c.failure='subscriber'
  with self.assertRaisesRegex(RuntimeError,'subscriber'):c.run()
 def test_queue_failure(self):
  c=ClockProbe(6);c.failure='queue'
  with self.assertRaisesRegex(RuntimeError,'queue'):c.run()
 def test_identity_loss(self):
  c=ClockProbe(6);c.failure='identity'
  with self.assertRaisesRegex(RuntimeError,'identity'):c.run()
 def test_handle_failure(self):
  c=ClockProbe(6);c.failure='handle'
  with self.assertRaisesRegex(ProbeFailure,'handle'):c.run()
 def test_warning_write_failure(self):
  c=ClockProbe(6)
  def fail(v):raise OSError('warning persistence')
  with self.assertRaises(OSError):wait_tracked(clock=lambda:c.now,origin=0,campaign_deadline=175,wait=c.wait,identity=c.identity,health=c.health,warning=fail,exit_elapsed=lambda:6)
 def test_warning_keeps_full_reconciliation(self):validate_lifecycle(*completed())
 def test_missing_start(self):
  rows,events,handles=completed()
  with self.assertRaises(ProbeFailure):validate_lifecycle(rows,events[1:],handles)
 def test_missing_stop(self):
  rows,events,handles=completed()
  with self.assertRaises(ProbeFailure):validate_lifecycle(rows,events[:1],handles)
 def test_orphan(self):
  rows,events,handles=completed();rows[0]['finalHandleState']=258
  with self.assertRaises(ProbeFailure):validate_lifecycle(rows,events,handles)
 def test_cleanup_failure(self):
  rows,events,handles=completed();handles[0]['exit']=17
  with self.assertRaises(ProbeFailure):validate_lifecycle(rows,events,handles)
 def test_identity_changed(self):
  rows,events,handles=completed();handles[0]['times'][0]='101'
  with self.assertRaises(ProbeFailure):validate_lifecycle(rows,events,handles)
 def test_duplicate_pid(self):
  rows,events,handles=completed()
  with self.assertRaises(ProbeFailure):validate_lifecycle(rows*2,events*2,handles*2)
 def test_warning_does_not_override_finalization_failure(self):
  validate_lifecycle(*completed());root=fixture()
  (root/'monitor-exit.json').write_text(json.dumps(dict(exit_code=1,identity=json.loads((root/'ready.json').read_text()))))
  with self.assertRaises(RuntimeError):finalize(root)
  self.assertFalse(accepted(root,1))
 def test_warning_does_not_override_durable_flush_failure(self):
  validate_lifecycle(*completed());root=fixture()
  def fail(p):raise OSError('durable flush')
  with self.assertRaises(OSError):finalize(root,sync=fail)
  self.assertFalse(accepted(root,1))
 def test_warning_does_not_override_archive_hash_failure(self):
  validate_lifecycle(*completed());root=fixture()
  def corrupt(a,b):shutil.copyfile(a,b);b.write_bytes(b'corrupt')
  with self.assertRaises(RuntimeError):finalize(root,copy=corrupt)
  self.assertFalse(accepted(root,1))
 def test_warning_does_not_override_archive_copy_failure(self):
  validate_lifecycle(*completed());root=fixture()
  def fail(a,b):raise OSError('archive denied')
  with self.assertRaises(OSError):finalize(root,copy=fail)
  self.assertFalse(accepted(root,1))
