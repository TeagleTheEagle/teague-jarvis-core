"""Paired devices talking to the one Core (docs/DEVICES.md; master document sections 5 and 19).

The device-facing routes are /api/device/<op>. A device proves who it is with its own key
(header X-Jarvis-Device: <id>.<key>), made when it paired with a code the owner read from the PC.
What it may do is decided here, on every request, from what the owner allows for that device:

  - a question may call only the tools marked for other devices in permissions.py (reads);
  - a picture needs the camera to be allowed, a transcription the microphone, a spoken reply the speakers;
  - any paired device may stop everything (the emergency stop), and that is never turned away for another
    reason; none can resume;
  - a revoked device is refused from its next request on, and what it was running is cancelled.

The Core still listens on 127.0.0.1 only. Reaching it from another machine is the owner's networking
decision; nothing here opens a port.
"""
import json
import threading
import time

import permissions
from devices import DeviceError, DeviceRefused

OPS = ('hello', 'status', 'start', 'events', 'cancel', 'transcribe', 'speech', 'stop', 'bye')
NEEDS = {'transcribe': 'microphone', 'speech': 'speakers'}
PAIR_CALLS_A_MINUTE = 10
SEEN_EVERY_SECONDS = 60
# What a device is told word for word. Anything else that goes wrong gets one general line: no raw Python
# message, no path and nothing from a provider crosses to a device.
SHOWABLE = frozenset((
    permissions.STOPPED_MESSAGE, 'Operation unavailable.', 'Supply only code and capabilities.', 'Supply only capabilities.',
    'Too many pairing attempts. Wait one minute.', 'Wearable request limit reached. Wait one minute.', 'Wearable service busy.',
    'Wearable conversation required.', 'Unknown wearable run.', 'Run expired.', 'Unknown fields.', 'Image too large.', 'Unsupported image.',
    'Invalid speech text.', 'Expected PCM data.', 'A request is already running. Stop it or wait for completion.'))
GENERAL = 'Invalid, busy, expired or unavailable device request.'


class Gateway:
    def __init__(self, app):
        self.app = app
        self.sessions = {}   # device id -> its own Service: its questions, its limit of requests a minute
        self.seen_at = {}    # device id -> when "last seen" was last written down
        self.lock = threading.Lock()
        self.pair_calls = []

    @property
    def book(self):
        return self.app.device_book

    def pair(self, body):
        """A device hands over the code the owner read from the PC. It has no key yet: the code is the proof."""
        if not isinstance(body, dict) or set(body) != {'code', 'capabilities'}:
            raise ValueError('Supply only code and capabilities.')
        now = time.monotonic()
        with self.lock:
            self.pair_calls = [t for t in self.pair_calls if now - t < 60]
            if len(self.pair_calls) >= PAIR_CALLS_A_MINUTE:
                raise ValueError('Too many pairing attempts. Wait one minute.')
            self.pair_calls.append(now)
        self.app.require_running()  # no new device joins while the emergency stop holds; the code stays good
        paired = self.book.finish_pairing(body['code'], body['capabilities'])
        self.app.audit('device paired: ' + paired['name'], paired['kind'], device=paired['device_id'])
        return paired

    def session(self, device_id):
        from wearables.service import Service
        with self.lock:
            session = self.sessions.get(device_id)
            if session is None:
                # Every conversation of a device starts with its own id: no device writes into another's.
                session = self.sessions[device_id] = Service(self.app, device_id, simulated=False, prefix='device-' + device_id + '-', register=False)
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
        return {'device_id': device['device_id'], 'name': device['name'], 'kind': device['kind'], 'declared': device['declared'],
                'allowed': device['allowed'], 'stopped': stopped, 'protocol': 1,
                'scope': 'Questions and reading. Saved things are changed only on the PC.'}

    def dispatch(self, credential, op, body):
        device = self.book.authenticate(credential)  # DeviceRefused: unknown device, wrong key or revoked
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
            return self.session(ident).dispatch('start', words)
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
        result = self.session(ident).dispatch(op, body)
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


def handle(handler):
    """POST /api/device/<op>. The same loopback and same-origin checks as every route. The proof is the device's
    own key: these routes ask neither for the owner's session nor for the desktop app's token."""
    gateway = getattr(handler.server.app, 'device_gateway', None)
    host = f'127.0.0.1:{handler.server.server_port}'
    if (gateway is None or handler.headers.get('Host') != host or handler.headers.get('Origin') not in (None, 'http://' + host)
            or handler.headers.get('Sec-Fetch-Site') == 'cross-site'):
        return _refuse_unread(handler, 403, {'error': 'Device access is not available here.'})
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
            return handler.send(200, gateway.pair(body))
        return handler.send(200, gateway.dispatch(handler.headers.get('X-Jarvis-Device', ''), op, body))
    except DeviceRefused:
        return handler.send(401, {'error': 'Device key invalid or revoked. Pair this device again on the PC.'})
    except DeviceError as exc:
        return handler.send(403, {'error': str(exc)})
    except (ValueError, TypeError, KeyError) as exc:
        return handler.send(400, {'error': str(exc) if str(exc) in SHOWABLE else GENERAL})
    except Exception:
        # No provider credentials, raw exceptions or file errors cross to a device.
        return handler.send(503, {'error': 'JARVIS service unavailable.'})
