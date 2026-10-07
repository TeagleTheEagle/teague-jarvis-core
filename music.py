"""Music by nickname from the owner's own files (release 1.0.16, item 5; docs/MUSIC.md).

"Jarvis, play workshop warrior": the Core answers these commands itself, with no AI in the loop, and plays the
owner's own music files through Windows' own media interface (winmm, the part of Windows that has played sound
files since Windows 95; no extra package). So the music plays whether the JARVIS window is open, minimised or in
the tray, and pause, resume, stop and volume are immediate. One song at a time.

The files live in a folder the owner fills (MP3 is the safe choice, WAV works too); a nickname points at a file
(table `music`, in the database and so in every backup; the files themselves are not backed up). The emergency stop
stops the music with everything else. The tool row is `play_music` (permissions.py): the owner's switch applies,
and the AI model may call it for phrasings the Core did not recognise.
"""
import ctypes
import re
import sys
import queue
import threading
import time
from pathlib import Path

import permissions

FORMATS = ('.mp3', '.wav')
ALIAS = 'jarvismusic'
DEFAULT_VOLUME = 80
VOLUME_STEP = 10
_NICKNAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9 '&.-]{0,59}")
_WORDS = re.compile(r'[^a-z0-9]+')
# Words that name nothing on their own: "play it", "play the" never pick a song by these alone.
FILLER = frozenset(('a', 'an', 'the', 'it', 'to', 'in', 'of', 'on', 'my', 'me', 'some', 'please', 'song', 'music', 'track', 'and', 'for'))


class MusicError(ValueError):
    """Something about the music that cannot be done; the message is fit to show and to speak."""


def normalise(text):
    """Lower case, letters and digits only, one space between words: how spoken names are compared."""
    return _WORDS.sub(' ', (text or '').lower()).strip()


def title_of(file):
    """What JARVIS calls a song: the file name without its ending."""
    return Path(file).stem


class MediaTimeout(MusicError):
    """The media interface did not answer in time (a stalled driver or drive): the one error after which the player
    cannot know whether a device is open."""


# ---- Windows' media interface ----
class Mci:
    """winmm.dll's mciSendString, every command sent from one long-lived thread of its own. Windows ties a device
    opened through the media interface to the thread that opened it: once that thread has ended, every other thread
    is told "The specified device is not open or is not recognized by MCI" while the sound plays on. The Core answers
    each request on its own thread, so in 1.0.16 a song opened by the "play" request could not be stopped, paused or
    even seen by the next request (seen by the owner on 2026-10-07: "Playing Daddy's Home." then "Nothing was
    playing."). Here one daemon thread owns every device for the life of the process. Not available off Windows."""

    THREAD = 'jarvis-music-mci'
    WAIT = 10   # seconds for one command; the media interface answers at once in practice (review of 2026-10-07, M3)

    def __init__(self):
        self.lock = threading.Lock()
        self.winmm = ctypes.windll.winmm if sys.platform == 'win32' else None
        self.queue = queue.Queue()
        self.thread = None
        self.stuck = False   # a command did not come back in time: later commands are refused at once until it does

    def _send_here(self, command):
        """One command on the calling thread (the worker's)."""
        answer = ctypes.create_unicode_buffer(512)
        code = self.winmm.mciSendStringW(command, answer, 511, None)
        if code:
            text = ctypes.create_unicode_buffer(512)
            self.winmm.mciGetErrorStringW(code, text, 511)
            raise MusicError((text.value or f'Windows media error {code}').rstrip('.') + '.')
        return answer.value

    def _work(self):
        while True:
            command, done = self.queue.get()
            try:
                done['result'] = self._send_here(command)
            except BaseException as exc:  # handed back to the caller; the worker lives on
                done['error'] = exc
            finally:
                self.stuck = False   # the interface answered, late or not: commands flow again
                done['event'].set()

    def send(self, command):
        if self.winmm is None:
            raise MusicError('Music plays on Windows only.')
        if self.stuck:
            raise MediaTimeout('Windows is not answering music commands; the music waits until it does.')
        with self.lock:
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self._work, name=self.THREAD, daemon=True)
                self.thread.start()
        done = {'event': threading.Event()}
        self.queue.put((command, done))
        if not done['event'].wait(self.WAIT):
            self.stuck = True
            raise MediaTimeout('Windows did not answer the music command in time.')
        if 'error' in done:
            raise done['error']
        return done['result']


def short_path(path):
    """The 8.3 form of a path on Windows when the volume keeps one (the media interface takes at most 260 characters,
    and plain ASCII is safest); otherwise the path itself, which the player quotes."""
    path = str(path)
    if sys.platform != 'win32':
        return path
    buffer = ctypes.create_unicode_buffer(1024)
    length = ctypes.windll.kernel32.GetShortPathNameW(path, buffer, 1024)
    return buffer.value if 0 < length < 1024 else path


class Player:
    """One song at a time through the media interface. `mci` is replaced in the tests by a recorder; `blocked` is
    asked right before a song opens (the emergency stop), so no song starts in the moment a stop arrives."""

    def __init__(self, mci=None, blocked=None):
        self.mci = mci if mci is not None else Mci()
        self.blocked = blocked
        self.lock = threading.RLock()
        self.now = None   # {'file', 'title', 'nickname', 'started'} while a song is open
        self.volume = DEFAULT_VOLUME
        self.stale_alias = False   # an open that timed out may have finished later and left the alias open (review L1)

    def _close(self):
        try:
            if self.now is not None:
                try:
                    self.mci.send(f'close {ALIAS}')
                except MusicError:
                    pass
        finally:
            self.now = None   # whatever happened, nothing is on the books (review L2)

    def play(self, path, nickname=None):
        with self.lock:
            self._close()
            if self.stale_alias:
                try:
                    self.mci.send(f'close {ALIAS}')
                except MusicError:
                    pass
                self.stale_alias = False
            if self.blocked and self.blocked():
                raise MusicError(permissions.STOPPED_MESSAGE)
            try:
                self.mci.send(f'open "{short_path(path)}" type mpegvideo alias {ALIAS}')
            except MediaTimeout:
                self.stale_alias = True
                raise
            self.now = {'file': Path(path).name, 'title': title_of(path), 'nickname': nickname, 'started': time.time()}
            try:
                self.mci.send(f'set {ALIAS} time format milliseconds')
                self.mci.send(f'setaudio {ALIAS} volume to {self.volume * 10}')
                self.mci.send(f'play {ALIAS} from 0')
                if self.blocked and self.blocked():  # a stop landed while the song was being opened
                    raise MusicError(permissions.STOPPED_MESSAGE)
            except MusicError:
                self._close()
                raise
            return dict(self.now)

    def mode(self):
        """'playing', 'paused' or 'nothing'. Only a song that ran out ('stopped') or a device that no longer answers
        is closed here; a passing state such as 'seeking' counts as playing."""
        with self.lock:
            if self.now is None:
                return 'nothing'
            try:
                mode = self.mci.send(f'status {ALIAS} mode').strip().lower()
            except MusicError:
                mode = 'stopped'
            if mode == 'stopped':
                self._close()
                return 'nothing'
            return 'paused' if mode == 'paused' else 'playing'

    def pause(self):
        with self.lock:
            if self.mode() != 'playing':
                raise MusicError('Nothing is playing.')
            self.mci.send(f'pause {ALIAS}')
            return dict(self.now)

    def resume(self):
        with self.lock:
            if self.mode() != 'paused':
                raise MusicError('Nothing is paused.')
            try:
                self.mci.send(f'resume {ALIAS}')
            except MusicError:
                self.mci.send(f'play {ALIAS}')
            return dict(self.now)

    def stop(self, lock_timeout=None):
        """Stops and closes the song; returns what was open, or None. `lock_timeout`: the emergency stop must never
        wait on a stalled media interface (review M3): when the player's lock cannot be had in that time, nothing is
        sent (the stop still holds, and no song can start while it does) and None is returned."""
        if not self.lock.acquire(timeout=-1 if lock_timeout is None else lock_timeout):
            return None
        try:
            was = self.now
            if was is not None:
                try:
                    self.mci.send(f'stop {ALIAS}')
                except MusicError:
                    pass
            self._close()
            return was
        finally:
            self.lock.release()

    def set_volume(self, percent):
        if type(percent) is not int or not 0 <= percent <= 100:
            raise MusicError('The volume is a whole number from 0 to 100.')
        with self.lock:
            self.volume = percent
            if self.now is not None:
                try:
                    self.mci.send(f'setaudio {ALIAS} volume to {percent * 10}')
                except MusicError:
                    pass  # the next song gets it
            return percent

    def status(self):
        with self.lock:
            mode = self.mode()
            result = {'state': mode, 'volume': self.volume, 'title': None, 'nickname': None, 'file': None, 'position_ms': None, 'length_ms': None}
            if mode != 'nothing' and self.now is not None:
                result.update(title=self.now['title'], nickname=self.now['nickname'], file=self.now['file'])
                for field, word in (('position_ms', 'position'), ('length_ms', 'length')):
                    try:
                        result[field] = int(self.mci.send(f'status {ALIAS} {word}').strip())
                    except (MusicError, ValueError):
                        pass
            return result


# ---- the owner's list ----
class Library:
    def __init__(self, store, folder):
        self.store, self.folder = store, Path(folder)
        try:
            self.folder.mkdir(parents=True, exist_ok=True)  # so the owner can copy files into the folder the panel shows
        except OSError:
            pass  # said by files(): an empty list
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS music (nickname TEXT PRIMARY KEY COLLATE NOCASE, file TEXT NOT NULL, added REAL NOT NULL)')
            made = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='music'").fetchone()
            if made and 'NOCASE' not in (made['sql'] or '').upper():  # a table made by an earlier development copy: one row per name whatever its case
                rows = db.execute('SELECT nickname, file, added FROM music ORDER BY added').fetchall()
                db.execute('DROP TABLE music')
                db.execute('CREATE TABLE music (nickname TEXT PRIMARY KEY COLLATE NOCASE, file TEXT NOT NULL, added REAL NOT NULL)')
                for row in rows:
                    db.execute('INSERT OR REPLACE INTO music(nickname, file, added) VALUES (?,?,?)', (row['nickname'], row['file'], row['added']))

    def files(self):
        """The music files in the folder (not in sub-folders), by name."""
        try:
            return sorted((p.name for p in self.folder.iterdir() if p.is_file() and p.suffix.lower() in FORMATS and not p.name.startswith('.')), key=str.lower)
        except OSError:
            return []

    def nicknames(self):
        files = set(self.files())
        with self.store.connect() as db:
            rows = db.execute('SELECT nickname, file, added FROM music ORDER BY nickname').fetchall()
        return [{'nickname': r['nickname'], 'file': r['file'], 'title': title_of(r['file']), 'present': r['file'] in files, 'added': r['added']} for r in rows]

    def add(self, nickname, file):
        if not isinstance(nickname, str) or not _NICKNAME.fullmatch(nickname.strip()):
            raise MusicError("A nickname has 1 to 60 letters, digits, spaces, apostrophes, hyphens, dots or ampersands.")
        if not isinstance(file, str) or file not in self.files():
            raise MusicError('Choose a file from the music folder.')
        with self.store.connect() as db:
            db.execute('INSERT OR REPLACE INTO music(nickname, file, added) VALUES (?,?,?)', (nickname.strip(), file, time.time()))
        return self.nicknames()

    def remove(self, nickname):
        if not isinstance(nickname, str) or not nickname.strip():
            raise MusicError('No such nickname.')
        with self.store.connect() as db:
            if not db.execute('DELETE FROM music WHERE nickname=?', (nickname.strip(),)).rowcount:
                raise MusicError('No such nickname.')
        return self.nicknames()

    def resolve(self, spoken):
        """The file for what was said, compared word by word: a nickname first (the same words; the nickname's words
        all said, for a nickname of two words or more; or the words said all in the nickname, for four letters or
        more), then a file whose name holds every word said. Filler words alone ("it", "the", "a") name nothing.
        (path, file name, nickname or None), or None when nothing matches."""
        if isinstance(spoken, str):   # the exact file name, whatever its case (the panel's lists, the start-up setting)
            file = next((f for f in self.files() if f.casefold() == spoken.strip().casefold()), None)
            if file:
                return self.folder / file, file, next((row['nickname'] for row in self.nicknames() if row['file'] == file), None)
        wanted = normalise(spoken)
        wanted = re.sub(r'^(?:the|a|an|my|some) ', '', wanted)  # "the workshop warrior" is the workshop warrior
        words = wanted.split()
        if not words:
            return None
        rows = [row for row in self.nicknames() if row['present']]
        for row in rows:
            if normalise(row['nickname']) == wanted:
                return self.folder / row['file'], row['file'], row['nickname']
        if set(words) <= FILLER:
            return None
        said = set(words)
        for row in rows:
            name_words = normalise(row['nickname']).split()
            name = set(name_words)
            if (len(name_words) >= 2 and name <= said) or (len(wanted.replace(' ', '')) >= 4 and said <= name):
                return self.folder / row['file'], row['file'], row['nickname']
        for file in self.files():
            name = set(normalise(title_of(file)).split())
            if said <= name:
                return self.folder / file, file, None
        return None


# ---- the commands the Core answers itself ----
_PREFIX = r"^(?:(?:hey|ok|okay)[, ]+)?(?:jarvis[, ]+)?(?:please[, ]+)?"
_SUFFIX = r"(?:[, ]+please)?[.!?]?$"
_MUSIC = r"(?:music|song|track|playback)"
_PLAY = re.compile(_PREFIX + r"play (?:(?:the|my) )?(?:song |track |music )?(.+?)" + _SUFFIX, re.I)
_STOP = re.compile(_PREFIX + r"(?:(?:stop|turn off|end|kill) (?:the )?" + _MUSIC + r"|stop playing|music off)" + _SUFFIX, re.I)
_PAUSE = re.compile(_PREFIX + r"pause(?: (?:the )?(?P<explicit>" + _MUSIC + r"))?" + _SUFFIX, re.I)
_RESUME = re.compile(_PREFIX + r"(?:resume|continue|unpause)(?: (?:the )?(?P<explicit>" + _MUSIC + r"))?" + _SUFFIX, re.I)
_VOLUME_WORD = re.compile(_PREFIX + r"(?:(?P<explicit>music )?(?:the )?volume (?P<dir1>up|down)|turn (?:it|(?P<explicit2>the music)|the volume) (?P<dir2>up|down)|(?P<louder>louder)|(?P<quieter>quieter|softer))" + _SUFFIX, re.I)
_VOLUME_TO = re.compile(_PREFIX + r"(?:(?P<explicit>music |set (?:the )?)?)volume (?:to )?(?P<value>\d{1,3})(?: ?(?:percent|%))?" + _SUFFIX, re.I)
_STATUS = re.compile(_PREFIX + r"(?:what(?:'s| is) playing|what (?:song|track) is (?:this|playing)|which song is this)" + _SUFFIX, re.I)
_NOT_MUSIC = re.compile(r"^(?:a |the )?(?:video|videos|movie|film|spotify|youtube|playlist on)\b|\bon (?:youtube|spotify)\b", re.I)


def command(text, open=True):
    """What the owner said, as (action, argument) for the player; None when it is not a music command.

    open: whether a song is open (playing or paused). The bare words ("pause", "resume", "continue", "volume up",
    "louder", "volume 40") are music only then; "continue" with nothing playing asks for the rest of an answer. The
    forms that name the music ("pause the music", "stop the music", "music volume up", "set the volume to 40",
    "what's playing") are music whatever plays. A "play" is only a candidate here: server.App decides it is music
    when a song of that name exists; otherwise the words go to the AI as an ordinary question (so "play a video
    about ..." and "spotify play ..." stay what they were)."""
    clean = (text or '').strip()
    if not clean or len(clean) > 200:
        return None
    if _STOP.fullmatch(clean):
        return 'stop', None
    if _STATUS.fullmatch(clean):
        return 'status', None
    match = _PAUSE.fullmatch(clean)
    if match:
        return ('pause', None) if open or match['explicit'] else None
    match = _RESUME.fullmatch(clean)
    if match:
        return ('resume', None) if open or match['explicit'] else None
    match = _VOLUME_TO.fullmatch(clean)
    if match:
        return ('volume', min(100, int(match['value']))) if open or match['explicit'] else None
    match = _VOLUME_WORD.fullmatch(clean)
    if match:
        if not (open or match['explicit'] or match['explicit2']):
            return None
        direction = match['dir1'] or match['dir2'] or ('up' if match['louder'] else 'down')
        return 'volume', direction.lower()
    match = _PLAY.fullmatch(clean)
    if match and not _NOT_MUSIC.search(match[1]):
        return 'play', match[1].strip()
    return None


class Desk:
    """The player and the list together: what the tool `play_music` does."""

    def __init__(self, store, folder, player=None, remember_volume=None):
        self.library = Library(store, folder)
        self.player = player if player is not None else Player()
        self.remember_volume = remember_volume  # called with the new volume, so Settings keeps it

    def act(self, args):
        """One tool call: {'action', 'query'?, 'volume'?}. Returns {'status', 'message', 'now', ...}."""
        action = args.get('action')
        if action == 'list':
            return {'status': 'completed', 'files': self.library.files(), 'nicknames': self.library.nicknames(), 'now': self.player.status(),
                    'folder': str(self.library.folder), 'message': self.list_message()}
        if action == 'status':
            now = self.player.status()
            return {'status': 'completed', 'now': now, 'message': self.now_message(now)}
        if action == 'play':
            query = args.get('query')
            found = self.library.resolve(query) if isinstance(query, str) else None
            if not found:
                asked = query.strip() if isinstance(query, str) else ''
                asked = asked[:60] + ('...' if len(asked) > 60 else '')
                raise MusicError((f'No song called {asked}. ' if asked else 'Say which song to play. ') + self.list_message())
            path, file, nickname = found
            self.player.play(path, nickname)
            return {'status': 'completed', 'now': self.player.status(), 'message': 'Playing ' + title_of(file) + '.'}
        if action == 'pause':
            was = self.player.pause()
            return {'status': 'completed', 'now': self.player.status(), 'message': 'Paused ' + was['title'] + '.'}
        if action == 'resume':
            was = self.player.resume()
            return {'status': 'completed', 'now': self.player.status(), 'message': 'Resuming ' + was['title'] + '.'}
        if action == 'stop':
            was = self.player.stop()
            return {'status': 'completed', 'now': self.player.status(), 'message': ('Stopped ' + was['title'] + '.') if was else 'Nothing was playing.'}
        if action == 'volume':
            value = args.get('volume')
            if value in ('up', 'down'):
                value = max(0, min(100, self.player.volume + (VOLUME_STEP if value == 'up' else -VOLUME_STEP)))
            volume = self.player.set_volume(value)
            if self.remember_volume:
                self.remember_volume(volume)
            return {'status': 'completed', 'now': self.player.status(), 'volume': volume, 'message': f'Music volume {volume} percent.'}
        raise MusicError('Unknown music action.')

    def list_message(self):
        rows = [row for row in self.library.nicknames() if row['present']]
        files = self.library.files()
        if not files:
            return 'Your music folder is empty: copy MP3 files into it (Settings > Music shows where).'
        named = {row['file'] for row in rows}
        said = [row['nickname'] for row in rows] + [title_of(f) for f in files if f not in named]  # nicknames, then the songs without one
        return 'Your songs: ' + ', '.join(said[:12]) + ('.' if len(said) <= 12 else f', and {len(said) - 12} more.')

    @staticmethod
    def now_message(now):
        if now['state'] == 'nothing':
            return 'Nothing is playing.'
        return ('Playing ' if now['state'] == 'playing' else 'Paused: ') + now['title'] + (f" (your nickname {now['nickname']})" if now['nickname'] else '') + '.'
