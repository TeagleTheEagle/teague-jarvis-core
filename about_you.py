"""What JARVIS knows about the owner's life, the You page (release 1.0.19; the owner's "lets make jarvis and me more connected
personally", choosing "He knows my life"; record docs/ABOUT-YOU.md).

The "You" panel at the top of the Memory section holds a few lines about the owner, the people who matter (with a
relation and a birthday), the dates to remember, likes, dislikes and goals. JARVIS reads a short summary of it with
every question, upcoming dates first (context); he reads the rest with the about_you tool; and he offers to add to it
with remember_about_you, which waits for the owner's OK on screen. Nothing is guessed in the background and nothing is
saved without the owner: the owner's own clicks on the panel, or an approval card the owner approves.

Everything here goes to the AI provider with the owner's questions, as the saved facts always have. Passwords, keys
and tokens are refused (content_guard's secret patterns)."""
import calendar
import datetime
import json
import re
import time
import uuid

import content_guard

SECTIONS = ('about', 'person', 'date', 'like', 'dislike', 'goal')
SECTION_NAMES = {'about': 'About you', 'person': 'People', 'date': 'Dates', 'like': 'Likes', 'dislike': 'Dislikes',
                 'goal': 'Goals'}
MAX_ENTRIES = 300
MAX_TITLE = {'about': 200, 'person': 80, 'date': 80, 'like': 120, 'dislike': 120, 'goal': 160}
MAX_DETAIL = 300
UPCOMING_DAYS = 30
CONTEXT_CHARS = 2500   # the summary in every question's context, as JSON
MONTHS = tuple(calendar.month_name)[1:]

GUIDANCE = ('The owner\'s "You" page (context about_owner) holds what they told JARVIS about their life: a few lines about'
            ' them, the people who matter, dates to remember, likes, dislikes and goals. Use it as someone who knows them'
            ' would: people by name and relation, an upcoming birthday or date when it fits the conversation; never recite'
            ' it. about_you reads all of it. When the owner tells you something personal that is worth keeping (a person, a'
            ' date, a like, a goal), you may offer to remember it with remember_about_you: at most one offer per answer,'
            ' only what the owner said about themselves or the people close to them, never passwords, keys or account'
            ' numbers, and health or money only when the owner asks to remember it. It waits for the owner\'s OK on screen'
            ' and nothing is saved until then: say you have offered, never that it is saved.')
_CONTROL = re.compile(r'[\x00-\x08\x0b-\x1f\x7f<>]')


class ProfileError(ValueError):
    """Said as it is."""


def parse_date(text):
    """'YYYY-MM-DD', 'MM-DD' or '' -> (month, day, year or None), or (None, None, None) for ''."""
    text = str(text or '').strip()
    if not text:
        return None, None, None
    match = re.fullmatch(r'(?:(\d{4})-)?(\d{1,2})-(\d{1,2})', text)
    if not match:
        raise ProfileError('Give a date as YYYY-MM-DD, or MM-DD when the year is not known.')
    year = int(match.group(1)) if match.group(1) else None
    return int(match.group(2)), int(match.group(3)), year


def _check_date(month, day, year):
    if month is None and day is None and year is None:
        return None, None, None
    try:
        month, day = int(month), int(day)
        year = int(year) if year not in (None, '') else None
    except (TypeError, ValueError):
        raise ProfileError('A date has a month and a day, and the year if it is known.') from None
    if not 1 <= month <= 12 or not 1 <= day <= calendar.monthrange(2000, month)[1]:   # 2000 is a leap year: 29 February is allowed
        raise ProfileError('That day does not exist in that month.')
    this_year = datetime.date.today().year
    if year is not None:
        if not 1900 <= year <= this_year + 1:
            raise ProfileError(f'A year is between 1900 and {this_year + 1}.')
        if day > calendar.monthrange(year, month)[1]:
            raise ProfileError('That day does not exist in that year.')
    return month, day, year


def _text(value, limit, what):
    value = ' '.join(str(value or '').split())
    if len(value) > limit:
        raise ProfileError(f'{what} has at most {limit} characters.')
    if _CONTROL.search(value):
        raise ProfileError(f'{what} cannot hold < or > or control characters.')
    if any(kind == 'secret' for kind, _ in content_guard.clean(value)[1]):
        raise ProfileError('Passwords, keys and tokens do not belong on the You page.')
    return value


def occurs(month, day, year_now):
    """The date a yearly month/day falls on in a year: 29 February is kept on 28 February in other years."""
    return datetime.date(year_now, month, min(day, calendar.monthrange(year_now, month)[1]))


def next_on(month, day, today):
    """The next time a yearly month/day comes round, today included."""
    when = occurs(month, day, today.year)
    return when if when >= today else occurs(month, day, today.year + 1)


def date_words(month, day, year=None):
    return f'{day} {MONTHS[month - 1]}' + (f' {year}' if year else '')


class Profile:
    """The rows of the You page. A row: id, section (SECTIONS), title (the line itself, a person's name or a date's
    name), detail (a relation or a note), month/day/year (a person's birthday or a date's day; the year may be unknown),
    created, updated, release (the JARVIS release it was saved under, as the saved facts)."""

    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS profile (id TEXT PRIMARY KEY, section TEXT NOT NULL, title TEXT NOT NULL, '
                       "detail TEXT NOT NULL DEFAULT '', month INTEGER, day INTEGER, year INTEGER, created REAL NOT NULL, "
                       'updated REAL NOT NULL, release TEXT)')

    def entries(self, section=None):
        with self.store.connect() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM profile ORDER BY created')]
        if section is not None:
            rows = [r for r in rows if r['section'] == section]
        return sorted(rows, key=lambda r: (SECTIONS.index(r['section']) if r['section'] in SECTIONS else len(SECTIONS), r['title'].casefold()))

    def check(self, section, title, detail='', month=None, day=None, year=None):
        """The fields of one row as they would be saved, or ProfileError said plainly."""
        if section not in SECTIONS:
            raise ProfileError('A section is one of: ' + ', '.join(SECTIONS) + '.')
        title = _text(title, MAX_TITLE[section], 'The ' + ('name' if section in ('person', 'date') else 'line'))
        if not title:
            raise ProfileError('Write the ' + ('name' if section in ('person', 'date') else 'line') + ' first.')
        detail = _text(detail, MAX_DETAIL, 'The detail')
        month, day, year = _check_date(month, day, year)
        if section == 'date' and month is None:
            raise ProfileError('A date to remember needs its day and month.')
        if section not in ('person', 'date') and month is not None:
            raise ProfileError('Only a person (a birthday) or a date to remember has a date.')
        return {'section': section, 'title': title, 'detail': detail, 'month': month, 'day': day, 'year': year}

    def add(self, section, title, detail='', month=None, day=None, year=None):
        fields = self.check(section, title, detail, month, day, year)
        now = time.time()
        with self.store.connect() as db:
            if db.execute('SELECT COUNT(*) FROM profile').fetchone()[0] >= MAX_ENTRIES:
                raise ProfileError(f'The You page holds at most {MAX_ENTRIES} entries. Remove one first.')
            same = db.execute('SELECT id FROM profile WHERE section=? AND lower(title)=lower(?) AND detail=? AND month IS ? AND day IS ? AND year IS ?',
                              (fields['section'], fields['title'], fields['detail'], fields['month'], fields['day'], fields['year'])).fetchone()
            if same:
                return self.get(same['id'])   # the same entry twice is kept once
            row = {'id': uuid.uuid4().hex, **fields, 'created': now, 'updated': now, 'release': getattr(self.store, 'release', None)}
            db.execute('INSERT INTO profile(id,section,title,detail,month,day,year,created,updated,release) '
                       'VALUES (:id,:section,:title,:detail,:month,:day,:year,:created,:updated,:release)', row)
        return row

    def get(self, entry_id):
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM profile WHERE id=?', (str(entry_id),)).fetchone()
        if not row:
            raise ProfileError('No such entry on the You page.')
        return dict(row)

    def update(self, entry_id, **changes):
        row = self.get(entry_id)
        merged = {key: changes.get(key, row[key]) for key in ('title', 'detail', 'month', 'day', 'year')}
        fields = self.check(row['section'], **merged)
        with self.store.connect() as db:
            db.execute('UPDATE profile SET title=:title, detail=:detail, month=:month, day=:day, year=:year, updated=:updated, release=:release WHERE id=:id',
                       {**fields, 'id': row['id'], 'updated': time.time(), 'release': getattr(self.store, 'release', None)})
        return self.get(row['id'])

    def remove(self, entry_id):
        row = self.get(entry_id)
        with self.store.connect() as db:
            db.execute('DELETE FROM profile WHERE id=?', (row['id'],))
        return {'removed': row['id'], 'title': row['title']}

    def upcoming(self, today=None, days=UPCOMING_DAYS):
        """The birthdays and dates within `days` of today, soonest first: entry, date, days until, and the age or the
        number of years when the year is known."""
        today = today or datetime.date.today()
        soon = []
        for row in self.entries():
            if row['section'] not in ('person', 'date') or row['month'] is None:
                continue
            when = next_on(row['month'], row['day'], today)
            until = (when - today).days
            if until <= days:
                soon.append({'entry': row, 'date': when, 'days': until, 'years': when.year - row['year'] if row['year'] else None})
        return sorted(soon, key=lambda s: (s['days'], s['entry']['title'].casefold()))

    @staticmethod
    def line(row):
        """One entry in plain words: "Will (brother), birthday 14 March 1996", "Wedding anniversary: 20 June 2020"."""
        title, detail = row['title'], row['detail']
        if row['section'] == 'person':
            text = title + (f' ({detail})' if detail else '')
            return text + (', birthday ' + date_words(row['month'], row['day'], row['year']) if row['month'] else '')
        if row['section'] == 'date':
            return title + ': ' + date_words(row['month'], row['day'], row['year']) + (f' ({detail})' if detail else '')
        return title + (f' ({detail})' if detail else '')

    @staticmethod
    def soon_words(item):
        row, days = item['entry'], item['days']
        when = 'today' if days == 0 else 'tomorrow' if days == 1 else f'in {days} days'
        name = (row['title'] + '’s birthday') if row['section'] == 'person' else row['title']
        years = item['years']
        extra = (f', turns {years}' if row['section'] == 'person' else f', {years} years') if years else ''
        return f"{name}: {when}, {item['date'].strftime('%A')} {item['date'].day} {MONTHS[item['date'].month - 1]}{extra}"

    def context(self, today=None):
        """The summary every question carries (about_owner), or None when the page is empty: what is coming up and the
        lines about the owner first, then the people, dates, goals, likes and dislikes, newest first, to CONTEXT_CHARS;
        what does not fit is counted, to be read with about_you."""
        rows = self.entries()
        if not rows:
            return None
        today = today or datetime.date.today()
        summary = {'today': today.isoformat(), 'coming_up': [self.soon_words(s) for s in self.upcoming(today)[:6]]}
        keys = {'about': 'about', 'person': 'people', 'date': 'dates', 'goal': 'goals', 'like': 'likes', 'dislike': 'dislikes'}
        room = CONTEXT_CHARS - len(json.dumps({'more': f'{MAX_ENTRIES} more on the You page: read them with about_you.'}))   # the count's own line
        left = 0
        for section in ('about', 'person', 'date', 'goal', 'like', 'dislike'):
            for row in sorted((r for r in rows if r['section'] == section), key=lambda r: r['updated'], reverse=True):
                trial = {**summary, keys[section]: summary.get(keys[section], []) + [self.line(row)]}
                if len(json.dumps(trial, ensure_ascii=False)) > room:
                    left += 1
                    continue
                summary = trial
        if not summary['coming_up']:
            del summary['coming_up']
        if left:
            summary['more'] = f'{left} more on the You page: read them with about_you.'
        return summary

    def search(self, query=''):
        """The entries whose words hold the query's words (all of them for an empty query), as lines."""
        words = [w for w in re.findall(r'\w+', str(query or '').casefold()) if len(w) > 1]
        found = []
        for row in self.entries():
            text = (self.line(row) + ' ' + SECTION_NAMES[row['section']]).casefold()
            if all(w in text for w in words):
                found.append({'section': SECTION_NAMES[row['section']], 'line': self.line(row), 'id': row['id']})
        return found
