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

Revoking is remembered twice: in the database, and in a small list beside the secret. So an older copy of the
database put back into the same installation (a restore) does not bring a revoked device back to life.

1.0.16 (docs/PHONE-CORE-1.0.16.md): a device also has the owner's tick "may save memories and tasks" (`writes`),
off for every new device; and a wrong pairing code is its own error (WrongCode), so that device_gateway.py can
count wrong codes per caller once the Core is reachable from other devices.
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
PAIRING_ATTEMPTS = 25   # wrong codes in all before a pairing ends (25 tries in a hundred million); device_gateway.py locks each caller out after 5
MAX_DEVICES = 20
SECRET_FILE = '.env.device-secret'    # .env-prefixed: never in a backup, never in git
REVOKED_FILE = '.env.device-revoked'  # the ids of revoked devices, beside the secret (see above)
_CREDENTIAL = re.compile(r'([a-f0-9]{16})\.([A-Za-z0-9_-]{43})')


class DeviceError(ValueError):
    """A request about devices that cannot be carried out; the message is fit to show."""


class WrongCode(DeviceError):
    """The pairing code handed over is not the one waiting. Counted per caller by device_gateway.py."""


class DeviceRefused(PermissionError):
    """The key is not one this Core accepts: unknown device, wrong key, revoked, or made for another
    installation. Deliberately says nothing about which."""

    def __init__(self):
        super().__init__('Device key invalid or revoked.')


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
            # 1.0.16: the owner's tick "may save memories and tasks". An older database gets the column (0 for every
            # device); an older JARVIS (after a rollback) ignores it.
            if 'writes' not in {row[1] for row in db.execute('PRAGMA table_info(devices)')}:
                db.execute('ALTER TABLE devices ADD COLUMN writes INTEGER NOT NULL DEFAULT 0')

    # ---- the secret that binds device keys to this installation ----
    def _secret(self, create=False):
        """The secret, or None when there is none that can be used. create: make one, but only when no file is
        there at all. A file that is there and cannot be read is never written over: every paired device's key
        depends on it."""
        path = self.config / SECRET_FILE
        try:
            value = path.read_text(encoding='ascii').strip()
            if re.fullmatch(r'[a-f0-9]{64}', value):
                return bytes.fromhex(value)
            present = True
        except FileNotFoundError:
            present = False
        except (OSError, ValueError):
            present = True
        if not create:
            return None
        if present:
            raise DeviceError('The device key file in the config folder cannot be read, so no device can be paired. '
                              'It was not replaced, because every paired device depends on it.')
        value = secrets.token_hex(32)
        try:
            self.config.mkdir(parents=True, exist_ok=True)
            with open(path, 'x', encoding='ascii') as handle:  # never over a file that appeared meanwhile
                handle.write(value + '\n')
        except FileExistsError:
            return self._secret()
        except OSError:
            raise DeviceError('The device key file could not be written in the config folder, so no device can be paired.') from None
        return bytes.fromhex(value)

    # ---- revoked devices, remembered beside the secret ----
    def _revoked_ids(self):
        try:
            value = json.loads((self.config / REVOKED_FILE).read_text(encoding='ascii'))
            return {k: v for k, v in value.items() if isinstance(k, str)} if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    def _remember_revoked(self, device_id, when):
        ids = self._revoked_ids()
        if device_id in ids:
            return
        ids[device_id] = when
        path = self.config / REVOKED_FILE
        partial = path.with_name(path.name + '.new')
        self.config.mkdir(parents=True, exist_ok=True)
        partial.write_text(json.dumps(ids), encoding='ascii')
        partial.replace(path)

    def _revoked(self, row, ids=None):
        """When this device was revoked (a time), or None. The database or the list beside the secret may say so."""
        ids = self._revoked_ids() if ids is None else ids
        return row['revoked'] or ids.get(row['id'])

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
            self._secret(create=True)  # made here, on the owner's own click, so a problem is said on the PC
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
            secret = self._secret()
            if secret is None:  # the file went missing since the owner started: nothing is used up
                raise DeviceError('The PC is not ready to pair. Start pairing again on the PC.')
            pending['attempts'] += 1
            matches = bool(re.fullmatch(r'\d{8}', digits)) and hmac.compare_digest(hashlib.sha256(digits.encode()).hexdigest(), pending['code_hash'])
            if not matches:
                if pending['attempts'] >= PAIRING_ATTEMPTS:
                    self.pending = None  # 25 wrong codes in all end this pairing (each caller is locked out after 5 by device_gateway.py)
                raise WrongCode('That code is not right. Check the code on the PC.')
            self.pending = None  # single use
            device_id, key = secrets.token_hex(8), secrets.token_urlsafe(32)
            now = self.clock()
            with self.store.connect() as db:
                db.execute('INSERT INTO devices(id,name,kind,key_hash,secret_id,declared,allowed,created,last_seen) VALUES (?,?,?,?,?,?,?,?,?)',
                           (device_id, pending['name'], pending['kind'], self._key_hash(secret, key), self._secret_id(secret),
                            json.dumps(declared), json.dumps(declared), now, now))
            # The owner started this pairing on the PC for this device: what it declares now is allowed, and each
            # item can be switched off in the Devices panel. Anything it declares later is not allowed by itself.
            return {'device_id': device_id, 'key': key, 'credential': device_id + '.' + key, 'name': pending['name'], 'kind': pending['kind'], 'allowed': declared, 'writes': False}

    # ---- every request of a paired device ----
    def authenticate(self, credential):
        """The device's row for `<id>.<key>`; PermissionError for anything else. Says nothing about why."""
        match = _CREDENTIAL.fullmatch(credential) if isinstance(credential, str) else None
        secret = self._secret()
        if not match or secret is None:
            raise DeviceRefused()
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM devices WHERE id=?', (match[1],)).fetchone()
        expected = self._key_hash(secret, match[2])
        # Compare even when the device is unknown, so an unknown id takes as long as a wrong key.
        valid = hmac.compare_digest(expected, row['key_hash'] if row else '0' * 64)
        if not row or not valid or self._revoked(row) or row['secret_id'] != self._secret_id(secret):
            raise DeviceRefused()
        return self._public(row, secret)

    def usable(self, device_id):
        """Is this device still paired and not revoked, right now? For the checks made again during a request."""
        with self.store.connect() as db:
            row = db.execute('SELECT id, revoked FROM devices WHERE id=?', (device_id,)).fetchone()
        return bool(row) and not self._revoked(row)

    def seen(self, device_id):
        with self.store.connect() as db:
            db.execute('UPDATE devices SET last_seen=? WHERE id=? AND revoked IS NULL', (self.clock(), device_id))

    def declare(self, device_id, declared):
        """The device says what it can do now. A capability it no longer declares is no longer allowed either;
        a new one is not allowed until the owner allows it."""
        declared = _clean_capabilities(declared)
        with self.lock, self.store.connect() as db:
            row = db.execute('SELECT allowed FROM devices WHERE id=? AND revoked IS NULL', (device_id,)).fetchone()
            if not row or device_id in self._revoked_ids():
                raise DeviceRefused()
            allowed = [c for c in json.loads(row['allowed']) if c in declared]
            db.execute('UPDATE devices SET declared=?, allowed=?, last_seen=? WHERE id=? AND revoked IS NULL', (json.dumps(declared), json.dumps(allowed), self.clock(), device_id))
        return {'declared': declared, 'allowed': allowed}

    # ---- the owner's panel ----
    def _public(self, row, secret=None, ids=None):
        secret = self._secret() if secret is None else secret
        revoked = self._revoked(row, ids)
        usable = not revoked and secret is not None and row['secret_id'] == self._secret_id(secret)
        return {'device_id': row['id'], 'name': row['name'], 'kind': row['kind'], 'declared': json.loads(row['declared']),
                'allowed': [] if revoked else json.loads(row['allowed']), 'created': row['created'], 'last_seen': row['last_seen'], 'revoked': revoked,
                # The owner's tick (1.0.16): may this device save memories and tasks? Never for a revoked device.
                'writes': bool(row['writes']) and not revoked,
                # False: the key was made for another installation (restored data); the device pairs again.
                'key_valid': usable}

    def list(self):
        secret, ids = self._secret(), self._revoked_ids()
        with self.store.connect() as db:
            return [self._public(row, secret, ids) for row in db.execute('SELECT * FROM devices ORDER BY created')]

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
            row = db.execute('SELECT id, declared, revoked FROM devices WHERE id=?', (device_id,)).fetchone()
            if not row:
                raise DeviceError('Device not found.')
            if self._revoked(row):
                raise DeviceError('This device is revoked. Pair it again to use it.')
            if any(c not in json.loads(row['declared']) for c in capabilities):
                raise DeviceError('Only a capability the device declares can be allowed.')
            db.execute('UPDATE devices SET allowed=? WHERE id=?', (json.dumps(capabilities), device_id))
        return self.get(device_id)

    def set_writes(self, device_id, allowed):
        """The owner's tick: may this device save memories and tasks? Off for every new device."""
        if type(allowed) is not bool:
            raise DeviceError('Say whether the device may save memories and tasks.')
        with self.lock, self.store.connect() as db:
            row = db.execute('SELECT id, revoked FROM devices WHERE id=?', (device_id,)).fetchone()
            if not row:
                raise DeviceError('Device not found.')
            if self._revoked(row):
                raise DeviceError('This device is revoked. Pair it again to use it.')
            db.execute('UPDATE devices SET writes=? WHERE id=?', (int(allowed), device_id))
        return self.get(device_id)

    def revoke(self, device_id):
        """From now on the device's key is refused. The row stays, so the activity log keeps its name."""
        now = self.clock()
        with self.store.connect() as db:
            changed = db.execute('UPDATE devices SET revoked=?, allowed=?, writes=0 WHERE id=? AND revoked IS NULL', (now, '[]', device_id)).rowcount
            if not changed and not db.execute('SELECT 1 FROM devices WHERE id=?', (device_id,)).fetchone():
                raise DeviceError('Device not found.')
        try:
            self._remember_revoked(device_id, now)  # so an older copy of the database cannot bring it back
        except OSError:
            pass  # the database already refuses the key; only the protection against an old copy is missing
        return self.get(device_id)

    def forget(self, device_id):
        """Remove a revoked device from the list."""
        with self.store.connect() as db:
            row = db.execute('SELECT id, revoked FROM devices WHERE id=?', (device_id,)).fetchone()
            if not row:
                raise DeviceError('Device not found.')
            if not self._revoked(row):
                raise DeviceError('Revoke the device first.')
            db.execute('DELETE FROM devices WHERE id=?', (device_id,))
        return {'forgotten': device_id}

    def names(self):
        """Device id -> name, for the activity log."""
        with self.store.connect() as db:
            return {row['id']: row['name'] for row in db.execute('SELECT id,name FROM devices')}
