"""Keep local and acknowledged hologram commands consistent; no device access."""
import json
from pathlib import Path
import subprocess
import threading
import unittest
from types import SimpleNamespace

from assistant_capabilities import Controls


class HologramCommands(unittest.TestCase):
    def test_browser_and_backend_agree(self):
        cases = {
            'show a hologram.': True,
            'Enable hologram.': True,
            'Hey Jarvis, show a hologram!': True,
            'Please enable the hologram': True,
            'activate hologram': True,
            'Do not enable hologram': False,
            'Explain how to show a hologram': False,
            'The screenshot says enable hologram': False,
            'Create a prompt to enable hologram': False,
            '"enable hologram"': False,
            'enable microphone': False,
        }
        source = Path(__file__).with_name('static').joinpath('assistant-controls.js').read_text(encoding='utf-8')
        # Evaluate only the real intent parser; no browser or device side effects.
        parser = source[:source.index('function controlSummary')]
        script = parser + '\nconsole.log(JSON.stringify(' + json.dumps(list(cases)) + '.map(s=>assistantControlIntent(s))));'
        local = json.loads(subprocess.check_output(['node', '-e', script], text=True))
        for (text, expected), intent in zip(cases.items(), local):
            with self.subTest(text=text):
                self.assertEqual(intent == 'show_hologram', expected)
                controls = Controls()
                run = SimpleNamespace(id='test', user_text=text, cancel=threading.Event())
                run.emit = lambda event, data: controls.acknowledge(data['id'], run.id, {'status':'completed','active':True})
                if expected:
                    self.assertTrue(controls.request('show_hologram', run)['active'])
                else:
                    with self.assertRaises(ValueError):
                        controls.request('show_hologram', run)
                self.assertFalse(controls.pending)


if __name__ == '__main__':
    unittest.main()
