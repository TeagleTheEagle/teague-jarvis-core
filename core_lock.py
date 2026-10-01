"""One JARVIS Core per data folder.

The Core holds an OS-level exclusive lock on <data>/core.lock for its whole lifetime.
The operating system releases it when the process exits for any reason, including a
crash, so a stale lock can never block the next start. A second Core for the same
data folder refuses to start instead of sharing memory with the first.

<data>/core-owner.json records the owner's pid and port for launchers and diagnostics.
It contains no secrets and is advisory: the lock, not the file, decides ownership.
"""
import json
import os
import time
from pathlib import Path

LOCK_NAME = 'core.lock'
OWNER_NAME = 'core-owner.json'
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

    def publish(self, port):
        self.owner = {'pid': os.getpid(), 'port': port, 'started': time.time()}
        partial = self.owner_path.with_suffix('.tmp')
        partial.write_text(json.dumps(self.owner), encoding='utf-8')
        os.replace(partial, self.owner_path)

    def release(self):
        if self.handle is None:
            return
        if self.owner is not None and read_owner(self.root).get('pid') == self.owner['pid']:
            try:
                self.owner_path.unlink()
            except OSError:
                pass
        self.handle.close()  # closing the handle releases the OS lock
        self.handle = None
