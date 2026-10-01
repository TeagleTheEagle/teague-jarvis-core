"""One JARVIS Core per data folder.

The Core holds an OS-level exclusive lock on <data>/core.lock for its whole lifetime.
The operating system releases it when the process exits for any reason, including a
crash, so a stale lock can never block the next start. A second Core for the same
data folder refuses to start instead of sharing memory with the first.

<data>/core-owner.json records the owner's pid and port for launchers and diagnostics.
It contains no secrets and is advisory: the lock, not the file, decides ownership.

A background Core (server.py --background) also writes <data>/core-connection.json
with its origin and client token so local apps can attach to the one running Core.
It has the same trust level as the desktop session file: it lives in the user's own
data folder, is git-ignored, and is removed when the Core stops.
"""
import json
import os
import time
from pathlib import Path

LOCK_NAME = 'core.lock'
OWNER_NAME = 'core-owner.json'
CONNECTION_NAME = 'core-connection.json'
ALREADY_RUNNING_EXIT_CODE = 3


class CoreAlreadyRunning(RuntimeError):
    def __init__(self, root, owner):
        self.root = root
        self.owner = owner
        detail = ''
        if owner.get('pid'):
            detail = f" (PID {owner['pid']}, port {owner.get('port', 'unknown')})"
        super().__init__(f'JARVIS Core is already running for this data folder{detail}.')


def _lock(handle):
    handle.seek(0)
    if os.name == 'nt':
        import msvcrt
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def read_owner(data_dir):
    try:
        owner = json.loads((Path(data_dir) / OWNER_NAME).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return owner if isinstance(owner, dict) else {}


class CoreLock:
    def __init__(self, data_dir):
        self.root = Path(data_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.owner_path = self.root / OWNER_NAME
        self.handle = open(self.root / LOCK_NAME, 'a+b')
        try:
            _lock(self.handle)
        except OSError:
            self.handle.close()
            self.handle = None
            raise CoreAlreadyRunning(self.root, read_owner(self.root)) from None
        self.owner = None

    @staticmethod
    def _write(path, data):
        partial = path.with_suffix('.tmp')
        partial.write_text(json.dumps(data), encoding='utf-8')
        os.replace(partial, path)

    def publish(self, port):
        self.owner = {'pid': os.getpid(), 'port': port, 'started': time.time()}
        self._write(self.owner_path, self.owner)

    def publish_connection(self, origin, token):
        self._write(self.root / CONNECTION_NAME, {'origin': origin, 'token': token, 'pid': os.getpid()})

    def release(self):
        if self.handle is None:
            return
        if self.owner is not None:
            for name in (OWNER_NAME, CONNECTION_NAME):
                path = self.root / name
                try:
                    if json.loads(path.read_text(encoding='utf-8')).get('pid') == self.owner['pid']:
                        path.unlink()
                except (OSError, ValueError):
                    pass
        self.handle.close()  # closing the handle releases the OS lock
        self.handle = None
