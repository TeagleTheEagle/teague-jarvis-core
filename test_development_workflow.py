import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import development
from server import App, Run


class DevelopmentWorkflowTests(unittest.TestCase):
    """A program file, running from the source folder: changed only after the owner's approval."""
    installed = False

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'program'
        self.root.mkdir()
        self.file = self.root / 'wake.py'
        self.original = 'threshold = 0.38\n'
        self.file.write_text(self.original, encoding='utf-8')
        (self.root / 'personality.txt').write_text('You are JARVIS.\n', encoding='utf-8')
        self.app = App(Path(self.temp.name) / 'store')
        self.patchers = [patch('server.ROOT', self.root),
                         # The packaged regression runs with JARVIS_DATA_DIR set; these tests say which case they mean.
                         patch('runtime_paths.installed', return_value=self.installed)]
        for patcher in self.patchers:
            patcher.start()
        self.where = self.app.development_layout()

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()
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
        self.assertIn('Python syntax', development.history(self.where)['changes'][0]['validation'])

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
        (self.where.data/'development'/p['proposal']/'candidate.txt').write_text('threshold = 99\n')
        with self.assertRaises(ValueError): self.app.approve(p['approval']['id'], True)
        self.assertEqual(self.file.read_text(), self.original)

    def test_rollback_cannot_erase_later_work(self):
        p = self.proposal(); self.app.approve(p['approval']['id'], True)
        self.file.write_text('threshold = 0.55\n')
        with self.assertRaises(ValueError): development.rollback(self.where, p['proposal'])
        self.assertEqual(self.file.read_text(), 'threshold = 0.55\n')

    def test_invalid_syntax_and_forbidden_sources(self):
        with self.assertRaises(ValueError): development.prepare(self.where, 'wake.py', 'def broken(', 'test')
        for path in ('.env', 'server.py', '../wake.py', 'desktop/main.cjs', 'permissions.py', 'development.py'):
            with self.assertRaises(ValueError): development.read(self.where, path)
        with self.assertRaises(ValueError): development.edit(self.where, 'wake.py', 'missing', 'x', 'test')
        self.assertEqual(self.file.read_text(), self.original)

    def test_a_bare_folder_still_means_the_source_layout(self):
        # improvement_experiment.py and repair_trial.py call the module with a folder only.
        p = development.prepare(self.root, 'wake.py', 'threshold = 0.41\n', 'test')
        self.assertTrue((self.root / 'data' / 'development' / p['proposal'] / 'candidate.txt').is_file())
        self.assertTrue(p['requires_approval'])

    def test_personality_and_style_ask_first_too(self):
        # Until 1.0.15 these two applied with no approval (development.IMMEDIATE).
        p = self.app.tool('development_edit', dict(path='personality.txt', old='JARVIS', new='JARVIS, and brief', reason='test'))
        self.assertEqual(p['status'], 'awaiting approval')
        self.assertEqual((self.root / 'personality.txt').read_text(), 'You are JARVIS.\n')
        style = self.app.tool('development_propose', dict(path='owner-style.css', content='body{font-size:18px}\n', reason='bigger text'))
        self.assertEqual(style['status'], 'awaiting approval')
        self.assertFalse((self.where.config / 'owner-style.css').exists())
        self.app.approve(style['approval']['id'], True)
        self.assertEqual((self.where.config / 'owner-style.css').read_text(), 'body{font-size:18px}\n')
        for bad in ('body{background:url(http://x/y.png)}', '@import "x.css";', 'body{'):
            with self.assertRaises(ValueError): development.prepare(self.where, 'owner-style.css', bad, 'test')


class InstalledDevelopmentTests(DevelopmentWorkflowTests):
    """An installed JARVIS: the release folder is never written; the owner's two files live in the config folder."""
    installed = True

    def setUp(self):
        super().setUp()
        # The install layout: <home>/releases/<id>/app is the program, <home>/config the owner's folder.
        self.config = Path(self.temp.name) / 'config'
        self.config.mkdir()
        self.config_patch = patch('runtime_paths.config_dir_for', return_value=self.config)
        self.config_patch.start()
        self.where = self.app.development_layout()

    def tearDown(self):
        self.config_patch.stop()
        super().tearDown()

    def program_files(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_approve_then_reviewed_rollback(self):
        before = self.program_files()
        p = self.proposal()
        self.assertEqual(p['status'], development.PROPOSAL_ONLY)
        self.assertNotIn('approval', p)
        self.assertEqual(self.app.approvals, {})
        with self.assertRaises(ValueError): development.apply(self.where, p['proposal'])
        with self.assertRaises(ValueError): development.rollback(self.where, p['proposal'])
        self.assertEqual(self.program_files(), before)
        row = development.history(self.where)['changes'][0]
        self.assertEqual((row['status'], row['can_undo']), (development.PROPOSAL_ONLY, False))

    def test_denied_expired_and_cancelled_never_apply(self):
        self.assertNotIn('approval', self.proposal())

    def test_changed_source_and_candidate_rejected(self):
        # Even a proposal file edited by hand to look approved is refused for a program file.
        p = self.proposal()
        meta = self.where.data / 'development' / p['proposal'] / 'meta.json'
        meta.write_text(meta.read_text().replace(development.PROPOSAL_ONLY, 'staged'))
        with self.assertRaises(ValueError): development.apply(self.where, p['proposal'])
        self.assertEqual(self.file.read_text(), self.original)

    def test_rollback_cannot_erase_later_work(self):
        pass  # nothing is ever applied to a program file here, so there is nothing to roll back

    def test_a_bare_folder_still_means_the_source_layout(self):
        pass  # covered by the source-folder case

    def test_personality_and_style_ask_first_too(self):
        before = self.program_files()
        p = self.app.tool('development_edit', dict(path='personality.txt', old='JARVIS', new='JARVIS, and brief', reason='test'))
        self.assertEqual(p['status'], 'awaiting approval')
        self.assertFalse((self.config / 'personality.txt').exists())
        self.app.approve(p['approval']['id'], True)
        self.assertEqual((self.config / 'personality.txt').read_text(), 'You are JARVIS, and brief.\n')
        self.assertEqual(development.read(self.where, 'personality.txt'), 'You are JARVIS, and brief.\n')
        style = self.app.tool('development_propose', dict(path='owner-style.css', content='body{font-size:18px}\n', reason='bigger text'))
        self.app.approve(style['approval']['id'], True)
        self.assertEqual((self.config / 'owner-style.css').read_text(), 'body{font-size:18px}\n')
        self.assertEqual(self.program_files(), before)  # the installed program is exactly as it was tested
        # Undo goes back to the personality the program ships with: no private copy is left behind,
        # so a later release's wording applies again.
        undo = self.app.tool('development_rollback', {'proposal': p['proposal']})
        self.app.approve(undo['approval']['id'], True)
        self.assertFalse((self.config / 'personality.txt').exists())
        undo = self.app.tool('development_rollback', {'proposal': style['proposal']})
        self.app.approve(undo['approval']['id'], True)
        self.assertFalse((self.config / 'owner-style.css').exists())
        self.assertEqual(self.program_files(), before)
        self.assertFalse((self.root / 'data').exists())  # proposals are kept with the data, not in the program
        self.assertTrue((self.app.store.root / 'development').is_dir())


if __name__ == '__main__':
    unittest.main()
