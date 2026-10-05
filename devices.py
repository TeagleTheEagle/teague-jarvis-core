"""The devices of the one Core: who they are, what they say they can do, and what the owner allows.

Master document sections 5 and 19: a device is introduced, pairs with the Core, declares what it can do, and
the Core decides. Being seen, registered or paired is not permission to do everything; each capability is
allowed by the owner, per device, and can be taken back at any time. ONE CORE, ONE MEMORY: a device is a client
and never holds a second JARVIS.

Identity lives in the Core's database and survives a restart. Presence (who is connected right now) stays in
memory, in device_registry.DeviceRegistry, as before.

A device's key is never stored: only a keyed hash of it, made with a secret that lives in the config folder
beside the key file. A backup carries the database but not that secret, so data restored into another
installation brings no working device keys with it: those devices pair again.
"""
import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from pathlib import Path

KINDS = ('phone', 'glasses', 'computer', 'other')            # what the owner can pair; 'pc' is the Core's own PC
CAPABILITIES = ('microphone', 'camera', 'speakers', 'display')
PAIRING_SECONDS = 300
PAIRING_ATTEMPTS = 5
MAX_DEVICES = 20
SECRET_FILE = '.env.device-secret'  # .env-prefixed: never in a backup, never in git
_CREDENTIAL = re.compile(r'([a-f0-9]{16})\.([A-Za-z0-9_-]{43})')


class DeviceError(ValueError):
    """A request about devices that cannot be carried out; the message is fit to show."""


def _clean_name(name):
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60 or re.search(r'[\x00-\x1f<>]', name):
        raise DeviceError('A device name has 1 to 60 characters.')
    return name.strip()


def _clean_capabilities(values):
    if not isinstance(values, (list, tuple, set, frozenset)) or any(v not in CAPABILITIES for v in values):
        raise DeviceError('A device can declare: ' + ', '.join(CAPABILITIES) + '.')
    return sorted(set(values), key=CAPABILITIES.index)


class DeviceBook:
    def __init__(self, store, config_dir, clock=time.time):
        self.store, self.config, self.clock = store, Path(config_dir), clock
        self.lock = threading.RLock()
        self.pending = None  # one pairing at a time: {'code_hash', 'name', 'kind', 'expires', 'attempts'}
        with store.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, key_hash TEXT NOT NULL, secret_id TEXT NOT NULL,
                declared TEXT NOT NULL, allowed TEXT NOT NULL, created REAL NOT NULL, last_seen REAL, revoked REAL)''')

    # ---- the secret that binds device keys to this installation ----
    def _secret(self, create=False):
        path = self.config / SECRET_FILE
        try:
            value = path.read_text(encoding='ascii').strip()
            if re.fullmatch(r'[a-f0-9]{64}', value):
                return bytes.fromhex(value)
        except (OSError, ValueError):
            pass
        if not create:
            return None
        value = secrets.token_hex(32)
        self.config.mkdir(parents=True, exist_ok=True)
        path.write_text(value + '\n', encoding='ascii')
        return bytes.fromhex(value)

    @staticmethod
    def _secret_id(secret):
        return hashlib.sha256(b'jarvis-device-secret:' + secret).hexdigest()[:16]

    @staticmethod
    def _key_hash(secret, key):
        return hmac.new(secret, key.encode('ascii'), hashlib.sha256).hexdigest()

    # ---- pairing: a code the owner reads from the PC ----
    def begin_pairing(self, name, kind):
        """Owner, on the PC: start pairing one device. Returns the code to type on the device, once."""
        name = _clean_name(name)
        if kind not in KINDS:
            raise DeviceError('Choose the kind of device: ' + ', '.join(KINDS) + '.')
        with self.lock:
            if len([d for d in self.list() if not d['revoked']]) >= MAX_DEVICES:
                raise DeviceError(f'At most {MAX_DEVICES} devices can be paired. Remove one first.')
            code = f'{secrets.randbelow(10 ** 8):08d}'
            self.pending = {'code_hash': hashlib.sha256(code.encode()).hexdigest(), 'name': name, 'kind': kind,
                            'expires': self.clock() + PAIRING_SECONDS, 'attempts': 0}
            return {'code': code[:4] + ' ' + code[4:], 'name': name, 'kind': kind, 'expires': self.pending['expires'], 'seconds': PAIRING_SECONDS}

    def cancel_pairing(self):
        with self.lock:
            self.pending = None

    def pairing(self):
        """What the owner's screen may show about a pairing in progress: never the code itself."""
        with self.lock:
            if self.pending and self.pending['expires'] <= self.clock():
                self.pending = None
            return None if not self.pending else {k: self.pending[k] for k in ('name', 'kind', 'expires')}

    def finish_pairing(self, code, declared):
        """The device: hand over the code. Returns the device's id and its own key, shown this once only."""
        declared = _clean_capabilities(declared)
        digits = re.sub(r'\s', '', code) if isinstance(code, str) else ''
        with self.lock:
            pending = self.pending
            if not pending or pending['expires'] <= self.clock():
                self.pending = None
                raise DeviceError('No pairing is waiting. Start pairing on the PC and use the new code.')
            pending['attempts'] += 1
            matches = bool(re.fullmatch(r'\d{8}', digits)) and hmac.compare_digest(hashlib.sha256(digits.encode()).hexdigest(), pending['code_hash'])
            if not matches:
                if pending['attempts'] >= PAIRING_ATTEMPTS:
                    self.pending = None  # a wrong code five times ends this pairing; the owner starts a new one
                raise DeviceError('That code is not right. Check the code on the PC.')
            self.pending = None  # single use
            secret = self._secret(create=True)
            device_id, key = secrets.token_hex(8), secrets.token_urlsafe(32)
            now = self.clock()
            with self.store.connect() as db:
                db.execute('INSERT INTO devices(id,name,kind,key_hash,secret_id,declared,allowed,created,last_seen) VALUES (?,?,?,?,?,?,?,?,?)',
                           (device_id, pending['name'], pending['kind'], self._key_hash(secret, key), self._secret_id(secret),
                            json.dumps(declared), json.dumps(declared), now, now))
            # The owner started this pairing on the PC for this device: what it declares now is allowed, and each
            # item can be switched off in the Devices panel. Anything it declares later is not allowed by itself.
            return {'device_id': device_id, 'key': key, 'credential': device_id + '.' + key, 'name': pending['name'], 'kind': pending['kind'], 'allowed': declared}

    # ---- every request of a paired device ----
    def authenticate(self, credential):
        """The device's row for `<id>.<key>`; PermissionError for anything else. Says nothing about why."""
        match = _CREDENTIAL.fullmatch(credential) if isinstance(credential, str) else None
        secret = self._secret()
        if not match or secret is None:
            raise PermissionError('Device key invalid or revoked.')
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM devices WHERE id=?', (match[1],)).fetchone()
        expected = self._key_hash(secret, match[2])
        # Compare even when the device is unknown, so an unknown id takes as long as a wrong key.
        valid = hmac.compare_digest(expected, row['key_hash'] if row else '0' * 64)
        if not row or not valid or row['revoked'] or row['secret_id'] != self._secret_id(secret):
            raise PermissionError('Device key invalid or revoked.')
        return self._public(row, secret)

    def seen(self, device_id):
        with self.store.connect() as db:
            db.execute('UPDATE devices SET last_seen=? WHERE id=? AND revoked IS NULL', (self.clock(), device_id))

    def declare(self, device_id, declared):
        """The device says what it can do now. A capability it no longer declares is no longer allowed either;
        a new one is not allowed until the owner allows it."""
        declared = _clean_capabilities(declared)
        with self.lock, self.store.connect() as db:
            row = db.execute('SELECT allowed FROM devices WHERE id=? AND revoked IS NULL', (device_id,)).fetchone()
            if not row:
                raise PermissionError('Device key invalid or revoked.')
            allowed = [c for c in json.loads(row['allowed']) if c in declared]
            db.execute('UPDATE devices SET declared=?, allowed=?, last_seen=? WHERE id=?', (json.dumps(declared), json.dumps(allowed), self.clock(), device_id))
        return {'declared': declared, 'allowed': allowed}

    # ---- the owner's panel ----
    def _public(self, row, secret=None):
        secret = self._secret() if secret is None else secret
        usable = not row['revoked'] and secret is not None and row['secret_id'] == self._secret_id(secret)
        return {'device_id': row['id'], 'name': row['name'], 'kind': row['kind'], 'declared': json.loads(row['declared']),
                'allowed': json.loads(row['allowed']), 'created': row['created'], 'last_seen': row['last_seen'], 'revoked': row['revoked'],
                # False: the key was made for another installation (restored data); the device pairs again.
                'key_valid': usable}

    def list(self):
        secret = self._secret()
        with self.store.connect() as db:
            return [self._public(row, secret) for row in db.execute('SELECT * FROM devices ORDER BY created')]

    def get(self, device_id):
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM devices WHERE id=?', (device_id,)).fetchone()
        if not row:
            raise DeviceError('Device not found.')
        return self._public(row)

    def rename(self, device_id, name):
        name = _clean_name(name)
        with self.store.connect() as db:
            if not db.execute('UPDATE devices SET name=? WHERE id=?', (name, device_id)).rowcount:
                raise DeviceError('Device not found.')
        return self.get(device_id)

    def allow(self, device_id, capabilities):
        """The owner's choice of what this device may use. Only what the device declares can be allowed."""
        capabilities = _clean_capabilities(capabilities)
        with self.lock, self.store.connect() as db:
            row = db.execute('SELECT declared, revoked FROM devices WHERE id=?', (device_id,)).fetchone()
            if not row:
                raise DeviceError('Device not found.')
            if row['revoked']:
                raise DeviceError('This device is revoked. Pair it again to use it.')
            if any(c not in json.loads(row['declared']) for c in capabilities):
                raise DeviceError('Only a capability the device declares can be allowed.')
            db.execute('UPDATE devices SET allowed=? WHERE id=?', (json.dumps(capabilities), device_id))
        return self.get(device_id)

    def revoke(self, device_id):
        """From now on the device's key is refused. The row stays, so the activity log keeps its name."""
        with self.store.connect() as db:
            changed = db.execute('UPDATE devices SET revoked=?, allowed=? WHERE id=? AND revoked IS NULL', (self.clock(), '[]', device_id)).rowcount
            if not changed and not db.execute('SELECT 1 FROM devices WHERE id=?', (device_id,)).fetchone():
                raise DeviceError('Device not found.')
        return self.get(device_id)

    def forget(self, device_id):
        """Remove a revoked device from the list."""
        with self.store.connect() as db:
            row = db.execute('SELECT revoked FROM devices WHERE id=?', (device_id,)).fetchone()
            if not row:
                raise DeviceError('Device not found.')
            if not row['revoked']:
                raise DeviceError('Revoke the device first.')
            db.execute('DELETE FROM devices WHERE id=?', (device_id,))
        return {'forgotten': device_id}

    def names(self):
        """Device id -> name, for the activity log."""
        with self.store.connect() as db:
            return {row['id']: row['name'] for row in db.execute('SELECT id,name FROM devices')}
