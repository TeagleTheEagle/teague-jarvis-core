"""Offline regression tests; never import server/actions or start the application.

Extract their actual AST definitions to avoid credential loading and unrelated
runtime initialization. Providers use stubs; Store uses disposable SQLite only.
"""
import ast
import contextlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import Mock, patch
import uuid

import providers
from store import Store

ROOT = Path(__file__).resolve().parent


def definitions(filename, names, namespace):
    tree = ast.parse((ROOT / filename).read_text(encoding='utf-8-sig'))
    selected = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names:
            selected.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            selected.append(node)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(ROOT / filename), 'exec'), namespace)
    return namespace


def app_fixture():
    ns = definitions('server.py', {'Run', 'App', 'WEARABLE_READ_TOOLS'}, dict(
        ROOT=ROOT, threading=threading, time=time, uuid=uuid, re=re,
        providers=providers, companion_tools=types.SimpleNamespace(stamp=lambda: {'at': 0}),
    ))
    app = ns['App'].__new__(ns['App'])
    app.stage4 = None
    app.lock = threading.RLock()
    app.runs = {}
    app.attachments = {}
    app.devices = Mock()
    app.timings = []
    app.store = Mock()
    return ns, app


class AdmissionTests(unittest.TestCase):
    def test_concurrent_admission_has_only_one_worker(self):
        ns, app = app_fixture()
        barrier = threading.Barrier(3)
        release = threading.Event(); finished = threading.Event()
        outcomes = []
        def work(run, text, attachment):
            try:
                release.wait(5)
            finally:
                with run.condition:
                    run.done = True
                    run.condition.notify_all()
                app.devices.finish(run.id)
                finished.set()
        app.work = work
        def submit():
            barrier.wait(5)
            try: outcomes.append(app.start_run({'text': 'hello', 'conversation': 'audit'}))
            except ValueError: outcomes.append('busy')
        submitters = [threading.Thread(target=submit) for _ in range(2)]
        try:
            for thread in submitters: thread.start()
            barrier.wait(5)
            for thread in submitters: thread.join(5)
            self.assertEqual(outcomes.count('busy'), 1)
            self.assertEqual(sum(isinstance(value, dict) for value in outcomes), 1)
            self.assertEqual(len(app.runs), 1)
        finally:
            release.set()
            for thread in submitters: thread.join(5)
            self.assertTrue(finished.wait(5))

    def test_bad_attachment_does_not_reserve_run(self):
        ns, app = app_fixture()
        for attachment in ({'bad': 'type'}, ['bad'], 42, True):
            with self.subTest(attachment=attachment):
                with self.assertRaises(ValueError):
                    app.start_run({'text': 'hello', 'conversation': 'audit', 'attachment': attachment})
                self.assertEqual(app.runs, {})
        with patch.object(threading, 'Thread'):
            self.assertIn('run_id', app.start_run({'text': 'hello', 'conversation': 'audit'}))

    def test_thread_start_failure_releases_admission(self):
        ns, app = app_fixture()
        with patch.object(threading, 'Thread') as thread:
            thread.return_value.start.side_effect = RuntimeError('synthetic start failure')
            with self.assertRaises(RuntimeError):
                app.start_run({'text': 'hello', 'conversation': 'audit'})
        self.assertEqual(app.runs, {})
        app.devices.finish.assert_called_once()

    def test_initial_store_failure_finishes_run(self):
        ns, app = app_fixture()
        run = ns['Run']('audit')
        app.runs[run.id] = run
        app.store.message.side_effect = OSError('synthetic write failure')
        app.work(run, 'hello', None)
        self.assertTrue(run.done)
        self.assertTrue(any(e['event'] == 'run.failed' for e in run.events))
        app.devices.finish.assert_called_once_with(run.id)
        with patch.object(threading, 'Thread'):
            self.assertIn('run_id', app.start_run({'text': 'next', 'conversation': 'audit'}))

    def test_telemetry_failure_still_finishes_run(self):
        ns, app = app_fixture()
        run = ns['Run']('audit')
        app.store.message.side_effect = OSError('synthetic write failure')
        ns['companion_tools'].stamp = Mock(side_effect=RuntimeError('telemetry failure'))
        with contextlib.suppress(RuntimeError):
            app.work(run, 'hello', None)
        self.assertTrue(run.done)
        app.devices.finish.assert_called_once_with(run.id)

    def test_failed_database_audit_still_notifies(self):
        ns, app = app_fixture()
        run = ns['Run']('audit')
        app.store.message.side_effect = OSError('synthetic write failure')
        app.store.audit.side_effect = OSError('same failed database')
        app.work(run, 'hello', None)
        self.assertTrue(run.done)
        self.assertIn('run.failed', [e['event'] for e in run.events])

    def test_attachment_consumption_and_failed_start_restore(self):
        ns, app = app_fixture()
        attachment = {'name': 'screen-capture.jpg', 'type': 'image', 'data': 'synthetic'}
        app.attachments['capture'] = attachment
        body = {'text': 'inspect', 'conversation': 'audit', 'attachment': 'capture'}
        with patch.object(threading, 'Thread') as thread:
            thread.return_value.start.side_effect = RuntimeError('synthetic')
            with self.assertRaises(RuntimeError): app.start_run(body)
        self.assertIs(app.attachments['capture'], attachment)
        with patch.object(threading, 'Thread') as thread:
            app.start_run(body)
            self.assertIs(thread.call_args.kwargs['args'][2], attachment)
        self.assertNotIn('capture', app.attachments)
        with self.assertRaises(ValueError): app.start_run(body)


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        ns = definitions('actions.py', {'_MATH', '_bounded_arithmetic', 'calculate'},
                         dict(ast=ast, math=math, re=re, statistics=statistics))
        self.calculate = ns['calculate']

    def test_compatible_arithmetic(self):
        for expression, expected in [('2+3*4', 14), ('-2**2', -4), ('2**-3', .125),
                ('sqrt(81)+abs(-3)', 12), ('round(pi, 3)', 3.142), ('5%2', 1),
                ('round(1234, -2)', 1200), ('10**100', 10**100)]:
            with self.subTest(expression=expression):
                self.assertEqual(self.calculate(expression, 'arithmetic')['result'], expected)

    def test_limits_and_numeric_only(self):
        # These baseline expressions are deliberately small and safe to execute.
        for expression in ('10**101', '1e101', 'True+1', '2**1001', "'x'*8", 'sqrt(-1)', '1/0'):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                self.calculate(expression, 'arithmetic')

    def test_never_uses_eval(self):
        with patch('builtins.eval', side_effect=AssertionError('eval must not execute')):
            self.assertEqual(self.calculate('2+3', 'arithmetic')['result'], 5)

    def test_other_modes(self):
        self.assertEqual(self.calculate('15% of 240', 'percent')['result'], 36)
        self.assertEqual(self.calculate('10 km to m', 'convert')['result'], 10000)
        self.assertEqual(self.calculate('1 2 3', 'statistics')['mean'], 2)

    def test_invalid_grammar_and_function_arguments(self):
        for expression in ('(', '[1]', 'pi.real', 'abs(1,2)', 'round(1,1.5)', 'round(1,1001)',
                           'sqrt(x=1)', '__import__("os")', '1j', '2<<3', 'sum(1)', '1e309'):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                self.calculate(expression, 'arithmetic')

    def test_depth_and_node_limits(self):
        for expression in ('-' * 40 + '1', '+'.join(['1'] * 100)):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                self.calculate(expression, 'arithmetic')


class StatisticsTests(unittest.TestCase):
    def setUp(self):
        ns = definitions('actions.py', {'_MATH', '_bounded_arithmetic', 'calculate'},
                         dict(ast=ast, math=math, re=re, statistics=statistics))
        self.calculate = ns['calculate']

    def finite_result(self, expression):
        result = self.calculate(expression, 'statistics')
        self.assertEqual(set(result), {'count', 'mean', 'median', 'minimum', 'maximum', 'stdev'})
        for field, value in result.items():
            with self.subTest(field=field):
                self.assertIsInstance(value, (int, float))
                self.assertNotIsInstance(value, bool)
                self.assertTrue(math.isfinite(value), (field, value))
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        return result

    def reject(self, expression):
        with self.assertRaises(ValueError):
            self.calculate(expression, 'statistics')

    def test_nan(self):
        self.reject('nan')

    def test_capital_nan(self):
        self.reject('NaN')

    def test_positive_infinity(self):
        self.reject('inf')

    def test_negative_infinity(self):
        self.reject('-inf')

    def test_decimal_exponent_overflow(self):
        self.reject('1e309')

    def test_other_nonfinite_spellings(self):
        for text in ('NAN', '+nan', '-NaN', 'Infinity', '+INF', '-Infinity', '-1e309'):
            with self.subTest(expression=text):
                self.reject(text)

    def test_mixed_finite_and_nonfinite(self):
        for text in ('1 nan 2', 'nan 1 2', '1 2 nan', '1 NaN 2', 'inf 1 2',
                     '1 -inf 2', '1 1e309 2', 'inf -inf', 'nan nan'):
            with self.subTest(expression=text):
                self.reject(text)

    def test_single_value(self):
        self.assertEqual(self.finite_result('42'),
                         dict(count=1, mean=42, median=42, minimum=42, maximum=42, stdev=0))

    def test_negative_values(self):
        self.assertEqual(self.finite_result('-3 -2 -1'),
                         dict(count=3, mean=-2, median=-2, minimum=-3, maximum=-1, stdev=1))

    def test_decimals(self):
        result = self.finite_result('0.5 1.5')
        self.assertEqual(result, dict(count=2, mean=1, median=1, minimum=0.5,
                                     maximum=1.5, stdev=math.sqrt(0.5)))

    def test_ordinary_sample_statistics(self):
        self.assertEqual(self.finite_result('1 2 3'),
                         dict(count=3, mean=2, median=2, minimum=1, maximum=3, stdev=1))

    def test_even_median_and_sample_stdev(self):
        self.assertEqual(self.finite_result('4 1 3 2'),
                         dict(count=4, mean=2.5, median=2.5, minimum=1, maximum=4,
                              stdev=math.sqrt(5/3)))

    def test_delimiters_and_repeated_values(self):
        self.assertEqual(self.finite_result(' 2, 2\t2\n2 '),
                         dict(count=4, mean=2, median=2, minimum=2, maximum=2, stdev=0))

    def test_proposed_cap_exact_boundaries(self):
        # The optional DeepSeek cap is not an existing statistics requirement.
        for value in (1e100, -1e100):
            with self.subTest(value=value):
                self.assertEqual(self.finite_result(repr(value))['mean'], value)
        result = self.finite_result('-1e100 1e100')
        self.assertAlmostEqual(result['stdev'] / 1e100, math.sqrt(2))

    def test_proposed_cap_adjacent_floats_remain_valid(self):
        for boundary in (1e100, -1e100):
            for direction in (-math.inf, math.inf):
                value = math.nextafter(boundary, direction)
                with self.subTest(value=value):
                    self.assertEqual(self.finite_result(repr(value))['mean'], value)

    def test_large_finite_values_without_arbitrary_cap(self):
        for text in ('1e101', '-1e101', '1e200', '1e308', '-1e308'):
            with self.subTest(expression=text):
                self.assertEqual(self.finite_result(text)['mean'], float(text))
        result = self.finite_result('-1e200 1e200')
        self.assertAlmostEqual(result['stdev'] / 1e200, math.sqrt(2))

    def test_unrepresentable_finite_calculations_rejected(self):
        for text in ('1e308 1e308', '-1e308 -1e308',
                     '-1.7976931348623157e308 1.7976931348623157e308'):
            with self.subTest(expression=text):
                self.reject(text)

    def test_no_nonfinite_output_can_escape(self):
        # Finite input is not sufficient: also enforce the output/serialization invariant.
        for function, value in (('fmean', math.inf), ('median', math.nan), ('stdev', math.inf)):
            with self.subTest(function=function), patch.object(statistics, function, return_value=value):
                self.reject('1 2 3')

    def test_input_shape_limits_preserved(self):
        for text in ('', '   ', ',', 'not-a-number', '1 2 bad', '1 ' * 251):
            with self.subTest(expression=text):
                self.reject(text)


class ProviderCancellationTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'JARVIS_PROVIDER': 'openai', 'OPENAI_API_KEY': 'synthetic', 'OPENAI_MODEL': 'fixture'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_cancelled_request_not_sent(self):
        cancel = threading.Event(); cancel.set()
        with patch.object(providers, 'request') as request:
            self.assertIsNone(providers.chat([], [], Mock(), cancel))
        request.assert_not_called()

    def test_cancel_during_failure_does_not_retry(self):
        cancel = threading.Event()
        def fail(*args, **kwargs):
            cancel.set()
            raise providers.ProviderError('Connection failed')
        with patch.object(providers, 'request', side_effect=fail) as request, patch.object(providers.time, 'sleep'):
            self.assertIsNone(providers.chat([], [], Mock(), cancel))
        self.assertEqual(request.call_count, 1)

    def test_cancelled_success_never_emitted(self):
        for model in ('fixture', 'gpt-6-fixture'):
            with self.subTest(model=model), patch.dict(os.environ, {'OPENAI_MODEL': model}):
                cancel = threading.Event(); emit = Mock()
                def result(*args, **kwargs):
                    cancel.set()
                    return {'choices': [{'message': {'content': 'late'}}], 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'late'}]}]}
                with patch.object(providers, 'request', side_effect=result):
                    self.assertIsNone(providers.chat([], [], emit, cancel))
                emit.assert_not_called()

    def test_cancel_in_backoff_does_not_retry(self):
        cancel = threading.Event()
        def stop(timeout): cancel.set(); return True
        with patch.object(cancel, 'wait', side_effect=stop), patch.object(providers, 'request', side_effect=providers.ProviderError('Connection failed')) as request:
            self.assertIsNone(providers.chat([], [], Mock(), cancel))
        self.assertEqual(request.call_count, 1)

    def test_retry_uses_remaining_budget(self):
        cancel = threading.Event()
        result = {'choices': [{'message': {'content': 'ok'}, 'finish_reason': 'stop'}]}
        with patch.object(cancel, 'wait', return_value=False), patch.object(providers.time, 'monotonic', side_effect=[0, 0, 50, 53]), patch.object(providers, 'request', side_effect=[providers.ProviderError('Connection failed'), result]) as request:
            self.assertEqual(providers.chat([], [], Mock(), cancel)['content'], 'ok')
        self.assertEqual([c.kwargs['timeout'] for c in request.call_args_list], [120, 67])

    def test_expired_budget_never_retries(self):
        cancel = threading.Event()
        with patch.object(providers.time, 'monotonic', side_effect=[0, 0, 121]), patch.object(providers, 'request', side_effect=providers.ProviderError('Connection failed')) as request:
            with self.assertRaises(providers.ProviderError): providers.chat([], [], Mock(), cancel)
        self.assertEqual(request.call_count, 1)

    def test_nonretryable_error_preserved(self):
        with patch.object(providers, 'request', side_effect=providers.ProviderError('HTTP 429')) as request:
            with self.assertRaises(providers.ProviderError) as caught:
                providers.chat([], [], Mock(), threading.Event())
        self.assertEqual(request.call_count, 1)
        self.assertEqual(caught.exception.retry_after, 30)


class PersistenceTests(unittest.TestCase):
    def test_delete_removes_only_target_context(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            for conversation in ('target', 'keep'):
                store.message(conversation, 'user', 'fixture')
                store.record_evidence(conversation, 'calculate', {'result': 2})
                store.save_research(conversation, 'fixture query', {'results': []})
            store.clear_conversation('target')
            self.assertEqual(store.history('target'), [])
            self.assertEqual(store.recent_evidence('target'), [])
            self.assertEqual(store.recent_research('target'), [])
            store.message('target', 'user', 'new conversation')
            self.assertEqual(store.recent_research('target'), [])
            self.assertTrue(store.history('keep'))
            self.assertTrue(store.recent_evidence('keep'))
            self.assertTrue(store.recent_research('keep'))

    def test_delete_rolls_back_all_context_on_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            store.message('target', 'user', 'fixture')
            store.record_evidence('target', 'calculate', {'result': 2})
            store.save_research('target', 'fixture', {})
            with store.connect() as db:
                db.execute("CREATE TRIGGER reject_delete BEFORE DELETE ON research BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
            with self.assertRaises(Exception): store.clear_conversation('target')
            self.assertTrue(store.history('target'))
            self.assertTrue(store.recent_evidence('target'))
            self.assertTrue(store.recent_research('target'))


class WorkerCancellationTests(unittest.TestCase):
    def exercise(self, retry=False):
        ns, app = app_fixture()
        run = ns['Run']('audit')
        app.last_health = None; app.check_results = {}
        app.store.settings.return_value = dict(name='fixture', response_length='short', tone='plain', humor=False)
        app.store.recent_research.return_value = []
        app.store.recent_evidence.return_value = []
        ns.update(os=os, json=json,
            memory=types.SimpleNamespace(command=lambda *a: None, relevant=lambda *a: []),
            actions=types.SimpleNamespace(local_command=lambda *a: None, TOOLS=[]),
            answer_evidence=types.SimpleNamespace(command=lambda *a: None, action_guard=lambda text, events: text, evidence=lambda *a: []),
            verified_status=types.SimpleNamespace(status_question=lambda *a: False, GUIDANCE='', guard=lambda text, context: text),
            workspaces=types.SimpleNamespace(context=lambda *a: None),
            conversation_context=types.SimpleNamespace(TOOL_GUIDANCE='', select_history=lambda *a: [{'role': 'user', 'content': 'fixture'}]))
        def response(*args, **kwargs):
            if retry: raise providers.ProviderError('stream failed')
            run.cancel.set()
            return {'role': 'assistant', 'content': 'late result'}
        def cancel_wait(timeout): run.cancel.set(); return True
        with tempfile.TemporaryDirectory() as folder:
            ns['ROOT'] = Path(folder)
            (ns['ROOT'] / 'personality.txt').write_text('Synthetic offline fixture.', encoding='utf-8')
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic'}, clear=True), patch.object(providers, 'chat', side_effect=response) as chat, patch.object(run.cancel, 'wait', side_effect=cancel_wait), patch.object(time, 'sleep'):
                app.work(run, 'fixture', None)
            self.assertEqual(chat.call_count, 1)
        self.assertTrue(run.done)
        self.assertIn('run.cancelled', [e['event'] for e in run.events])
        self.assertNotIn('assistant.delta', [e['event'] for e in run.events])
        self.assertNotIn('assistant.completed', [e['event'] for e in run.events])
        app.store.message.assert_called_once_with('audit', 'user', 'fixture')

    def test_late_provider_result_not_published(self):
        self.exercise()

    def test_outer_retry_cancelled_during_backoff(self):
        self.exercise(retry=True)


class WearableTests(unittest.TestCase):
    def test_recall_allowed_mutations_denied(self):
        ns, app = app_fixture()
        run = ns['Run']('audit'); run.wearable = True
        ns['actions'] = types.SimpleNamespace(validate=lambda name, args: args)
        ns['conversation_context'] = types.SimpleNamespace(search_saved=Mock(return_value={'results': []}), read_saved=Mock(return_value={'messages': []}))
        for name, args in [('conversation_search', {'query': 'fixture'}), ('conversation_read', {'conversation': 'audit'})]:
            with self.subTest(name=name):
                app.tool(name, args, run)
        for name in ('save_item', 'create_file', 'open_app', 'development_edit'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                app.tool(name, {}, run)

    def test_advertised_recall_names_match_gateway(self):
        source = (ROOT / 'server.py').read_text(encoding='utf-8-sig')
        tree = ast.parse(source)
        work = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'work')
        legacy = [n.value for n in ast.walk(work) if isinstance(n, ast.Constant) and n.value in ('search_conversations', 'read_conversation')]
        self.assertEqual(legacy, [])


if __name__ == '__main__':
    # Hard fail on unexpected outbound access, including accidentally unmocked calls.
    with patch('socket.socket.connect', side_effect=AssertionError('offline tests: network forbidden')):
        unittest.main(verbosity=2)
