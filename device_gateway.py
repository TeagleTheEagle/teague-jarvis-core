"""Paired devices talking to the one Core (docs/DEVICES.md, docs/PHONE-CORE-1.0.16.md; master document sections 5 and 19).

The device-facing routes are /api/device/<op>. A device proves who it is with its own key
(header X-Jarvis-Device: <id>.<key>), made when it paired with a code the owner read from the PC.
What it may do is decided here, on every request, from what the owner allows for that device:

  - a question may call only the tools marked for other devices in permissions.py (reads); with the owner's tick
    "may save memories and tasks" (1.0.16) also the few saving tools marked for that, and its memory commands work;
  - a picture needs the camera to be allowed, a transcription the microphone, a spoken reply the speakers;
  - it may read its own conversations, the PC's health and an overview of tasks and reminders (1.0.16); never
    another device's conversations and never the PC's chats;
  - any paired device may stop everything (the emergency stop), and that is never turned away for another
    reason; none can resume;
  - a revoked device is refused from its next request on, and what it was running is cancelled.

Two doors lead here: the Core's own on 127.0.0.1, and (1.0.16, off by default) the private-network door of
remote_devices.py at the PC's Tailscale address, which serves these routes and nothing else. Wrong codes and
wrong keys are counted per caller (its address; for keys also the device id it claims): too many lock that caller
out of pairing, or of that device id, for fifteen minutes. A valid key is never a guess, so a request with a valid
key is never turned away by a lockout: the stop of a paired device always goes through.
"""
import json
import threading
import time

import permissions
from devices import DeviceError, DeviceRefused, WrongCode

OPS = ('hello', 'status', 'start', 'events', 'cancel', 'transcribe', 'speech', 'stop', 'bye',
       'conversations', 'history', 'metrics', 'overview')
NEEDS = {'transcribe': 'microphone', 'speech': 'speakers'}
PAIR_CALLS_A_MINUTE = 10          # per caller
PAIR_CALLS_A_MINUTE_IN_ALL = 60   # everyone together
WRONG_CODES_BEFORE_LOCKOUT = 5    # per caller, within LOCKOUT_SECONDS; the pairing itself goes on (devices.PAIRING_ATTEMPTS in all)
BAD_KEYS_A_MINUTE = 20            # per caller and claimed device id
LOCKOUT_SECONDS = 900
SEEN_EVERY_SECONDS = 60
LOCKED_MESSAGE = 'Too many attempts from this device. Wait fifteen minutes.'
# What a device is told word for word. Anything else that goes wrong gets one general line: no raw Python
# message, no path and nothing from a provider crosses to a device.
SHOWABLE = frozenset((
    permissions.STOPPED_MESSAGE, 'Operation unavailable.', 'Supply only code and capabilities.', 'Supply only capabilities.',
    'Too many pairing attempts. Wait one minute.', 'Wearable request limit reached. Wait one minute.', 'Wearable service busy.',
    'Wearable conversation required.', 'Unknown wearable run.', 'Run expired.', 'Unknown fields.', 'Image too large.', 'Unsupported image.',
    'Invalid speech text.', 'Expected PCM data.', 'A request is already running. Stop it or wait for completion.',
    'Supply only run_id and after.', LOCKED_MESSAGE))
GENERAL = 'Invalid, busy, expired or unavailable device request.'


class TooManyAttempts(ValueError):
    """This caller tried too many wrong codes or wrong keys; it waits. Answered 429."""

    def __init__(self):
        super().__init__(LOCKED_MESSAGE)


class Gateway:
    def __init__(self, app):
        self.app = app
        self.sessions = {}   # device id -> its own Service: its questions, its limit of requests a minute
        self.seen_at = {}    # device id -> when "last seen" was last written down
        self.lock = threading.Lock()
        self.pair_calls = []  # everyone's pairing calls, for the limit in all
        self.callers = {}     # ('pair', address) or ('key', address, claimed id) -> {'calls': [times], 'tries': [times], 'locked': until}

    @property
    def book(self):
        return self.app.device_book

    # ---- callers, counted by address (and, for keys, by the device id they claim) ----
    def _record(self, key, now, window):
        """Must hold self.lock. The caller's record under `key`, with tries older than `window` forgotten.
        Raises TooManyAttempts while that caller is locked out."""
        if len(self.callers) > 500:  # forget records nothing is remembered about any more
            for stale in [k for k, v in self.callers.items() if v['locked'] <= now and not v['tries'] and not v['calls']]:
                del self.callers[stale]
        record = self.callers.setdefault(key, {'calls': [], 'tries': [], 'locked': 0.0})
        record['calls'] = [t for t in record['calls'] if now - t < 60]
        record['tries'] = [t for t in record['tries'] if now - t < window]
        if record['locked'] > now:
            raise TooManyAttempts()
        return record

    def _failed(self, key, now, window, limit):
        """Count one wrong try under `key`. (locked, just_now): whether the caller is locked out, and whether this
        try was the one that locked it (so the activity row is written once)."""
        with self.lock:
            if len(self.callers) > 500:
                for stale in [k for k, v in self.callers.items() if v['locked'] <= now and not v['tries'] and not v['calls']]:
                    del self.callers[stale]
            record = self.callers.setdefault(key, {'calls': [], 'tries': [], 'locked': 0.0})
            if record['locked'] > now:
                return True, False
            record['tries'] = [t for t in record['tries'] if now - t < window] + [now]
            if len(record['tries']) >= limit:
                record['locked'], record['tries'] = now + LOCKOUT_SECONDS, []
                return True, True
            return False, False

    def _note_lockout(self, caller, why):
        """The activity row for a lockout, written outside the lock; the lockout holds whether or not it is written."""
        try:
            self.app.audit('device door: a caller is locked out', f'{why} from {caller or "?"}')
        except Exception:
            pass

    def pair(self, body, caller=None):
        """A device hands over the code the owner read from the PC. It has no key yet: the code is the proof."""
        if not isinstance(body, dict) or set(body) != {'code', 'capabilities'}:
            raise ValueError('Supply only code and capabilities.')
        now = time.monotonic()
        with self.lock:
            record = self._record(('pair', caller), now, LOCKOUT_SECONDS)
            self.pair_calls = [t for t in self.pair_calls if now - t < 60]
            if len(record['calls']) >= PAIR_CALLS_A_MINUTE or len(self.pair_calls) >= PAIR_CALLS_A_MINUTE_IN_ALL:
                raise ValueError('Too many pairing attempts. Wait one minute.')
            record['calls'].append(now)
            self.pair_calls.append(now)
        self.app.require_running()  # no new device joins while the emergency stop holds; the code stays good
        try:
            paired = self.book.finish_pairing(body['code'], body['capabilities'])
        except WrongCode:
            locked, just_now = self._failed(('pair', caller), now, LOCKOUT_SECONDS, WRONG_CODES_BEFORE_LOCKOUT)
            if locked:
                if just_now:
                    self._note_lockout(caller, 'wrong pairing codes')
                raise TooManyAttempts() from None
            raise
        self.app.audit('device paired: ' + paired['name'], paired['kind'], device=paired['device_id'])
        return paired

    def session(self, device):
        """The device's own Service, from its row (the owner's tick is read from it at every request) or its id."""
        from wearables.service import Service
        ident = device['device_id'] if isinstance(device, dict) else device
        with self.lock:
            session = self.sessions.get(ident)
            if session is None:
                # Every conversation of a device starts with its own id: no device writes into another's.
                session = self.sessions[ident] = Service(self.app, ident, simulated=False, prefix='device-' + ident + '-', register=False)
            if isinstance(device, dict):
                session.writes = bool(device.get('writes'))  # the owner's tick, as it stands at this request
            return session

    def present(self, device):
        """Presence in the Core's registry: what the device declares, and of that what the owner allows."""
        self.app.devices.register(device['device_id'], device['declared'], ready=device['allowed'], ttl=120, simulated=False)

    def seen(self, device_id):
        """"Last seen" for the owner's panel: written at most once a minute, and never worth failing a request for
        (the database may be busy, for example during a backup)."""
        now = time.monotonic()
        with self.lock:
            if now - self.seen_at.get(device_id, -SEEN_EVERY_SECONDS) < SEEN_EVERY_SECONDS:
                return
            self.seen_at[device_id] = now
        try:
            self.book.seen(device_id)
        except Exception:
            with self.lock:
                self.seen_at.pop(device_id, None)

    @staticmethod
    def describe(device, stopped):
        writes = bool(device.get('writes'))
        return {'device_id': device['device_id'], 'name': device['name'], 'kind': device['kind'], 'declared': device['declared'],
                'allowed': device['allowed'], 'writes': writes, 'stopped': stopped, 'protocol': 2,
                'scope': 'Questions, reading, and saving memories, notes, tasks and timers.' if writes
                         else 'Questions and reading. Saved things are changed only on the PC.'}

    def dispatch(self, credential, op, body, caller=None):
        now = time.monotonic()
        try:
            device = self.book.authenticate(credential)  # DeviceRefused: unknown device, wrong key or revoked
        except DeviceRefused:
            # A wrong key is counted against this caller and the device id it claimed; a valid key never is.
            claimed = credential.split('.', 1)[0][:16] if isinstance(credential, str) else ''
            locked, just_now = self._failed(('key', caller, claimed), now, 60, BAD_KEYS_A_MINUTE)
            if locked:
                if just_now:
                    self._note_lockout(caller, 'wrong keys for device ' + (claimed or '?'))
                raise TooManyAttempts() from None
            raise
        if op not in OPS or not isinstance(body, dict):
            raise ValueError('Operation unavailable.')
        ident = device['device_id']
        # The emergency stop comes before everything else about the request: it is not turned away because the
        # database is busy, because a picture came with it or because a capability is not allowed.
        if op == 'stop':
            return {'stopped': self.app.emergency_stop(ident, 'Stop from ' + device['name'])['stopped']}
        if op == 'start' and self.app.stopped is None and permissions.stop_phrase(body.get('text')):
            words = {'text': body['text']}
            if isinstance(body.get('conversation'), str):
                words['conversation'] = body['conversation']
            return self.session(device).dispatch('start', words)
        self.seen(ident)
        if op == 'hello':
            if set(body) - {'capabilities'}:
                raise ValueError('Supply only capabilities.')
            if 'capabilities' in body:
                self.book.declare(ident, body['capabilities'])
                device = self.book.get(ident)
        self.present(device)
        if not self.book.usable(ident):
            # Revoked while this request was on its way in: nothing more happens for it.
            self.revoked(ident)
            raise DeviceRefused()
        stopped = self.app.stopped is not None
        if op in ('hello', 'status'):
            return self.describe(device, stopped)
        if op == 'bye':
            self.app.devices.disconnect(ident)
            return {'disconnected': True}
        need = NEEDS.get(op) or ('camera' if op == 'start' and body.get('image') else None)
        if need and need not in device['allowed']:
            raise DeviceError(f'The {need} of this device is not allowed. The owner allows it in Settings > Devices on the PC.')
        result = self.session(device).dispatch(op, body)
        if op == 'start' and not self.book.usable(ident):
            # Revoked while the question was being started: it is cancelled like everything else of that device.
            run = self.app.runs.get(result.get('run_id'))
            if run:
                run.cancel.set()
            self.revoked(ident)
            raise DeviceRefused()
        return result

    def revoked(self, device_id):
        """The owner revoked (or removed) the device: stop what it was running and forget its session."""
        with self.lock:
            session = self.sessions.pop(device_id, None)
            self.seen_at.pop(device_id, None)
        for run_id in list(session.runs) if session else []:
            run = self.app.runs.get(run_id)
            if run:
                run.cancel.set()
        self.app.devices.forget(device_id)


def _refuse_unread(handler, status, payload):
    """Refuse a request whose body was not read: close the connection afterwards, and throw the unread body away
    first so that the client receives this answer and not a broken connection (server.Handler.discard_body)."""
    handler.close_connection = True
    handler.send(status, payload)
    getattr(handler, 'discard_body', lambda: None)()


def accepted_hosts(server):
    """The Host values a door accepts: the Core's own door exactly its 127.0.0.1 address (as in 1.0.15); the
    private-network door (remote_devices.Door) its Tailscale address and names, compared in lower case."""
    hosts = getattr(server, 'device_hosts', None)
    return frozenset(h.lower() for h in hosts) if hosts else frozenset({f'127.0.0.1:{server.server_port}'})


def handle(handler):
    """POST /api/device/<op>, through either door. The request must name the door it came through, and a browser
    origin is accepted on the Core's own door only (same origin), never on the private-network door. The proof is
    the device's own key: these routes ask neither for the owner's session nor for the desktop app's token."""
    server = handler.server
    gateway = getattr(getattr(server, 'app', None), 'device_gateway', None)
    door = bool(getattr(server, 'device_door', False))
    host = handler.headers.get('Host') or ''
    if door:
        host = host.strip().lower()  # names are not case-sensitive; the PC door compares exactly, as before
    origin = handler.headers.get('Origin')
    if (gateway is None or host not in accepted_hosts(server) or (origin is not None and (door or origin != 'http://' + host))
            or handler.headers.get('Sec-Fetch-Site') == 'cross-site'):
        return _refuse_unread(handler, 403, {'error': 'Device access is not available here.'})
    caller = handler.client_address[0] if getattr(handler, 'client_address', None) else None
    try:
        size = int(handler.headers.get('Content-Length', '0'))
        if handler.headers.get('Transfer-Encoding') or handler.headers.get_content_type() != 'application/json' or not 0 < size <= 3 * 1024 * 1024:
            return _refuse_unread(handler, 400, {'error': 'Use a bounded JSON request.'})
        try:
            body = json.loads(handler.rfile.read(size))
        except ValueError:
            return handler.send(400, {'error': 'Use a bounded JSON request.'})
        op = handler.path.rsplit('/', 1)[-1]
        if op == 'pair':
            return handler.send(200, gateway.pair(body, caller))
        return handler.send(200, gateway.dispatch(handler.headers.get('X-Jarvis-Device', ''), op, body, caller))
    except TooManyAttempts:
        return handler.send(429, {'error': LOCKED_MESSAGE})
    except DeviceRefused:
        return handler.send(401, {'error': 'Device key invalid or revoked. Pair this device again on the PC.'})
    except DeviceError as exc:
        return handler.send(403, {'error': str(exc)})
    except (ValueError, TypeError, KeyError) as exc:
        return handler.send(400, {'error': str(exc) if str(exc) in SHOWABLE else GENERAL})
    except Exception:
        # No provider credentials, raw exceptions or file errors cross to a device.
        return handler.send(503, {'error': 'JARVIS service unavailable.'})
