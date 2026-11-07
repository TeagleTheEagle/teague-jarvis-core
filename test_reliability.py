import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch
from server import App, Run
import actions
import connection_checks
import providers


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = App(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self, action='save_item', args=None, run=None):
        return self.app.tool('preview_action', {'action':action, 'arguments_json':json.dumps(args or {'kind':'note','body':'Review before saving'})}, run)

    def test_preview_does_not_write_and_approval_only_once(self):
        item = self.prepare()
        self.assertEqual(self.app.store.items('note'), [])
        self.assertEqual(self.app.approve(item['approval']['id'], True)['status'], 'applied')
        self.assertEqual(len(self.app.store.items('note')), 1)
        with self.assertRaises(ValueError): self.app.approve(item['approval']['id'], True)

    def test_denied_expired_and_cancelled_do_not_write(self):
        item = self.prepare()
        self.app.approve(item['approval']['id'], False)
        item = self.prepare()
        self.app.approvals[item['approval']['id']]['expires'] = time.time()-1
        with self.assertRaises(ValueError): self.app.approve(item['approval']['id'], True)
        run = Run('test'); self.app.runs[run.id] = run
        item = self.prepare(run=run);run.cancel.set()
        with self.assertRaises(ValueError): self.app.approve(item['approval']['id'], True)
        self.assertEqual(self.app.store.items('note'), [])

    def test_allowlist_and_exact_file_content(self):
        with self.assertRaises(ValueError): self.prepare('open_app', {'app':'calculator'})
        with self.assertRaises(ValueError): self.prepare(args={'kind':'memory','body':'secret'})
        args={'title':'Draft','content':'Exact reviewed content','format':'txt'}
        with patch('actions.create_document', return_value={'url':'/api/files/test.txt'}) as create:
            item=self.prepare('create_file',args);create.assert_not_called()
            self.app.approve(item['approval']['id'],True)
            self.assertEqual(create.call_args.kwargs,args)

    def test_checks_are_explicit_and_cooldown_reuses_result(self):
        with patch('connection_checks.check', return_value={'service':'chat','checked_at':time.time(),'status':'passed'}) as check:
            self.app.connection_test('chat');self.assertTrue(self.app.connection_test('chat')['cached'])
            check.assert_called_once()


class ConnectionTests(unittest.TestCase):
    def test_real_generation_required(self):
        with patch('providers.chat',return_value={'content':None}):
            self.assertEqual(connection_checks.check('chat')['status'],'failed')
        with patch('providers.chat',return_value={'content':'READY'}):
            self.assertEqual(connection_checks.check('chat')['status'],'passed')

    def test_full_question_sends_what_a_real_question_sends_and_runs_no_tool(self):
        messages = [{'role': 'system', 'content': 'instructions ' * 50}, {'role': 'user', 'content': 'What time is it?'}]
        tools = [{'type': 'function', 'function': {'name': 'time_now'}}, {'type': 'function', 'function': {'name': 'set_timer'}}]
        full = lambda: (messages, tools)
        asked = {'role': 'assistant', 'tool_calls': [{'id': 'c', 'function': {'name': 'time_now', 'arguments': '{}'}}]}
        with patch('providers.chat', return_value=asked) as chat:
            result = connection_checks.check('full', None, full)
        self.assertEqual(result['status'], 'passed')
        self.assertIs(chat.call_args.args[0], messages)
        self.assertIs(chat.call_args.args[1], tools)
        self.assertIn('all 2 tools', result['detail'])
        self.assertIn('It asked for a tool', result['detail'])
        self.assertIn('No tool was run', result['detail'])
        with patch('providers.chat', return_value={'content': 'It is noon.'}):
            self.assertIn('answered in text', connection_checks.check('full', None, full)['detail'])
        for empty in ({'content': None}, {'content': '', 'tool_calls': []}, None):
            with patch('providers.chat', return_value=empty):
                self.assertEqual(connection_checks.check('full', None, full)['status'], 'failed')
        # The provider's refusal of a real-size question is the answer the owner needs, in our own words.
        refused = providers.ProviderError('Qwen chat: The request is larger than this provider or plan accepts at once. (HTTP 413)')
        with patch('providers.chat', side_effect=refused):
            result = connection_checks.check('full', None, full)
        self.assertEqual((result['status'], result['detail']), ('failed', str(refused)))
        self.assertEqual(connection_checks.check('full')['status'], 'failed')  # nothing to send: said, not guessed
        with self.assertRaises(ValueError): connection_checks.check('everything')
        # The tiny test says that it was tiny.
        with patch('providers.chat', return_value={'content': 'READY'}):
            self.assertIn('tiny request', connection_checks.check('chat')['detail'])

    def test_the_settings_test_sends_a_real_size_question_without_anything_saved(self):
        # Settings > Connections > "Real-size question": the full instructions and every tool on offer, as a real
        # question sends them; no conversation, saved fact or file; and no tool is run.
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        app = App(temp.name)
        app.store.put('memory', 'Preference: I prefer tea')
        app.store.message('c', 'user', 'a private chat line')
        app.set_permission('open_app', 'ask')
        app.set_permission('web_search', 'off')
        asked = {'role': 'assistant', 'tool_calls': [{'id': 'c', 'function': {'name': 'time_now', 'arguments': '{}'}}]}
        with patch('providers.chat', return_value=asked) as chat, patch.object(app, 'tool', side_effect=AssertionError('no tool is run')):
            result = app.connection_test('full')
        self.assertEqual(result['status'], 'passed')
        messages, tools = chat.call_args.args[0], chat.call_args.args[1]
        self.assertEqual(messages[0], {'role': 'system', 'content': app.instructions()})
        self.assertIn('development_read', messages[0]['content'])  # the Core's own guidance is part of it
        sent = json.dumps(messages)
        self.assertNotIn('I prefer tea', sent)
        self.assertNotIn('a private chat line', sent)
        self.assertEqual(json.loads(messages[1]['content'].split(': ', 1)[1])['saved_facts'], [])
        names = [t['function']['name'] for t in tools]
        self.assertEqual(len(names), len(actions.TOOLS) - 1)
        self.assertNotIn('web_search', names)                      # switched off: not offered, as in a real question
        self.assertIn('asked on screen', next(t for t in tools if t['function']['name'] == 'open_app')['function']['description'])
        self.assertIn(f'all {len(names)} tools', result['detail'])
        self.assertEqual(app.check_results['full']['status'], 'passed')
        with self.assertRaises(ValueError): app.connection_test('everything')

    def test_voice_empty_audio_and_manual_browser(self):
        with patch('providers.capabilities',return_value={'voice_provider':'browser'}),patch('providers.speech') as speech:
            self.assertEqual(connection_checks.check('voice')['status'],'manual_check');speech.assert_not_called()
        with patch('providers.capabilities',return_value={'voice_provider':'fish'}),patch('providers.speech',return_value=b''):
            self.assertEqual(connection_checks.check('voice')['status'],'failed')

    def test_search_checks_results_and_does_not_return_payload(self):
        with patch.dict(os.environ,{'JARVIS_PROVIDER':'openrouter','OPENROUTER_API_KEY':'private-test-key'}),patch('providers.openrouter_search',return_value=[{'url':'private-payload'}]):
            result=connection_checks.check('search');self.assertEqual(result['status'],'passed')
            self.assertNotIn('private',str(result))

    def test_unexpected_errors_are_sanitized(self):
        with patch('providers.chat',side_effect=RuntimeError('secret')):
            result=connection_checks.check('chat');self.assertNotIn('secret',str(result))

    def test_maps_failure_is_not_success(self):
        with patch('maps.directions',side_effect=ValueError('Routes unavailable')):
            self.assertEqual(connection_checks.check('maps')['status'],'failed')
