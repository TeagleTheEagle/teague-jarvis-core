"""Standing responsibilities and emergency authority (standing.py; owner, 2026-10-13, "all four"): the watch that warns,
a mission's approval covering its workshop work, the emergency authority (restart, backup, lockdown) and the warning
before a risky action. Each is a switch the owner can turn off; none spends, sends, deletes or changes JARVIS himself.
"""
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import content_guard
import permissions
import standing
import workshop
from server import App, Run
from store import Store


class FakeBackup:
    def __init__(self, status):
        self.current, self.runs = status, 0

    def status(self):
        return {'enabled': True, 'overdue': False, 'never_succeeded': False, 'last_error': '', **self.current}

    def run(self):
        self.runs += 1
        return 'tried'


class WatchTests(unittest.TestCase):
    """A: the standing watch. C: a backup when backups keep failing."""

    def setUp(self):
        self.settings = {}
        self.notices, self.dropped = [], []
        self.parts = {'drives': [{'drive': 'C:', 'free_percent': 4, 'free_gb': 9.1, 'total_gb': 237.0}], 'battery': {'present': True, 'percent': 12, 'on_mains': False}}
        self.backup = FakeBackup({'overdue': True, 'last_error': 'The backup folder is not reachable (is the drive connected?).'})
        self.watch = standing.Watch(lambda: self.settings, self.notify, self.dropped.append, backup=self.backup, read=lambda: self.parts)

    def notify(self, text, key):
        self.notices.append((key, text))
        return True

    def test_each_problem_is_said_once_and_again_after_it_cleared(self):
        raised = self.watch.run_once()
        self.assertEqual(sorted(raised), ['watch:backup', 'watch:battery', 'watch:drive:C:'])
        texts = dict(self.notices)
        self.assertEqual(texts['watch:drive:C:'], 'Drive C: is nearly full: 9.1 GB free of 237.0 GB.')
        self.assertEqual(texts['watch:battery'], 'The battery is at 12% and not on mains power.')
        self.assertIn('not worked for a while: The backup folder is not reachable', texts['watch:backup'])
        self.assertIn('JARVIS tried one just now', texts['watch:backup'])
        self.assertEqual(self.backup.runs, 1, 'C: one try at once')
        self.assertEqual(self.watch.run_once(), [], 'nothing twice while it lasts')
        self.assertEqual(self.backup.runs, 1, 'and not tried again every look')
        self.parts['battery']['on_mains'] = True
        self.parts['drives'][0]['free_percent'] = 30
        self.backup.current = {'overdue': False}
        self.assertEqual(self.watch.run_once(), [])
        self.assertEqual(sorted(self.dropped), ['watch:backup', 'watch:battery', 'watch:drive:C:'], 'cleared: the keys go, so it can be said again later')
        self.parts['drives'][0]['free_percent'] = 3
        self.assertEqual(self.watch.run_once(), ['watch:drive:C:'])

    def test_the_switches(self):
        self.settings['watch_problems'] = False
        self.assertEqual(self.watch.run_once(), ['watch:backup'], 'the watch off: only the emergency backup speaks')
        self.assertEqual(self.backup.runs, 1)
        self.settings['emergency_backup'] = False
        watch = standing.Watch(lambda: self.settings, self.notify, self.dropped.append, backup=self.backup, read=lambda: self.parts)
        self.assertEqual(watch.run_once(), [], 'both off: silence')
        self.assertEqual(self.backup.runs, 1)
        self.settings['watch_problems'] = True
        watch = standing.Watch(lambda: self.settings, self.notify, self.dropped.append, backup=self.backup, read=lambda: self.parts)
        raised = watch.run_once()
        self.assertEqual(sorted(raised), ['watch:backup', 'watch:battery', 'watch:drive:C:'])
        self.assertEqual(self.backup.runs, 1, 'the emergency backup off: said, not tried')
        self.assertNotIn('tried one', [t for k, t in self.notices if k == 'watch:backup'][-1])

    def test_an_unreadable_pc_or_a_missing_backup_record_is_no_problem(self):
        def boom():
            raise OSError('no')
        watch = standing.Watch(lambda: {}, self.notify, self.dropped.append, backup=None, read=boom)
        self.assertEqual(watch.run_once(), [])
        self.assertEqual(watch.conditions(), {})


class LockdownTests(unittest.TestCase):
    """C: the lockdown, counted from the guard's marks."""

    def setUp(self):
        self.settings, self.said = {}, []
        self.clock = [1000.0]
        self.lockdown = standing.Lockdown(lambda: self.settings, self.settings.update, self.said.append, clock=lambda: self.clock[0])

    def test_three_marked_questions_in_ten_minutes_lock_the_core_down_once(self):
        self.assertFalse(self.lockdown.tainted())
        self.clock[0] += 200
        self.assertFalse(self.lockdown.tainted())
        self.assertEqual(self.settings, {})
        self.clock[0] += 200
        self.assertTrue(self.lockdown.tainted())
        self.assertEqual(self.settings, {'lockdown': True})
        self.assertTrue(self.said and self.said[0].startswith('JARVIS locked himself down: 3 questions'))
        self.assertFalse(self.lockdown.tainted(), 'already locked: nothing more')
        self.lockdown.end()
        self.assertEqual(self.settings, {'lockdown': False})
        self.assertEqual(self.lockdown.hits, [])

    def test_old_marks_do_not_count_and_the_switch_off_means_no_lockdown(self):
        self.lockdown.tainted(); self.lockdown.tainted()
        self.clock[0] += standing.LOCKDOWN_WINDOW + 1
        self.assertFalse(self.lockdown.tainted(), 'two marks are ten minutes old')
        self.settings['emergency_lockdown'] = False
        self.lockdown.tainted(); self.lockdown.tainted()
        self.assertFalse(self.lockdown.tainted())
        self.assertNotIn('lockdown', self.settings)


class RiskTests(unittest.TestCase):
    """D: what is risky, in plain sentences."""

    def test_commands_folders_and_programs(self):
        for command in ('rmdir /s /q build', 'rd /s build', 'del /s /q *.log', 'rm -rf dist', 'Remove-Item out -Recurse -Force', 'format d:',
                        'shutdown /r /t 0', 'git push --force', 'git reset --hard', 'reg delete HKCU\\Software\\x /f', 'pip uninstall -y numpy'):
            with self.subTest(command=command):
                self.assertIn('hard to undo', standing.risk('workshop_run', {'command': command}))
        self.assertIn('hard to undo', standing.risk('workshop_run', {'command': 'cd build && rm -rf out'}), 'after a separator too')
        for command in ('python tidy.py', 'dir', 'git status', 'pip install requests', 'echo rm -rf is dangerous', 'del old.txt', 'rmdir empty'):
            with self.subTest(command=command):
                self.assertIsNone(standing.risk('workshop_run', {'command': command}))
        self.assertIn('deletes a folder', standing.risk('workshop_files', {'action': 'delete', 'path': 'projects/old'}))
        self.assertIn('whole workshop', standing.risk('workshop_files', {'action': 'delete', 'path': ''}))
        self.assertIsNone(standing.risk('workshop_files', {'action': 'delete', 'path': 'notes/old.txt'}))
        self.assertIsNone(standing.risk('workshop_files', {'action': 'write', 'path': 'projects/old'}))
        self.assertIn('program to download', standing.risk('computer_open_page', {'url': 'https://example.com/setup.exe?x=1'}))
        self.assertIsNone(standing.risk('computer_open_page', {'url': 'https://example.com/page'}))
        self.assertIsNone(standing.risk('web_search', {'query': 'rm -rf'}))
        self.assertIsNone(standing.risk('workshop_run', None))


class InTheCoreTests(unittest.TestCase):
    """Through App.tool and the settings, as a question and the owner's clicks reach it."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = App(Path(self.temp.name))
        self.run = Run('standing-test')
        self.run.user_text = 'clear the build folder'
        self.app.runs[self.run.id] = self.run
        self.app.set_permission('workshop_files', permissions.DEFAULT)
        self.app.set_permission('workshop_run', permissions.DEFAULT)

    def mission_run(self, covered):
        run = Run('mission-chat')
        run.mission = 'm-1'
        run.covered = covered
        self.app.runs[run.id] = run
        return run

    def test_the_switches_ship_on_and_show_in_settings_permissions(self):
        listing = self.app.permissions_listing()
        self.assertEqual([s['name'] for s in listing['standing']['switches']], list(standing.SWITCHES))
        self.assertTrue(all(s['on'] for s in listing['standing']['switches']))
        self.assertFalse(listing['standing']['lockdown'])
        self.app.save_settings({'warn_risky': False})
        self.assertFalse(next(s for s in self.app.permissions_listing()['standing']['switches'] if s['name'] == 'warn_risky')['on'])
        written = json.loads((self.app.store.root / standing.FILE).read_text(encoding='utf-8'))
        self.assertEqual(written, {'emergency_restart': True, 'restart_window_seconds': standing.RESTART_WINDOW}, 'what the desktop app reads')
        self.app.save_settings({'emergency_restart': False})
        self.assertFalse(json.loads((self.app.store.root / standing.FILE).read_text(encoding='utf-8'))['emergency_restart'])

    def test_a_risky_command_asks_once_with_the_warning_and_the_yes_runs_it(self):
        with patch.object(self.app.workshop.runner, 'run', return_value={'status': 'completed', 'exit_code': 0}) as ran:
            result = self.app.tool('workshop_run', {'command': 'rmdir /s /q build'}, self.run)
            self.assertEqual(result['status'], 'awaiting approval')
            self.assertTrue(result['summary'].startswith('JARVIS warns: This command can wipe'), result['summary'])
            self.assertIn('Still go ahead?', result['summary'])
            card = self.app.approvals[result['approval']['id']]
            self.assertIn('Still go ahead?', card['warning'])
            self.assertTrue(self.app.approval_rows()[0]['detail'].startswith('JARVIS warns:'), 'a device sees the warning first')
            ran.assert_not_called()
            done = self.app.approve(result['approval']['id'], True)
            self.assertEqual(done['status'], 'applied')
            ran.assert_called_once()
            # The same command again asks again: the warning is per call, not a veto and not a memory.
            self.assertEqual(self.app.tool('workshop_run', {'command': 'rmdir /s /q build'}, self.run)['status'], 'awaiting approval')
            # A plain command runs at once with the switch at Allowed.
            self.assertEqual(self.app.tool('workshop_run', {'command': 'dir'}, self.run)['status'], 'completed')
        self.app.save_settings({'warn_risky': False})
        with patch.object(self.app.workshop.runner, 'run', return_value={'status': 'completed', 'exit_code': 0}):
            self.assertEqual(self.app.tool('workshop_run', {'command': 'rmdir /s /q build'}, self.run)['status'], 'completed', 'the switch off: as before')

    def test_a_tool_at_ask_first_carries_the_warning_on_its_card(self):
        self.app.set_permission('workshop_files', permissions.ASK)
        result = self.app.tool('workshop_files', {'action': 'delete', 'path': 'projects/old'}, self.run)
        self.assertEqual(result['status'], 'awaiting approval')
        self.assertIn('deletes a folder', self.app.approvals[result['approval']['id']]['warning'])
        result = self.app.tool('workshop_files', {'action': 'list', 'path': ''}, self.run)
        self.assertEqual(result['status'], 'completed', 'a read is neither asked nor warned')

    def test_the_owners_approval_of_a_mission_covers_its_workshop_work(self):
        self.app.set_permission('workshop_files', permissions.ASK)
        self.app.set_permission('workshop_run', permissions.ASK)
        covered = self.mission_run(True)
        result = self.app.tool('workshop_files', {'action': 'write', 'path': 'note.txt', 'content': 'from a covered mission'}, covered)
        self.assertEqual(result['status'], 'written')
        self.assertEqual((self.app.workshop.home / 'note.txt').read_text(encoding='utf-8'), 'from a covered mission')
        with patch.object(self.app.workshop.runner, 'run', return_value={'status': 'completed', 'exit_code': 0}) as ran:
            self.assertEqual(self.app.tool('workshop_run', {'command': 'dir'}, covered)['status'], 'completed')
            ran.assert_called_once()
            # Not covered: the model started it with the switch at Allowed, so no card was ever shown.
            plain = self.mission_run(False)
            self.assertEqual(self.app.tool('workshop_run', {'command': 'dir'}, plain)['status'], 'awaiting approval')
            # Covered, but Off stays off; taint still asks; the stop still refuses; outside the workshop still asks.
            self.app.set_permission('workshop_run', permissions.OFF)
            with self.assertRaises(ValueError):
                self.app.tool('workshop_run', {'command': 'dir'}, covered)
            self.app.set_permission('workshop_run', permissions.ASK)
            covered.tainted = True
            self.assertEqual(self.app.tool('workshop_run', {'command': 'dir'}, covered)['status'], 'awaiting approval')
            covered.tainted = False
            self.app.stopped = time.time()
            with self.assertRaises(ValueError):
                self.app.tool('workshop_run', {'command': 'dir'}, covered)
            self.app.stopped = None
        self.app.set_permission('open_app', permissions.ASK)
        self.assertEqual(self.app.tool('open_app', {'app': 'calculator'}, covered)['status'], 'awaiting approval', 'the PC outside the workshop is not covered')
        self.app.save_settings({'mission_covers': False})
        self.assertEqual(self.app.tool('workshop_files', {'action': 'write', 'path': 'two.txt', 'content': 'x'}, covered)['status'], 'awaiting approval', 'the switch off')

    def test_a_mission_the_owner_starts_or_approves_is_covered_and_one_the_model_starts_alone_is_not(self):
        started = []
        def fake(goal, covered=False):
            started.append((goal, covered))
            return {'status': 'started', 'id': 'm', 'chat': 'c', 'minutes': 5, 'note': ''}
        with patch.object(self.app.workshop, 'start_mission', fake):
            self.app.workshop_action({'action': 'start', 'goal': 'Tidy the downloads folder by type'})          # the owner's own click
            self.app.tool('workshop_mission', {'action': 'start', 'goal': 'Sort the photos by year'}, self.run, approved=True)   # his yes on the card
            self.app.set_permission('workshop_mission', permissions.DEFAULT)
            self.app.tool('workshop_mission', {'action': 'start', 'goal': 'List the largest files here'}, self.run)   # the model alone, switch Allowed
        self.assertEqual([c for _, c in started], [True, True, False])

    def test_the_lockdown_makes_every_action_ask_until_the_owner_ends_it(self):
        self.assertEqual(self.app.tool_mode('workshop_run'), permissions.DEFAULT)
        for n in range(standing.LOCKDOWN_HITS):
            run = Run('q' + str(n))
            content_guard.mark(run, [('instruction', 'instructions to ignore its rules')], 'web_search', self.app.audit)
            self.assertTrue(run.tainted)
        self.assertTrue(self.app.store.settings()['lockdown'])
        self.assertEqual(self.app.tool_mode('workshop_run'), permissions.ASK)
        self.assertEqual(self.app.tool_mode('save_item'), permissions.ASK)
        self.assertEqual(self.app.tool_mode('web_search'), permissions.DEFAULT, 'a read cannot ask, so it is not changed')
        self.app.set_permission('open_app', permissions.OFF)
        self.assertEqual(self.app.tool_mode('open_app'), permissions.OFF, 'Off stays off')
        offered = {t['function']['name']: t for t in self.app.offered_tools()}
        self.assertIn('ask', json.dumps(offered['save_item']).lower())
        with patch.object(self.app.workshop.runner, 'run', return_value={'status': 'completed', 'exit_code': 0}):
            self.assertEqual(self.app.tool('workshop_run', {'command': 'dir'}, self.run)['status'], 'awaiting approval')
        self.assertTrue(self.app.permissions_listing()['standing']['lockdown'])
        self.app.save_settings({'lockdown': False})   # the owner's END LOCKDOWN click
        self.assertFalse(self.app.store.settings()['lockdown'])
        self.assertEqual(self.app.tool_mode('workshop_run'), permissions.DEFAULT)
        with self.app.store.connect() as db:
            seen = [r['action'] for r in db.execute('SELECT action FROM audit ORDER BY id')]
        self.assertIn('lockdown', seen)

    def test_the_lockdown_switch_off_means_no_lockdown(self):
        self.app.save_settings({'emergency_lockdown': False})
        for n in range(standing.LOCKDOWN_HITS + 1):
            content_guard.mark(Run('q' + str(n)), [('hidden', 'invisible characters that hide or reorder text')], 'mail_read', self.app.audit)
        self.assertFalse(self.app.store.settings()['lockdown'])

    def test_a_notice_is_kept_and_spoken_as_a_nudge_is(self):
        said = []
        with patch.object(self.app, 'say', lambda words: said.append(words) or True):
            self.app.save_settings({'proactive': True})
            self.assertTrue(self.app.standing_notice('Drive C: is nearly full: 9 GB free of 237 GB.', key='watch:drive:C:'))
            self.assertFalse(self.app.standing_notice('Drive C: is nearly full: 9 GB free of 237 GB.', key='watch:drive:C:'), 'once per key')
        self.assertEqual(said, ['Drive C: is nearly full: 9 GB free of 237 GB.'])
        self.assertEqual(self.app.notices.recent(1)[0]['kind'], 'system')
        self.assertEqual(self.app.notices.drop('watch:drive:C:'), 1)


if __name__ == '__main__':
    unittest.main()
