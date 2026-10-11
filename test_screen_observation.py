import tempfile,unittest
from unittest.mock import patch
from server import App,Run
class ScreenObservationTests(unittest.TestCase):
    def test_screen_cannot_execute_even_unexpected_tool_call(self):
        with tempfile.TemporaryDirectory() as folder:
            app=App(folder);run=Run('screen-test')
            attachment={'type':'image','name':'screen-capture.jpg','data':'data:image/jpeg;base64,test'}
            response={'role':'assistant','content':'','tool_calls':[{'id':'x','function':{'name':'navigate_panel','arguments':'{"panel":"projects"}'}}]}
            with patch.dict('os.environ',{'OPENAI_API_KEY':'test-placeholder'}),patch('providers.chat',return_value=response) as chat,patch.object(app,'tool') as tool:
                app.work(run,'Review this screen',attachment)
            self.assertEqual(chat.call_args.args[1],[])
            tool.assert_not_called()
            self.assertTrue(any(e['event']=='run.failed' for e in run.events))

    def test_screen_submission_consumes_image_and_saves_text_only(self):
        with tempfile.TemporaryDirectory() as folder:
            app=App(folder)
            app.attachments['shot']={'id':'shot','type':'image','name':'screen-capture.jpg','data':'data:image/jpeg;base64,c3ludGhldGlj'}
            response={'role':'assistant','content':'The test image is visible.'}
            with patch.dict('os.environ',{'OPENAI_API_KEY':'test-placeholder'}),patch('providers.chat',return_value=response) as chat:
                result=app.start_run({'conversation':'screen-test','text':'Review this screenshot','attachment':'shot'})
                run=app.runs[result['run_id']]
                with run.condition:
                    run.condition.wait_for(lambda:run.done,timeout=5)
                self.assertTrue(run.done)
                self.assertNotIn('shot',app.attachments)
                self.assertEqual(chat.call_args.args[1],[])
                self.assertTrue(any(e['event']=='assistant.completed' for e in run.events))
                self.assertNotIn('base64',str(app.store.history('screen-test')))
