"""Automatic backups (release 1.0.15, scope item 6; master document section 11).

On a schedule the owner sets, to a folder the owner chooses (for example a backup drive), each one made and
verified by recovery.Recovery exactly as a backup made by hand, and old automatic backups thinned out.
Off until the owner picks a folder. Nothing here uploads anything.

The rules, in one place:
  - a backup is made only while JARVIS is idle and not under an emergency stop; a missed one is made at the
    next chance (a PC that was off at the chosen time catches up when JARVIS next runs);
  - only backups this module made are ever thinned; a backup made by hand in the same folder is never touched;
  - the newest automatic backup is always kept;
  - a failure is recorded with its reason and tried again an hour later, not every minute.
"""
import datetime
import threading
import time
from pathlib import Path

SUBFOLDER = 'JARVIS automatic backups'
EVERY = ('day', 'week')
RETRY_SECONDS = 3600
KEEP_ALL_DAYS, KEEP_WEEKLY_WEEKS, KEEP_MONTHLY_DAYS = 7, 8, 365
DEFAULT = {'folder': '', 'every': 'day', 'at': '12:00', 'enabled': False, 'last_success': None, 'last_id': None,
           'last_attempt': None, 'last_error': '', 'made': []}


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
    try:
        hour, minute = text.split(':')
        if len(hour) == 2 and len(minute) == 2 and 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59:
            return int(hour), int(minute)
    except (ValueError, AttributeError):
        pass
    return None


def _planned_before(now, at):
    """The latest planned time of day at or before `now`, in local time: today's if it has passed, else yesterday's."""
    hour, minute = _time_of_day(at) or (12, 0)
    moment = datetime.datetime.fromtimestamp(now)
    planned = moment.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return planned if planned <= moment else planned - datetime.timedelta(days=1)


def _gap(every):
    """How far a planned moment must lie after the last success to count. A day: at least half a day, so a
    backup that was caught up late is not repeated a few hours later. A week: seven days, less an hour of slack."""
    return 7 * 86400 - 3600 if every == 'week' else 12 * 3600


def _retry_at(state):
    attempt, success = state.get('last_attempt'), state.get('last_success')
    return attempt + RETRY_SECONDS if attempt and (not success or attempt > success) else 0


def due(state, now):
    """Is an automatic backup due at `now` (seconds since the epoch, judged in local time)?"""
    if not state.get('enabled') or not state.get('folder'):
        return False
    if now < _retry_at(state):
        return False  # the last try failed less than an hour ago
    success = state.get('last_success')
    if not success:
        return True  # never made one: the first is made at once, whatever the time of day
    return _planned_before(now, state.get('at', '')).timestamp() - success >= _gap(state.get('every'))


def next_due(state, now):
    """When the next automatic backup is planned (None when off); for the owner's screen."""
    if not state.get('enabled') or not state.get('folder'):
        return None
    if due(state, now):
        return now
    success, retry = state.get('last_success'), _retry_at(state)
    if not success:
        return retry
    planned = _planned_before(now, state.get('at', '')) + datetime.timedelta(days=1)
    while planned.timestamp() - success < _gap(state.get('every')):
        planned += datetime.timedelta(days=1)
    return max(planned.timestamp(), retry)


def thin(made, now):
    """The ids of automatic backups to delete. Kept: every backup of the last 7 days; then the newest of each
    week for 8 weeks; then the newest of each month up to a year; and always the newest of all."""
    rows = sorted((r for r in made if isinstance(r.get('created'), (int, float))), key=lambda r: r['created'], reverse=True)
    keep, weeks, months = set(), set(), set()
    for index, row in enumerate(rows):
        age_days = (now - row['created']) / 86400
        stamp = datetime.datetime.fromtimestamp(row['created'])
        if index == 0 or age_days <= KEEP_ALL_DAYS:
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


class AutoBackup:
    """load() and save(state) keep the settings and the record of what was made (the Core's database, out of
    reach of the settings page and of a restored JSON backup). make(folder) returns a recovery.Recovery for it."""

    def __init__(self, load, save, make, clock=time.time, idle=lambda: True, stopped=lambda: False, note=lambda action, status: None):
        self.load, self.save, self.make, self.clock, self.idle, self.stopped, self.note = load, save, make, clock, idle, stopped, note
        self.lock = threading.Lock()

    def state(self):
        return {**DEFAULT, **(self.load() or {})}

    def status(self):
        """What Settings > Backups shows."""
        state, now = self.state(), self.clock()
        folder = Path(state['folder']) / SUBFOLDER if state['folder'] else None
        reachable = bool(folder and Path(state['folder']).is_dir())
        period = 7 * 86400 if state['every'] == 'week' else 86400
        late = bool(state['enabled'] and state['last_success'] and now - state['last_success'] > 2 * period + 3600)
        return {'enabled': state['enabled'], 'folder': state['folder'], 'backups_in': str(folder) if folder else '', 'every': state['every'], 'at': state['at'],
                'folder_reachable': reachable, 'last_success': state['last_success'], 'last_id': state['last_id'], 'last_attempt': state['last_attempt'],
                'last_error': state['last_error'], 'kept': len(state['made']), 'next_due': next_due(state, now),
                # True: on, but no automatic backup has succeeded for more than two periods.
                'overdue': late or bool(state['enabled'] and not state['last_success'] and state['last_error'])}

    def configure(self, folder, every, at):
        """The owner picks the folder and the schedule: this turns automatic backups on."""
        folder, every, at = clean_settings(folder, every, at)
        if not Path(folder).is_dir():
            raise BackupSetting('That folder does not exist or its drive is not connected. Create or connect it first.')
        self.make(str(Path(folder) / SUBFOLDER))  # refuses a folder inside JARVIS's own data or program, and creates the subfolder
        state = self.state()
        state.update(folder=folder, every=every, at=at, enabled=True, last_error='', last_attempt=None)
        self.save(state)
        self.note('automatic backups', 'on: ' + every)
        return self.status()

    def turn_off(self):
        state = self.state()
        state.update(enabled=False)
        self.save(state)
        self.note('automatic backups', 'off')
        return self.status()

    def run_if_due(self):
        """Called about once a minute by the Core. Returns the status after a backup was tried, else None."""
        state = self.state()
        if not due(state, self.clock()) or self.stopped() or not self.idle():
            return None
        return self.run()

    def run(self):
        """Make one automatic backup now, verify it, and thin the older ones."""
        if not self.lock.acquire(False):
            return None
        try:
            state, now = self.state(), self.clock()
            if not state['folder']:
                raise BackupSetting('Choose the folder for automatic backups first.')
            state['last_attempt'] = now
            try:
                if not Path(state['folder']).is_dir():
                    raise BackupSetting('The backup folder is not reachable (is the drive connected?).')
                service = self.make(str(Path(state['folder']) / SUBFOLDER))
                result = service.create()  # made and verified exactly as a backup made by hand
                state['made'] = [r for r in state['made'] if r.get('id') != result['id']] + [{'id': result['id'], 'created': now, 'bytes': result.get('bytes')}]
                state.update(last_success=now, last_id=result['id'], last_error='')
                removed = []
                for ident in thin(state['made'], now):
                    try:
                        archive = service.archive(ident)
                        archive.unlink(missing_ok=True)
                        (archive.parent / (ident + '.restore-check.json')).unlink(missing_ok=True)
                        removed.append(ident)
                    except (OSError, ValueError):
                        continue  # cannot be removed now: stays on the list and is tried again next time
                state['made'] = [r for r in state['made'] if r['id'] not in removed]
                self.save(state)
                self.note('automatic backup', 'verified' + (f'; {len(removed)} old removed' if removed else ''))
            except Exception as exc:
                # Our own messages are fit to show; anything else is reduced to its kind, never a path or content.
                state['last_error'] = str(exc) if isinstance(exc, ValueError) and len(str(exc)) <= 300 else type(exc).__name__
                self.save(state)
                self.note('automatic backup', 'failed')
            return self.status()
        finally:
            self.lock.release()
