"""switch_over.py against synthetic installations only (no real data)."""
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import core_lock
import recovery
import switch_over
from store import Store
from test_recovery import ReadOnlyMedia


def snapshot(folder):
    # core.lock is the persistent (empty) Core lock file; holding it, not its existence, means ownership.
    return sorted((str(p.relative_to(folder)), p.stat().st_size) for p in Path(folder).rglob('*')
                  if p.is_file() and p.name != core_lock.LOCK_NAME)


class SwitchOverTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        # Old installation with saved memories and a generated document.
        self.old = base / 'old'
        (self.old / 'data' / 'generated').mkdir(parents=True)
        (self.old / 'server.py').write_text('# old code\n', encoding='utf-8')
        (self.old / 'personality.txt').write_text('Old personality.\n', encoding='utf-8')
        store = Store(self.old / 'data')
        store.put('memory', 'Favourite colour is blue')
        store.put('memory', 'Prefers short answers')
        (self.old / 'data' / 'generated' / 'report.txt').write_text('saved report', encoding='utf-8')
        result = recovery.Recovery(self.old, self.old / 'data', base / 'backups').create()
        self.archive = base / 'backups' / (result['id'] + '.zip')
        self.counts = result['database_counts']
        # New installation with test data, models and a log that must survive.
        self.new = base / 'new'
        self.data = self.new / 'data'
        (self.data / 'wake-models').mkdir(parents=True)
        (self.data / 'wake-models' / 'hey_jarvis.onnx').write_bytes(b'model')
        (self.data / 'logs').mkdir()
        (self.data / 'logs' / 'core.log').write_text('log', encoding='utf-8')
        Store(self.data).put('memory', 'test-only memory')
        (self.new / 'personality.txt').write_text('New personality.\n', encoding='utf-8')

    def test_dry_run_verifies_and_changes_nothing(self):
        before = snapshot(self.new)
        manifest, imported, skipped, replaced, config = switch_over.plan(self.archive, self.data, self.new)
        self.assertEqual(snapshot(self.new), before)
        self.assertIn('data/jarvis.sqlite3', imported)
        self.assertIn('jarvis.sqlite3', replaced)
        self.assertEqual(config['personality.txt'], 'differs')

    def test_apply_imports_memory_and_keeps_models_logs_and_previous_data(self):
        result = switch_over.apply(self.archive, self.data, self.new)
        self.assertEqual(result['database_counts'], self.counts)
        memories = [m['body'] for m in Store(self.data).items('memory')]
        self.assertIn('Favourite colour is blue', memories)
        self.assertNotIn('test-only memory', memories)
        self.assertEqual((self.data / 'generated' / 'report.txt').read_text(encoding='utf-8'), 'saved report')
        self.assertEqual((self.data / 'wake-models' / 'hey_jarvis.onnx').read_bytes(), b'model')
        self.assertEqual((self.data / 'logs' / 'core.log').read_text(encoding='utf-8'), 'log')
        aside = Path(result['previous_data_moved_to'])
        self.assertTrue((aside / 'jarvis.sqlite3').is_file())  # previous data kept, not deleted
        self.assertEqual((self.new / 'personality.txt').read_text(encoding='utf-8'), 'New personality.\n')
        self.assertFalse(any(p.name.startswith('.switchover-') for p in self.data.iterdir()))

    def test_personal_config_only_when_asked(self):
        result = switch_over.apply(self.archive, self.data, self.new, include_personal_config=True)
        self.assertEqual(result['personal_config_written'], ['personality.txt'])
        self.assertEqual((self.new / 'personality.txt').read_text(encoding='utf-8'), 'Old personality.\n')

    def test_installed_release_restores_personal_config_into_the_config_folder(self):
        home = self.new.parent / 'home'
        app = home / 'releases' / '1.0.0-abc' / 'app'  # an installed release's layout
        app.mkdir(parents=True)
        (home / 'config').mkdir()
        (app.parent / 'manifest.json').write_text('{"product": "JARVIS"}', encoding='utf-8')
        (app / 'personality.txt').write_text('Shipped default.\n', encoding='utf-8')
        manifest, imported, skipped, replaced, config = switch_over.plan(self.archive, self.data, app)
        self.assertEqual(config['personality.txt'], 'differs')  # the config folder has none yet
        result = switch_over.apply(self.archive, self.data, app, include_personal_config=True)
        self.assertEqual(result['personal_config_written'], ['personality.txt'])
        self.assertEqual((home / 'config' / 'personality.txt').read_text(encoding='utf-8'), 'Old personality.\n')
        self.assertEqual((app / 'personality.txt').read_text(encoding='utf-8'), 'Shipped default.\n')  # program files untouched

    def test_refuses_while_jarvis_is_running(self):
        running = core_lock.CoreLock(self.data)
        self.addCleanup(running.release)
        before = snapshot(self.new)
        with self.assertRaises(core_lock.CoreAlreadyRunning):
            switch_over.apply(self.archive, self.data, self.new)
        self.assertEqual(snapshot(self.new), before)

    def test_tampered_backup_is_refused_before_any_change(self):
        tampered = self.archive.with_name('tampered.zip')
        with zipfile.ZipFile(self.archive) as src, zipfile.ZipFile(tampered, 'w') as dst:
            for info in src.infolist():
                data = src.read(info.filename)
                dst.writestr(info, data + b'x' if info.filename == 'data/generated/report.txt' else data)
        before = snapshot(self.new)
        with self.assertRaises(ValueError):
            switch_over.apply(tampered, self.data, self.new)
        self.assertEqual(snapshot(self.new), before)

    def test_failure_after_placement_restores_previous_state(self):
        before = snapshot(self.new)
        real = recovery.check_database
        calls = []
        def failing(path):
            calls.append(path)
            if len(calls) > 1:  # first call is the archive verification; fail the post-import check
                raise ValueError('simulated failure')
            return real(path)
        with patch.object(recovery, 'check_database', side_effect=failing), self.assertRaises(ValueError):
            switch_over.apply(self.archive, self.data, self.new)
        self.assertEqual(snapshot(self.new), before)
        self.assertEqual([m['body'] for m in Store(self.data).items('memory')], ['test-only memory'])

    def on_disc(self):
        disc = self.new.parent / 'disc'
        disc.mkdir()
        shutil.copyfile(self.archive, disc / self.archive.name)
        return disc, disc / self.archive.name

    def test_dry_run_from_a_writable_folder_creates_no_backup_folder(self):
        switch_over.plan(self.archive, self.data, self.new)
        self.assertFalse(recovery.default_folder(self.new, self.data).exists())

    def test_dry_run_and_import_from_read_only_media(self):
        # Gate 18 incident 04: the backup sat on a read-only disc and the check never returned.
        disc, archive = self.on_disc()
        before = snapshot(self.new)
        with ReadOnlyMedia(disc):
            switch_over.plan(archive, self.data, self.new)
            self.assertEqual(snapshot(self.new), before)
            result = switch_over.apply(archive, self.data, self.new)
        self.assertEqual(result['database_counts'], self.counts)
        self.assertIn('Favourite colour is blue', [m['body'] for m in Store(self.data).items('memory')])
        fallback = recovery.default_folder(self.new, self.data)
        self.assertEqual(list(fallback.iterdir()), [])  # used for the check, nothing left in it
        self.assertEqual([p.name for p in disc.iterdir()], [archive.name])

    def test_installed_layout_dry_run_from_a_disc_adds_only_an_empty_backup_folder(self):
        disc, archive = self.on_disc()
        home = self.new.parent / 'home'
        app = home / 'releases' / '1.0.0-abc' / 'app'
        app.mkdir(parents=True)
        (app.parent / 'manifest.json').write_text('{"product": "JARVIS"}', encoding='utf-8')
        Store(home / 'data').put('memory', 'test-only memory')
        before = snapshot(home)
        with ReadOnlyMedia(disc):
            switch_over.plan(archive, home / 'data', app)
        self.assertEqual(snapshot(home), before)
        self.assertEqual(sorted(p.name for p in home.iterdir()), ['data', 'data-backups', 'releases'])
        self.assertEqual(list((home / 'data-backups').iterdir()), [])

    def test_data_folder_refusing_folders_fails_fast_and_changes_nothing(self):
        before = snapshot(self.new)
        with ReadOnlyMedia(self.data), self.assertRaises(recovery.NoWorkFolder) as caught:
            switch_over.apply(self.archive, self.data, self.new)
        self.assertEqual(str(caught.exception), switch_over.DATA_FOLDER_REFUSED)
        self.assertEqual(snapshot(self.new), before)
        core_lock.CoreLock(self.data).release()  # the Core lock was released

    def test_command_line_answers_plainly_when_the_backup_cannot_be_checked(self):
        disc, archive = self.on_disc()
        out = io.StringIO()
        # From the command line the fallback is the backup folder beside this data folder; refuse both
        # (computed as switch_over computes it, so a short-name or junction TEMP gives the same path).
        with ReadOnlyMedia(disc, recovery.default_folder(switch_over.ROOT, self.data)), contextlib.redirect_stdout(out):
            code = switch_over.main(['--archive', str(archive), '--data', str(self.data)])
        self.assertEqual(code, 2)
        answer = json.loads(out.getvalue())
        self.assertEqual(answer['status'], 'refused')
        self.assertIn('Copy the backup .zip to an ordinary folder', answer['reason'])


if __name__ == '__main__':
    unittest.main()
