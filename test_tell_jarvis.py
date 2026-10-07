"""tools/host/tell_jarvis.py against a test Core: pairing with the code the owner read, the update saved as a memory
through the device route once the owner's tick is on, the refusals in plain words. The live JARVIS is never reached:
every call carries --url of the test server."""
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_device_gateway import DeviceCase

sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools' / 'host'))
try:
    import tell_jarvis  # noqa: E402
except ImportError:  # tools/host is not shipped in a release: the release regression skips this module
    raise unittest.SkipTest('tools/host/tell_jarvis.py is not shipped in a release')


class TellJarvisTests(DeviceCase):
    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.key_file = str(Path(folder.name) / 'claude-device.json')

    def run_tool(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with patch('sys.stdout', new=out), patch('sys.stderr', new=err):
            code = tell_jarvis.main([*argv, '--url', self.url, '--credential-file', self.key_file])
        return code, out.getvalue().strip(), err.getvalue().strip()

    def test_pair_say_and_the_refusals(self):
        # Not paired yet: said plainly, nothing reached.
        code, out, err = self.run_tool('say', 'Item A is done')
        self.assertEqual(code, 1)
        self.assertIn('Not paired yet', err)
        # The owner starts the pairing on the PC and reads the code; the tool pairs and keeps the key beside the repo.
        status, started = self.owner('/api/devices', {'action': 'pair', 'name': 'Claude Code', 'kind': 'computer'})
        self.assertEqual(status, 200, started)
        self.assertEqual(self.run_tool('pair', '12')[0], 1)  # not a code
        code, out, err = self.run_tool('pair', *started['code'].split())
        self.assertEqual((code, err), (0, ''), (out, err))
        self.assertIn('Paired as Claude Code', out)
        self.assertIn('tick "May save memories and tasks"', out)
        saved = json.loads(Path(self.key_file).read_text(encoding='utf-8'))
        ident = saved['device_id']
        self.assertEqual(self.rows()[ident]['name'], 'Claude Code')
        # Without the owner's tick the update is refused before anything is sent.
        code, out, err = self.run_tool('say', 'Item A is done')
        self.assertEqual(code, 1)
        self.assertIn('may not save memories', err)
        self.assertEqual(self.app.store.items('memory'), [])
        # With the tick: the update is saved as a memory, by the Core itself (no model is asked).
        self.owner('/api/devices', {'action': 'writes', 'id': ident, 'allowed': True})
        with patch.dict(os.environ, {}, clear=True):
            code, out, err = self.run_tool('say', 'Item A, approve from the pocket, is committed as 7b03879.')
        self.assertEqual((code, err), (0, ''), (out, err))
        memories = [m['body'] for m in self.app.store.items('memory')]
        self.assertEqual(len(memories), 1)
        self.assertIn('Claude Code reports: Item A, approve from the pocket, is committed as 7b03879.', memories[0])
        self.assertTrue(out)
        # status shows what the device may do.
        code, out, err = self.run_tool('status')
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)['writes'])
        # Revoked on the PC: refused plainly.
        self.owner('/api/devices', {'action': 'revoke', 'id': ident})
        code, out, err = self.run_tool('say', 'Another update')
        self.assertEqual(code, 1)
        self.assertIn('Pair this device again', err)

    def test_no_core_is_said_plainly(self):
        out, err = io.StringIO(), io.StringIO()
        with patch('sys.stdout', new=out), patch('sys.stderr', new=err), patch.object(tell_jarvis, 'core_url', return_value=None):
            code = tell_jarvis.main(['status', '--credential-file', self.key_file])
        self.assertEqual(code, 1)
        self.assertIn('not running', err.getvalue())


if __name__ == '__main__':
    unittest.main()
