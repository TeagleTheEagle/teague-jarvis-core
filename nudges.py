"""The owner's routine, the nudges it gives, and the notices JARVIS keeps (item F of docs/PHONE-ACCESS-PLAN.md;
JARVIS's own wish: "time-aware nudges tied to your actual routine: one prompt at a collision point, never nagging").

- Routine: the owner's week as blocks (days, start, end, label) in the table `routine`, kept in Settings > Routine.
- A collision: an open task with a due time, or a reminder, due inside a routine block or within an hour after it,
  found when the block is about to start (within 15 minutes) or is running. One nudge per collision, ever (the
  table `notices` keeps a key for it); none while the emergency stop holds or in quiet hours.
- Notices: everything JARVIS has to say on its own (a nudge, an announcement a device asked for, something new
  waiting for approval, a system note), kept in the table `notices`, shown on the PC, spoken when the owner's
  "proactive" setting is on, and listed to paired devices (the `notices` op; docs/MAC-REQUESTS-20261007.md).
The clock (`start_nudges`) looks once a minute, like the automatic backups' clock.
"""
import datetime
import re
import threading
import time
import uuid

DAYS = ('MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU')
TIME = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
MAX_BLOCKS = 40
KINDS = ('nudge', 'announce', 'approval', 'system')
KEEP = 500           # notices kept; older ones go
SOON_MINUTES = 15    # a block about to start
AFTER_MINUTES = 60   # a due time shortly after a block still collides with it


class RoutineError(ValueError):
    """Said as it is."""


def _minutes(value):
    match = TIME.match(str(value or '').strip())
    if not match:
        raise RoutineError('Give a time as HH:MM, for example 18:30.')
    return int(match.group(1)) * 60 + int(match.group(2))


def _days(value):
    if isinstance(value, str):
        value = [d for d in value.replace(' ', '').split(',') if d]
    if not isinstance(value, (list, tuple)) or not value or any(str(d).upper() not in DAYS for d in value):
        raise RoutineError('Choose the days as MO, TU, WE, TH, FR, SA, SU.')
    return ','.join(sorted({str(d).upper() for d in value}, key=DAYS.index))


class Routine:
    """The owner's week as blocks. A block: id, days ('MO,TU,...'), start and end ('HH:MM', the end after the
    start, both on the same day), label (what the owner calls it: work, gym, school)."""

    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS routine (id TEXT PRIMARY KEY, days TEXT NOT NULL, start TEXT NOT NULL, end TEXT NOT NULL, label TEXT NOT NULL, created REAL NOT NULL)')

    def blocks(self):
        with self.store.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM routine ORDER BY start, created')]

    def add(self, days, start, end, label):
        days = _days(days)
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 40 or re.search(r'[\x00-\x1f<>]', label):
            raise RoutineError('A block has a label of 1 to 40 characters.')
        if _minutes(start) >= _minutes(end):
            raise RoutineError('A block ends after it starts, on the same day. Split a night shift into two blocks.')
        with self.store.connect() as db:
            if db.execute('SELECT COUNT(*) FROM routine').fetchone()[0] >= MAX_BLOCKS:
                raise RoutineError(f'At most {MAX_BLOCKS} blocks. Remove one first.')
            row = {'id': uuid.uuid4().hex, 'days': days, 'start': str(start).strip(), 'end': str(end).strip(), 'label': label.strip(), 'created': time.time()}
            db.execute('INSERT INTO routine(id,days,start,end,label,created) VALUES (:id,:days,:start,:end,:label,:created)', row)
        return row

    def remove(self, block_id):
        with self.store.connect() as db:
            if not db.execute('DELETE FROM routine WHERE id=?', (str(block_id),)).rowcount:
                raise RoutineError('No such block.')
        return {'removed': str(block_id)}


class Notices:
    """What JARVIS has to say on its own, kept so the PC and the devices can show it. `key` makes a notice happen
    once: a second add with the same key returns None."""

    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS notices (id TEXT PRIMARY KEY, kind TEXT NOT NULL, text TEXT NOT NULL, created REAL NOT NULL, key TEXT UNIQUE, spoken INTEGER NOT NULL DEFAULT 0)')

    def add(self, kind, text, key=None, spoken=False):
        if kind not in KINDS:
            raise ValueError('Unknown kind of notice.')
        text = ' '.join(str(text or '').split())[:600]
        if not text:
            raise ValueError('A notice says something.')
        row = {'id': uuid.uuid4().hex, 'kind': kind, 'text': text, 'created': time.time(), 'key': key, 'spoken': int(bool(spoken))}
        with self.store.connect() as db:
            if key and db.execute('SELECT 1 FROM notices WHERE key=?', (key,)).fetchone():
                return None
            db.execute('INSERT INTO notices(id,kind,text,created,key,spoken) VALUES (:id,:kind,:text,:created,:key,:spoken)', row)
            # The newest KEEP of this kind stay. Pruned per kind, so a flood of announcements never removes today's nudge
            # keys (the nudge would be raised again).
            db.execute('DELETE FROM notices WHERE kind=? AND id NOT IN (SELECT id FROM notices WHERE kind=? ORDER BY created DESC, rowid DESC LIMIT ?)', (kind, kind, KEEP))
        return row

    def mark_spoken(self, notice_id):
        with self.store.connect() as db:
            db.execute('UPDATE notices SET spoken=1 WHERE id=?', (notice_id,))

    def drop(self, key):
        """A keyed notice that no longer applies (an approval answered or run out) goes."""
        with self.store.connect() as db:
            return db.execute('DELETE FROM notices WHERE key=?', (str(key),)).rowcount

    @staticmethod
    def _where(after, kinds):
        clauses, values = [], []
        if after is not None:
            clauses.append('created >= ?')  # the same tick as the mark counts as new
            values.append(float(after))
        if kinds is not None:
            kinds = sorted(set(kinds)) or ['']
            clauses.append('kind IN (' + ','.join('?' * len(kinds)) + ')')
            values.extend(kinds)
        return (' WHERE ' + ' AND '.join(clauses) if clauses else ''), values

    def recent(self, limit=50, after=None, kinds=None):
        """Newest first; `after` an epoch time (at or after it); `kinds` a set of kinds to include; at most 200."""
        where, values = self._where(after, kinds)
        with self.store.connect() as db:
            return [dict(r) for r in db.execute('SELECT id,kind,text,created,spoken FROM notices' + where + ' ORDER BY created DESC, rowid DESC LIMIT ?',
                                                values + [max(1, min(int(limit), 200))])]

    def count_after(self, after, kinds=None):
        where, values = self._where(after, kinds)
        with self.store.connect() as db:
            return db.execute('SELECT COUNT(*) FROM notices' + where, values).fetchone()[0]


def collisions(blocks, tasks, reminders, now):
    """The nudges due now: for each routine block that is about to start or running today, the open tasks and the
    reminders due inside it or within an hour after it. Returns [{'key', 'text', 'block', 'item'}]."""
    found = []
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)  # local wall-clock time, as the due times below (fromtimestamp) are
    today = now.date()
    day = DAYS[now.weekday()]
    minute = now.hour * 60 + now.minute
    for block in blocks:
        if day not in block['days'].split(','):
            continue
        start, end = _minutes(block['start']), _minutes(block['end'])
        if not (start - SOON_MINUTES <= minute < end):
            continue
        # Naive local times throughout: the C library places each due time in its own offset, so a day on which the
        # clocks change is still read right (a fixed offset taken from `now` would be an hour off after the change).
        window_start = datetime.datetime.combine(today, datetime.time(start // 60, start % 60))
        window_end = datetime.datetime.combine(today, datetime.time(end // 60, end % 60))
        late_end = window_end + datetime.timedelta(minutes=AFTER_MINUTES)
        items = [('task', t['id'], t['body'], t.get('due')) for t in tasks if t.get('due') and not t.get('completed')]
        items += [('reminder', r['id'], r['title'], r.get('due')) for r in reminders if r.get('due') and not r.get('fired')]
        for kind, ident, title, due in items:
            when = datetime.datetime.fromtimestamp(float(due))
            if not (window_start <= when < late_end) or when < now:
                continue
            at = when.strftime('%H:%M')
            title = ' '.join(str(title).split())
            title = title[:77].rstrip() + '...' if len(title) > 80 else title  # a long task body is not read out whole
            if when < window_end:
                text = f'"{title}" is due at {at}, during {block["label"]} ({block["start"]} to {block["end"]}).'
            else:
                text = f'{block["label"]} runs till {block["end"]}; "{title}" is due at {at}.'
            found.append({'key': f'{kind}:{ident}:{block["id"]}:{today.isoformat()}', 'text': text, 'block': block['id'], 'item': ident})
    return found


class Clock:
    """Once a minute: the collisions of the moment become nudges, each once. `notify(notice)` is the Core's: it
    shows and speaks the notice as the owner's settings allow."""

    def __init__(self, routine, notices, tasks, reminders, settings, stopped, notify, now=None):
        self.routine, self.notices, self.tasks, self.reminders = routine, notices, tasks, reminders
        self.settings, self.stopped, self.notify, self.now = settings, stopped, notify, now or datetime.datetime.now  # naive local time

    def run_once(self):
        if self.stopped():
            return []
        blocks = self.routine.blocks()
        if not blocks:
            return []
        if self.settings().get('quiet_hours'):
            return []
        made = []
        for hit in collisions(blocks, self.tasks(), self.reminders(), self.now()):
            notice = self.notices.add('nudge', hit['text'], key=hit['key'])
            if notice:
                made.append(notice)
                try:
                    self.notify(notice)
                except Exception:
                    pass  # the nudge is kept whatever the speaking does
        return made


def start_nudges(clock, first=90, every=60, stop=None):
    """The quiet clock in the Core, like the automatic backups': a look once a minute. `stop` ends it."""
    if clock is None:
        return None
    stop = stop or threading.Event()

    def tick():
        wait = first
        while not stop.wait(wait):
            wait = every
            try:
                clock.run_once()
            except Exception:
                pass  # a failed look is not worth stopping the clock for
    thread = threading.Thread(target=tick, name='routine-nudges', daemon=True)
    thread.start()
    return thread
