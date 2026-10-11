"""Make a synthetic JARVIS backup for the Gate 18 guest-script rehearsal (made-up data only).

Installs the build from an extracted package into a new sandbox home, writes a made-up personality and two
made-up memories, asks the running Core for a verified backup (Settings > Backup & recovery does the same),
rehearses it, stops JARVIS, and lays out a "disc" folder: the backup zip plus BACKUP-RECORD.json, as the real
recovery disc carries them. Touches nothing outside the work folder given on the command line.

  python make_synthetic_backup.py <extracted package folder> <new work folder>
"""
import hashlib, json, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

PACKAGE, WORK = Path(sys.argv[1]), Path(sys.argv[2])
A, DISC = WORK / 'home-a', WORK / 'disc'
MEMORIES = ['Gate 18 rehearsal memory one: the test colour is teal', 'Gate 18 rehearsal memory two: the test number is 42']


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def api(route, body=None, timeout=600):
    link = json.loads((A / 'data' / 'core-connection.json').read_text(encoding='utf-8'))
    h = {'X-Jarvis-Desktop': link['token']}
    page = urllib.request.urlopen(urllib.request.Request(link['origin'] + '/', headers=h), timeout=10)
    h['Cookie'] = (page.headers.get('Set-Cookie') or '').split(';')[0]
    req = urllib.request.Request(link['origin'] + route, headers={**h, 'Content-Type': 'application/json'},
                                 data=None if body is None else json.dumps(body).encode(), method='GET' if body is None else 'POST')
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


assert not WORK.exists(), 'the work folder must be new'
WORK.mkdir(parents=True)
python = PACKAGE / 'release' / 'python' / 'python.exe'
out = json.loads(subprocess.run([str(python), str(PACKAGE / 'installer.py'), 'install', '--package', str(PACKAGE), '--home', str(A), '--no-shortcuts'],
                                capture_output=True, text=True, timeout=3600).stdout)
(A / 'config' / 'personality.txt').write_text('Gate 18 rehearsal personality: answer briefly.\n', encoding='utf-8')
subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(A / 'JARVIS.ps1')], check=True)
for _ in range(480):
    if (A / 'data' / 'core-connection.json').exists():
        break
    time.sleep(0.5)
time.sleep(3)
for m in MEMORIES:
    api('/api/item', {'kind': 'memory', 'body': m})
backup = api('/api/recovery', {'action': 'create'})
rehearsal = api('/api/recovery', {'action': 'rehearse', 'id': backup['id']})
archive = A / 'data-backups' / (backup['id'] + '.zip')
try:
    api('/api/shutdown', {})
except Exception:
    pass
for _ in range(120):
    if not (A / 'data' / 'core-connection.json').exists():
        break
    time.sleep(0.5)
time.sleep(5)
subprocess.run(['powershell', '-NoProfile', '-Command', "Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '" + str(A / 'releases')
                + "\\*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"], capture_output=True)
DISC.mkdir()
shutil.copyfile(archive, DISC / archive.name)
record = {'schema': 'stage6-gate18-backup-on-disc-v1', 'file': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha256(archive), 'synthetic': True}
(DISC / 'BACKUP-RECORD.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({'install': out.get('status'), 'release': out.get('release'), 'backup': backup.get('status'), 'rehearsal': rehearsal.get('status'),
                  'database_counts': backup.get('database_counts'), 'disc': str(DISC), **record}, indent=2))
