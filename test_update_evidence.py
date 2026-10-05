import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from server import App, Run
import update_history
import verified_status


class UpdateEvidence(unittest.TestCase):
    def test_same_clock_tick_keeps_both_records(self):
        with tempfile.TemporaryDirectory() as tmp, patch('update_history.time.time',return_value=1), patch('update_history.time.time_ns',return_value=1):
            root=Path(tmp);(root/'server.py').write_text('first')
            first,_=update_history.observe(root,root/'data')
            (root/'server.py').write_text('second')
            second,records=update_history.observe(root,root/'data')
            self.assertEqual(len(records),2)
            self.assertEqual(records[0]['revision'],second['revision'])
            self.assertNotEqual(first['revision'],second['revision'])

    def test_source_history_persists_and_excludes_private_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'static').mkdir();(root/'desktop').mkdir()
            (root/'server.py').write_text('first')
            (root/'.env').write_text('private-key')
            baseline=update_history.snapshot(root)['revision']
            first=update_history.history(root,root/'data',baseline)
            self.assertEqual(len(first['observations']),1)
            self.assertNotIn('private-key',json.dumps(first))
            (root/'server.py').write_text('second')
            second=update_history.history(root,root/'data',baseline)
            self.assertTrue(second['source_changed_since_backend_start'])
            self.assertEqual(second['observations'][0]['changed_files'],['server.py'])
            self.assertEqual(len(update_history.history(root,root/'data',baseline)['observations']),2)
            self.assertEqual(second['observations'][-1]['revision'],baseline)

    def test_missing_failed_and_stale_results(self):
        missing=verified_status.guard('OpenAI model access succeeded.',{})
        self.assertIn('not checked',missing)
        failed=verified_status.report({'connections':{'chat':{'status':'failed','checked_at':1,'detail':'Request failed.'}}})
        self.assertIn('failed',failed);self.assertIn('historical result',failed)
        self.assertEqual(verified_status.guard('A suggested interface design.',{}),'A suggested interface design.')

    def test_no_unsupported_success_is_streamed_or_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=App(tmp);run=Run('evidence-test')
            def fake(messages,tools,emit,cancel,vision):
                emit('assistant.delta',{'text':'OpenAI model access succeeded.'})
                return {'role':'assistant','content':'OpenAI model access succeeded.'}
            with patch.dict(os.environ,{'OPENAI_API_KEY':'fake-test'}),patch('providers.chat',side_effect=fake):
                app.work(run,'Tell me something useful',None)
            self.assertFalse(any(e['event']=='run.failed' for e in run.events),run.events)
            output=' '.join(e['data'].get('text','') for e in run.events)
            self.assertNotIn('access succeeded',output)
            self.assertIn('not checked',output)
            self.assertNotIn('access succeeded',app.store.history('evidence-test')[-1]['content'])

    def test_service_question_bypasses_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=App(tmp);run=Run('status-test')
            with patch('providers.chat',side_effect=AssertionError('No model needed')):
                app.work(run,'Did OpenAI model access succeed?',None)
            self.assertTrue(any(e['event']=='assistant.completed' and 'not checked' in e['data']['text'] for e in run.events))
            self.assertIn('updates',app.tool('development_history',{}))

    def test_test_claim_requires_execution_result_and_scope(self):
        self.assertIn('No matching test',verified_status.guard('All tests passed.',{}))
        self.assertIn('No matching test',verified_status.guard('I tested the microphone.',{}))
        result=verified_status.guard('All tests passed.',{'tests':[{'status':'failed','exit_code':1,'scope':'Python tests only'}]})
        self.assertIn('failed: Python tests only',result)
        self.assertNotIn('All tests passed',result)
        result=verified_status.guard('All tests passed.',{'tests':[{'status':'passed','exit_code':0,'scope':'Python tests only'}]})
        self.assertIn('passed: Python tests only',result)
        self.assertIn('does not prove',result)


if __name__=='__main__':unittest.main()
