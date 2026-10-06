"""The private-network door: paired devices reaching the one Core from the owner's other devices (release 1.0.16,
docs/PHONE-CORE-1.0.16.md; docs/PHONE-PLAN.md section 5, decision D1 option A).

The Core itself still listens on 127.0.0.1 only. When the owner turns the switch on (Settings > Devices), a second
and separate door opens on a fixed port at the PC's Tailscale address, and nowhere else. Through that door only the
device routes are served (/api/device/<op>, device_gateway.py: each request proves itself with the device's own
key); every owner route, page and file is refused there. The door is a different server object bound to a
different address, so nothing of the PC-only door changes.

Off by default. Turning it on is the owner's act (CLAUDE.md: networking is owner-only). The switch state lives in
the control table (store.py), out of reach of the settings page, the JSON export and a restored JSON backup.
The address comes from Tailscale itself (`tailscale ip -4`, an address in 100.64.0.0/10) and from nowhere else:
when Tailscale is not installed, not running or signed out, the switch says so and nothing is open. A watcher
looks again every few seconds while the switch is on, so the door opens by itself when Tailscale comes up and
closes when the address goes away.
"""
import json
import ipaddress
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import device_gateway

DEFAULT_PORT = 8790
PORT_RANGE = (1024, 65535)
TAILSCALE_RANGE = ipaddress.ip_network('100.64.0.0/10')
TAILSCALE_EXE = Path(r'C:\Program Files\Tailscale\tailscale.exe')
LOOK_EVERY_SECONDS = 15   # how often the address is looked for again while the switch is on
NAME_CACHE_SECONDS = 60   # how long the PC's Tailscale name is kept before Tailscale is asked again

_name_cache = {'at': 0.0, 'name': None}


def tailscale_command():
    """Tailscale's own command on this PC, or None when it is not installed."""
    return str(TAILSCALE_EXE) if TAILSCALE_EXE.is_file() else shutil.which('tailscale')


def _tailscale(*args, timeout=3):
    """Ask Tailscale's own command for something; None when it is not installed or does not answer."""
    exe = tailscale_command()
    if not exe:
        return None
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
    try:
        done = subprocess.run([exe, *args], capture_output=True, text=True, timeout=timeout, **flags)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def tailscale_address():
    """This PC's Tailscale IPv4 address as Tailscale reports it, or None. No other source: an address in the same
    range on another adapter (a carrier link) is not Tailscale and never gets the door."""
    answer = _tailscale('ip', '-4')
    for value in (answer.split() if answer else ()):
        try:
            if ipaddress.ip_address(value) in TAILSCALE_RANGE:
                return value
        except ValueError:
            continue
    return None


def tailscale_name():
    """This PC's name on the owner's Tailscale network (MagicDNS, 'pc.tailnet.ts.net'), or None. Kept for a minute."""
    now = time.monotonic()
    if now - _name_cache['at'] < NAME_CACHE_SECONDS:
        return _name_cache['name']
    name = None
    answer = _tailscale('status', '--json')
    if answer:
        try:
            value = json.loads(answer).get('Self', {}).get('DNSName', '')
            if isinstance(value, str) and value.strip('.'):
                name = value.strip('.').lower()
        except (ValueError, AttributeError):
            name = None
    _name_cache.update(at=now, name=name)
    return name


def find_address():
    """{'installed': is Tailscale's command on this PC, 'address': this PC's Tailscale address or None,
    'name': its Tailscale name or None}."""
    installed = tailscale_command() is not None
    address = tailscale_address() if installed else None
    return {'installed': installed, 'address': address, 'name': tailscale_name() if address else None}


class Door(ThreadingHTTPServer):
    """The server object of the private-network door. device_gateway.handle reads `device_hosts` (the Host values
    it accepts) and `device_door` (no browser origin is ever accepted here)."""
    daemon_threads = True
    allow_reuse_address = False  # never take over a port something else on this PC holds
    device_door = True
    device_hosts = frozenset()
    app = None

    def server_bind(self):
        if sys.platform == 'win32':  # and not even a process of the same user may share the address
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        # Bind without HTTPServer's reverse DNS lookup of the address (socket.getfqdn), which can hang for seconds on
        # a private address while the door's lock is held; the address itself is the server's name.
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[0], self.server_address[1]


class DoorHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    timeout = 30                 # a peer that connects and says nothing does not hold a thread for ever
    server_version = 'JARVIS'    # no Python version in the answers
    sys_version = ''
    REFUSED = {'error': 'Not available here. This door serves paired devices only.'}

    def log_message(self, *args):
        pass  # nothing of a device's request is logged

    def version_string(self):
        return 'JARVIS'

    def send(self, status, data, mime='application/json', **ignored):
        content = json.dumps(data, ensure_ascii=False).encode() if mime == 'application/json' else data
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(content)

    def send_error(self, code, message=None, explain=None):
        """A malformed request or an unknown method: the same plain JSON line, never Python's HTML page."""
        self.close_connection = True
        try:
            self.send(code if code >= 500 or code == 400 else 404, self.REFUSED)
        except OSError:
            pass

    def discard_body(self, limit=1024 * 1024):
        """After a refusal that did not read the body: throw the body away (bounded) so the client sees the refusal."""
        try:
            remaining = min(int(self.headers.get('Content-Length', '0')), limit)
            self.connection.settimeout(2)
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, 65536))
                if not chunk:
                    break
                remaining -= len(chunk)
        except (ValueError, OSError):
            pass

    def refuse(self):
        self.close_connection = True
        self.send(404, self.REFUSED)
        self.discard_body()

    def do_POST(self):
        if self.path.startswith('/api/device/'):
            return device_gateway.handle(self)
        self.refuse()

    do_GET = do_HEAD = do_PUT = do_DELETE = do_OPTIONS = do_PATCH = refuse


class RemoteDevices:
    """The switch, the door, the watcher and what the owner's panel says about them."""

    def __init__(self, app, load, save, find=find_address):
        self.app, self.load, self.save, self.find = app, load, save, find
        self.lock = threading.RLock()
        self.door = None
        self.thread = None
        self.bound = None        # {'address', 'port', 'name'} while the door is open
        self.found = {}          # what the last look for the address gave
        self.problem = None      # why the door could not be opened, in words fit for the panel
        self.looked = 0.0
        self.stopping = threading.Event()
        self.watcher = None

    # ---- the switch ----
    def state(self):
        value = self.load() or {}
        port = value.get('port')
        if type(port) is not int or not PORT_RANGE[0] <= port <= PORT_RANGE[1]:
            port = DEFAULT_PORT
        return {'enabled': value.get('enabled') is True, 'port': port}

    def configure(self, enabled, port=None):
        """The owner's click: on or off, and the port. Saved first; then the door follows."""
        if type(enabled) is not bool:
            raise ValueError('Say whether the private-network door is on or off.')
        if port is None:
            port = self.state()['port']
        if type(port) is not int or not PORT_RANGE[0] <= port <= PORT_RANGE[1]:
            raise ValueError(f'The port is a whole number from {PORT_RANGE[0]} to {PORT_RANGE[1]}.')
        with self.lock:
            self.save({'enabled': enabled, 'port': port, 'changed': time.time()})
            self.close()
            self.looked = 0.0
        self.app.audit('private network door switch', ('on, port %d' % port) if enabled else 'off')
        return self.status()

    # ---- the door ----
    def ensure(self):
        """Open the door when the switch is on and this PC has a Tailscale address; close it when the switch is off
        or the address went away; look for the address again at most every LOOK_EVERY_SECONDS."""
        with self.lock:
            state = self.state()
            if not state['enabled']:
                self.close()
                self.found, self.problem = {}, None
                return
            now = time.monotonic()
            if self.looked and now - self.looked < LOOK_EVERY_SECONDS:
                return
            self.looked = now
            try:
                self.found = dict(self.find() or {})
            except Exception:
                self.found = {}
            address, name = self.found.get('address'), self.found.get('name')
            if not address:
                self.close()
                self.problem = None
                return
            if self.door is not None and self.bound and (self.bound['address'], self.bound['port']) == (address, state['port']):
                if name != self.bound.get('name'):  # the name became known or changed: accept it too
                    self.bound['name'] = name
                    self.door.device_hosts = self.hosts(address, state['port'], name)
                return
            self.close()
            self.open(address, state['port'], name)

    @staticmethod
    def hosts(address, port, name):
        """What a request through the door may name as its Host: the address, the PC's full Tailscale name, and
        the short name (the first label, as MagicDNS also resolves it), each with the port."""
        accepted = {f'{address}:{port}'}
        if name:
            full = name.lower().strip('.')
            accepted.add(f'{full}:{port}')
            accepted.add(f'{full.split(".")[0]}:{port}')
        return frozenset(accepted)

    def open(self, address, port, name):
        try:
            door = Door((address, port), DoorHandler)
        except OSError as exc:
            reason = getattr(exc, 'strerror', None) or str(exc)
            self.problem = f'port {port} at {address} could not be opened ({reason.strip().rstrip(".")})'
            self.app.audit('private network door', 'could not open port %d' % port)
            return
        door.app = self.app
        door.device_hosts = self.hosts(address, port, name)
        self.door, self.bound, self.problem = door, {'address': address, 'port': port, 'name': name}, None
        self.thread = threading.Thread(target=door.serve_forever, daemon=True, name='jarvis-device-door')
        self.thread.start()
        self.app.audit('private network door', f'open at {address}:{port}')

    def close(self):
        with self.lock:
            door, self.door = self.door, None
            thread, self.thread = self.thread, None
            bound, self.bound = self.bound, None
        if door is None:
            return
        door.shutdown()
        door.server_close()
        if thread:
            thread.join(timeout=5)
        try:
            self.app.audit('private network door', 'closed' + (f' ({bound["address"]}:{bound["port"]})' if bound else ''))
        except Exception:
            pass  # closing never fails on a row that could not be written

    # ---- the watcher: the door follows Tailscale and the switch without anyone asking ----
    def watch(self):
        """Start looking every LOOK_EVERY_SECONDS (a daemon thread). Called once by server.main()."""
        with self.lock:
            if self.watcher is not None:
                return
            self.stopping.clear()
            self.watcher = threading.Thread(target=self._watch, daemon=True, name='jarvis-device-door-watch')
            self.watcher.start()

    def _watch(self):
        while not self.stopping.wait(LOOK_EVERY_SECONDS):
            try:
                self.ensure()
            except Exception:
                pass  # the next look tries again

    def shutdown(self):
        """The Core stops: stop watching and close the door."""
        self.stopping.set()
        watcher, self.watcher = self.watcher, None
        if watcher:
            watcher.join(timeout=5)
        self.close()

    # ---- the panel ----
    def status(self):
        with self.lock:
            self.ensure()
            state = self.state()
            is_open = self.door is not None
            found = self.found if state['enabled'] else {}
            address = self.bound['address'] if is_open else found.get('address')
            name = self.bound.get('name') if is_open else found.get('name')
            if not state['enabled']:
                message = 'Off. JARVIS listens only on this PC.'
            elif is_open:
                message = (f"Open at {address}:{state['port']}" + (f' ({name})' if name else '')
                           + '. Only devices on your private network can reach it, each with its own key, and only the device routes.')
            elif self.problem:
                message = 'On, but ' + self.problem + '. Nothing is open.'
            elif found and found.get('installed') is False:
                message = 'On, but Tailscale is not installed on this PC (its command was not found). Nothing is open.'
            else:
                message = 'On, but this PC has no Tailscale address (Tailscale is not running or not signed in). Nothing is open.'
            return {**state, 'open': is_open, 'address': address, 'name': name, 'default_port': DEFAULT_PORT, 'message': message}
