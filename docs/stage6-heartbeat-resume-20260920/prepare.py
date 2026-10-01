"""Preserve sacrificial monitor evidence; never inspect VM/configuration paths."""
import datetime, hashlib, json, pathlib, shutil, subprocess

R = pathlib.Path(__file__).resolve().parent
OLD = R.parent / 'stage6-heartbeat-decoupled-20260918'
REPO = R.parent.parent

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def inventory(root):
    rows = []
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise RuntimeError('Unexpected symlink: ' + str(p))
        if p.is_file():
            before = p.stat()
            sha = digest(p)
            after = p.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError('Changed during inventory: ' + str(p))
            rows.append(dict(path=str(p.relative_to(root)), bytes=before.st_size,
                             mtime_ns=before.st_mtime_ns, sha256=sha))
    return rows

def save(name, value):
    with (R/name).open('x', encoding='utf-8') as f:
        json.dump(value, f, sort_keys=True, indent=2)

if __name__ == '__main__':
    save('preserved-inventory-before.json', inventory(OLD))
    selected = [p for p in OLD.iterdir() if p.is_file() and
                (p.suffix in ('.py', '.ps1') or p.name in ('DESIGN.md', 'J6Probe.exe'))]
    copies = []
    for p in selected:
        dest = R/p.name
        if dest.exists():
            raise RuntimeError('Refusing overwrite: ' + str(dest))
        shutil.copyfile(p, dest)
        if digest(dest) != digest(p):
            raise RuntimeError('Copy mismatch')
        copies.append(dict(path=p.name, sha256=digest(p)))
    save('validation-source-copy.json', copies)
    status = subprocess.check_output(['git', '--no-optional-locks', 'status', '--short', '--untracked-files=no'], cwd=REPO).decode()
    save('tracked-status-before.json', {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status':status})
    # Hash modified tracked files only; no environment/credential files are read.
    names = subprocess.check_output(['git', '--no-optional-locks', 'diff', '--name-only', '-z', 'HEAD'], cwd=REPO).decode().split('\0')
    rows=[]
    for name in filter(None, names):
        if pathlib.Path(name).name.startswith('.env'):
            raise RuntimeError('Refusing secret file')
        p=REPO/name
        rows.append(dict(path=name, sha256=digest(p) if p.is_file() else None))
    save('preexisting-tracked-changes.json', rows)
    print(json.dumps({'preserved_files':len(json.loads((R/'preserved-inventory-before.json').read_text())), 'copied_sources':len(copies), 'preexisting_tracked_changes':len(rows)}))
