"""Automatic backups connected in the Core (release 1.0.15, scope item 6; docs/AUTOMATIC-BACKUPS.md): where the
owner's choice is kept, the owner's routes, when a backup is made and when it waits, and the quiet clock.
The schedule and the thinning themselves are tested in test_auto_backup.py.
"""
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import auto_backup
import permissions
import server
from server import App, Handler, Run, Server
from store import Store


class CoreCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data, self.drive = Path(self.temp.name) / 'data', Path(self.temp.name) / 'backup-drive'
        self.data.mkdir()
        self.drive.mkdir()
        self.app = App(str(self.data))
        self.backups = self.drive / auto_backup.SUBFOLDER

    def turn_on(self, **more):
        return self.app.auto_backup_action({'action': 'configure', 'folder': str(self.drive), 'every': 'day', 'at': '12:00', **more})

    def rows(self, action):
        return [row['status'] for row in self.app.store.logs() if row['action'] == action]


class CoreTests(CoreCase):
    def test_off_until_the_owner_chooses_a_folder(self):
        status = self.app.auto_backup.status()
        self.assertEqual((status['enabled'], status['folder'], status['next_due'], status['overdue']), (False, '', None, False))
        self.assertIsNone(self.app.auto_backup.run_if_due())
        self.assertIsNone(self.app.store.auto_backup_state())
        self.assertFalse(self.backups.exists())
        with self.assertRaises(ValueError):
            self.app.auto_backup_action({'action': 'run'})  # nothing to back up to yet

    def test_the_owner_turns_it_on_and_the_first_backup_is_made_checked_and_recorded(self):
        status = self.turn_on()
        self.assertEqual((status['enabled'], status['folder_reachable'], status['backups_in']), (True, True, str(self.backups)))
        made = self.app.auto_backup.run_if_due()  # never made one: the first is due at once
        self.assertEqual((made['last_error'], made['kept'], made['overdue']), ('', 1, False))
        archives = list(self.backups.glob('*.zip'))
        self.assertEqual([p.stem for p in archives], [made['last_id']])
        self.assertIsNone(self.app.auto_backup.run_if_due())  # not again until tomorrow's time
        self.assertEqual(self.rows('automatic backups'), ['on: day'])
        self.assertEqual(self.rows('automatic backup'), ['verified'])
        # The choice and the record survive a restart of the Core.
        again = App(str(self.data)).auto_backup.status()
        self.assertEqual((again['enabled'], again['folder'], again['last_id'], again['kept']), (True, str(self.drive), made['last_id'], 1))

    def test_it_waits_while_jarvis_answers_and_while_the_emergency_stop_holds(self):
        self.turn_on()
        busy = Run('c')
        self.app.runs[busy.id] = busy
        self.assertIsNone(self.app.auto_backup.run_if_due())
        with self.assertRaises(ValueError) as refused:
            self.app.auto_backup_action({'action': 'run'})
        self.assertIn('answering a question', str(refused.exception))
        busy.done = True
        self.app.emergency_stop('pc', 'test')
        self.assertIsNone(self.app.auto_backup.run_if_due())
        with self.assertRaises(ValueError) as refused:
            self.app.auto_backup_action({'action': 'run'})
        self.assertEqual(str(refused.exception), permissions.STOPPED_MESSAGE)
        self.assertEqual(list(self.backups.glob('*.zip')), [])
        self.app.resume('pc')
        self.assertEqual(self.app.auto_backup_action({'action': 'run'})['kept'], 1)  # BACK UP NOW

    def test_turning_off_keeps_the_folder_and_the_backups(self):
        self.turn_on()
        self.app.auto_backup.run_if_due()
        status = self.app.auto_backup_action({'action': 'off'})
        self.assertEqual((status['enabled'], status['folder'], status['kept'], status['next_due']), (False, str(self.drive), 1, None))
        self.assertEqual(len(list(self.backups.glob('*.zip'))), 1)
        self.assertIsNone(self.app.auto_backup.run_if_due())
        self.assertEqual(self.rows('automatic backups'), ['off', 'on: day'])

    def test_what_the_owner_may_send_is_checked(self):
        for body in ({'action': 'configure', 'folder': 'relative/folder', 'every': 'day', 'at': '12:00'},
                     {'action': 'configure', 'folder': str(self.drive), 'every': 'hour', 'at': '12:00'},
                     {'action': 'configure', 'folder': str(self.drive), 'every': 'day', 'at': 'noon'},
                     {'action': 'configure', 'folder': str(self.drive / 'not-there'), 'every': 'day', 'at': '12:00'},
                     {'action': 'configure', 'folder': str(self.data / 'inside-the-data'), 'every': 'day', 'at': '12:00'},
                     {'action': 'configure', 'folder': str(self.drive), 'every': 'day', 'at': '12:00', 'enabled': True},
                     {'action': 'delete-everything'}, {}):
            with self.assertRaises(ValueError, msg=str(body)):
                self.app.auto_backup_action(body)
        self.assertFalse(self.app.auto_backup.status()['enabled'])

    def test_the_choice_is_out_of_reach_of_settings_export_and_a_restored_json_backup(self):
        self.turn_on()
        store = self.app.store
        self.assertNotIn('auto_backup', store.settings())
        with self.assertRaises(ValueError):
            store.save_settings({'auto_backup': {'enabled': False}})
        store.import_data({'settings': [{'key': 'auto_backup', 'value': json.dumps({'enabled': True, 'folder': 'C:/somewhere/else'})}], 'items': []})
        self.assertEqual(Store(self.data).auto_backup_state()['folder'], str(self.drive))
        with store.connect() as db:  # an unreadable record reads as "nothing chosen": off
            db.execute("INSERT OR REPLACE INTO control VALUES ('auto_backup','not json')")
        self.assertFalse(App(str(self.data)).auto_backup.status()['enabled'])


class ClockTests(CoreCase):
    def test_the_core_looks_about_once_a_minute_and_a_failed_look_does_not_stop_the_clock(self):
        looks, stop = [], threading.Event()

        def look():
            looks.append(time.monotonic())
            if len(looks) == 2:
                raise RuntimeError('a look that fails')
            if len(looks) >= 4:
                stop.set()

        with patch.object(self.app.auto_backup, 'run_if_due', side_effect=look):
            thread = server.start_auto_backups(self.app, first=0.01, every=0.01, stop=stop)
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(looks), 4)
        self.assertTrue(thread.daemon)  # it never keeps the Core from closing

    def test_a_backup_is_made_by_the_clock_when_one_is_due(self):
        self.turn_on()
        stop = threading.Event()
        thread = server.start_auto_backups(self.app, first=0.01, every=0.05, stop=stop)
        deadline = time.monotonic() + 30
        while not list(self.backups.glob('*.zip')) and time.monotonic() < deadline:
            time.sleep(0.05)
        stop.set()
        thread.join(30)
        self.assertEqual(len(list(self.backups.glob('*.zip'))), 1)


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data, self.drive = Path(self.temp.name) / 'data', Path(self.temp.name) / 'backup-drive'
        self.data.mkdir()
        self.drive.mkdir()
        self.server = Server(('127.0.0.1', 0), Handler)
        self.server.app = App(str(self.data))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def req(self, path, data=None, signed_in=True):
        headers = {'Content-Type': 'application/json', **({'Cookie': 'jarvis_session=' + self.server.app.session} if signed_in else {})}
        request = urllib.request.Request(self.url + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_only_the_signed_in_owner_reads_and_changes_it(self):
        self.assertEqual(self.req('/api/auto-backup', signed_in=False)[0], 401)
        self.assertEqual(self.req('/api/auto-backup', {'action': 'configure', 'folder': str(self.drive), 'every': 'day', 'at': '12:00'}, signed_in=False)[0], 401)
        status, off = self.req('/api/auto-backup')
        self.assertEqual((status, off['enabled']), (200, False))
        status, on = self.req('/api/auto-backup', {'action': 'configure', 'folder': str(self.drive), 'every': 'week', 'at': '08:30'})
        self.assertEqual((status, on['enabled'], on['every'], on['at']), (200, True, 'week', '08:30'))
        status, refused = self.req('/api/auto-backup', {'action': 'configure', 'folder': 'nowhere', 'every': 'day', 'at': '12:00'})
        self.assertEqual(status, 400)
        self.assertIn('full path', refused['error'])
        status, made = self.req('/api/auto-backup', {'action': 'run'})
        self.assertEqual((status, made['kept'], made['last_error']), (200, 1, ''))
        self.assertNotIn('auto_backup', json.dumps(self.req('/api/export')[1]))

    def test_an_automatic_backup_is_listed_and_test_restored_like_any_other(self):
        self.assertEqual(self.req('/api/recovery', {'action': 'list', 'where': 'automatic'})[0], 400)  # no folder chosen yet
        self.req('/api/auto-backup', {'action': 'configure', 'folder': str(self.drive), 'every': 'day', 'at': '12:00'})
        made = self.req('/api/auto-backup', {'action': 'run'})[1]
        status, listed = self.req('/api/recovery', {'action': 'list', 'where': 'automatic'})
        self.assertEqual((status, [row['id'] for row in listed['backups']]), (200, [made['last_id']]))
        self.assertEqual(self.req('/api/recovery', {'action': 'list'})[1]['backups'], [])  # the default folder holds none
        status, rehearsed = self.req('/api/recovery', {'action': 'rehearse', 'id': made['last_id'], 'where': 'automatic'})
        self.assertEqual(status, 200, rehearsed)
        self.assertIn('passed', rehearsed['status'])
        self.assertEqual(self.req('/api/recovery', {'action': 'create', 'where': 'automatic'})[0], 400)  # made with BACK UP NOW
        self.assertEqual(self.req('/api/recovery', {'action': 'list', 'where': 'elsewhere'})[0], 400)


class ReviewTests(CoreCase):
    """The independent review of 2026-10-06 (docs/AUTOMATIC-BACKUPS.md section 5), the Core's part."""

    def test_a_folder_inside_the_program_is_refused_and_nothing_is_created_there(self):
        """A6: a folder inside JARVIS's own program folder was accepted, and backups were written into it."""
        inside = Path(server.ROOT) / 'static'
        self.assertTrue(inside.is_dir())
        for folder in (str(server.ROOT), str(inside)):
            with self.assertRaises(ValueError) as refused:
                self.app.auto_backup_action({'action': 'configure', 'folder': folder, 'every': 'day', 'at': '12:00'})
            self.assertIn("inside JARVIS's own program or data folder", str(refused.exception))
            self.assertFalse((Path(folder) / auto_backup.SUBFOLDER).exists())
        self.assertFalse(self.app.auto_backup.status()['enabled'])

    def held(self):
        """The state a backup puts the Core in while it copies the database: its lock taken, writes refused."""
        import sqlite3
        import recovery
        gate = sqlite3.connect(self.data / 'jarvis.sqlite3', timeout=2)
        gate.execute('BEGIN IMMEDIATE')
        self.assertTrue(recovery.LOCK.acquire(False))

        def release():
            if recovery.LOCK.locked():
                recovery.LOCK.release()
                gate.rollback()
                gate.close()
        self.addCleanup(release)
        return release

    def question(self, text):
        run = Run('during-backup')
        run.device = 'pc'
        self.app.runs[run.id] = run
        worker = threading.Thread(target=self.app.work, args=(run, text, None), daemon=True)
        refuse = patch.object(server.providers, 'request', side_effect=AssertionError('no provider is asked in this test'))
        refuse.start()
        self.addCleanup(refuse.stop)
        worker.start()
        time.sleep(0.7)
        return run, worker

    def test_a_question_that_arrives_during_a_backup_waits_for_it(self):
        """A3: with the database held for more than 10 seconds a question failed "internally" and a note was lost."""
        release = self.held()
        started = time.monotonic()
        self.assertIn('settings', self.app.state())                      # a reading of the state does not wait for the database
        self.assertLess(time.monotonic() - started, 3)
        run, worker = self.question('note: buy milk')
        self.assertFalse(run.done)                                       # waiting, not failed
        release()                                                        # the backup has finished
        worker.join(20)
        events = {e['event']: e['data'] for e in run.events}
        self.assertIn('assistant.completed', events, events)
        self.assertEqual([item['body'] for item in self.app.store.items('note')], ['buy milk'])
        self.assertEqual(self.rows('run'), [])                           # no "internal error"

    def test_a_backup_that_does_not_finish_turns_the_question_away_in_plain_words_and_stop_ends_the_wait(self):
        self.held()
        self.app.BACKUP_WAIT_SECONDS = 0.3
        run, worker = self.question('note: buy milk')
        worker.join(10)
        self.assertEqual(run.events[-1]['event'], 'run.failed')
        self.assertEqual(run.events[-1]['data']['message'], 'A backup of JARVIS is being made and has not finished. Ask again in a moment.')
        self.app.BACKUP_WAIT_SECONDS = 60
        run, worker = self.question('note: buy bread')
        self.assertFalse(run.done)
        run.cancel.set()                                                 # the owner presses Stop while waiting
        worker.join(5)
        self.assertEqual(run.events[-1]['event'], 'run.cancelled')
        self.assertEqual(self.app.store.items('note'), [])


if __name__ == '__main__':
    unittest.main()
