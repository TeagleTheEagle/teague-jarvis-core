import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import development
from server import App, Run


class DevelopmentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.file = self.root / 'wake.py'
        self.original = 'threshold = 0.38\n'
        self.file.write_text(self.original, encoding='utf-8')
        self.app = App(self.root / 'store')
        self.patcher = patch('server.ROOT', self.root)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def proposal(self, run=None):
        return self.app.tool('development_edit', dict(path='wake.py', old='0.38', new='0.40', reason='Test exact edit'), run)

    def test_approve_then_reviewed_rollback(self):
        p = self.proposal()
        self.assertEqual(self.file.read_text(), self.original)
        self.assertIn('-threshold = 0.38', p['diff'])
        self.assertEqual(self.app.approvals[p['approval']['id']]['preview']['diff'], p['diff'])
        self.app.approve(p['approval']['id'], True)
        self.assertEqual(self.file.read_text(), 'threshold = 0.40\n')
        with self.assertRaises(ValueError):
            self.app.approve(p['approval']['id'], True)
        undo = self.app.tool('development_rollback', {'proposal': p['proposal']})
        self.assertEqual(self.file.read_text(), 'threshold = 0.40\n')
        self.app.approve(undo['approval']['id'], True)
        self.assertEqual(self.file.read_text(), self.original)
        self.assertIn('Python syntax', development.history(self.root)['changes'][0]['validation'])

    def test_denied_expired_and_cancelled_never_apply(self):
        p = self.proposal()
        self.app.approve(p['approval']['id'], False)
        p = self.proposal()
        self.app.approvals[p['approval']['id']]['expires'] = 0
        with self.assertRaises(ValueError): self.app.approve(p['approval']['id'], True)
        run = Run('test'); self.app.runs[run.id] = run
        p = self.proposal(run); run.cancel.set()
        with self.assertRaises(ValueError): self.app.approve(p['approval']['id'], True)
        self.assertEqual(self.file.read_text(), self.original)

    def test_changed_source_and_candidate_rejected(self):
        p = self.proposal(); self.file.write_text('threshold = 0.50\n')
        with self.assertRaises(ValueError): self.app.approve(p['approval']['id'], True)
        self.file.write_text(self.original); p = self.proposal()
        (self.root/'data/development'/p['proposal']/'candidate.txt').write_text('threshold = 99\n')
        with self.assertRaises(ValueError): self.app.approve(p['approval']['id'], True)
        self.assertEqual(self.file.read_text(), self.original)

    def test_rollback_cannot_erase_later_work(self):
        p = self.proposal(); self.app.approve(p['approval']['id'], True)
        self.file.write_text('threshold = 0.55\n')
        with self.assertRaises(ValueError): development.rollback(self.root, p['proposal'])
        self.assertEqual(self.file.read_text(), 'threshold = 0.55\n')

    def test_invalid_syntax_and_forbidden_sources(self):
        with self.assertRaises(ValueError): development.prepare(self.root, 'wake.py', 'def broken(', 'test')
        for path in ('.env', 'server.py', '../wake.py', 'desktop/main.cjs'):
            with self.assertRaises(ValueError): development.read(self.root, path)
        with self.assertRaises(ValueError): development.edit(self.root, 'wake.py', 'missing', 'x', 'test')
        self.assertEqual(self.file.read_text(), self.original)
