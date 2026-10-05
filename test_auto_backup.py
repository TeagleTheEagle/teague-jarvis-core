"""Automatic backups (release 1.0.15, scope item 6; master document section 11): on a schedule, to a folder the
owner chooses, each one verified, old ones thinned out, off until the owner picks the folder."""
import datetime
import tempfile
import unittest
import zipfile
from pathlib import Path

import auto_backup
import recovery
from auto_backup import AutoBackup, BackupSetting, due, next_due, thin
from store import Store


def at(year, month, day, hour=0, minute=0):
    return datetime.datetime(year, month, day, hour, minute).timestamp()


ON = {'enabled': True, 'folder': 'X:/backups', 'every': 'day', 'at': '12:00'}


class ScheduleTests(unittest.TestCase):
    def test_off_until_the_owner_picks_a_folder(self):
        self.assertFalse(due({}, at(2026, 10, 6, 13)))
        self.assertFalse(due({'enabled': True, 'folder': ''}, at(2026, 10, 6, 13)))
        self.assertFalse(due({**ON, 'enabled': False}, at(2026, 10, 6, 13)))
        self.assertIsNone(next_due({**ON, 'enabled': False}, at(2026, 10, 6, 13)))

    def test_the_first_backup_is_made_at_once_and_then_one_a_day_at_the_chosen_time(self):
        self.assertTrue(due(ON, at(2026, 10, 6, 9)))  # never made one: do not wait for noon
        made = {**ON, 'last_success': at(2026, 10, 6, 12, 0) + 5, 'last_attempt': at(2026, 10, 6, 12, 0)}
        for hour in (12, 13, 18, 23):
            self.assertFalse(due(made, at(2026, 10, 6, hour, 30)), hour)
        self.assertFalse(due(made, at(2026, 10, 7, 11, 59)))
        self.assertTrue(due(made, at(2026, 10, 7, 12, 0)))
        self.assertEqual(next_due(made, at(2026, 10, 6, 18)), at(2026, 10, 7, 12))
        self.assertEqual(next_due(made, at(2026, 10, 7, 12, 30)), at(2026, 10, 7, 12, 30))  # due now

    def test_a_pc_that_was_off_at_the_chosen_time_catches_up_and_does_not_repeat_it_hours_later(self):
        made = {**ON, 'last_success': at(2026, 10, 5, 12, 0)}
        self.assertTrue(due(made, at(2026, 10, 6, 20, 0)))   # off at noon on the 6th: made in the evening
        late = {**ON, 'last_success': at(2026, 10, 6, 20, 0)}
        self.assertTrue(due(late, at(2026, 10, 7, 12, 0)))   # next day at noon as usual (16 hours later)
        early = {**ON, 'last_success': at(2026, 10, 7, 3, 0)}  # caught up after midnight
        self.assertFalse(due(early, at(2026, 10, 7, 12, 0)))  # not again nine hours later
        self.assertTrue(due(early, at(2026, 10, 8, 12, 0)))
        self.assertEqual(next_due(early, at(2026, 10, 7, 12, 0)), at(2026, 10, 8, 12, 0))

    def test_every_week(self):
        weekly = {**ON, 'every': 'week', 'last_success': at(2026, 10, 5, 12, 0) + 30}
        for day in (6, 8, 11):
            self.assertFalse(due(weekly, at(2026, 10, day, 12, 30)), day)
        self.assertFalse(due(weekly, at(2026, 10, 12, 11, 0)))
        self.assertTrue(due(weekly, at(2026, 10, 12, 12, 0)))
        self.assertEqual(next_due(weekly, at(2026, 10, 6, 9)), at(2026, 10, 12, 12))

    def test_a_failure_is_tried_again_an_hour_later_not_every_minute(self):
        failed = {**ON, 'last_attempt': at(2026, 10, 6, 12, 0), 'last_error': 'drive missing'}
        self.assertFalse(due(failed, at(2026, 10, 6, 12, 1)))
        self.assertFalse(due(failed, at(2026, 10, 6, 12, 59)))
        self.assertTrue(due(failed, at(2026, 10, 6, 13, 0)))
        self.assertEqual(next_due(failed, at(2026, 10, 6, 12, 30)), at(2026, 10, 6, 13, 0))
        after_success = {**ON, 'last_success': at(2026, 10, 5, 12), 'last_attempt': at(2026, 10, 6, 12, 0)}
        self.assertFalse(due(after_success, at(2026, 10, 6, 12, 30)))
        self.assertTrue(due(after_success, at(2026, 10, 6, 13, 0)))

    def test_settings_are_checked(self):
        self.assertEqual(auto_backup.clean_settings(' C:/Backups ', 'week', '03:30')[1:], ('week', '03:30'))
        for folder, every, time_of_day in (('', 'day', '12:00'), (None, 'day', '12:00'), ('backups', 'day', '12:00'), ('C:/b', 'hour', '12:00'),
                                           ('C:/b', 'day', '25:00'), ('C:/b', 'day', '12:60'), ('C:/b', 'day', 'noon'), ('C:/b', 'day', None), ('C:/' + 'x' * 400, 'day', '12:00')):
            with self.assertRaises(BackupSetting): auto_backup.clean_settings(folder, every, time_of_day)


class ThinningTests(unittest.TestCase):
    def test_what_is_kept(self):
        now = at(2026, 10, 6, 12)
        made = [{'id': f'd{days:03d}', 'created': now - days * 86400} for days in range(0, 400)]  # one a day for 400 days
        removed = set(thin(made, now))
        kept = [r for r in made if r['id'] not in removed]
        ages = [round((now - r['created']) / 86400) for r in kept]
        self.assertEqual(ages[:8], [0, 1, 2, 3, 4, 5, 6, 7])           # every backup of the last week
        weekly = [a for a in ages if 7 < a <= 63]
        self.assertTrue(8 <= len(weekly) <= 9, weekly)                   # then about one a week for eight weeks
        self.assertTrue(all(b - a <= 7 for a, b in zip(weekly, weekly[1:])), weekly)
        monthly = [a for a in ages if 63 < a <= 365]
        self.assertTrue(9 <= len(monthly) <= 11, monthly)                # then one a month up to a year
        self.assertFalse([a for a in ages if a > 365])                   # nothing older than a year
        self.assertLess(len(kept), 32)

    def test_the_newest_is_always_kept_and_strange_rows_are_left_alone(self):
        now = at(2026, 10, 6, 12)
        old = [{'id': 'ancient', 'created': now - 900 * 86400}]
        self.assertEqual(thin(old, now), [])                             # the only backup, however old
        self.assertEqual(thin(old + [{'id': 'new', 'created': now}], now), [])  # the newest seven stay, whatever their age
        week = [{'id': f'd{day}', 'created': now - day * 86400} for day in range(7)]
        self.assertEqual(thin(old + week, now), ['ancient'])             # with seven newer ones the ancient one goes
        self.assertEqual(thin([{'id': 'x'}, {'id': 'y', 'created': 'yesterday'}, 'junk', {'id': 5, 'created': now}], now), [])
        self.assertEqual(thin([], now), [])
        self.assertEqual(thin(None, now), [])

    def test_one_backup_made_with_the_clock_far_ahead_does_not_cost_the_older_ones(self):
        """Review finding A2: ages are measured from "now"; a PC clock set two years ahead for one backup made every
        older automatic backup look ancient, and all but one were removed."""
        real = at(2026, 10, 10, 12)
        made = [{'id': f'd{day}', 'created': real - day * 86400} for day in range(10)]
        wrong = at(2028, 10, 20, 12)
        gone = thin(made + [{'id': 'future', 'created': wrong}], wrong)
        self.assertEqual(len(made) + 1 - len(gone), 7)                   # seven stay; before the fix one did
        self.assertNotIn('future', gone)
        self.assertEqual(sorted(gone), ['d6', 'd7', 'd8', 'd9'])         # and it is the oldest that go


class ClockTests(unittest.TestCase):
    """Review finding A2, the schedule: a time recorded while the clock was ahead must not stop the backups."""

    def test_a_success_recorded_in_the_future_counts_as_none(self):
        future = {**ON, 'last_success': at(2028, 10, 20, 12), 'last_attempt': at(2028, 10, 20, 12)}
        now = at(2026, 10, 10, 9)
        self.assertTrue(due(future, now))                                # before the fix: not due for two years
        self.assertEqual(next_due(future, now), now)
        failed = {**ON, 'last_attempt': at(2028, 10, 20, 12), 'last_error': 'x'}
        self.assertTrue(due(failed, now))                                # nor does a failed try from the future hold it up
        self.assertFalse(due({**ON, 'last_success': now + 60}, now + 30))  # a few seconds ahead is just the clock's grain

    def test_the_weekday_holds(self):
        """Review finding A9: after a backup a few seconds late, the next week's fell on the following day."""
        weekly = {**ON, 'every': 'week', 'last_success': at(2026, 10, 1, 12, 0) + 5}   # a Thursday, five seconds late
        self.assertTrue(due(weekly, at(2026, 10, 8, 12, 0)))             # the next Thursday at noon
        self.assertFalse(due(weekly, at(2026, 10, 7, 12, 0)))            # not the Wednesday
        caught_up = {**ON, 'every': 'week', 'last_success': at(2026, 10, 1, 21, 0)}    # made nine hours late
        self.assertTrue(due(caught_up, at(2026, 10, 8, 12, 0)))          # still the Thursday

    def test_the_time_of_day_is_two_digits_a_colon_and_two_digits(self):
        for bad in ('+1:00', ' 1:00', '1:00', '24:00', '12:60', '12:0', '12:000', 'noon', '', None, 1200):
            with self.assertRaises(BackupSetting, msg=repr(bad)):
                auto_backup.clean_settings('X:/backups', 'day', bad)
        self.assertEqual(auto_backup.clean_settings('X:/backups', 'day', '00:05')[2], '00:05')


class RunTests(unittest.TestCase):
    """The real backup code (recovery.Recovery) writing into a temporary folder."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.app = self.base / 'app'
        self.app.mkdir()
        (self.app / 'server.py').write_text('# program\n', encoding='utf-8')
        self.data = self.app / 'data'
        Store(self.data).put('memory', 'Favourite colour is cyan')
        self.drive = self.base / 'backup-drive'
        self.drive.mkdir()
        self.saved, self.notes = {}, []
        self.now = [at(2026, 10, 6, 9)]
        self.idle, self.stopped = [True], [False]
        self.auto = AutoBackup(lambda: dict(self.saved), self.saved.update, lambda folder: recovery.Recovery(self.app, self.data, folder),
                               clock=lambda: self.now[0], idle=lambda: self.idle[0], stopped=lambda: self.stopped[0],
                               note=lambda action, status: self.notes.append((action, status)))

    def archives(self):
        folder = self.drive / auto_backup.SUBFOLDER
        return sorted(p.name for p in folder.glob('*.zip')) if folder.is_dir() else []

    def test_off_until_configured_then_made_verified_and_recorded(self):
        self.assertEqual((self.auto.status()['enabled'], self.auto.status()['next_due']), (False, None))
        self.assertIsNone(self.auto.run_if_due())
        self.assertEqual(self.archives(), [])
        status = self.auto.configure(str(self.drive), 'day', '12:00')
        self.assertTrue(status['enabled'] and status['folder_reachable'])
        self.assertEqual(status['backups_in'], str(self.drive / auto_backup.SUBFOLDER))
        status = self.auto.run_if_due()  # the first one is made at once
        self.assertEqual((status['last_error'], status['kept'], status['overdue']), ('', 1, False))
        self.assertEqual(len(self.archives()), 1)
        self.assertEqual(self.archives()[0], status['last_id'] + '.zip')
        manifest = recovery.verify(self.drive / auto_backup.SUBFOLDER / self.archives()[0])  # a real, verifiable backup
        self.assertEqual(manifest['database_counts']['items'], 1)
        with zipfile.ZipFile(self.drive / auto_backup.SUBFOLDER / self.archives()[0]) as z:
            self.assertIn('data/jarvis.sqlite3', z.namelist())
        self.assertIsNone(self.auto.run_if_due())  # not again today
        self.assertEqual(self.notes, [('automatic backups', 'on: day'), ('automatic backup', 'verified')])
        self.assertEqual(status['next_due'], at(2026, 10, 7, 12))

    def test_it_waits_while_jarvis_is_busy_or_stopped(self):
        self.auto.configure(str(self.drive), 'day', '12:00')
        self.idle[0] = False
        self.assertIsNone(self.auto.run_if_due())
        self.idle[0], self.stopped[0] = True, True
        self.assertIsNone(self.auto.run_if_due())
        self.assertEqual(self.archives(), [])
        self.stopped[0] = False
        self.assertEqual(self.auto.run_if_due()['kept'], 1)

    def test_a_missing_drive_is_said_and_tried_again_later(self):
        self.auto.configure(str(self.drive), 'day', '12:00')
        gone = self.base / 'unplugged'
        self.drive.rename(gone)
        status = self.auto.run_if_due()
        self.assertIn('not reachable', status['last_error'])
        self.assertEqual((status['folder_reachable'], status['never_succeeded'], status['overdue'], status['last_success']), (False, True, False, None))
        self.assertIsNone(self.auto.run_if_due())  # not every minute
        self.now[0] += 3600
        gone.rename(self.drive)
        status = self.auto.run_if_due()
        self.assertEqual((status['last_error'], status['kept'], status['overdue']), ('', 1, False))
        self.assertEqual([n for n in self.notes if n[0] == 'automatic backup'], [('automatic backup', 'failed'), ('automatic backup', 'verified')])

    def test_old_automatic_backups_are_thinned_and_a_backup_made_by_hand_is_never_touched(self):
        self.auto.configure(str(self.drive), 'day', '12:00')
        by_hand = recovery.Recovery(self.app, self.data, self.drive / auto_backup.SUBFOLDER).create()['id']
        for day in range(40):  # forty days, one automatic backup a day
            self.now[0] = at(2026, 10, 6, 12) + day * 86400
            self.assertEqual(self.auto.run_if_due()['last_error'], '', day)
        status = self.auto.status()
        self.assertLess(status['kept'], 16)
        self.assertGreaterEqual(status['kept'], 12)
        self.assertEqual(len(self.archives()), status['kept'] + 1)
        self.assertIn(by_hand + '.zip', self.archives())
        self.assertIn(status['last_id'] + '.zip', self.archives())
        self.assertIn(('automatic backup', 'verified; 1 old removed'), self.notes)

    def test_turning_off_keeps_the_backups_and_the_folder(self):
        self.auto.configure(str(self.drive), 'week', '03:00')
        self.auto.run_if_due()
        status = self.auto.turn_off()
        self.assertEqual((status['enabled'], status['folder'], status['kept'], status['next_due']), (False, str(self.drive), 1, None))
        self.now[0] += 30 * 86400
        self.assertIsNone(self.auto.run_if_due())
        self.assertEqual(len(self.archives()), 1)

    def test_a_folder_that_cannot_be_used_is_refused_and_nothing_is_turned_on(self):
        for folder in (str(self.base / 'missing'), str(self.data), 'relative/folder', ''):
            with self.assertRaises(ValueError): self.auto.configure(folder, 'day', '12:00')
        self.assertFalse(self.auto.status()['enabled'])
        self.assertEqual(self.saved, {})

    # ---- the independent review of 2026-10-06 (docs/AUTOMATIC-BACKUPS.md section 5) ----

    def during_a_backup(self, act):
        """Makes one automatic backup and calls act() while its files are being written (the real backup code)."""
        real = recovery.Recovery.create

        def create(service):
            act()
            return real(service)

        recovery.Recovery.create = create
        try:
            return self.auto.run()
        finally:
            recovery.Recovery.create = real

    def test_what_the_owner_changes_while_a_backup_is_made_stays_changed(self):
        """A1: TURN OFF during a running backup was switched on again when the backup finished."""
        self.auto.configure(str(self.drive), 'day', '12:00')
        status = self.during_a_backup(self.auto.turn_off)
        self.assertFalse(status['enabled'])
        self.assertEqual((status['kept'], status['last_error'], len(self.archives())), (1, '', 1))  # the backup itself is recorded
        self.auto.configure(str(self.drive), 'day', '12:00')
        self.now[0] = at(2026, 10, 7, 12)
        status = self.during_a_backup(lambda: self.auto.configure(str(self.drive), 'week', '03:30'))
        self.assertEqual((status['enabled'], status['every'], status['at'], status['kept']), (True, 'week', '03:30', 2))

    def test_another_folder_starts_afresh_and_leaves_the_old_one_alone(self):
        """A7: after a move the new folder stayed empty until the next planned time while the screen counted the old backups."""
        self.auto.configure(str(self.drive), 'day', '12:00')
        self.auto.run_if_due()
        other = self.base / 'second-drive'
        other.mkdir()
        status = self.auto.configure(str(other), 'day', '12:00')
        self.assertEqual((status['kept'], status['last_success'], status['next_due']), (0, None, self.now[0]))
        status = self.auto.run_if_due()                                   # the first one there is made at once
        self.assertEqual((status['kept'], len(list((other / auto_backup.SUBFOLDER).glob('*.zip')))), (1, 1))
        self.assertEqual(len(self.archives()), 1)                         # the old folder keeps what it had
        # A folder changed while a backup was being made: that backup stays in the old folder, off the record.
        self.now[0] = at(2026, 10, 7, 12)
        status = self.during_a_backup(lambda: self.auto.configure(str(self.drive), 'day', '12:00'))
        self.assertEqual((status['folder'], status['kept'], status['last_success']), (str(self.drive), 0, None))
        self.assertIn(('automatic backup', 'verified; the folder was changed meanwhile'), self.notes)

    def test_a_full_drive_is_said_in_plain_words(self):
        """A4: a full backup drive was reported only as "OSError"."""
        self.auto.configure(str(self.drive), 'day', '12:00')
        for error in (OSError(28, 'No space left on device'), OSError(22, 'x', None, 112)):
            real = recovery.Recovery.create

            def create(service, error=error):
                raise error

            recovery.Recovery.create = create
            try:
                status = self.auto.run()
            finally:
                recovery.Recovery.create = real
            self.assertEqual(status['last_error'], auto_backup.DRIVE_FULL)
        self.assertEqual(self.auto.status()['never_succeeded'], True)

    def test_a_record_that_cannot_be_saved_does_not_mean_a_backup_every_minute(self):
        """A5: with the record unsaveable, a full backup was made at every look, unrecorded and never thinned."""
        self.auto.configure(str(self.drive), 'day', '12:00')
        save, self.auto.save = self.auto.save, lambda state: (_ for _ in ()).throw(OSError(28, 'system disk full'))
        self.auto.run_if_due()
        for minute in range(1, 5):
            self.now[0] += 60
            self.assertIsNone(self.auto.run_if_due(), minute)
        self.assertEqual(len(self.archives()), 1)                         # one, not five
        self.assertIn(('automatic backup', 'its record could not be saved'), self.notes)
        self.auto.save = save
        self.now[0] += 3600
        self.assertEqual(self.auto.run_if_due()['kept'], 1)               # an hour later it is tried again, and recorded

    def test_a_write_protected_folder_is_refused_in_plain_words(self):
        """A8: a folder JARVIS could not write to answered "Local operation failed"."""
        def refuse(folder):
            raise PermissionError(13, 'Access is denied')
        self.auto.make = refuse
        with self.assertRaisesRegex(BackupSetting, 'cannot create its backup folder'):
            self.auto.configure(str(self.drive), 'day', '12:00')
        self.assertFalse(self.auto.status()['enabled'])

    def test_nothing_old_is_removed_while_the_stop_holds_or_when_switched_off(self):
        """A11: a backup already running went on to remove old backups under an emergency stop."""
        self.auto.configure(str(self.drive), 'day', '12:00')
        for day in range(12):
            self.now[0] = at(2026, 8, 1, 12) + day * 7 * 86400            # twelve weekly-spaced backups: all kept so far
            self.auto.run()
        before = len(self.archives())
        self.now[0] = at(2027, 6, 1, 12)                                  # much later: several would now be thinned
        self.assertTrue(auto_backup.thin(self.auto.state()['made'], self.now[0]))
        self.stopped[0] = True
        self.auto.run()                                                   # (BACK UP NOW is refused under a stop by the Core; here the backup was already running)
        self.assertEqual(len(self.archives()), before + 1)
        self.stopped[0] = False
        self.auto.turn_off()
        self.now[0] += 86400
        self.auto.run()                                                   # BACK UP NOW after TURN OFF: made, nothing removed
        self.assertEqual(len(self.archives()), before + 2)
        self.auto.configure(str(self.drive), 'day', '12:00')
        self.now[0] += 86400
        self.auto.run()
        self.assertLess(len(self.archives()), before + 3)                 # on again and no stop: thinned as usual

    def test_what_an_unfinished_backup_left_behind_is_removed_after_a_day(self):
        """A11: a Core closed during a backup left a working folder and a half-written copy, each a full backup in size."""
        self.auto.configure(str(self.drive), 'day', '12:00')
        folder = self.drive / auto_backup.SUBFOLDER
        import os
        old = self.now[0] - 2 * 86400
        stale = [folder / '.building-abc123', folder / ('a' * 32 + '.zip.publishing-' + 'b' * 32)]
        stale[0].mkdir(); (stale[0] / 'backup.zip').write_bytes(b'x' * 10); stale[1].write_bytes(b'y' * 10)
        fresh = folder / '.building-new999'; fresh.mkdir()
        keep = [folder / 'my notes.txt', folder / ('c' * 32 + '.zip'), folder / '.building-not ours', folder / 'holiday.publishing-photos']
        keep[0].write_text('mine', encoding='utf-8'); keep[1].write_bytes(b'by hand'); keep[2].mkdir(); keep[3].write_bytes(b'z')
        for path in stale + keep:
            os.utime(path, (old, old))
        os.utime(fresh, (self.now[0], self.now[0]))
        self.assertEqual(self.auto.run_if_due()['last_error'], '')
        self.assertFalse(any(path.exists() for path in stale))
        self.assertTrue(all(path.exists() for path in keep + [fresh]))

    def test_a_record_with_strange_rows_is_read_without_trusting_them(self):
        """A11: a row without an id made a finished backup count as failed."""
        self.auto.configure(str(self.drive), 'day', '12:00')
        self.saved['made'] = [{'created': 5}, 'junk', {'id': 7, 'created': 5}, {'id': 'x' * 32, 'created': self.now[0] - 86400}]
        status = self.auto.run_if_due()
        self.assertEqual((status['last_error'], status['kept']), ('', 2))
        self.assertEqual(self.notes[-1], ('automatic backup', 'verified'))


if __name__ == '__main__':
    unittest.main()
