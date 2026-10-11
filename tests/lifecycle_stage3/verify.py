"""Independent TEST dataset verifier. No migrator or production imports."""
import hashlib
import json
from pathlib import Path
import sqlite3


def sha(data):
    return hashlib.sha256(data).hexdigest()


def database(path):
    # mode=ro refuses missing input; no Store constructor, SQL from schemas or extensions.
    db = sqlite3.connect(Path(path).absolute().as_uri() + '?mode=ro', uri=True)
    try:
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('BEGIN')
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('INTEGRITY')
        if db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('FOREIGN_KEYS')
        schema = db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
        tables = {}
        for kind, name, _, sql in schema:
            if kind != 'table':
                continue
            quoted = '"' + name.replace('"', '""') + '"'
            rows = db.execute('SELECT * FROM ' + quoted).fetchall()
            # Type-tagged cells preserve blobs, nulls, floats and strings unambiguously.
            serial = sorted(json.dumps([(type(v).__name__, v.hex() if isinstance(v, bytes) else v)
                                        for v in row], ensure_ascii=True) for row in rows)
            tables[name] = {'rows': len(rows), 'sha256': sha('\n'.join(serial).encode())}
        validate_budget(db)
        return {'schema': sha(json.dumps(schema).encode()),
                'version': db.execute('PRAGMA user_version').fetchone()[0], 'tables': tables}
    finally:
        db.close()


def validate_budget(db):
    # Independent read-only assertions over the fixture's canonical budget schema.
    db.row_factory = sqlite3.Row
    for limit in db.execute('SELECT * FROM project_budget_limits'):
        charged = [0, 0]
        for row in db.execute('SELECT * FROM project_budget_reservations WHERE project=?', (limit['project'],)):
            if row['state'] not in ('held', 'started', 'recovery_required', 'settled', 'released'):
                raise ValueError('RESERVATION_STATE')
            if row['revision'] < 0 or row['started'] not in (0, 1):
                raise ValueError('RESERVATION_REVISION')
            if (row['state'] == 'held' and row['started']) or (row['state'] == 'started' and not row['started']):
                raise ValueError('RESERVATION_STATE')
            if row['state'] == 'settled' and (not row['started'] or row['outcome'] not in ('succeeded', 'failed') or not row['evidence']):
                raise ValueError('RESERVATION_EVIDENCE')
            for i, (reserved, consumed) in enumerate((('core_requests', 'used_core'), ('container_checks', 'used_container'))):
                if not 0 <= row[consumed] <= row[reserved] <= 10000:
                    raise ValueError('RESERVATION_AMOUNTS')
                if row['state'] == 'released' and (row['started'] or row[consumed]):
                    raise ValueError('RESERVATION_RELEASE')
                charged[i] += row[consumed] if row['state'] == 'settled' else 0 if row['state'] == 'released' else row[reserved]
        if charged[0] > limit['core_requests'] or charged[1] > limit['container_checks']:
            raise ValueError('BUDGET_TOTAL')


def inventory(folder):
    folder = Path(folder)
    files = {}
    for path in sorted((folder / 'persistent').rglob('*')):
        if path.is_symlink() or (path.exists() and path.stat().st_file_attributes & 0x400):
            raise ValueError('LINK')
        if path.is_file():
            files[path.relative_to(folder).as_posix()] = sha(path.read_bytes())
    return {'database': database(folder / 'jarvis.sqlite3'), 'artifacts': files,
            'identity': json.loads((folder / 'identity.json').read_text())}


def verify(folder, expected):
    found = inventory(folder)
    if found != expected:
        raise ValueError('CONTENT_MISMATCH')
    allowed = {'jarvis.sqlite3', 'jarvis.sqlite3-wal', 'jarvis.sqlite3-shm', 'identity.json', 'persistent'}
    if set(p.name for p in Path(folder).iterdir()) - allowed:
        raise ValueError('UNEXPECTED_MIGRATED_STATE')
    return {'status': 'VERIFIED', 'tables': len(found['database']['tables']),
            'rows': sum(v['rows'] for v in found['database']['tables'].values()),
            'artifacts': len(found['artifacts']), 'execution_authorized': False}
