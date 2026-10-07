"""Item E (docs/PHONE-ACCESS-1.0.17.md section 5): every saved thing records the release it was saved under; the
Memory page shows it; the model is told it with one rule; an older database gains the column; a restored backup
keeps or marks it."""
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import memory
import providers
import runtime_paths
from server import App, Run
from store import Store
from test_device_gateway import DONE, ENV


class StampTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)

    def test_every_saved_thing_is_stamped_and_an_edit_restamps(self):
        store = Store(self.folder)
        self.assertEqual(store.release, 'development')
        first = store.put('memory', 'I prefer short answers')
        store.release = '1.0.17-abc'
        store.put('note', 'Buy milk')
        store.put('task', 'Call the bank')
        rows = {r['body']: r['release'] for kind in ('memory', 'note', 'task') for r in store.items(kind)}
        self.assertEqual(rows, {'I prefer short answers': 'development', 'Buy milk': '1.0.17-abc', 'Call the bank': '1.0.17-abc'})
        store.put('memory', 'I prefer very short answers', first['id'])
        self.assertEqual(store.items('memory')[0]['release'], '1.0.17-abc')   # edited now: saved under the release that runs now
        self.assertEqual(memory.stamped(store.items('memory')[0]), 'I prefer very short answers [saved under 1.0.17-abc]')
        self.assertEqual(memory.stamped({'body': 'old', 'release': None}), 'old')

    def test_an_older_database_gains_the_column_and_its_rows_stay_unstamped(self):
        path = self.folder / 'jarvis.sqlite3'
        db = sqlite3.connect(path)   # closed by hand: a 'with' only commits, and an open file cannot be cleaned up on Windows
        db.execute('CREATE TABLE items (id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL, item_key TEXT, category TEXT, source TEXT, confidence REAL NOT NULL DEFAULT 1.0)')
        db.execute("INSERT INTO items VALUES ('a','memory','JARVIS cannot send mail',1.0,1.0,'text:jarvis cannot send mail','fact','user',1.0)")
        db.commit()
        db.close()
        store = Store(self.folder)
        with store.connect() as db:
            self.assertIn('release', {row[1] for row in db.execute('PRAGMA table_info(items)')})
        (old,) = store.items('memory')
        self.assertIsNone(old['release'])
        self.assertEqual(memory.stamped(old), 'JARVIS cannot send mail')
        store.release = '1.0.17-abc'
        store.put('memory', 'JARVIS can send mail after approval')
        self.assertEqual({r['body']: r['release'] for r in store.items('memory')}, {'JARVIS cannot send mail': None, 'JARVIS can send mail after approval': '1.0.17-abc'})

    def test_a_restored_backup_keeps_its_stamp_or_is_marked(self):
        store = Store(self.folder)
        store.release = '1.0.17-abc'
        store.import_data({'items': [{'kind': 'memory', 'body': 'from 1.0.16', 'id': 'x1', 'release': '1.0.16-fccde24e2cc6'},
                                     {'kind': 'memory', 'body': 'from long ago', 'id': 'x2'}]})
        self.assertEqual({r['body']: r['release'] for r in store.items('memory')}, {'from 1.0.16': '1.0.16-fccde24e2cc6', 'from long ago': 'pre-1.0.17 backup'})
        # A backup's stamp is checked: blank or not text means a backup made before 1.0.17; a long one is cut.
        store.import_data({'items': [{'kind': 'memory', 'body': 'blank', 'id': 'x3', 'release': '   '}, {'kind': 'memory', 'body': 'number', 'id': 'x4', 'release': 7},
                                     {'kind': 'memory', 'body': 'long', 'id': 'x5', 'release': 'r' * 200}]})
        stamps = {r['body']: r['release'] for r in store.items('memory')}
        self.assertEqual((stamps['blank'], stamps['number'], len(stamps['long'])), ('pre-1.0.17 backup', 'pre-1.0.17 backup', 80))

    def test_the_core_stamps_with_its_release_and_tells_the_model_the_rule(self):
        app = App(str(self.folder))
        self.assertTrue(app.store.release.startswith('development ') or app.store.release == runtime_paths.release_id())
        stamp = app.store.release   # "development <revision>" in the repository; the release id in the release regression
        app.store.put('memory', 'I prefer short answers')
        app.store.release = '1.0.11-old'
        app.store.put('memory', 'JARVIS cannot read mail')
        run = Run('stamp-test')
        app.runs[run.id] = run
        bodies = []
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda url, body=None, headers=None, **k: (bodies.append(body), DONE)[1]):
            app.work(run, 'Can you read my mail? Remember my preference.', None)
        context = json.loads(bodies[0]['messages'][1]['content'].split(': ', 1)[1])
        self.assertIn('JARVIS cannot read mail [saved under 1.0.11-old]', context['saved_facts'])
        self.assertIn('I prefer short answers [saved under ' + stamp + ']', context['saved_facts'])
        self.assertEqual(context['saved_facts_note'], memory.STAMP_NOTE)
        self.assertIn('newer release is right', context['saved_facts_note'])
        # The Memory page gets the stamp with each row.
        self.assertTrue(all('release' in row for row in app.state()['memory']))


if __name__ == '__main__':
    unittest.main()


class ReviewTests(unittest.TestCase):
    """The review's cases: every edit path re-stamps, a client cannot choose a stamp, the export carries it."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)

    def test_a_re_said_memory_and_a_correction_through_jarvis_take_the_release_that_runs_now(self):
        import assistant_capabilities
        store = Store(self.folder)
        store.release = '1.0.11-old'
        saved = store.put('memory', 'I prefer short answers')
        store.put('memory', 'JARVIS cannot read mail')
        store.release = '1.0.17-abc'
        store.put('memory', 'I prefer short answers')   # the same fact said again: one row, re-stamped
        self.assertEqual([(r['body'], r['release']) for r in store.items('memory') if r['body'] == 'I prefer short answers'], [('I prefer short answers', '1.0.17-abc')])
        self.assertEqual(len(store.items('memory')), 2)
        old = next(r for r in store.items('memory') if r['body'] == 'JARVIS cannot read mail')
        assistant_capabilities.manage_memory(store, 'update', old['id'], 'JARVIS can read mail since 1.0.17')
        corrected = next(r for r in store.items('memory') if r['id'] == old['id'])
        self.assertEqual((corrected['body'], corrected['release']), ('JARVIS can read mail since 1.0.17', '1.0.17-abc'))
        store.save_settings({'name': 'Ben'})   # the derived name row too
        store.put('memory', 'My name is Benjamin')
        store.release = '1.0.18-next'
        store.save_settings({'name': 'Benjamin T'})
        name_row = next(r for r in store.items('memory') if r['body'].startswith('Preferred name:'))
        self.assertEqual(name_row['release'], '1.0.18-next')

    def test_the_note_comes_only_with_a_stamped_fact(self):
        app = App(str(self.folder))
        run = Run('note-test')
        app.runs[run.id] = run
        bodies = []
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda url, body=None, headers=None, **k: (bodies.append(body), DONE)[1]):
            app.work(run, 'Hello there', None)
        context = json.loads(bodies[0]['messages'][1]['content'].split(': ', 1)[1])
        self.assertEqual(context['saved_facts'], [])
        self.assertNotIn('saved_facts_note', context)


class RouteTests(unittest.TestCase):
    def test_a_client_cannot_choose_the_stamp_and_the_export_carries_it(self):
        from test_device_gateway import DeviceCase
        case = DeviceCase('setUp')   # the harness, used for its owner routes
        case.setUp()
        try:
            status, saved = case.owner('/api/item', {'kind': 'memory', 'body': 'From the window', 'release': 'chosen by a client'})
            self.assertEqual(status, 200, saved)
            (row,) = case.app.store.items('memory')
            self.assertEqual(row['release'], case.app.store.release)
            status, exported = case.owner('/api/export')
            self.assertEqual(status, 200)
            self.assertEqual([r['release'] for r in exported['items']], [case.app.store.release])
        finally:
            case.doCleanups()
