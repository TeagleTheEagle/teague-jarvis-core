"""Acceptance rejection tests only; no changes to monitor/finalizer behavior."""
import json
import unittest
from test_finalization import fixture
from finalize import finalize, accepted

class EventRejection(unittest.TestCase):
    def test_duplicate_pid_is_rejected(self):
        root=fixture()
        (root/'probes.json').write_text(json.dumps([{'pid':444,'exit':0},{'pid':444,'exit':0}]))
        with self.assertRaisesRegex(RuntimeError, 'Ambiguous probe PID reuse'):
            finalize(root)
        self.assertFalse(accepted(root, 1))

    def test_missing_stop_is_not_accepted_despite_healthy_heartbeat(self):
        root=fixture()
        (root/'events.jsonl').write_text(json.dumps({'pid':444,'kind':'start','name':'J6Probe.exe'})+'\n')
        result=json.loads((root/'monitor-result.json').read_text())
        result['events']=1
        (root/'monitor-result.json').write_text(json.dumps(result))
        with self.assertRaisesRegex(RuntimeError, 'Event count mismatch'):
            finalize(root)
        self.assertFalse(accepted(root, 1))

    def test_wrong_pid_events_are_rejected_even_when_totals_match(self):
        root=fixture()
        (root/'events.jsonl').write_text(''.join(json.dumps({'pid':555,'kind':k,'name':'J6Probe.exe'})+'\n' for k in ('start','stop')))
        with self.assertRaisesRegex(RuntimeError, 'Probe event mismatch'):
            finalize(root)
        self.assertFalse(accepted(root, 1))
