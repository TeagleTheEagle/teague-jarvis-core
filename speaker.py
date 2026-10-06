"""Speech on this PC without the JARVIS window (item F of docs/PHONE-ACCESS-PLAN.md): a nudge or an announcement is
spoken through Windows' own player (winmm), so it is heard whether the window is open, hidden or closed. The voice
is the one JARVIS uses (voice_engine); the sound is written to a temporary file for the player and removed after.
Sounds are made and played one after another on one thread of their own, so a slow voice provider never holds the
caller, and two announcements never talk over each other. Nothing here chooses words or decides whether to speak:
server.App does, under the owner's settings and the emergency stop."""
import ctypes
import queue
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

MAX_SECONDS = 120
MAX_WAITING = 2      # sounds that may wait while one plays; a further one is skipped (its notice stays on screen)
IDLE_SECONDS = 30    # the player's thread ends after this long with nothing to play; the next sound starts a new one
_queue = queue.Queue()
_lock = threading.Lock()
_worker = None
_speaking = False    # True from the moment a sound is being made until it has finished playing


class SpeakerError(RuntimeError):
    """Said as it is; never the system's own text."""


def _command(text):
    buffer = ctypes.create_unicode_buffer(256)
    if ctypes.windll.winmm.mciSendStringW(text, buffer, 256, 0):
        raise SpeakerError('The PC could not play the sound.')
    return buffer.value


def play(audio, mime, wait=True, blocked=None):
    """Play one sound (MP3 or WAV bytes) on this PC's speakers. wait: return when it has finished (at most
    MAX_SECONDS); blocked: a function that says the sound must stop now (the emergency stop)."""
    if sys.platform != 'win32':
        raise SpeakerError('Speech on the PC plays on Windows only.')
    if not isinstance(audio, bytes) or not 100 <= len(audio) <= 16 * 1024 * 1024:
        raise SpeakerError('No usable sound to play.')
    wav = mime == 'audio/wav' or audio[:4] == b'RIFF'
    alias = 'jarvisvoice' + uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix='jarvis-say-') as folder:
        path = Path(folder) / ('say.wav' if wav else 'say.mp3')
        path.write_bytes(audio)
        opened = False
        try:
            _command(f'open "{path}" type {"waveaudio" if wav else "mpegvideo"} alias {alias}')
            opened = True
            _command(f'play {alias}')
            if wait:
                deadline = time.monotonic() + MAX_SECONDS
                while _command(f'status {alias} mode') == 'playing' and time.monotonic() < deadline:
                    if blocked and blocked():
                        _command(f'stop {alias}')
                        break
                    time.sleep(0.1)
        finally:
            if opened:
                try:
                    _command(f'close {alias}')
                except SpeakerError:
                    pass
    return True


def speaking():
    """True while this PC is making or playing a sound of its own (the window pauses its wake detection then)."""
    return _speaking


def play_later(audio=None, mime=None, blocked=None, make_audio=None, mime_of=None):
    """Queue one sound for the player's thread: `audio` and `mime` as they are, or `make_audio()` called on that
    thread (a slow voice provider never holds the caller) with `mime_of(audio)` naming what it made. Returns the
    queued item at once, or None when MAX_WAITING sounds already wait: that one is not spoken."""
    global _worker
    with _lock:
        if _queue.qsize() >= MAX_WAITING:
            return None
        item = {'make': make_audio or (lambda: audio), 'mime_of': mime_of or (lambda made: mime), 'blocked': blocked}
        _queue.put(item)
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(target=_drain, name='jarvis-say', daemon=True)
            _worker.start()
    return item


def wait_idle(timeout=10.0):
    """For tests: True once nothing is queued or playing."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _speaking and _queue.empty():
            return True
        time.sleep(0.02)
    return False


def _drain():
    global _speaking, _worker
    while True:
        try:
            item = _queue.get(timeout=IDLE_SECONDS)
        except queue.Empty:
            with _lock:
                if _queue.empty():
                    _worker = None
                    return
            continue
        _speaking = True
        try:
            if not (item['blocked'] and item['blocked']()):
                made = item['make']()
                play(made, item['mime_of'](made), True, item['blocked'])
        except Exception:
            pass  # a sound that could not be made or played is not worth a crash; the notice is still on screen
        finally:
            _speaking = not _queue.empty()
