"""Stage 7 lifecycle rehearsal on a fresh D: sandbox: install, update while running, verify
after use, rollback, uninstall (data kept, no program residue), reinstall. Synthetic memory only."""
import json, sqlite3, subprocess, time, urllib.request
from pathlib import Path

HOME = Path(r'D:\JARVIS-release-work\sandbox-home')
BUILD = Path(r'D:\JARVIS-release-work\release')
OLD_ID, NEW_ID = '1.0.2-3dc1a2016c6b', '1.0.3-f3f8e4b2c30e'
V1, V2 = BUILD / f'JARVIS-{OLD_ID}', BUILD / f'JARVIS-{NEW_ID}'
MEMORY = 'Rehearsal memory: the test colour is teal'


def installer(package, *args):
    r = subprocess.run([str(package / 'release' / 'python' / 'python.exe'), str(package / 'installer.py'), *args,
                        '--home', str(HOME), '--no-shortcuts'], capture_output=True, text=True, timeout=3600)
    return json.loads(r.stdout)


def processes(under):
    script = "@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '" + str(under) + "\\*' }).Count"
    return int(subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True).stdout.strip() or 0)


def launch_and_wait():
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(HOME / 'JARVIS.ps1')], check=True)
    for _ in range(240):
        if (HOME / 'data' / 'core-connection.json').exists():
            break
        time.sleep(0.5)
    time.sleep(3)


def api(route, body=None):
    link = json.loads((HOME / 'data' / 'core-connection.json').read_text(encoding='utf-8'))
    h = {'X-Jarvis-Desktop': link['token']}
    page = urllib.request.urlopen(urllib.request.Request(link['origin'] + '/', headers=h), timeout=10)
    h['Cookie'] = (page.headers.get('Set-Cookie') or '').split(';')[0]
    req = urllib.request.Request(link['origin'] + route, headers={**h, 'Content-Type': 'application/json'},
                                 data=None if body is None else json.dumps(body).encode(), method='GET' if body is None else 'POST')
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def memories():
    db = sqlite3.connect((HOME / 'data' / 'jarvis.sqlite3').as_uri() + '?mode=ro', uri=True)
    try:
        return [r[0] for r in db.execute("SELECT body FROM items WHERE kind='memory'")]
    finally:
        db.close()


def report(step, **facts):
    print(f'{step:<30}', json.dumps(facts), flush=True)


old, new = HOME / 'releases' / OLD_ID, HOME / 'releases' / NEW_ID

out = installer(V1, 'install', '--package', str(V1))
report('0 fresh install 1.0.2', result=out['status'], release=out.get('release'))
launch_and_wait()
api('/api/item', {'kind': 'memory', 'body': MEMORY})
report('  running 1.0.2', processes_old=processes(old), memory_saved=MEMORY in memories())
out = installer(V1, 'verify')
report('  verify 1.0.2 while in use', result=out['status'], reason=out.get('reason'))

out = installer(V2, 'install', '--package', str(V2))
report('1 update while running', result=out['status'], release=out.get('release'), previous=out.get('previous'),
       stale_old_processes=processes(old), memory_kept=MEMORY in memories())
launch_and_wait()
report('  launch 1.0.3', processes_new=processes(new), processes_old=processes(old))
out = installer(V2, 'verify')
report('  verify 1.0.3 after use', result=out['status'], reason=out.get('reason'))

out = installer(V2, 'rollback')
report('2 rollback', result=out['status'], release=out.get('release'), reason=out.get('reason'),
       stale_new_processes=processes(new), memory_kept=MEMORY in memories())
launch_and_wait()
report('  launch 1.0.2 again', processes_old=processes(old), processes_new=processes(new))

out = installer(V2, 'uninstall')
leftover = sum(1 for p in (HOME / 'releases').rglob('*') if p.is_file()) if (HOME / 'releases').exists() else 0
report('3 uninstall', result=out['status'], files_removed=out.get('program_files_removed'), kept=out.get('kept'),
       jarvis_processes=processes(HOME), home_now=sorted(p.name for p in HOME.iterdir()),
       leftover_program_files=leftover, memory_kept=MEMORY in memories())

out = installer(V2, 'install', '--package', str(V2))
report('4 reinstall 1.0.3', result=out['status'], release=out.get('release'), memory_restored=MEMORY in memories())
out = installer(V2, 'verify')
report('5 verify installed files', result=out['status'], release=out.get('release'))
