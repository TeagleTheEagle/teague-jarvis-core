import asyncio
import base64
import io
import json
import tempfile
import unittest
import threading
import urllib.request
import urllib.error
from unittest.mock import patch
from PIL import Image
from server import App
from wearables.service import Service
from wearables.config import Config
from wearables.intent import needs_camera
from wearables.interaction import Interaction
from wearables.local_device import LocalDevelopmentAdapter
from wearables.mock_core import MockCore
from wearables.contracts import WearableError
from wearables.real_core import RealCore
from server import Server, Handler


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.app=App(self.temp.name);self.service=Service(self.app)
    def tearDown(self):self.temp.cleanup()
    def wait(self,result):
        run=self.app.runs[result['run_id']]
        with run.condition:run.condition.wait_for(lambda:run.done,5)
        self.assertTrue(run.done)
        return run

    def test_real_vision_reuses_context_guard_and_memory(self):
        self.app.store.put('memory','Favourite colour is cyan.')
        output=io.BytesIO();Image.new('RGB',(4,4),'blue').save(output,format='PNG')
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test'}),patch('providers.chat',return_value={'role':'assistant','content':'A blue fixture, sir.'}) as chat:
            result=self.service.dispatch('start',{'text':'What am I looking at?','image':base64.b64encode(output.getvalue()).decode()})
            run=self.wait(result)
        self.assertTrue(run.wearable)
        self.assertEqual(chat.call_args.args[1],[])
        self.assertTrue(chat.call_args.args[4])
        self.assertIn('cyan',str(chat.call_args.args[0]))
        self.assertIn('wearable conversation',str(chat.call_args.args[0]))
        self.assertFalse(self.app.attachments)
        self.assertTrue(self.app.store.history('wearable-local'))
        self.assertNotIn('base64',str(self.app.store.history('wearable-local')))

    def test_pc_control_denied_on_fast_path(self):
        with patch('actions.local_command',return_value=('assistant_control',{'action':'show_companion'})),patch.object(self.app.controls,'request') as control:
            run=self.wait(self.service.dispatch('start',{'text':'show hologram'}))
        control.assert_not_called()
        self.assertTrue(any(e['event']=='run.failed' for e in run.events))

    def test_vision_unexpected_tool_rejected(self):
        output=io.BytesIO();Image.new('RGB',(4,4)).save(output,format='PNG')
        response={'role':'assistant','tool_calls':[{'id':'x','function':{'name':'time_now','arguments':'{}'}}]}
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test'}),patch('providers.chat',return_value=response),patch.object(self.app,'tool') as tool:
            run=self.wait(self.service.dispatch('start',{'text':'read this','image':base64.b64encode(output.getvalue()).decode()}))
        tool.assert_not_called();self.assertTrue(any(e['event']=='run.failed' for e in run.events))

    def test_voice_uses_saved_profile(self):
        self.app.store.save_settings({'voice_profile':'fish'})
        with patch.object(self.app.voice_engine,'synthesize',return_value=b'a'*100) as synth:
            self.service.dispatch('speech',{'text':'Hello'})
        synth.assert_called_once_with('Hello','fish')

    def test_restricted_run_and_malformed_image(self):
        for op,body in [('events',{'run_id':'desktop-run'}),('cancel',{'run_id':'desktop-run'}),('shutdown',{}),('start',{'text':'hi','conversation':'desktop'}),('start',{'text':'look','image':'not-base64'})]:
            with self.assertRaises(ValueError):self.service.dispatch(op,body)

    def test_http_adapter_auth_and_existing_time_path(self):
        server=Server(('127.0.0.1',0),Handler);server.app=self.app;server.wearable_service=self.service
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url=f'http://127.0.0.1:{server.server_port}'
        try:
            core=RealCore({'url':url,'token':self.service.token})
            self.assertTrue(core.request('status',{})['available'])
            with self.assertRaises(WearableError):RealCore({'url':url,'token':'wrong'}).request('status',{})
            request=urllib.request.Request(url+'/api/wearable/status',data=b'{}',headers={'Content-Type':'application/json','X-Jarvis-Wearable':self.service.token,'Origin':'https://example.com'})
            with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(request)
            # Real HTTP adapter, real App orchestration, local time tool; no provider call.
            with patch('actions.local_command',return_value=('time_now',{})),patch('providers.chat',side_effect=AssertionError('No AI needed')):
                answer=asyncio.run(core.respond('What time is it?'))
            self.assertTrue(answer)
        finally:server.shutdown();server.server_close();thread.join()


class InteractionTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_camera_for_time(self):
        device=LocalDevelopmentAdapter();device.connect();device.permissions['camera']=False
        result=await Interaction(device,Config()).run('JARVIS what time is it?')
        self.assertFalse(result['camera_used']);self.assertNotIn('error',result)

    async def test_real_calls_and_tts_failure_keeps_answer(self):
        class Stub(MockCore):
            async def respond(self,text,image):return 'Existing core answer'
            async def synthesize(self,text):raise WearableError('TTS_UNAVAILABLE')
        device=LocalDevelopmentAdapter();device.connect()
        result=await Interaction(device,Config('real','real','fixture','real'),Stub()).run('read this')
        self.assertEqual(result['answer'],'Existing core answer');self.assertEqual(result['error'],'TTS_UNAVAILABLE')
        self.assertEqual(device.get_device_state()['state'],'IDLE')

    async def test_config_and_intents(self):
        for text in ['what am I looking at?','JARVIS, read this.','describe this']:
            self.assertTrue(needs_camera(text))
        self.assertFalse(needs_camera('what time is it?'))
        with self.assertRaises(WearableError):Config('mock','mock','fixture','real').validate()

    async def test_all_mock_no_real_adapter(self):
        device=LocalDevelopmentAdapter();device.connect()
        result=await Interaction(device,Config()).run()
        self.assertEqual(result['answer_source'],'mock')
        self.assertIsNone(result['latency_ms']['AI_first_token'])
