import threading
import unittest
from unittest.mock import patch
import repair_sandbox as r


class SandboxTests(unittest.TestCase):
    def test_rejects_general_code_before_runtime(self):
        with patch.object(r, '_execute_probe', side_effect=AssertionError('must not run')):
            for code in ('import os', 'def delay(seconds):\n return open("x")',
                         'def delay(seconds):\n while True: pass'):
                with self.subTest(code=code), self.assertRaises(ValueError):
                    r.check_candidate(code)

    def test_runtime_output_cannot_override_independent_result(self):
        result = dict(status='EXITED', exit_code=0, cleanup=True,
                      output='[0,0,2,0.5,0,100]')
        with patch.object(r, '_execute_probe', return_value=result):
            self.assertEqual(r.check_candidate('def delay(seconds):\n return 0\n')['status'], 'NOT_ACCEPTED')
            self.assertEqual(r.check_candidate('def delay(seconds):\n return max(0, seconds)\n')['status'], 'READY_FOR_REVIEW')

    def test_malformed_failed_and_truncated_output_rejected(self):
        for output, code, status in [('[]', 0, 'EXITED'), ('true', 0, 'EXITED'),
                                     ('[0,0,2,0.5,0,100]', 1, 'EXITED'),
                                     ('[0,0,2,0.5,0,100]', 0, 'OUTPUT_LIMIT')]:
            with patch.object(r, '_execute_probe', return_value=dict(
                    status=status, exit_code=code, output=output, cleanup=True)):
                self.assertEqual(r.check_candidate('def delay(seconds):\n return max(0,seconds)\n')['status'], 'NOT_ACCEPTED')

    def test_cancel_before_start_and_invalid_budgets(self):
        stop = threading.Event()
        stop.set()
        with patch.object(r, 'preflight', side_effect=AssertionError('must not start')):
            self.assertEqual(r._execute_probe('pass', stop)['status'], 'CANCELLED')
            for budget in (0, -1, 16, True, float('nan')):
                with self.assertRaises(ValueError):
                    r._execute_probe('pass', seconds=budget)

    def test_environment_does_not_forward_secrets(self):
        with patch.dict(r.os.environ, {'OPENROUTER_API_KEY': 'fake', 'WSLENV': 'OPENROUTER_API_KEY',
                                      'HTTP_PROXY': 'fake'}):
            self.assertNotIn('OPENROUTER_API_KEY', r.environment())
            self.assertNotIn('WSLENV', r.environment())
            self.assertNotIn('HTTP_PROXY', r.environment())
