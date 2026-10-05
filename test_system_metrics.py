"""The Command dashboard's PC readings are measured, bounded and honest about what they cover. Offline."""
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import system_metrics


class SystemMetricsTests(unittest.TestCase):
    def setUp(self):
        system_metrics._previous = None

    def test_processor_share_comes_from_two_readings(self):
        readings = iter([(100, 300, 100), (150, 450, 150)])  # idle +50 of kernel+user +200: 75% busy
        with patch.object(system_metrics, '_system_times', side_effect=lambda: next(readings)):
            self.assertIsNone(system_metrics.cpu_percent())  # nothing to compare with yet
            self.assertEqual(system_metrics.cpu_percent(), 75.0)

    def test_unreadable_or_unchanged_times_give_none_not_a_guess(self):
        with patch.object(system_metrics, '_system_times', return_value=None):
            self.assertIsNone(system_metrics.cpu_percent())
            self.assertIsNone(system_metrics.cpu_percent())
        readings = iter([(1, 2, 3), (1, 2, 3)])
        with patch.object(system_metrics, '_system_times', side_effect=lambda: next(readings)):
            system_metrics.cpu_percent()
            self.assertIsNone(system_metrics.cpu_percent())

    def test_snapshot_reports_scope_and_last_completed_response(self):
        timings = [{'elapsed_ms': 900, 'cancelled': False}, {'elapsed_ms': 7237, 'cancelled': False}, {'elapsed_ms': 50, 'cancelled': True}]
        with tempfile.TemporaryDirectory() as folder:
            result = system_metrics.snapshot(folder, time.time() - 65, timings)
        self.assertEqual(result['last_response_ms'], 7237)
        self.assertEqual(result['responses_measured'], 2)
        self.assertGreaterEqual(result['core_uptime_seconds'], 65)
        self.assertIn('not measured', result['scope'])
        self.assertIsNotNone(result['disk'])
        self.assertTrue(0 <= result['disk']['used_percent'] <= 100)
        self.assertIsNone(system_metrics.snapshot(folder, time.time(), [])['last_response_ms'])

    @unittest.skipUnless(sys.platform == 'win32', 'Windows readings')
    def test_real_windows_readings_are_in_range(self):
        system_metrics.cpu_percent()
        time.sleep(0.2)
        cpu = system_metrics.cpu_percent()
        self.assertTrue(cpu is None or 0 <= cpu <= 100)
        memory = system_metrics.memory()
        self.assertTrue(0 <= memory['used_percent'] <= 100)
        self.assertGreater(memory['total_bytes'], memory['available_bytes'])


if __name__ == '__main__':
    unittest.main()
