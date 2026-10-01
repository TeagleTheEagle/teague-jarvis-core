"""Gate 18 rehearsal on local D: sandboxes with synthetic data only (packaged releases).

Covers the Gate 18 list: backup identity, restore into a disposable target, state/data
integrity, configuration, startup, version identity, no duplicate Core, clean shutdown,
rollback readiness, backup source unchanged. Touches nothing outside D:\\JARVIS-release-work."""
import hashlib, json, os, sqlite3, subprocess, sys, time, urllib.request, zipfile
from pathlib import Path

WORK = Path(r'D:\JARVIS-release-work\gate18')
BUILD = Path(r'D:\JARVIS-release-work\release')
OLD_ID, NEW_ID = '1.0.8-d326428391cc', sys.argv[1]
OLD, NEW = BUILD / f'JARVIS-{OLD_ID}', BUILD / f'JARVIS-{NEW_ID}'
A, B = WORK / 'home-a', WORK / 'home-b'   # A: the install that is backed up; B: the disposable restore target
MEMORIES = ['Gate 18 memory one: the test colour is teal', 'Gate 18 memory two: the test number is 42']
PERSONALITY = 'Gate 18 synthetic personality: answer briefly.\n'


def report(step, **facts):
    print(f'{step:<36}', json.dumps(facts), flush=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def installer(package, home, *args):
    cmd = [str(package / 'release' / 'python' / 'python.exe'), str(package / 'installer.py'), *args, '--home', str(home), '--no-shortcuts']
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, timeout=3600).stdout)


def current_release(home):
    ident = json.loads((home / 'current.json').read_text(encoding='utf-8'))['release']
    release = home / 'releases' / ident
    return release / 'python' / 'python.exe', release / 'app', ident


def app_cli(home, script, *args):
    """A shipped command line run from the installed release with no JARVIS_* environment:
    it must find the install's own data folder (RECOVERY.md, command-line use)."""
    python, app, _ = current_release(home)
    env = {k: v for k, v in os.environ.items() if not k.startswith('JARVIS_')}
    r = subprocess.run([str(python), str(app / script), *args], cwd=app, env=env, capture_output=True, text=True, timeout=1800)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {'status': 'error', 'stdout': r.stdout[-400:], 'stderr': r.stderr[-800:]}


def processes(home):
    script = "@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '" + str(home / 'releases') + "\\*' }).Count"
    return int(subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True).stdout.strip() or 0)


def launch(home):
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(home / 'JARVIS.ps1')], check=True)
    for _ in range(240):
        if (home / 'data' / 'core-connection.json').exists():
            break
        time.sleep(0.5)
    time.sleep(3)


def api(home, route, body=None, timeout=120):
    link = json.loads((home / 'data' / 'core-connection.json').read_text(encoding='utf-8'))
    h = {'X-Jarvis-Desktop': link['token']}
    page = urllib.request.urlopen(urllib.request.Request(link['origin'] + '/', headers=h), timeout=10)
    h['Cookie'] = (page.headers.get('Set-Cookie') or '').split(';')[0]
    req = urllib.request.Request(link['origin'] + route, headers={**h, 'Content-Type': 'application/json'},
                                 data=None if body is None else json.dumps(body).encode(), method='GET' if body is None else 'POST')
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def shutdown(home):
    """Ask the Core to stop (what tray 'Quit JARVIS completely' does); report what was left."""
    try:
        api(home, '/api/shutdown', {})
    except Exception:
        pass
    for _ in range(120):
        if not (home / 'data' / 'core-connection.json').exists():
            break
        time.sleep(0.5)
    core_stopped = not (home / 'data' / 'core-connection.json').exists()
    time.sleep(5)
    left = processes(home)
    if left:
        subprocess.run(['powershell', '-NoProfile', '-Command', "Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '"
                        + str(home / 'releases') + "\\*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
                       capture_output=True)
        time.sleep(2)
    return {'core_stopped_on_request': core_stopped, 'desktop_processes_left_then_closed': left, 'processes_now': processes(home)}


def memories(home):
    db = sqlite3.connect((home / 'data' / 'jarvis.sqlite3').as_uri() + '?mode=ro', uri=True)
    try:
        return [r[0] for r in db.execute("SELECT body FROM items WHERE kind='memory'")]
    finally:
        db.close()


def identity(home):
    updates = api(home, '/api/state').get('updates', {})
    return {'installed_release': updates.get('installed_release'), 'source_revision': updates.get('source_revision')}


assert not WORK.exists(), 'gate18 work folder must be new'
WORK.mkdir(parents=True)

# 1. The install that will be backed up: owner configuration plus saved memories.
out = installer(NEW, A, 'install', '--package', str(NEW))
(A / 'config' / 'personality.txt').write_text(PERSONALITY, encoding='utf-8')
launch(A)
for m in MEMORIES:
    api(A, '/api/item', {'kind': 'memory', 'body': m})
ident_a = identity(A)
report('1 source install A', result=out['status'], release=out.get('release'), **ident_a,
       memories_saved=all(m in memories(A) for m in MEMORIES))

# 2. Backup through the Core (Settings > Backup & recovery), verified two ways.
backup = api(A, '/api/recovery', {'action': 'create'}, timeout=600)
archive = A / 'data-backups' / (backup['id'] + '.zip')
hash_before = sha256(archive)
rehearsal = api(A, '/api/recovery', {'action': 'rehearse', 'id': backup['id']}, timeout=600)
report('2 backup identity', result=backup['status'], id=backup['id'], bytes=archive.stat().st_size, sha256=hash_before,
       database_counts=backup['database_counts'], rehearsal=rehearsal['status'],
       archive_outside_program_files='releases' not in archive.parts)
cli = app_cli(A, 'recovery.py', 'verify', '--id', backup['id'])
report('  shipped CLI verify, no env', result=cli.get('status'), files=cli.get('files'), error=cli.get('stderr'))
with zipfile.ZipFile(archive) as z:
    names = set(z.namelist())
    personality_in_backup = 'app/personality.txt' in names and z.read('app/personality.txt').decode('utf-8') == PERSONALITY
report('  owner configuration in backup', personality_txt=personality_in_backup, preferences_json='app/desktop/preferences.json' in names)
report('  shutdown A', **shutdown(A))

# 3. Disposable restore target B: OLD then NEW (so a rollback exists), then import the backup.
installer(OLD, B, 'install', '--package', str(OLD))
out = installer(NEW, B, 'install', '--package', str(NEW))
report('3 target install B', release=out.get('release'), previous=out.get('previous'))
dry = app_cli(B, 'switch_over.py', '--archive', str(archive))
report('  switch-over dry run', result=dry.get('status'), files_to_import=dry.get('files_to_import'),
       personal_config=dry.get('personal_config'), error=dry.get('stderr'))
imported = app_cli(B, 'switch_over.py', '--archive', str(archive), '--apply', '--include-personal-config')
report('  switch-over import', result=imported.get('status'), files_imported=imported.get('files_imported'),
       database_counts=imported.get('database_counts'), personal_config_written=imported.get('personal_config_written'),
       error=imported.get('stderr'))
config_personality = B / 'config' / 'personality.txt'
report('  restored state before launch', memories_restored=all(m in memories(B) for m in MEMORIES),
       personality_in_config=config_personality.exists() and config_personality.read_text(encoding='utf-8') == PERSONALITY,
       program_files=installer(NEW, B, 'verify')['status'])

# 4. Startup on the restored data: identity, duplicate-Core fencing, clean shutdown.
launch(B)
ident_b = identity(B)
origin = json.loads((B / 'data' / 'core-connection.json').read_text(encoding='utf-8'))['origin']
subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(B / 'JARVIS.ps1')], capture_output=True)  # a second launch
time.sleep(10)
report('4 startup on restored data', processes=processes(B), **ident_b, same_identity_as_A=ident_b == ident_a,
       memories_via_api=sum(1 for i in api(B, '/api/state').get('memory', []) if i.get('body') in MEMORIES),
       second_launch_joined_same_core=json.loads((B / 'data' / 'core-connection.json').read_text(encoding='utf-8'))['origin'] == origin)
report('  shutdown B', **shutdown(B))

# 5. Rollback readiness with the restored data in place.
rb = installer(NEW, B, 'rollback')
launch(B)
report('5 rollback with restored data', result=rb['status'], release=rb.get('release'),
       memories_kept=all(m in memories(B) for m in MEMORIES), processes=processes(B), **identity(B))
report('  shutdown after rollback', **shutdown(B))

# 6. The backup source is unchanged by everything above (backup/restore-source preservation).
report('6 backup source unchanged', sha256_unchanged=sha256(archive) == hash_before, bytes=archive.stat().st_size)
