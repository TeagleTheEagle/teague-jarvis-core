import asyncio
import unittest
from unittest.mock import patch
import repair_trial as r


class RepairTrialTests(unittest.TestCase):
    def test_evaluation_and_regression(self):
        self.assertEqual(sum(r.score(r.BEFORE)), 4)
        self.assertTrue(all(r.score('def delay(seconds):\n return max(0, seconds)\n')))
        self.assertFalse(all(r.score('def delay(seconds):\n return 0\n')))

    def test_rejects_execution_paths(self):
        expressions = ["__import__('os')", "open('x')", 'seconds.__class__', '[x for x in seconds]',
                       'max(0, seconds, 3)', 'max(0, x=seconds)', '(lambda: 0)()', '10**100000', '1e999']
        for expression in expressions:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                r.validate_candidate('def delay(seconds):\n return '+expression)
        for source in ['import os\ndef delay(seconds):\n return seconds',
                       '@print\ndef delay(seconds):\n return seconds',
                       'def delay(seconds=print(1)):\n return seconds',
                       'def delay(seconds):\n while True: pass',
                       'def delay(seconds):\n return seconds\nprint(1)']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                r.validate_candidate(source)

    def test_bounded_input(self):
        for source in ('x'*2001, 'def delay(seconds):\n return '+'max(0,'*30+'seconds'+')'*30):
            with self.assertRaises(ValueError):
                r.validate_candidate(source)

    def test_existing_client_contract_without_live_calls(self):
        class FakeCore:
            measurements = []
            async def respond(self, text, **kwargs):
                assert kwargs['conversation'].startswith('wearable-')
                return '```python\ndef delay(seconds):\n return max(0, seconds)\n```'
        with patch('development.apply', side_effect=AssertionError('No deployment')):
            report = asyncio.run(r.trial(FakeCore()))
        self.assertEqual(report['status'], 'READY_FOR_REVIEW')
        self.assertTrue(report['source_unchanged'])
        self.assertFalse(report['deployed'])
