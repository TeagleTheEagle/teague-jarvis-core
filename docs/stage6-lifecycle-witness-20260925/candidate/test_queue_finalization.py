"""Fail-closed acceptance regressions using disposable evidence fixtures."""
import json,unittest
from test_finalization import fixture
from finalize import finalize,accepted
class QueueFinalization(unittest.TestCase):
 def test_residue_blocks_acceptance(self):
  r=fixture();(r/'queue-state.json').write_text(json.dumps(dict(enqueued=2,selected=1,persisted=1,removed=1,remaining=1,failed=False)))
  with self.assertRaisesRegex(RuntimeError,'Queue reconciliation'):finalize(r)
  self.assertFalse(accepted(r,1))
 def test_write_failure_latch_blocks_acceptance(self):
  r=fixture();(r/'queue-state.json').write_text(json.dumps(dict(enqueued=2,selected=2,persisted=2,removed=2,remaining=0,failed=True)))
  with self.assertRaisesRegex(RuntimeError,'Queue reconciliation'):finalize(r)
  self.assertFalse(accepted(r,1))
 def test_late_queue_failure_blocks_acceptance(self):
  r=fixture();(r/'queue-failure.json').write_text(json.dumps({'error':'late enqueue during teardown'}))
  with self.assertRaisesRegex(RuntimeError,'Preserved failure'):finalize(r)
  self.assertFalse(accepted(r,1))
 def test_malformed_event_blocks_acceptance(self):
  r=fixture();(r/'events.jsonl').write_text('{"broken":\n')
  with self.assertRaises(ValueError):finalize(r)
  self.assertFalse(accepted(r,1))
 def test_identity_ambiguity_blocks_acceptance(self):
  r=fixture();v=json.loads((r/'monitor-exit.json').read_text());v['identity']['created']='wrong';(r/'monitor-exit.json').write_text(json.dumps(v))
  with self.assertRaisesRegex(RuntimeError,'identity invalid'):finalize(r)
  self.assertFalse(accepted(r,1))
 def test_queue_mismatch_despite_matching_event_totals(self):
  r=fixture();(r/'queue-state.json').write_text(json.dumps(dict(enqueued=3,selected=2,persisted=2,removed=2,remaining=0,failed=False)))
  with self.assertRaisesRegex(RuntimeError,'Queue reconciliation'):finalize(r)
  self.assertFalse(accepted(r,1))
if __name__=='__main__':unittest.main(verbosity=2)
