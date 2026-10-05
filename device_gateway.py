"""Paired devices talking to the one Core (docs/DEVICES.md; master document sections 5 and 19).

The device-facing routes are /api/device/<op>. A device proves who it is with its own key
(header X-Jarvis-Device: <id>.<key>), made when it paired with a code the owner read from the PC.
What it may do is decided here, on every request, from what the owner allows for that device:

  - a question may call only the tools marked for other devices in permissions.py (reads);
  - a picture needs the camera to be allowed, a transcription the microphone, a spoken reply the speakers;
  - any paired device may stop everything (the emergency stop); none can resume;
  - a revoked device is refused from its next request on, and what it was running is cancelled.

The Core still listens on 127.0.0.1 only. Reaching it from another machine is the owner's networking
decision; nothing here opens a port.
"""
import json
import threading
import time

from devices import DeviceError

OPS = ('hello', 'status', 'start', 'events', 'cancel', 'transcribe', 'speech', 'stop', 'bye')
NEEDS = {'transcribe': 'microphone', 'speech': 'speakers'}
PAIR_CALLS_A_MINUTE = 10


class Gateway:
    def __init__(self, app):
        self.app = app
        self.sessions = {}  # device id -> its own Service: its runs, its rate limit
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
        paired = self.book.finish_pairing(body['code'], body['capabilities'])
        self.app.audit('device paired: ' + paired['name'], paired['kind'], device=paired['device_id'])
        return paired

    def session(self, device_id):
        from wearables.service import Service
        with self.lock:
            session = self.sessions.get(device_id)
            if session is None:
                session = self.sessions[device_id] = Service(self.app, device_id, simulated=False, prefix='device-', register=False)
            return session

    def present(self, device):
        """Presence in the Core's registry: what the device declares, and of that what the owner allows."""
        self.app.devices.register(device['device_id'], device['declared'], ready=device['allowed'], ttl=120, simulated=False)

    @staticmethod
    def describe(device, stopped):
        return {'device_id': device['device_id'], 'name': device['name'], 'kind': device['kind'], 'declared': device['declared'],
                'allowed': device['allowed'], 'stopped': stopped, 'protocol': 1,
                'scope': 'Questions and reading. Saved things are changed only on the PC.'}

    def dispatch(self, credential, op, body):
        device = self.book.authenticate(credential)  # PermissionError: unknown device, wrong key or revoked
        if op not in OPS or not isinstance(body, dict):
            raise ValueError('Operation unavailable.')
        ident = device['device_id']
        self.book.seen(ident)
        if op == 'hello':
            if set(body) - {'capabilities'}:
                raise ValueError('Supply only capabilities.')
            if 'capabilities' in body:
                self.book.declare(ident, body['capabilities'])
                device = self.book.get(ident)
        self.present(device)
        stopped = self.app.stopped is not None
        if op in ('hello', 'status'):
            return self.describe(device, stopped)
        if op == 'stop':
            # Stopping is safe from anywhere; resuming is the owner's, on the PC.
            return {'stopped': self.app.emergency_stop(ident, 'Stop from ' + device['name'])['stopped']}
        if op == 'bye':
            self.app.devices.disconnect(ident)
            return {'disconnected': True}
        need = NEEDS.get(op) or ('camera' if op == 'start' and body.get('image') else None)
        if need and need not in device['allowed']:
            raise DeviceError(f'The {need} of this device is not allowed. The owner allows it in Settings > Devices on the PC.')
        return self.session(ident).dispatch(op, body)

    def revoked(self, device_id):
        """The owner revoked the device: stop what it was running and forget its session."""
        with self.lock:
            session = self.sessions.pop(device_id, None)
        for run_id in list(session.runs) if session else []:
            run = self.app.runs.get(run_id)
            if run:
                run.cancel.set()
        self.app.devices.disconnect(device_id)


def handle(handler):
    """POST /api/device/<op>. Same loopback and same-origin checks as every route; the credential is the device's own key."""
    gateway = getattr(handler.server.app, 'device_gateway', None)
    host = f'127.0.0.1:{handler.server.server_port}'
    if (gateway is None or handler.headers.get('Host') != host or handler.headers.get('Origin') not in (None, 'http://' + host)
            or handler.headers.get('Sec-Fetch-Site') == 'cross-site'):
        handler.close_connection = True
        return handler.send(403, {'error': 'Device access is not available here.'})
    try:
        size = int(handler.headers.get('Content-Length', '0'))
        if handler.headers.get('Transfer-Encoding') or handler.headers.get_content_type() != 'application/json' or not 0 < size <= 3 * 1024 * 1024:
            handler.close_connection = True
            return handler.send(400, {'error': 'Use a bounded JSON request.'})
        try:
            body = json.loads(handler.rfile.read(size))
        except ValueError:
            return handler.send(400, {'error': 'Use a bounded JSON request.'})
        op = handler.path.rsplit('/', 1)[-1]
        if op == 'pair':
            return handler.send(200, gateway.pair(body))
        return handler.send(200, gateway.dispatch(handler.headers.get('X-Jarvis-Device', ''), op, body))
    except PermissionError:
        return handler.send(401, {'error': 'Device key invalid or revoked. Pair this device again on the PC.'})
    except DeviceError as exc:
        return handler.send(403, {'error': str(exc)})
    except (ValueError, TypeError, KeyError) as exc:
        # Messages raised on purpose are fit to show; anything else gets the general line.
        text = str(exc) if isinstance(exc, ValueError) and str(exc) and len(str(exc)) <= 200 else 'Invalid, busy, expired or unavailable device request.'
        return handler.send(400, {'error': text})
    except Exception:
        # No provider credentials or raw exceptions cross to a device.
        return handler.send(503, {'error': 'JARVIS service unavailable.'})
