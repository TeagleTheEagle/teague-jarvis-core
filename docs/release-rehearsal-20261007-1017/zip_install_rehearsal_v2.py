"""Distributable zip rehearsal, version 2 (release 1.0.17 and later: JARVIS as his own app): hash check, Windows
extraction, install.cmd into a sandbox home (no shortcuts; the installer withholds the real ones for any home that is
not the PC's own), launch through the current release's own JARVIS.exe (version 1 started JARVIS.ps1, which a release
with its own program no longer has), verify, uninstall. Never runs install.cmd without --home.

    .venv\\Scripts\\python.exe docs\\release-rehearsal-20261007-1017\\zip_install_rehearsal_v2.py <release id>
"""
import hashlib, json, subprocess, sys, time, urllib.request
from pathlib import Path

WORK = Path(r'D:\JARVIS-release-work')
RELEASE_ID = sys.argv[1]
RECORD = json.loads((WORK / 'release' / f'JARVIS-{RELEASE_ID}.release.json').read_text(encoding='utf-8'))
ZIP = WORK / 'release' / RECORD['zip']
EXTRACT = WORK / f'zip-test-{RELEASE_ID}' / 'extracted'
HOME = WORK / f'zip-test-{RELEASE_ID}' / 'sandbox-home'


def report(step, **facts):
    print(f'{step:<30}', json.dumps(facts), flush=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def ps(script, timeout=1800):
    return subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True, timeout=timeout)


def processes():
    out = ps("@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '" + str(HOME) + "\\*' } | ForEach-Object { $_.Name }) -join ','").stdout
    names = [n for n in out.strip().split(',') if n]
    return {'count': len(names), 'names': sorted(set(names))}


def core_answers():
    try:
        link = json.loads((HOME / 'data' / 'core-connection.json').read_text(encoding='utf-8'))
        urllib.request.urlopen(urllib.request.Request(link['origin'] + '/', headers={'X-Jarvis-Desktop': link['token']}), timeout=10).close()
        return True
    except (OSError, ValueError, KeyError):
        return False


assert not EXTRACT.exists() and not HOME.exists(), 'zip-test folders must be new'
report('0 zip hash', matches_record=sha256(ZIP) == RECORD['zip_sha256'], bytes=ZIP.stat().st_size)

r = ps(f"Expand-Archive -LiteralPath '{ZIP}' -DestinationPath '{EXTRACT}'", timeout=3600)
package = EXTRACT / f'JARVIS-{RELEASE_ID}'
report('1 extract (Expand-Archive)', ok=r.returncode == 0, package_files=sorted(p.name for p in package.iterdir()))

started = time.time()
r = subprocess.run(['cmd', '/c', str(package / 'install.cmd'), '--home', str(HOME), '--no-shortcuts'],
                   stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=3600)
out = json.loads(r.stdout)
report('2 install.cmd', exit_code=r.returncode, result=out['status'], release=out.get('release'), shortcuts=out.get('shortcuts'),
       launcher_script_written=(HOME / 'JARVIS.ps1').exists(), seconds=round(time.time() - started))

# 3 launch: the current release's own program, started with no arguments as a double-click would (1.0.17: no JARVIS.ps1).
current = json.loads((HOME / 'current.json').read_text(encoding='utf-8'))['release']
program = HOME / 'releases' / current / 'electron' / 'JARVIS.exe'
assert program.is_file(), f'no JARVIS.exe in the installed release: {program}'
started = time.time()
subprocess.Popen([str(program)], cwd=str(program.parent), creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
for _ in range(360):
    if (HOME / 'data' / 'core-connection.json').exists() and core_answers():
        break
    time.sleep(0.5)
time.sleep(3)
report('3 launch (JARVIS.exe)', program=str(program.relative_to(HOME)), processes=processes(), core_answers=core_answers(), seconds=round(time.time() - started, 1))

installer = [str(package / 'release' / 'python' / 'python.exe'), str(package / 'installer.py')]
out = json.loads(subprocess.run([*installer, 'verify', '--home', str(HOME)], capture_output=True, text=True, timeout=3600).stdout)
report('4 verify after use', result=out['status'], release=out.get('release'))

out = json.loads(subprocess.run([*installer, 'uninstall', '--home', str(HOME), '--no-shortcuts'], capture_output=True, text=True, timeout=3600).stdout)
leftover = sum(1 for p in (HOME / 'releases').rglob('*') if p.is_file()) if (HOME / 'releases').exists() else 0
time.sleep(2)
report('5 uninstall', result=out['status'], files_removed=out.get('program_files_removed'), kept=out.get('kept'), shortcuts=out.get('shortcuts'),
       jarvis_processes=processes()['count'], leftover_program_files=leftover)
