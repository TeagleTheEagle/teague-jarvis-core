import asyncio
import json
import threading
import unittest
from unittest.mock import patch
import repair_workflow as r

GOOD = 'def delay(seconds):\n return max(0, seconds)\n'


class CoreFixture:
    def __init__(self, answer=None):
        self.calls = 0
        self.answer = answer or json.dumps({'diagnosis':'Negative values pass through.', 'candidate':GOOD})

    async def respond(self, text, conversation):
        self.calls += 1
        assert conversation.startswith('wearable-')
        assert 'Observed failures:' in text
        return self.answer


def checker(source, cancel):
    if source == r.BEFORE:
        return dict(execution_status='EXITED', exit_code=0, cleanup=True,
                    runtime_values=[x for x, _ in r.CASES], status='NOT_ACCEPTED')
    return dict(status='READY_FOR_REVIEW', cleanup=True)


class WorkflowTests(unittest.TestCase):
    def test_one_core_one_request_no_deployment(self):
        core = CoreFixture()
        with patch('development.apply', side_effect=AssertionError('No deployment')):
            report = asyncio.run(r.run(core, checker=checker))
        self.assertEqual(report['status'], 'READY_FOR_REVIEW')
        self.assertEqual(core.calls, 1)
        self.assertEqual(report['resources']['container_checks'], 2)
        self.assertEqual(len(report['observed_failures']), 2)
        self.assertFalse(report['deployed'])

    def test_bad_baseline_never_calls_core(self):
        core = CoreFixture()
        report = asyncio.run(r.run(core, checker=lambda *_: {}))
        self.assertEqual(report['status'], 'FAILED')
        self.assertEqual(core.calls, 0)

    def test_invalid_generated_code_never_reaches_second_container(self):
        core = CoreFixture(json.dumps({'diagnosis':'bad', 'candidate':'import os'}))
        report = asyncio.run(r.run(core, checker=checker))
        self.assertEqual(report['status'], 'FAILED')
        self.assertEqual(report['resources']['container_checks'], 1)

    def test_failed_verification_cannot_be_approved(self):
        report = asyncio.run(r.run(CoreFixture(), checker=lambda source, stop:
                                   checker(source, stop) if source == r.BEFORE else {'status':'FAILED'}))
        self.assertEqual(report['status'], 'REJECTED')

    def test_precancel_no_work(self):
        stop = threading.Event()
        stop.set()
        core = CoreFixture()
        report = asyncio.run(r.run(core, stop, checker))
        self.assertEqual(report['status'], 'CANCELLED')
        self.assertEqual(core.calls, 0)
        self.assertEqual(report['resources']['container_checks'], 0)

    def test_provider_failure_no_retry_no_raw_error(self):
        class Failing(CoreFixture):
            async def respond(self, *args, **kwargs):
                self.calls += 1
                raise RuntimeError('secret-like-text')
        core = Failing()
        report = asyncio.run(r.run(core, checker=checker))
        self.assertEqual(report['status'], 'FAILED')
        self.assertEqual(core.calls, 1)
        self.assertNotIn('secret-like-text', json.dumps(report))

    def test_cancellation_reaches_provider(self):
        stop = threading.Event()
        class Waiting(CoreFixture):
            cancelled = False
            async def respond(self, *args, **kwargs):
                stop.set()
                try:
                    await asyncio.sleep(60)
                finally:
                    self.cancelled = True
        core = Waiting()
        report = asyncio.run(r.run(core, stop, checker))
        self.assertEqual(report['status'], 'CANCELLED')
        self.assertTrue(core.cancelled)

    def test_schema_and_budget_rejection(self):
        for text in ('[]', '{}', 'x'*5001, json.dumps({'diagnosis':'x','candidate':GOOD,'execute':True})):
            with self.assertRaises(ValueError):
                r.parse_answer(text)
        for seconds in (False, 0, 181, float('nan')):
            with self.assertRaises(ValueError):
                asyncio.run(r.run(CoreFixture(), seconds=seconds))
