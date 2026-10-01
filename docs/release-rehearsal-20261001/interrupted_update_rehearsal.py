"""Real-process interrupted update on the D: sandbox: kill the 1.0.4 installer mid-copy while
JARVIS 1.0.3 is running, check JARVIS is unharmed, then rerun the installer to finish."""
import json, sqlite3, subprocess, time, urllib.request
from pathlib import Path

HOME = Path(r'D:\JARVIS-release-work\sandbox-home')
BUILD = Path(r'D:\JARVIS-release-work\release')
OLD_ID, NEW_ID = '1.0.3-f3f8e4b2c30e', '1.0.4-5eb1df88bf4a'
NEW = BUILD / f'JARVIS-{NEW_ID}'
MEMORY = 'Rehearsal memory: the test colour is teal'


def installer_cmd(*args):
    return [str(NEW / 'release' / 'python' / 'python.exe'), str(NEW / 'installer.py'), *args, '--home', str(HOME), '--no-shortcuts']


def installer(*args):
    return json.loads(subprocess.run(installer_cmd(*args), capture_output=True, text=True, timeout=3600).stdout)


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


def core_answers():
    try:
        link = json.loads((HOME / 'data' / 'core-connection.json').read_text(encoding='utf-8'))
        urllib.request.urlopen(urllib.request.Request(link['origin'] + '/', headers={'X-Jarvis-Desktop': link['token']}), timeout=10).close()
        return True
    except (OSError, ValueError, KeyError):
        return False


def memory_kept():
    db = sqlite3.connect((HOME / 'data' / 'jarvis.sqlite3').as_uri() + '?mode=ro', uri=True)
    try:
        return MEMORY in [r[0] for r in db.execute("SELECT body FROM items WHERE kind='memory'")]
    finally:
        db.close()


def report(step, **facts):
    print(f'{step:<34}', json.dumps(facts), flush=True)


old, new = HOME / 'releases' / OLD_ID, HOME / 'releases' / NEW_ID
status = installer('status')
report('0 starting point', current=status['current']['release'], memory_kept=memory_kept())
launch_and_wait()
report('  JARVIS 1.0.3 running', processes_old=processes(old), core_answers=core_answers())

proc = subprocess.Popen(installer_cmd('install', '--package', str(NEW)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
incoming = HOME / 'releases' / f'.incoming-{NEW_ID}'
copied = 0
for _ in range(1200):
    if incoming.exists():
        copied = sum(1 for p in incoming.rglob('*') if p.is_file())
        if copied >= 3000:
            break
    time.sleep(0.25)
subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], capture_output=True)
proc.wait(timeout=60)
partial = sum(1 for p in incoming.rglob('*') if p.is_file()) if incoming.exists() else 0
report('1 installer killed mid-copy', files_copied_when_killed=partial, of_total=10645,
       current=installer('status')['current']['release'])
report('  JARVIS unharmed', processes_old=processes(old), core_answers=core_answers(), memory_kept=memory_kept(),
       new_release_folder_exists=new.exists())
out = installer('verify')
report('  verify current release', result=out['status'], release=out.get('release'), reason=out.get('reason'))

out = installer('install', '--package', str(NEW))
report('2 rerun installer', result=out['status'], release=out.get('release'), previous=out.get('previous'),
       leftover_incoming=incoming.exists(), stale_old_processes=processes(old))
launch_and_wait()
report('  launch 1.0.4', processes_new=processes(new), core_answers=core_answers(), memory_kept=memory_kept())
out = installer('verify')
report('  verify 1.0.4 after use', result=out['status'], release=out.get('release'), reason=out.get('reason'))
