import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from server import App, Run


class AutomaticActionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'static').mkdir()
        (self.root / 'static/pro.css').write_text('body { color: white; }')
        self.app = App(self.root / 'store')

    def tearDown(self):
        self.temp.cleanup()

    def test_launch_immediate_without_approval(self):
        with patch('actions.launch_app', return_value={'status':'launched', 'app':'calculator'}) as launch:
            result = self.app.tool('open_app', {'app':'calculator'})
        launch.assert_called_once_with('calculator')
        self.assertEqual(self.app.describe('open_app', result), 'calculator launched.')
        self.assertFalse(self.app.approvals)

    def test_change_and_rollback_retain_backup(self):
        # Until 1.0.15 a style change applied with no approval. Since 1.0.15 every change JARVIS makes to
        # itself asks first (permissions.py; master document section 6), the style included.
        with patch('server.ROOT', self.root), patch('runtime_paths.installed', return_value=False):
            result = self.app.tool('development_propose', {'path':'static/pro.css', 'content':'body { color: cyan; }', 'reason':'test'})
            self.assertEqual(result['status'], 'awaiting approval')
            self.assertEqual((self.root/'static/pro.css').read_text(), 'body { color: white; }')
            self.assertEqual(self.app.approve(result['approval']['id'], True)['status'], 'applied')
            self.assertEqual((self.root/'static/pro.css').read_text(), 'body { color: cyan; }')
            undo = self.app.tool('development_rollback', {'proposal':result['proposal']})
            self.assertEqual((self.root/'static/pro.css').read_text(), 'body { color: cyan; }')
            self.app.approve(undo['approval']['id'], True)
            self.assertEqual((self.root/'static/pro.css').read_text(), 'body { color: white; }')
        self.assertFalse(self.app.approvals)

    def test_unsupported_and_cancelled_actions_stay_blocked(self):
        with self.assertRaises(ValueError):
            self.app.tool('open_app', {'app':'powershell'})
        with self.assertRaises(ValueError):
            self.app.tool('development_propose', {'path':'.env', 'content':'x', 'reason':'test'})
        run = Run('test'); run.cancel.set()
        with patch('actions.launch_app') as launch, self.assertRaises(ValueError):
            self.app.tool('open_app', {'app':'calculator'}, run)
        launch.assert_not_called()
