"""Settings > AI > backup provider: OpenAI and Qwen stand in for each other when the owner allows it."""
import io
import os
import tempfile
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

import providers
import server
from server import App, Run

STOP = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'The answer.'}}]}
TOOL = {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
    {'id': 'c1', 'type': 'function', 'function': {'name': 'time_now', 'arguments': '{}'}}]}}]}
BOTH = {'JARVIS_PROVIDER': 'qwen', 'DASHSCOPE_API_KEY': 'qwen-test-key', 'OPENAI_API_KEY': 'openai-test-key'}
QUESTION = 'Compare Paris and Lyon for a weekend away.'
NOTE = '[OpenAI answered this question because Qwen could not. Qwen chat: Alibaba Cloud refused access: the account balance is overdue or empty.]'


def billing():
    """The error JARVIS really builds when Alibaba answers HTTP 400 Arrearage (an overdue account)."""
    upstream = urllib.error.HTTPError('https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions', 400, 'error', {},
                                      io.BytesIO(b'{"error":{"code":"Arrearage","message":"UPSTREAM-DETAIL-NOT-SHOWN"}}'))
    return providers._http_error('Qwen chat: ', 'Qwen', upstream)


def unreachable(text='Qwen chat: Connection failed. Check internet access and provider availability.'):
    error = providers.ProviderError(text)
    error.unreachable, error.service = True, 'Qwen'
    return error


def no_credit():
    error = providers.ProviderError('OpenAI chat: OpenAI reports a billing or quota limit on this account. Waiting will not help. (HTTP 429, type insufficient_quota)')
    error.status, error.limit, error.service = 429, 'billing', 'OpenAI'
    return error


class BackupChoiceTests(unittest.TestCase):
    def choose(self, env, vision=False):
        with patch.dict(os.environ, env, clear=True):
            return providers.backup_provider(vision)

    def test_the_other_provider_needs_its_own_key(self):
        self.assertEqual(self.choose(BOTH), 'openai')
        self.assertEqual(self.choose({**BOTH, 'JARVIS_PROVIDER': 'openai'}), 'qwen')
        self.assertEqual(self.choose({'OPENAI_API_KEY': 'k', 'DASHSCOPE_API_KEY': 'k'}), 'qwen')  # no line: OpenAI is chosen
        self.assertIsNone(self.choose({'JARVIS_PROVIDER': 'qwen', 'DASHSCOPE_API_KEY': 'k'}))
        self.assertIsNone(self.choose({'JARVIS_PROVIDER': 'openai', 'OPENAI_API_KEY': 'k'}))
        self.assertIsNone(self.choose({**BOTH, 'JARVIS_PROVIDER': 'groq'}))

    def test_pictures_need_a_picture_model_on_the_backup(self):
        self.assertEqual(self.choose(BOTH, vision=True), 'openai')  # OpenAI has a default picture model
        self.assertIsNone(self.choose({**BOTH, 'OPENAI_VISION_MODEL': ''}, vision=True))
        self.assertIsNone(self.choose({**BOTH, 'JARVIS_PROVIDER': 'openai'}, vision=True))
        self.assertEqual(self.choose({**BOTH, 'JARVIS_PROVIDER': 'openai', 'QWEN_VISION_MODEL': 'qwen3.8-max'}, vision=True), 'qwen')

    def test_settings_can_show_whether_a_backup_is_available(self):
        with patch.dict(os.environ, BOTH, clear=True):
            self.assertEqual(providers.capabilities()['backup'], 'OpenAI')
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'qwen', 'DASHSCOPE_API_KEY': 'k'}, clear=True):
            self.assertIsNone(providers.capabilities()['backup'])

    def test_only_a_refusal_or_an_unreachable_provider_is_worth_a_backup(self):
        self.assertTrue(providers.backup_worthy(billing()))
        self.assertTrue(providers.backup_worthy(unreachable()))
        self.assertTrue(providers.backup_worthy(no_credit()))
        for local in ('Qwen is selected. Add DASHSCOPE_API_KEY locally and restart JARVIS.',
                      'Image understanding needs a Qwen vision model. Authorise one for your key and set QWEN_VISION_MODEL.',
                      'Qwen did not return a complete response. No partial answer was accepted.',
                      'The response reached its token limit. Please narrow the request or split it into smaller steps.'):
            self.assertFalse(providers.backup_worthy(providers.ProviderError(local)), local)

    def test_a_real_network_failure_is_marked_unreachable(self):
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError(TimeoutError())), self.assertRaises(providers.ProviderError) as raised:
            providers.request('https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions', {'model': 'x'})
        self.assertTrue(raised.exception.unreachable)
        self.assertIn('timed out', str(raised.exception))
        self.assertTrue(providers.backup_worthy(raised.exception))

    def test_the_note_is_one_sentence_of_our_own_words(self):
        with patch.dict(os.environ, BOTH, clear=True):
            self.assertEqual(providers.backup_note('openai', billing()), NOTE)
            note = providers.backup_note('openai', unreachable())
        self.assertEqual(note, '[OpenAI answered this question because Qwen could not. Qwen chat: Connection failed.]')
        self.assertNotIn('UPSTREAM', NOTE)
        self.assertNotIn('HTTP', NOTE)
        self.assertEqual(providers.BACKUP_NOTE.sub('', 'Fine.\n\n' + NOTE), 'Fine.')

    def test_use_sends_one_request_to_the_named_provider_with_its_own_key(self):
        with patch.dict(os.environ, BOTH, clear=True), patch.object(providers, 'request', return_value=STOP) as request:
            providers.chat([], [], lambda *args: None, threading.Event(), use='openai')
            url, body, headers = request.call_args.args[:3]
            self.assertEqual(url, 'https://api.openai.com/v1/chat/completions')
            self.assertEqual(headers['Authorization'], 'Bearer openai-test-key')
            self.assertNotIn('enable_thinking', body)
            providers.chat([], [], lambda *args: None, threading.Event())
            self.assertIn('dashscope', request.call_args.args[0])
            self.assertEqual(request.call_args.args[2]['Authorization'], 'Bearer qwen-test-key')
        with patch.dict(os.environ, {**BOTH, 'JARVIS_PROVIDER': 'openai'}, clear=True), patch.object(providers, 'request', return_value=STOP) as request:
            providers.chat([], [], lambda *args: None, threading.Event(), use='qwen')
            self.assertIn('dashscope', request.call_args.args[0])
            self.assertEqual(request.call_args.args[2]['Authorization'], 'Bearer qwen-test-key')


class BackupRunTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name
        self.app = App(folder.name)

    def run_question(self, qwen, openai, text=QUESTION, attachment=None, env=BOTH, cancel_on=None, hang=0, wearable=False,
                     conversation='backup-test'):
        """One question. qwen and openai are lists of replies or errors, taken in order by provider address.
        cancel_on stops the question when that provider is asked; hang moves the clock on by that many seconds
        each time a provider fails, as if it had hung first."""
        self.calls, self.bodies = [], []
        run = Run(conversation)
        if wearable:
            run.wearable = True
        clock = {'offset': 0}
        real_time = time.time

        def request(url, body=None, headers=None, **kwargs):
            name = 'qwen' if 'dashscope' in url else 'openai'
            self.calls.append(name)
            self.bodies.append(body)
            if cancel_on == name:
                run.cancel.set()
            reply = (qwen if name == 'qwen' else openai).pop(0)
            if isinstance(reply, Exception):
                clock['offset'] += hang
                raise reply
            return reply

        with patch.dict(os.environ, env, clear=True), patch.object(providers, 'request', side_effect=request), \
                patch.object(run.cancel, 'wait', side_effect=lambda seconds: run.cancel.is_set()), \
                patch('time.time', side_effect=lambda: real_time() + clock['offset']):
            self.app.work(run, text, attachment)
        return self.calls, {e['event']: e['data'] for e in run.events}, run

    def switch_on(self, **more):
        self.app.store.save_settings({'provider_backup': True, **more})

    def audit_rows(self):
        return [row['action'] for row in self.app.store.logs() if 'backup provider' in row['action']]

    def test_on_by_default_on_the_owners_word(self):
        # Owner, 2026-10-05: "backup on".
        self.assertIs(self.app.store.settings()['provider_backup'], True)
        calls, events, _ = self.run_question([billing()], [STOP])
        self.assertEqual(calls, ['qwen', 'openai'])
        self.assertTrue(events['assistant.completed']['text'].endswith(NOTE))

    def test_switched_off_the_failure_is_reported_as_before(self):
        self.app.store.save_settings({'provider_backup': False})
        calls, events, _ = self.run_question([billing()], [STOP])
        self.assertEqual(calls, ['qwen'])
        self.assertIn('overdue', events['run.failed']['message'])
        self.assertEqual(events['run.failed']['limit'], 'billing')
        self.assertNotIn('provider.backup', events)
        self.assertEqual(self.audit_rows(), [])

    def test_switched_on_the_other_provider_answers_and_the_reply_says_so(self):
        self.switch_on()
        calls, events, _ = self.run_question([billing()], [STOP])
        self.assertEqual(calls, ['qwen', 'openai'])
        self.assertEqual(events['assistant.completed']['text'], 'The answer.\n\n' + NOTE)
        self.assertEqual(events['provider.backup'], {'from': 'Qwen', 'to': 'OpenAI', 'reason': 'Qwen chat: Alibaba Cloud refused access: the account balance is overdue or empty.'})
        self.assertNotIn('run.failed', events)
        self.assertEqual(self.app.store.history('backup-test', 5)[-1]['content'], 'The answer.\n\n' + NOTE)
        self.assertEqual(self.audit_rows(), ['backup provider took over: OpenAI'])

    def test_a_dropped_connection_is_retried_first_then_the_backup_answers(self):
        self.switch_on()
        calls, events, _ = self.run_question([unreachable(), unreachable()], [STOP])
        self.assertEqual(calls, ['qwen', 'qwen', 'openai'])
        self.assertIn('assistant.completed', events)

    def test_the_question_stays_with_the_backup_for_its_tool_rounds(self):
        self.switch_on()
        calls, events, _ = self.run_question([billing()], [dict(TOOL), STOP])
        self.assertEqual(calls, ['qwen', 'openai', 'openai'])
        self.assertTrue(events['assistant.completed']['text'].endswith(NOTE))

    def test_the_backup_gets_its_own_time_after_the_chosen_provider_hung(self):
        # The chosen provider hangs for most of the question's 120 seconds and then cannot be reached. The backup's
        # tool round must not then be cut off as "time limit exceeded" after the tool has already run.
        self.switch_on()
        slow = unreachable('Qwen chat: Connection timed out. Try again shortly.')
        calls, events, _ = self.run_question([slow], [dict(TOOL), STOP], hang=125)
        self.assertEqual(calls, ['qwen', 'openai', 'openai'])
        self.assertIn('assistant.completed', events)
        self.assertNotIn('run.failed', events)

    def test_without_a_backup_the_time_limit_still_ends_a_slow_question(self):
        # The first try hangs for 125 seconds and drops, the retry asks for a tool; the next round is past the limit.
        calls, events, _ = self.run_question([unreachable(), dict(TOOL), STOP], [STOP], hang=125)
        self.assertEqual(calls, ['qwen', 'qwen'])
        self.assertEqual(events['run.failed']['message'], 'Request time limit exceeded.')

    def test_never_after_a_tool_has_run_in_the_question(self):
        self.switch_on()
        calls, events, _ = self.run_question([dict(TOOL), billing()], [STOP])
        self.assertEqual(calls, ['qwen', 'qwen'])
        self.assertIn('overdue', events['run.failed']['message'])
        self.assertNotIn('provider.backup', events)

    def test_not_for_a_missing_key_a_missing_picture_model_or_a_reply_cut_short(self):
        self.switch_on()
        calls, events, _ = self.run_question([STOP], [STOP], env={'JARVIS_PROVIDER': 'qwen', 'OPENAI_API_KEY': 'openai-test-key'})
        self.assertEqual(calls, [])  # Qwen is chosen and has no key: say so, do not quietly use OpenAI
        self.assertIn('DASHSCOPE_API_KEY', events['run.failed']['message'])
        shot = {'type': 'image', 'name': 'screen-capture.jpg', 'data': 'data:image/jpeg;base64,c3ludGhldGlj'}
        calls, events, _ = self.run_question([STOP], [STOP], text='Review this screen', attachment=shot)
        self.assertEqual(calls, [])  # no QWEN_VISION_MODEL line
        self.assertIn('QWEN_VISION_MODEL', events['run.failed']['message'])
        cut = {'choices': [{'finish_reason': 'length', 'message': {'content': 'partial'}}]}
        calls, events, _ = self.run_question([cut], [STOP])
        self.assertEqual(calls, ['qwen'])
        self.assertIn('complete response', events['run.failed']['message'])

    def test_when_the_backup_fails_too_both_reasons_are_given(self):
        self.switch_on()
        calls, events, _ = self.run_question([billing()], [no_credit()])
        self.assertEqual(calls, ['qwen', 'openai'])
        message = events['run.failed']['message']
        self.assertIn('overdue', message)
        self.assertIn('The backup provider, OpenAI, also failed: OpenAI chat: OpenAI reports a billing or quota limit', message)
        self.assertEqual(events['run.failed']['limit'], 'billing')
        self.assertEqual(events['run.failed']['provider'], 'Qwen')
        self.assertNotIn('provider.backup', events)
        self.assertEqual(self.audit_rows(), [])

    def test_a_failure_after_the_backup_took_over_still_says_that_it_had(self):
        self.switch_on()
        calls, events, _ = self.run_question([billing()], [dict(TOOL), no_credit()])
        self.assertEqual(calls, ['qwen', 'openai', 'openai'])
        message = events['run.failed']['message']
        self.assertIn('OpenAI reports a billing or quota limit', message)
        self.assertIn('[OpenAI had taken over this question because Qwen could not. Qwen chat: Alibaba Cloud refused access', message)
        self.assertEqual(self.audit_rows(), ['backup provider took over: OpenAI'])

    def test_no_backup_without_the_other_key_or_for_a_stopped_question(self):
        self.switch_on()
        calls, events, _ = self.run_question([billing()], [STOP], env={'JARVIS_PROVIDER': 'qwen', 'DASHSCOPE_API_KEY': 'k'})
        self.assertEqual(calls, ['qwen'])
        self.assertIn('run.failed', events)
        calls, events, _ = self.run_question([billing()], [STOP], cancel_on='qwen')
        self.assertEqual(calls, ['qwen'])
        self.assertIn('run.cancelled', events)

    def test_a_question_stopped_while_the_backup_is_asked_records_no_takeover(self):
        self.switch_on()
        calls, events, _ = self.run_question([billing()], [STOP], cancel_on='openai')
        self.assertEqual(calls, ['qwen', 'openai'])
        self.assertIn('run.cancelled', events)
        self.assertNotIn('provider.backup', events)
        self.assertNotIn('assistant.completed', events)
        self.assertEqual(self.audit_rows(), [])

    def test_it_works_the_other_way_round(self):
        self.switch_on(answer_mode='auto')
        calls, events, _ = self.run_question([STOP], [no_credit()], env={**BOTH, 'JARVIS_PROVIDER': 'openai'})
        self.assertEqual(calls, ['openai', 'qwen'])
        self.assertTrue(events['assistant.completed']['text'].endswith(
            '[Qwen answered this question because OpenAI could not. OpenAI chat: OpenAI reports a billing or quota limit on this account.]'))
        self.assertIs(self.bodies[-1]['enable_thinking'], False)  # the saved answer mode applies to the backup as well

    def test_the_newer_openai_models_work_as_the_backup(self):
        self.switch_on()
        reply = {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'The answer.'}]}]}
        calls, events, _ = self.run_question([billing()], [reply], env={**BOTH, 'OPENAI_MODEL': 'gpt-6-astra'})
        self.assertEqual(calls, ['qwen', 'openai'])
        self.assertEqual(events['assistant.completed']['text'], 'The answer.\n\n' + NOTE)
        self.assertEqual(self.bodies[-1]['model'], 'gpt-6-astra')

    def test_a_screen_capture_can_fall_back_and_still_gets_no_tools(self):
        self.switch_on()
        shot = {'type': 'image', 'name': 'screen-capture.jpg', 'data': 'data:image/jpeg;base64,c3ludGhldGlj'}
        calls, events, _ = self.run_question([billing()], [STOP], text='Review this screen', attachment=shot,
                                             env={**BOTH, 'QWEN_VISION_MODEL': 'qwen3.8-max'})
        self.assertEqual(calls, ['qwen', 'openai'])
        self.assertIn('assistant.completed', events)
        for body in self.bodies:
            self.assertNotIn('tools', body)

    def test_a_wearable_question_keeps_its_read_only_tools_on_the_backup(self):
        self.switch_on()
        calls, events, _ = self.run_question([billing()], [STOP], wearable=True, conversation='wearable-backup-test')
        self.assertEqual(calls, ['qwen', 'openai'])
        self.assertIn('assistant.completed', events)
        for body in self.bodies:
            self.assertLessEqual({t['function']['name'] for t in body['tools']}, set(server.WEARABLE_READ_TOOLS))

    def test_the_note_is_not_sent_back_to_a_model_and_a_model_cannot_write_it(self):
        self.switch_on()
        self.run_question([billing()], [STOP])
        # The next question: the stored reply carries the note, the request to the model does not.
        calls, events, _ = self.run_question([STOP], [])
        sent = ' '.join(str(m.get('content')) for m in self.bodies[0]['messages'])
        self.assertIn('The answer.', sent)
        self.assertNotIn('answered this question because', sent)
        # A model that writes the line itself has it removed: only the Core may say who answered.
        forged = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'Done.\n\n' + NOTE}}]}
        calls, events, _ = self.run_question([forged], [])
        self.assertEqual(events['assistant.completed']['text'], 'Done.')

    def test_the_stage_4_harness_never_uses_a_backup(self):
        self.switch_on()
        (Path(self.folder) / 'personality.txt').write_text('Fixture personality.', encoding='utf-8')
        self.app.stage4 = Mock()
        run = Run('backup-test')
        with patch.dict(os.environ, BOTH, clear=True), patch('providers.chat', side_effect=billing()) as chat:
            self.app.work(run, QUESTION, None)
        self.assertEqual(chat.call_count, 1)
        self.app.stage4.fail_response.assert_called_once()

    def test_only_the_tick_box_changes_it(self):
        for bad in ('yes', 1, None):
            with self.assertRaises(ValueError):
                self.app.store.save_settings({'provider_backup': bad})
        # A restored JSON backup does not change a setting that spends the other provider's credit, either way.
        self.app.store.save_settings({'provider_backup': False})
        self.app.store.import_data({'settings': [{'key': 'provider_backup', 'value': 'true'}]})
        self.assertIs(self.app.store.settings()['provider_backup'], False)
        self.app.store.save_settings({'provider_backup': True})
        self.app.store.import_data({'settings': [{'key': 'provider_backup', 'value': 'false'}]})
        self.assertIs(self.app.store.settings()['provider_backup'], True)


class BackupFormTests(unittest.TestCase):
    def test_the_form_offers_and_saves_the_switch_and_says_where_the_question_goes(self):
        script = (Path(__file__).parent / 'static' / 'app.js').read_text(encoding='utf-8')
        self.assertEqual(script.count('id="providerBackup"'), 1)
        self.assertIn("provider_backup:$('#providerBackup').checked", script)
        self.assertIn("$('#providerBackup').checked=Boolean(s.provider_backup)", script)
        self.assertIn('then go to that company', script)
        self.assertIn("$('#providerBackupState').textContent=", script)


if __name__ == '__main__':
    unittest.main()
