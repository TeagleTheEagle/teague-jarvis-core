import datetime
import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch
import answer_evidence as ae
import actions
import providers
import workspaces
from server import App,Run


class EvidenceTests(unittest.TestCase):
    def test_failure_is_not_empty_and_other_sections_survive(self):
        def fail():raise OSError('private diagnostic')
        r=ae.briefing({'tasks':lambda:[],'news':fail,'projects':lambda:[{'name':'Real project'}]})
        text=ae.briefing_details(r)
        self.assertEqual(r['status'],'partial')
        self.assertIn('Tasks: nothing found',text)
        self.assertIn('News: could not check',text)
        self.assertIn('Real project',text)
        self.assertNotIn('private diagnostic',text)
        spoken=ae.describe_briefing(r)
        self.assertNotIn('Checked at',spoken)
        self.assertNotIn('http',spoken)
        self.assertIn("I couldn't get the news",spoken)

    def test_stale_and_missing_retrieval_time_are_labelled(self):
        for raw,status in [({'results':[]},'unverified'),({'results':[],'retrieved_at':'2000-01-01T00:00:00+00:00'},'stale'),({'results':[],'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cached':True},'stale')]:
            with self.subTest(status=status):self.assertEqual(ae.briefing({'news':lambda:raw})['sections']['news']['status'],status)
        self.assertEqual(ae.publication_status('Mon, 01 Jan 2001 00:00:00 GMT',time.time()),'older than 48 hours')
        self.assertEqual(ae.publication_status('not a date',time.time()),'publication date unverified')

    def test_empty_valid_feed_differs_from_invalid_feed(self):
        with patch('actions.request',return_value=b'<rss><channel/></rss>'):
            self.assertEqual(actions.news_search()['results'],[])
        with patch('actions.request',return_value=b'<html/>'):
            with self.assertRaises(providers.ProviderError):actions.news_search()

    def test_preview_is_not_completed(self):
        event={'event':'tool.completed','data':{'name':'preview_action','result':{'status':'awaiting approval'},'checked_at':1}}
        reply=ae.action_guard("I've saved your note.",[event])
        self.assertTrue(reply.startswith("I've saved your note.\n\nAction evidence"))  # 1.0.17: the reply stays, the truth under it
        self.assertIn('awaiting approval',reply)
        self.assertIn('does not mean completed',reply)
        self.assertEqual(ae.action_guard('I created the file.',[]),'I created the file.\n\n'+ae.NO_ACTION_NOTE)
        self.assertEqual(ae.action_guard('Here is a design suggestion.',[]),'Here is a design suggestion.')

    def test_requested_and_failed_receipts(self):
        rows=[{'event':'tool.completed','data':{'name':'inspect_interface','result':{'status':'inspection_requested'},'checked_at':1}}, {'event':'tool.failed','data':{'name':'save_item','checked_at':2}}]
        r=ae.evidence(rows)
        self.assertEqual([x['status'] for x in r],['inspection_requested','failed'])
        self.assertEqual(ae.receipt('unknown',{}),'result returned; completion not inferred')

    def test_commands_do_not_swallow_multistep_or_writes(self):
        self.assertEqual(ae.command('Give me my daily briefing.'),('daily_briefing',{}))
        self.assertIsNone(ae.command('Give me my daily briefing and create a task'))
        self.assertIsNone(ae.command('Delete all my projects'))


class WorkEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.app=App(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_briefing_uses_registry_and_excludes_completed_tasks(self):
        workspaces.change(self.app.store,{'action':'create','name':'Current project'})
        t=self.app.store.task_put('Finished task');self.app.store.complete_task(t['id'],True)
        self.app.store.task_put('Outstanding task')
        run=Run('brief')
        with patch('providers.chat',side_effect=AssertionError('No model needed')),patch('actions.news_search',side_effect=providers.ProviderError('offline')):
            self.app.work(run,'Give me my daily briefing',None)
        reply=next(e['data']['text'] for e in run.events if e['event']=='assistant.completed')
        self.assertIn('Current project',reply);self.assertIn('Outstanding task',reply)
        self.assertNotIn('Finished task',reply);self.assertIn("I couldn't get the news",reply)
        self.assertIn("I can't check your calendar",reply)
        self.assertEqual(next(e['data']['result']['status'] for e in run.events if e['event']=='tool.completed'),'partial')

    def test_model_cannot_claim_preview_applied(self):
        run=Run('pending')
        responses=[{'role':'assistant','content':'Saved!','tool_calls':[{'id':'c1','type':'function','function':{'name':'preview_action','arguments':json.dumps({'action':'save_item','arguments_json':json.dumps({'kind':'note','body':'Draft note'})})}}]}, {'role':'assistant','content':"I've saved your note."}]
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':'test'}),patch('providers.chat',side_effect=responses):self.app.work(run,'Prepare a note for review',None)
        reply=next(e['data']['text'] for e in run.events if e['event']=='assistant.completed')
        self.assertIn('awaiting approval',reply);self.assertIn('does not mean completed',reply)  # 1.0.17: the claim stays, the truth under it
        self.assertTrue(reply.startswith("I've saved your note.\n\nAction evidence"))
        self.assertEqual(self.app.store.items('note'),[])
        self.assertNotIn('Saved!',str(run.events))

    def test_failed_tool_record_visible_and_no_false_success(self):
        run=Run('failed')
        responses=[{'role':'assistant','content':'','tool_calls':[{'id':'c1','type':'function','function':{'name':'create_file','arguments':json.dumps({'title':'Test','content':'x','format':'txt'})}}]}, {'role':'assistant','content':'I created the file.'}]
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':'test'}),patch('providers.chat',side_effect=responses),patch('actions.create_document',side_effect=ValueError('unavailable')):
            self.app.work(run,'Make a document about testing',None)
        reply=next(e['data']['text'] for e in run.events if e['event']=='assistant.completed')
        self.assertIn('create file: failed',reply);self.assertTrue(reply.startswith('I created the file.\n\nAction evidence'))  # 1.0.17
        evidence=next(e['data'] for e in run.events if e['event']=='answer.evidence')
        self.assertEqual(evidence['tools'][0]['status'],'failed')

if __name__=='__main__':unittest.main()
