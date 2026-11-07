"""Settings > Answer speed: which Qwen model answers and whether it thinks first (providers.qwen_plan)."""
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import connection_checks
import providers
import store
from server import App, Run

STOP = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'Hi'}}]}
TOOL = {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
    {'id': 'c1', 'type': 'function', 'function': {'name': 'time_now', 'arguments': '{}'}}]}}]}
OPENROUTER = {'JARVIS_PROVIDER': 'openrouter', 'OPENROUTER_API_KEY': 'test-key'}  # the models are fixed in the program (2026-10-13): no model lines


def ask(**kwargs):
    """One Qwen request with the given mode/text/vision; returns the request body JARVIS would send."""
    vision = kwargs.pop('vision', False)
    tools = kwargs.pop('tools', [])
    with patch.object(providers, 'request', return_value=STOP) as request:
        providers.chat([], tools, lambda *args: None, threading.Event(), vision, **kwargs)
    return request.call_args.args[1]


class PlanTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {'JARVIS_PROVIDER': 'openrouter', 'OPENROUTER_API_KEY': 'test-key'}, clear=True)
        env.start()
        self.addCleanup(env.stop)

    def test_depth_words(self):
        for text in ('Think hard about this', 'please THINK CAREFULLY before answering', 'think it through with me',
                     'Take your time on this one', 'I need a deep dive into my budget', 'think really hard',
                     'reason step by step', 'think step-by-step', 'think about this carefully', 'think long and hard',
                     'think more carefully', 'think real hard', 'I want you thinking hard here', 'a deep-dive on costs',
                     'think  hard\nabout it', "don't rush. Think hard about it."):
            self.assertTrue(providers.wants_depth(text), text)
        for text in ('', None, 'What time is it?', 'I think hard drives are slower than SSDs', 'what do you think',
                     'think about hardware prices', 'deep sea fishing', 'analyse my screen',
                     "don't think hard about it, just answer quickly", 'no need to think carefully',
                     'I think hard work pays off', 'tell Sam to take your time off', 'book a deep dive at the reef'):
            self.assertFalse(providers.wants_depth(text), text)

    def test_depth_words_stay_fast_on_hostile_text(self):
        started = threading.Event()
        text = ('think ' * 60000) + ('very ' * 60000) + 'x'
        timer = threading.Timer(5, started.set)
        timer.start()
        try:
            providers.wants_depth(text)
        finally:
            timer.cancel()
        self.assertFalse(started.is_set())

    def test_labels_and_checks_name_the_model_that_answers(self):
        main, fast = providers.OPENROUTER_DEFAULT_MODEL, providers.OPENROUTER_DEFAULT_FAST_MODEL
        self.assertEqual(providers.capabilities()['model'], main)
        self.assertEqual(providers.capabilities('auto')['model'], main)
        self.assertEqual(providers.capabilities('economy')['model'], fast)
        with patch.object(providers, 'request', return_value=STOP) as request:
            self.assertEqual(connection_checks.check('chat', 'economy')['status'], 'passed')
        self.assertEqual(request.call_args.args[1]['model'], fast)
        with patch.object(providers, 'request', return_value=STOP) as request:
            connection_checks.check('chat')
        self.assertEqual(request.call_args.args[1]['model'], main)

    def test_chat_options_are_empty_when_nothing_changes(self):
        self.assertEqual(providers.chat_options(None, 'hello'), {})
        self.assertEqual(providers.chat_options('deep', 'anything'), {})
        self.assertEqual(providers.chat_options('nonsense', 'anything'), {})
        # "think hard" asks OpenRouter for more than Deep does, so even in Deep those words go along (review of 2026-10-12, M1).
        self.assertEqual(providers.chat_options(None, 'think hard'), {'mode': 'deep', 'text': 'think hard'})
        self.assertEqual(providers.chat_options('auto', 'hello'), {'mode': 'auto', 'text': 'hello'})
        self.assertEqual(providers.chat_options('economy', ''), {'mode': 'economy', 'text': ''})


class AnswerModeSettingTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name
        self.app = App(folder.name)

    def chat_call(self, text):
        """The arguments the Core passes to providers.chat for one typed question."""
        run = Run('answer-mode-test')
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-placeholder'}), \
                patch('providers.chat', return_value={'role': 'assistant', 'content': 'Paris.'}) as chat:
            self.app.work(run, text, None)
        self.assertTrue(any(e['event'] == 'assistant.completed' for e in run.events), run.events[-1])
        return chat.call_args

    def openrouter_bodies(self, text, replies, attachment=None):
        """Every request body one question sends to OpenRouter, with providers.request standing in for it."""
        run = Run('answer-mode-test')
        with patch.dict(os.environ, OPENROUTER, clear=True), patch.object(providers, 'request', side_effect=replies) as request, \
                patch.object(run.cancel, 'wait', return_value=False):
            self.app.work(run, text, attachment)
        self.assertTrue(any(e['event'] == 'assistant.completed' for e in run.events), run.events[-1])
        return [call.args[1] for call in request.call_args_list]

    def test_the_two_copies_of_the_modes_agree(self):
        self.assertEqual(store.ANSWER_MODES, providers.ANSWER_MODES)
        self.assertEqual(store.DEFAULT_ANSWER_MODE, providers.DEFAULT_ANSWER_MODE)

    def test_default_is_deep_and_the_everyday_call_is_unchanged(self):
        self.assertEqual(self.app.store.settings()['answer_mode'], 'deep')
        call = self.chat_call('What is the capital of France?')
        self.assertEqual(len(call.args), 5)
        # Settings > AI > Backup is on by default: OpenRouter may try its backup model (plan D8).
        self.assertEqual(call.kwargs, {'fallback': True})
        # "think hard" asks OpenRouter for more than Deep does, so the words go along (review of 2026-10-12, M1).
        text = 'Think hard about the capital of France.'
        self.assertEqual(self.chat_call(text).kwargs, {'mode': 'deep', 'text': text, 'fallback': True})

    def test_the_setting_and_the_users_words_reach_the_provider(self):
        for mode in ('auto', 'economy'):
            self.app.store.save_settings({'answer_mode': mode})
            text = 'Think hard about the capital of France.'
            self.assertEqual(self.chat_call(text).kwargs, {'mode': mode, 'text': text, 'fallback': True})
        self.app.store.save_settings({'answer_mode': 'auto'})
        self.assertEqual(self.chat_call('What is the capital of France?').kwargs, {'mode': 'auto', 'text': 'What is the capital of France?', 'fallback': True})

    def test_every_request_of_one_question_uses_the_same_plan(self):
        main, fast = providers.OPENROUTER_DEFAULT_MODEL, providers.OPENROUTER_DEFAULT_FAST_MODEL
        expected = {'deep': (main, 'medium'), 'auto': (main, 'minimal'), 'economy': (fast, 'none')}
        for mode, (model, effort) in expected.items():
            self.app.store.save_settings({'answer_mode': mode})
            # a tool round, then the answer
            bodies = self.openrouter_bodies('What time is it right now, please?', [TOOL, STOP])
            self.assertEqual(len(bodies), 2, mode)
            # a dropped connection on the first try, then the answer on the retry
            bodies += self.openrouter_bodies('Tell me about France.', [providers.ProviderError('OpenRouter chat: Connection failed.'), STOP])
            self.assertEqual(len(bodies), 4, mode)
            for body in bodies:
                self.assertEqual(body['model'], model, mode)
                self.assertEqual(body['reasoning']['effort'], effort, mode)

    def test_a_screen_capture_stays_on_the_vision_model_in_economy(self):
        self.app.store.save_settings({'answer_mode': 'economy'})
        shot = {'type': 'image', 'name': 'screen-capture.jpg', 'data': 'data:image/jpeg;base64,c3ludGhldGlj'}
        bodies = self.openrouter_bodies('Review this screen', [STOP], shot)
        self.assertEqual([body['model'] for body in bodies], [providers.OPENROUTER_DEFAULT_MODEL])  # the main model sees pictures
        self.assertEqual(bodies[0]['reasoning']['effort'], 'minimal')  # pictures keep the main path's thinking, not Economy's
        self.assertNotIn('tools', bodies[0])

    def test_the_stage_4_harness_keeps_its_five_argument_chat(self):
        self.app.store.save_settings({'answer_mode': 'economy'})
        (Path(self.folder) / 'personality.txt').write_text('Fixture personality.', encoding='utf-8')
        self.app.stage4 = Mock()
        seen = []

        def chat(messages, tools, callback, cancel, vision=False):
            seen.append(vision)
            return {'role': 'assistant', 'content': 'Fixture answer.'}

        run = Run('answer-mode-test')
        with patch('providers.chat', side_effect=chat):
            self.app.work(run, 'Think hard about this fixture.', None)
        self.assertEqual(seen, [False])
        self.app.stage4.finish_response.assert_called_once()
        self.app.stage4.fail_response.assert_not_called()

    def test_only_the_three_modes_can_be_saved(self):
        for mode in providers.ANSWER_MODES:
            self.app.store.save_settings({'answer_mode': mode})
            self.assertEqual(self.app.store.settings()['answer_mode'], mode)
        for bad in ('fast', '', 'DEEP', 5):
            with self.assertRaises(ValueError):
                self.app.store.save_settings({'answer_mode': bad})
        self.assertEqual(self.app.store.settings()['answer_mode'], 'economy')

    def test_an_unknown_stored_value_reads_as_the_default(self):
        with self.app.store.connect() as db:
            db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('answer_mode', json.dumps('turbo')))
        self.assertEqual(self.app.store.settings()['answer_mode'], 'deep')

    def test_the_json_backup_carries_the_mode_and_refuses_an_unknown_one(self):
        self.app.store.import_data({'settings': [{'key': 'answer_mode', 'value': json.dumps('auto')}]})
        self.assertEqual(self.app.store.settings()['answer_mode'], 'auto')
        self.app.store.import_data({'settings': [{'key': 'answer_mode', 'value': json.dumps('turbo')}]})
        self.assertEqual(self.app.store.settings()['answer_mode'], 'auto')


class SettingsFormTests(unittest.TestCase):
    """The Settings form offers the three modes and saves the choice under the key the Core validates."""

    def test_the_form_offers_and_saves_the_three_modes(self):
        script = (Path(__file__).parent / 'static' / 'app.js').read_text(encoding='utf-8')
        for mode in providers.ANSWER_MODES:
            self.assertEqual(script.count(f'<option value="{mode}">'), 1, mode)
        self.assertIn("answer_mode:$('#answerMode').value", script)
        self.assertIn("$('#answerMode').value=s.answer_mode||'" + providers.DEFAULT_ANSWER_MODE + "'", script)


if __name__ == '__main__':
    unittest.main()
