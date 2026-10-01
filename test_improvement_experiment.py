import threading
import unittest
from unittest.mock import patch

import improvement_experiment as experiment


class ExperimentTests(unittest.TestCase):
    def test_fixed_candidate_passes_without_applying(self):
        with patch('development.apply', side_effect=AssertionError('Deployment forbidden')):
            result = experiment.run_experiment()
        self.assertEqual(result['status'], 'READY_FOR_REVIEW')
        self.assertEqual(result['baseline']['exit_code'], 1)
        self.assertEqual(result['candidate']['exit_code'], 0)
        self.assertTrue(result['source_unchanged'])

    def test_cancelled_before_work_launches_nothing(self):
        cancel = threading.Event()
        cancel.set()
        with patch('subprocess.Popen') as launch, self.assertRaises(InterruptedError):
            experiment.run_experiment(cancel)
        launch.assert_not_called()

    def test_expired_budget(self):
        with self.assertRaises(TimeoutError):
            experiment.checkpoint(threading.Event(), 10, clock=lambda: 10)
        for seconds in (0, -1, 31, float('nan')):
            with self.assertRaises(ValueError):
                experiment.run_experiment(seconds=seconds)

    def test_failed_candidate_cannot_pass_review_gate(self):
        responses = [dict(exit_code=1, summary='3/4 checks passed'), dict(exit_code=1, summary='2/4 checks passed')]
        with patch.object(experiment, 'check_fixture', side_effect=responses):
            self.assertEqual(experiment.run_experiment()['status'], 'FAILED')

    def test_cancellation_during_child_kills_and_reaps(self):
        cancel = threading.Event()
        with patch('subprocess.Popen') as launch:
            child = launch.return_value.__enter__.return_value
            child.poll.return_value = None
            def communicate(**kwargs):
                if kwargs:
                    cancel.set()
                    raise experiment.subprocess.TimeoutExpired('fixture', .05)
                return '', ''
            child.communicate.side_effect = communicate
            with self.assertRaises(InterruptedError):
                experiment.check_fixture(experiment.Path('.'), 'wake.py', cancel, experiment.time.monotonic()+5)
            child.kill.assert_called_once()
            self.assertEqual(child.communicate.call_count, 2)
