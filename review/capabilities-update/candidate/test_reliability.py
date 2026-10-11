import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch
from server import App, Run
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

    def test_voice_empty_audio_and_manual_browser(self):
        with patch('providers.capabilities',return_value={'voice_provider':'browser'}),patch('providers.speech') as speech:
            self.assertEqual(connection_checks.check('voice')['status'],'manual_check');speech.assert_not_called()
        with patch('providers.capabilities',return_value={'voice_provider':'fish'}),patch('providers.speech',return_value=b''):
            self.assertEqual(connection_checks.check('voice')['status'],'failed')

    def test_search_checks_results_and_does_not_return_payload(self):
        with patch.dict(os.environ,{'BRAVE_API_KEY':'private-test-key'}),patch('providers.request',return_value={'web':{'results':[{'url':'private-payload'}]}}):
            result=connection_checks.check('search');self.assertEqual(result['status'],'passed')
            self.assertNotIn('private',str(result))

    def test_unexpected_errors_are_sanitized(self):
        with patch('providers.chat',side_effect=RuntimeError('secret')):
            result=connection_checks.check('chat');self.assertNotIn('secret',str(result))

    def test_maps_failure_is_not_success(self):
        with patch('maps.directions',side_effect=ValueError('Routes unavailable')):
            self.assertEqual(connection_checks.check('maps')['status'],'failed')
