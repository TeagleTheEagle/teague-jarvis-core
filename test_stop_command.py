"""Speech-stop variants must route locally and remain narrowly authorised."""
import json
from pathlib import Path
import subprocess
import threading
import unittest
from types import SimpleNamespace
from assistant_capabilities import Controls


class StopCommands(unittest.TestCase):
    def test_repeated_stop_and_negative_requests(self):
        cases = {'Stop, stop speaking.': True, 'Stop.': True,
                 'Hey Jarvis, stop stop talking!': True,
                 'Please stop speaking': True, 'stop stop stop': True,
                 'Do not stop speaking': False, 'stop screen sharing': False,
                 'Explain stop speaking': False, '"stop speaking"': False}
        source = Path(__file__).with_name('static').joinpath('assistant-controls.js').read_text(encoding='utf-8')
        code = source[:source.index('// Archive/tracker')]
        code += '\nconst state={interrupted:false,mic:true}; let stopped=0; function stopSpeech(){stopped++;}\n'
        code += 'console.log(JSON.stringify(' + json.dumps(list(cases)) + '.map(assistantControlIntent)));\n'
        code += "performAssistantControl('stop_speaking').then(r=>console.log(JSON.stringify({result:r,stopped,state})));"
        lines = subprocess.check_output(['node','-e',code],text=True).splitlines()
        for (text, expected), intent in zip(cases.items(),json.loads(lines[0])):
            with self.subTest(text=text):
                self.assertEqual(intent == 'stop_speaking', expected)
                controls = Controls()
                run = SimpleNamespace(id='test',user_text=text,cancel=threading.Event())
                run.emit = lambda event,data: controls.acknowledge(data['id'],run.id,{'status':'completed','active':False})
                if expected:
                    self.assertEqual(controls.request('stop_speaking',run)['status'],'completed')
                else:
                    with self.assertRaises(ValueError): controls.request('stop_speaking',run)
        result = json.loads(lines[1])
        self.assertEqual(result['stopped'],1)
        self.assertTrue(result['state']['interrupted'])
        self.assertTrue(result['state']['mic'])
        self.assertEqual(result['result']['status'],'completed')


if __name__ == '__main__': unittest.main()
