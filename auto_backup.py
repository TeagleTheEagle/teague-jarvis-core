"""Automatic backups (release 1.0.15, scope item 6; master document section 11).

On a schedule the owner sets, to a folder the owner chooses (for example a backup drive), each one made and
verified by recovery.Recovery exactly as a backup made by hand, and old automatic backups thinned out.
Off until the owner picks a folder. Nothing here uploads anything.

The rules, in one place:
  - a backup is started only while JARVIS is idle and not under an emergency stop; a missed one is made at the
    next chance (a PC that was off at the chosen time catches up when JARVIS next runs);
  - only backups this module made are ever thinned; a backup made by hand in the same folder is never touched;
  - the newest seven automatic backups are always kept, whatever the clock says; nothing old is removed while
    the emergency stop holds or while automatic backups are switched off;
  - what the owner changes while a backup is being made stays as the owner set it;
  - a failure is recorded with its reason and tried again an hour later, not every minute.
"""
import datetime
import errno
import re
import shutil
import threading
import time
from pathlib import Path

SUBFOLDER = 'JARVIS automatic backups'
EVERY = ('day', 'week')
RETRY_SECONDS = 3600
KEEP_NEWEST, KEEP_ALL_DAYS, KEEP_WEEKLY_WEEKS, KEEP_MONTHLY_DAYS = 7, 7, 8, 365
CLOCK_SLACK = 300        # a time this far ahead of the clock is still "now"; further ahead, the clock was wrong when it was written
LEFTOVER_SECONDS = 86400  # working files of a backup that never finished (the Core was closed meanwhile) are removed after a day
DEFAULT = {'folder': '', 'every': 'day', 'at': '12:00', 'enabled': False, 'last_success': None, 'last_id': None,
           'last_attempt': None, 'last_error': '', 'made': []}
DRIVE_FULL = 'The backup drive is full. Free some space on it or choose another folder; JARVIS does not remove backups it would otherwise keep.'
_WORK_FOLDER = re.compile(r'\.building-[A-Za-z0-9_]+')
_HALF_PUBLISHED = re.compile(r'[a-f0-9]{32}\.zip\.publishing-[a-f0-9]{32}')


class BackupSetting(ValueError):
    """A setting the owner gave that cannot be used; the message is fit to show."""


def clean_settings(folder, every, at):
    if not isinstance(folder, str) or not folder.strip() or len(folder) > 400:
        raise BackupSetting('Choose the folder for automatic backups.')
    path = Path(folder.strip())
    if not path.is_absolute():
        raise BackupSetting('Give the full path of the folder, for example E:\\JARVIS-BACKUP.')
    if every not in EVERY:
        raise BackupSetting('Choose every day or every week.')
    if not isinstance(at, str) or not _time_of_day(at):
        raise BackupSetting('The time of day must look like 12:00.')
    return str(path), every, at


def _time_of_day(text):
    if isinstance(text, str) and re.fullmatch(r'[0-9]{2}:[0-9]{2}', text):
        hour, minute = int(text[:2]), int(text[3:])
        if hour <= 23 and minute <= 59:
            return hour, minute
    return None


def _planned_before(now, at):
    """The latest planned time of day at or before `now`, in local time: today's if it has passed, else yesterday's."""
    hour, minute = _time_of_day(at) or (12, 0)
    moment = datetime.datetime.fromtimestamp(now)
    planned = moment.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return planned if planned <= moment else planned - datetime.timedelta(days=1)


def _gap(every):
    """How far a planned moment must lie after the last success to count. A day: at least half a day, so a
    backup that was caught up late is not repeated a few hours later. A week: six and a half days, so the
    weekday holds when a backup ran a few seconds, or up to half a day, after its planned time."""
    return 6.5 * 86400 if every == 'week' else 12 * 3600


def _past(moment, now):
    """A recorded time, or None when there is none or it lies ahead of the clock (it was written while the PC's
    clock was wrong; it is then treated as never having happened, so that one bad clock cannot stop the schedule)."""
    return moment if isinstance(moment, (int, float)) and 0 < moment <= now + CLOCK_SLACK else None


def _retry_at(state, now):
    attempt, success = _past(state.get('last_attempt'), now), _past(state.get('last_success'), now)
    return attempt + RETRY_SECONDS if attempt and (not success or attempt > success) else 0


def due(state, now):
    """Is an automatic backup due at `now` (seconds since the epoch, judged in local time)?"""
    if not state.get('enabled') or not state.get('folder'):
        return False
    if now < _retry_at(state, now):
        return False  # the last try failed less than an hour ago
    success = _past(state.get('last_success'), now)
    if not success:
        return True  # never made one: the first is made at once, whatever the time of day
    return _planned_before(now, state.get('at', '')).timestamp() - success >= _gap(state.get('every'))


def next_due(state, now):
    """When the next automatic backup is planned (None when off); for the owner's screen."""
    if not state.get('enabled') or not state.get('folder'):
        return None
    if due(state, now):
        return now
    success, retry = _past(state.get('last_success'), now), _retry_at(state, now)
    if not success:
        return retry
    planned = _planned_before(now, state.get('at', '')) + datetime.timedelta(days=1)
    while planned.timestamp() - success < _gap(state.get('every')):
        planned += datetime.timedelta(days=1)
    return max(planned.timestamp(), retry)


def thin(made, now):
    """The ids of automatic backups to delete. Kept: the newest seven whatever their age (a wrong clock must not
    cost the backups); every backup of the last 7 days; then the newest of each week for 8 weeks; then the newest
    of each month up to a year."""
    rows = sorted(_rows(made), key=lambda r: r['created'], reverse=True)
    keep, weeks, months = set(), set(), set()
    for index, row in enumerate(rows):
        age_days = (now - row['created']) / 86400
        stamp = datetime.datetime.fromtimestamp(row['created'])
        if index < KEEP_NEWEST or age_days <= KEEP_ALL_DAYS:
            keep.add(row['id'])
        elif age_days <= KEEP_ALL_DAYS + KEEP_WEEKLY_WEEKS * 7:
            week = stamp.isocalendar()[:2]
            if week not in weeks:
                weeks.add(week); keep.add(row['id'])
        elif age_days <= KEEP_MONTHLY_DAYS:
            month = (stamp.year, stamp.month)
            if month not in months:
                months.add(month); keep.add(row['id'])
    return [row['id'] for row in rows if row['id'] not in keep]


def _rows(made):
    """The usable rows of the record of backups made (anything else in it is ignored, never trusted)."""
    return [r for r in (made if isinstance(made, list) else []) if isinstance(r, dict) and isinstance(r.get('id'), str) and isinstance(r.get('created'), (int, float))]


def sweep(folder, now):
    """Removes what a backup that never finished left in the automatic folder (the Core was closed or the PC went
    off meanwhile): its working folder and a half-written copy, each of them a full backup in size. Only names this
    program gives such files, only directly in that folder, only when older than a day. Returns how many."""
    removed = 0
    try:
        entries = list(Path(folder).iterdir())
    except OSError:
        return 0
    for entry in entries:
        try:
            if entry.is_symlink() or now - entry.stat().st_mtime < LEFTOVER_SECONDS:
                continue
            if entry.is_dir() and _WORK_FOLDER.fullmatch(entry.name):
                shutil.rmtree(entry)
            elif entry.is_file() and _HALF_PUBLISHED.fullmatch(entry.name):
                entry.unlink()
            else:
                continue
            removed += 1
        except OSError:
            continue  # in use or protected: it stays, and is looked at again next time
    return removed


def _reason(exc):
    """A failure in words fit to show: our own messages as they are, a full drive in plain words, anything else
    reduced to its kind (never a path or content)."""
    if isinstance(exc, OSError) and (exc.errno == errno.ENOSPC or getattr(exc, 'winerror', None) in (39, 112)):
        return DRIVE_FULL
    return str(exc) if isinstance(exc, ValueError) and len(str(exc)) <= 300 else type(exc).__name__


class AutoBackup:
    """load() and save(state) keep the settings and the record of what was made (the Core's database, out of
    reach of the settings page and of a restored JSON backup). make(folder) returns a recovery.Recovery for it."""

    def __init__(self, load, save, make, clock=time.time, idle=lambda: True, stopped=lambda: False, note=lambda action, status: None):
        self.load, self.save, self.make, self.clock, self.idle, self.stopped, self.note = load, save, make, clock, idle, stopped, note
        self.lock = threading.Lock()     # one automatic backup at a time
        self.record = threading.Lock()   # the record is read, changed and saved as one step
        self.unsaved_until = 0           # a backup whose record could not be saved: no new one before this time

    def state(self):
        state = {**DEFAULT, **(self.load() or {})}
        state['made'] = _rows(state['made'])
        return state

    def change(self, change):
        """Read the record, change it and save it as one step, so that the clock's backup and the owner's clicks
        cannot overwrite each other. Returns the record as saved."""
        with self.record:
            state = self.state()
            change(state)
            self.save(state)
            return state

    def status(self):
        """What Settings > Backups shows."""
        state, now = self.state(), self.clock()
        folder = Path(state['folder']) / SUBFOLDER if state['folder'] else None
        reachable = bool(folder and Path(state['folder']).is_dir())
        period = 7 * 86400 if state['every'] == 'week' else 86400
        success = _past(state['last_success'], now)
        never = bool(state['enabled'] and not success and state['last_error'])
        return {'enabled': state['enabled'], 'folder': state['folder'], 'backups_in': str(folder) if folder else '', 'every': state['every'], 'at': state['at'],
                'folder_reachable': reachable, 'last_success': success, 'last_id': state['last_id'], 'last_attempt': _past(state['last_attempt'], now),
                'last_error': state['last_error'], 'kept': len(state['made']), 'ids': [row['id'] for row in state['made']], 'next_due': next_due(state, now),
                # overdue: on, but no automatic backup has succeeded for more than two periods. never_succeeded: on, and
                # the first one has not worked yet. stop_holds: nothing starts while the emergency stop holds.
                'overdue': bool(state['enabled'] and success and now - success > 2 * period + 3600), 'never_succeeded': never,
                'stop_holds': bool(self.stopped()), 'running': self.lock.locked()}

    def configure(self, folder, every, at):
        """The owner picks the folder and the schedule: this turns automatic backups on."""
        folder, every, at = clean_settings(folder, every, at)
        if not Path(folder).is_dir():
            raise BackupSetting('That folder does not exist or its drive is not connected. Create or connect it first.')
        try:
            self.make(str(Path(folder) / SUBFOLDER))  # refuses a folder inside JARVIS's own data or program, and creates the subfolder
        except ValueError:
            raise BackupSetting("That folder is inside JARVIS's own program or data folder. Choose a folder somewhere else, for example on the backup drive.") from None
        except OSError:
            raise BackupSetting('JARVIS cannot create its backup folder there (is the folder or the drive write-protected?). Choose another folder.') from None

        def settings(state):
            if state['folder'] != folder:
                # Another folder: the schedule starts afresh there (the first backup is made at the next idle moment).
                # The backups in the old folder stay where they are and are no longer thinned.
                state.update(last_success=None, last_id=None, made=[])
            state.update(folder=folder, every=every, at=at, enabled=True, last_error='', last_attempt=None)
        self.change(settings)
        self.unsaved_until = 0
        self.note('automatic backups', 'on: ' + every)
        return self.status()

    def turn_off(self):
        self.change(lambda state: state.update(enabled=False))
        self.note('automatic backups', 'off')
        return self.status()

    def run_if_due(self):
        """Called about once a minute by the Core. Returns the status after a backup was tried, else None."""
        now = self.clock()
        if now < self.unsaved_until or not due(self.state(), now) or self.stopped() or not self.idle():
            return None
        return self.run()

    def run(self):
        """Make one automatic backup now, verify it, and thin the older ones."""
        if not self.lock.acquire(False):
            return None
        try:
            state, now = self.state(), self.clock()
            folder = state['folder']
            if not folder:
                raise BackupSetting('Choose the folder for automatic backups first.')
            try:
                try:
                    if not Path(folder).is_dir():
                        raise BackupSetting('The backup folder is not reachable (is the drive connected?).')
                    service = self.make(str(Path(folder) / SUBFOLDER))
                    if hasattr(service, 'folder'):
                        sweep(service.folder, now)
                    result = service.create()  # made and verified exactly as a backup made by hand
                except Exception as exc:
                    reason = _reason(exc)
                    self.change(lambda fresh: fresh.update(last_attempt=now, last_error=reason) if fresh['folder'] == folder else None)
                    self.note('automatic backup', 'failed')
                    return self.status()
                # The record is read again here: what the owner changed while the backup was being made (switched
                # off, another schedule) stays. After a change of folder this backup belongs to the old one, which
                # is no longer on the record.
                row = {'id': result['id'], 'created': now, 'bytes': result.get('bytes')}
                fresh = self.change(lambda fresh: fresh.update(made=[r for r in fresh['made'] if r['id'] != row['id']] + [row], last_attempt=now,
                                                               last_success=now, last_id=row['id'], last_error='') if fresh['folder'] == folder else None)
                removed = []
                if fresh['folder'] == folder and fresh['enabled'] and not self.stopped():
                    for ident in thin(fresh['made'], now):
                        try:
                            archive = service.archive(ident)
                            archive.unlink(missing_ok=True)
                            (archive.parent / (ident + '.restore-check.json')).unlink(missing_ok=True)
                            removed.append(ident)
                        except (OSError, ValueError):
                            continue  # cannot be removed now: stays on the list and is tried again next time
                    if removed:
                        self.change(lambda fresh: fresh.update(made=[r for r in fresh['made'] if r['id'] not in removed]) if fresh['folder'] == folder else None)
                self.unsaved_until = 0
                self.note('automatic backup', 'verified' + (f'; {len(removed)} old removed' if removed else '') + ('' if fresh['folder'] == folder else '; the folder was changed meanwhile'))
            except Exception:
                # The record itself could not be saved (a full system disk, a locked database). Without it the schedule
                # would see "nothing made" and make a full backup every minute: wait as after a failure instead.
                self.unsaved_until = now + RETRY_SECONDS
                try:
                    self.note('automatic backup', 'its record could not be saved')
                except Exception:
                    pass
            return self.status()
        finally:
            self.lock.release()
