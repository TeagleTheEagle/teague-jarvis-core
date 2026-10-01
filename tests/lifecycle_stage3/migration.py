"""Isolated TEST migration only. Fixed paths, no production/App imports or start path."""
import ctypes
from ctypes import wintypes
import errno
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).absolute().parent))
import verify

BASE = Path(__file__).absolute().parent / 'evidence'
K = ctypes.WinDLL('kernel32', use_last_error=True)
K.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                          wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
K.CreateFileW.restype = wintypes.HANDLE
K.CloseHandle.argtypes = [wintypes.HANDLE]


def check_paths(root):
    root = Path(os.path.abspath(root))
    if root.parent != BASE or not re.fullmatch(r'TEST-[a-f0-9]{32}', root.name):
        raise ValueError('TEST_ROOT_REQUIRED')
    for path in [root, *root.parents]:
        if not path.exists() or path.stat(follow_symlinks=False).st_file_attributes & 0x400:
            raise ValueError('REPARSE_OR_MISSING')
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            p = Path(directory) / name
            st = p.stat(follow_symlinks=False)
            if st.st_file_attributes & 0x400 or (p.is_file() and st.st_nlink != 1):
                raise ValueError('REPARSE_OR_HARDLINK')
    if (root / 'TEST_ONLY').read_text() != root.name:
        raise ValueError('TEST_MARKER')
    return root


class Lock:
    def __init__(self, root):
        self.root = check_paths(root)
        self.h = K.CreateFileW(str(root / 'migration.lock'), 0xc0000000, 0, None, 4, 0x00200080, None)
        if self.h == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_last_error(), 'TEST_LOCK_UNAVAILABLE')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        K.CloseHandle(self.h)


def write(path, value):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temp.open('x', encoding='utf-8') as f:
        json.dump(value, f, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def read(path):
    return json.loads(path.read_text())


def fault_at(fault, point):
    if fault == point:
        raise RuntimeError('INJECTED_' + point)
    if fault == 'crash-' + point:
        os._exit(83)


def raw_stamp(folder):
    # Conservative rollback guard includes SQLite/WAL bytes, not just logical values.
    return {p.relative_to(folder).as_posix(): verify.sha(p.read_bytes())
            for p in sorted(folder.rglob('*')) if p.is_file() and not p.name.endswith('-shm')}


def source_expected(root):
    source = root / 'source'
    expected_identity = {'mode': 'TEST', 'installation_id': 'TEST-installation', 'data_id': root.name}
    if read(source / 'identity.json') != expected_identity:
        raise ValueError('SOURCE_IDENTITY')
    known = {'jarvis.sqlite3', 'jarvis.sqlite3-wal', 'jarvis.sqlite3-shm', 'persistent', 'identity.json',
             'runtime', 'secrets', 'cache'}
    if {p.name for p in source.iterdir()} - known:
        raise ValueError('UNCLASSIFIED_SOURCE')
    result = verify.inventory(source)
    policy = read(root / 'fixture-policy.json')
    if result['database']['schema'] != policy['schema'] or result['database']['version'] != 1:
        raise ValueError('SCHEMA_MISMATCH')
    if sorted(result['artifacts']) != policy['artifacts']:
        raise ValueError('UNCLASSIFIED_OR_MISSING_ARTIFACT')
    return result


def migrate(root, operation='migration-1', fault=None, recover=False):
    root = check_paths(root)
    if not re.fullmatch(r'[a-z0-9-]{1,40}', operation):
        raise ValueError('OPERATION_ID')
    with Lock(root):
        journal_path = root / 'journal.json'
        if journal_path.exists():
            journal = read(journal_path)
            if journal.get('operation') != operation or journal.get('namespace') != root.name:
                raise ValueError('OPERATION_CONFLICT')
            if journal.get('phase') == 'ACTIVE':
                if read(root / 'mapping.json') != {'active': 'canonical', 'data_id': root.name}:
                    raise ValueError('MAPPING_CONFLICT')
                verify.verify(root / 'canonical', journal['expected'])
                return {'status': 'ACTIVE_TEST_ONLY', 'idempotent': True, 'execution_authorized': False}
            if not recover or journal.get('phase') not in ('VERIFIED', 'PUBLISHED'):
                raise ValueError('RECOVERY_REQUIRED')
            # Explicit recovery only completes already verified publication. Partial backup is retained.
            if source_expected(root) != journal['expected']:
                raise ValueError('SOURCE_CHANGED')
        else:
            if read(root / 'mapping.json') != {'active': 'source', 'data_id': root.name}:
                raise ValueError('MAPPING_IDENTITY')
            if any((root / n).exists() for n in ('backup', 'staging', 'canonical')):
                raise ValueError('DESTINATION_NOT_EMPTY')
            journal = {'namespace': root.name, 'operation': operation, 'phase': 'PREPARED'}
            write(journal_path, journal)
            fault_at(fault, 'prepared')
            # Only a TEST source may be opened for the reservation; no production path parameters.
            gate = sqlite3.connect((root / 'source/jarvis.sqlite3').as_uri() + '?mode=rw', uri=True, timeout=.2)
            try:
                gate.execute('BEGIN IMMEDIATE')
                expected = source_expected(root)
                journal['expected'] = expected
                write(journal_path, journal)
                if fault == 'hold':
                    write(root / 'held.json', {'held': True})
                    time.sleep(1)
                if fault == 'disk-full':
                    raise OSError(errno.ENOSPC, 'INJECTED_DISK_FULL')
                backup = root / 'backup'
                backup.mkdir()
                src = sqlite3.connect((root / 'source/jarvis.sqlite3').as_uri() + '?mode=ro', uri=True)
                dst = sqlite3.connect(backup / 'jarvis.sqlite3')
                start = time.monotonic()
                def progress(status, remaining, total):
                    if time.monotonic() - start > 5:
                        raise TimeoutError('BACKUP_DEADLINE')
                    fault_at(fault, 'backup-copy')
                    if fault == 'disk-full-backup':
                        raise OSError(errno.ENOSPC, 'INJECTED_DISK_FULL_DURING_BACKUP')
                try:
                    src.backup(dst, pages=1, progress=progress)
                finally:
                    src.close()
                    dst.close()
                shutil.copytree(root / 'source/persistent', backup / 'persistent')
                shutil.copyfile(root / 'source/identity.json', backup / 'identity.json')
                if fault == 'artifact-race':
                    (root / 'source/persistent/personality.txt').write_text('TEST concurrent change')
                if source_expected(root) != expected:
                    raise ValueError('SOURCE_CHANGED')
                verify.verify(backup, expected)
                journal['phase'] = 'BACKED_UP'
                write(journal_path, journal)
            finally:
                gate.rollback()
                gate.close()
            fault_at(fault, 'backed-up')
            shutil.copytree(backup, root / 'staging')
            if fault == 'corrupt-staging':
                (root / 'staging/jarvis.sqlite3').write_bytes(b'corrupt')
            if fault == 'omit-artifact':
                (root / 'staging/persistent/personality.txt').unlink()
            verify.verify(root / 'staging', expected)
            journal['phase'] = 'VERIFIED'
            write(journal_path, journal)
            fault_at(fault, 'verified')
        if (root / 'canonical').exists():
            if (root / 'staging').exists():
                raise ValueError('AMBIGUOUS_PUBLICATION')
            verify.verify(root / 'canonical', journal['expected'])
        else:
            verify.verify(root / 'staging', journal['expected'])
            os.rename(root / 'staging', root / 'canonical')
        fault_at(fault, 'renamed')
        journal['phase'] = 'PUBLISHED'
        write(journal_path, journal)
        fault_at(fault, 'published')
        if source_expected(root) != journal['expected']:
            raise ValueError('SOURCE_CHANGED')
        # Mapping changes TEST directories only. No Core or production config is involved.
        mapping = read(root / 'mapping.json')
        if mapping not in ({'active': 'source', 'data_id': root.name}, {'active': 'canonical', 'data_id': root.name}):
            raise ValueError('MAPPING_CONFLICT')
        journal['source_stamp'] = raw_stamp(root / 'source')
        journal['canonical_stamp'] = raw_stamp(root / 'canonical')
        write(journal_path, journal)
        write(root / 'mapping.json', {'active': 'canonical', 'data_id': root.name})
        fault_at(fault, 'mapped')
        journal['phase'] = 'ACTIVE'
        write(journal_path, journal)
        return {'status': 'ACTIVE_TEST_ONLY', 'idempotent': False, 'execution_authorized': False}


def rollback(root):
    root = check_paths(root)
    with Lock(root):
        journal = read(root / 'journal.json')
        if journal.get('namespace') != root.name:
            raise ValueError('JOURNAL_IDENTITY')
        mapping = read(root / 'mapping.json')
        if mapping == {'active': 'source', 'data_id': root.name}:
            if journal.get('phase') in ('CANCELLED_BEFORE_CUTOVER', 'ROLLED_BACK_WITHOUT_NEW_WRITES'):
                return {'status': journal['phase'], 'idempotent': True, 'execution_authorized': False}
            # Before cutover: retain source and all partial evidence; no deletion or replay.
            journal['phase'] = 'CANCELLED_BEFORE_CUTOVER'
        elif mapping == {'active': 'canonical', 'data_id': root.name}:
            if (raw_stamp(root / 'canonical') != journal.get('canonical_stamp') or
                    raw_stamp(root / 'source') != journal.get('source_stamp')):
                raise ValueError('NEW_WRITES_ROLLBACK_REFUSED')
            verify.verify(root / 'canonical', journal['expected'])
            if source_expected(root) != journal['expected']:
                raise ValueError('SOURCE_CHANGED')
            write(root / 'mapping.json', {'active': 'source', 'data_id': root.name})
            journal['phase'] = 'ROLLED_BACK_WITHOUT_NEW_WRITES'
        else:
            raise ValueError('MAPPING_CONFLICT')
        write(root / 'journal.json', journal)
        return {'status': journal['phase'], 'execution_authorized': False}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='TEST ONLY isolated migration; never starts JARVIS')
    parser.add_argument('root')
    parser.add_argument('--operation', default='migration-1')
    parser.add_argument('--fault')
    parser.add_argument('--recover', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()
    try:
        result = rollback(args.root) if args.rollback else migrate(args.root, args.operation, args.fault, args.recover)
        print(json.dumps(result))
    except Exception as exc:
        print(json.dumps({'status': 'REFUSED', 'error_type': type(exc).__name__, 'execution_authorized': False}))
        raise SystemExit(1)
