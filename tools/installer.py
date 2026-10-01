"""JARVIS per-user installer (docs/RELEASE-DESIGN.md). No administrator rights.

Shipped beside the release and run with the release's own bundled Python:
    install.cmd                                   install or update to this release
    python installer.py rollback                  switch back to the previous release
    python installer.py uninstall                 remove the program; data and keys are kept
    python installer.py uninstall --remove-data CONFIRM-DELETE-MY-JARVIS-DATA
    python installer.py verify | status

Layout under --home (default %LOCALAPPDATA%\\JARVIS):
    current.json  JARVIS.ps1  releases\\<id>\\  data\\  config\\  profile\\
Program files are verified file-by-file against the release manifest before use, staged
beside the live release and switched in one atomic step, so an interrupted install or
update leaves the previous release current. Data, config and profile folders are never
modified by install, update, rollback or uninstall (unless data removal is confirmed).
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CONFIRM_DATA_REMOVAL = 'CONFIRM-DELETE-MY-JARVIS-DATA'
SHORTCUT = 'JARVIS.lnk'
LEGACY_SHORTCUT = 'JARVIS Desktop.lnk'  # created by the pre-release Install-JARVIS-Shortcuts.ps1

LAUNCHER = r'''param([switch]$LoginLaunch)
# JARVIS launcher (written by installer.py). Starts the current release's desktop app,
# which joins the shared background Core or starts it.
$ErrorActionPreference = 'Stop'
$jarvisHome = $PSScriptRoot
$current = Get-Content -LiteralPath (Join-Path $jarvisHome 'current.json') -Raw | ConvertFrom-Json
$release = Join-Path (Join-Path $jarvisHome 'releases') $current.release
$env:JARVIS_DATA_DIR = Join-Path $jarvisHome 'data'
$env:JARVIS_CONFIG_DIR = Join-Path $jarvisHome 'config'
$env:JARVIS_MODELS_DIR = Join-Path $release 'models'
$env:JARVIS_PYTHON = Join-Path $release 'python\python.exe'
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
$arguments = @('"' + (Join-Path $release 'app\desktop') + '"', ('"--user-data-dir=' + (Join-Path $jarvisHome 'profile') + '"'))
if ($LoginLaunch) { $arguments += '--login-launch' }
Start-Process -FilePath (Join-Path $release 'electron\electron.exe') -ArgumentList $arguments -WorkingDirectory (Join-Path $release 'app\desktop')
'''


class InstallError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise InstallError(message)


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def ps_quote(text):
    """A PowerShell single-quoted literal."""
    return "'" + str(text).replace("'", "''") + "'"


def default_home():
    return Path(os.environ['LOCALAPPDATA']) / 'JARVIS'


def read_manifest(release):
    manifest = json.loads((Path(release) / 'manifest.json').read_text(encoding='utf-8'))
    require(manifest.get('product') == 'JARVIS' and manifest.get('format') == 1, 'Not a JARVIS release manifest.')
    for entry in manifest['files']:
        parts = Path(entry['path']).parts
        require(entry['path'] != 'manifest.json' and not Path(entry['path']).is_absolute()
                and '..' not in parts and ':' not in entry['path'], 'Unsafe path in release manifest.')
    return manifest


def verify_release(release, manifest=None):
    """Every manifest file present with the exact hash and size; nothing else."""
    release = Path(release)
    manifest = manifest or read_manifest(release)
    expected = {e['path']: e for e in manifest['files']}
    for path, entry in expected.items():
        file = release / path
        require(file.is_file() and file.stat().st_size == entry['bytes'] and file_sha256(file) == entry['sha256'],
                f'Release file missing or changed: {path}')
    extra = [p.relative_to(release).as_posix() for p in release.rglob('*')
             if p.is_file() and p.name != 'manifest.json' and p.relative_to(release).as_posix() not in expected]
    require(not extra, f'Unexpected files in release: {extra[:3]}')
    return manifest


def read_current(home):
    try:
        return json.loads((Path(home) / 'current.json').read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None


def atomic_write(path, text):
    """Write via a flushed side file and one rename, so a crash or power cut leaves the old or the new file."""
    path = Path(path)
    pending = path.with_name(path.name + '.pending')
    with pending.open('w', encoding='utf-8', newline='') as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(pending, path)


def write_current(home, release_id, previous):
    atomic_write(Path(home) / 'current.json',
                 json.dumps({'release': release_id, 'previous': previous, 'switched_at': time.time()}))


def stop_running_jarvis(home, timeout=30):
    """Ask the shared Core to shut down, then end any leftover JARVIS processes from this home."""
    home = Path(home)
    try:
        link = json.loads((home / 'data' / 'core-connection.json').read_text(encoding='utf-8'))
        headers = {'X-Jarvis-Desktop': link['token']}
        with urllib.request.urlopen(urllib.request.Request(link['origin'] + '/', headers=headers), timeout=5) as page:
            cookie = (page.headers.get('Set-Cookie') or '').split(';')[0]
        request = urllib.request.Request(link['origin'] + '/api/shutdown', data=b'{}', method='POST',
                                         headers={**headers, 'Cookie': cookie, 'Content-Type': 'application/json'})
        urllib.request.urlopen(request, timeout=10).close()
    except (OSError, ValueError, KeyError):
        pass  # no running Core, or it is already stopping
    deadline = time.time() + timeout
    while time.time() < deadline and (home / 'data' / 'core-connection.json').exists():
        time.sleep(0.5)
    if os.name == 'nt' and (home / 'releases').is_dir():
        # Only processes whose executable lives inside this JARVIS home's releases.
        script = ("$root=[IO.Path]::GetFullPath(" + ps_quote(str(home / 'releases') + os.sep) + ");"
                  "Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and "
                  "$_.ExecutablePath.StartsWith($root, [StringComparison]::OrdinalIgnoreCase) } | "
                  "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
        subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, timeout=60)


def write_shortcuts(home):
    script = ("$s=New-Object -ComObject WScript.Shell;"
              "foreach($pair in @(@([Environment]::GetFolderPath('Desktop'),''),@([Environment]::GetFolderPath('Startup'),' -LoginLaunch'))){"
              "$l=$s.CreateShortcut((Join-Path $pair[0] '" + SHORTCUT + "'));"
              "$l.TargetPath=(Get-Command powershell.exe).Source;"
              "$l.Arguments='-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File \"'+" + ps_quote(Path(home) / 'JARVIS.ps1') + "+'\"'+$pair[1];"
              "$l.WindowStyle=7;$l.WorkingDirectory=" + ps_quote(home) + ";$l.Description='JARVIS';$l.Save()}")
    subprocess.run(['powershell', '-NoProfile', '-Command', script], check=True, capture_output=True, timeout=60)


def remove_shortcuts(name=SHORTCUT):
    script = ("foreach($d in @([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('Startup'))){"
              "Remove-Item -LiteralPath (Join-Path $d " + ps_quote(name) + ") -ErrorAction SilentlyContinue}")
    subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, timeout=60)


def install(package, home, shortcuts=True, stop=stop_running_jarvis, replace_legacy_shortcuts=False):
    package, home = Path(package), Path(home)
    source = package / 'release'
    manifest = verify_release(source)  # refuse a damaged or tampered package before touching anything
    release_id = manifest['release_id']
    releases = home / 'releases'
    for folder in (releases, home / 'data', home / 'config', home / 'profile'):
        folder.mkdir(parents=True, exist_ok=True)
    for leftover in [*releases.glob('.incoming-*'), *releases.glob('.damaged-*')]:  # an earlier interrupted install
        shutil.rmtree(leftover, ignore_errors=True)
    target = releases / release_id
    current = read_current(home)
    if target.exists():
        try:
            verify_release(target, manifest)
        except InstallError:  # damaged: replace it from the package instead of refusing forever
            if current and current['release'] == release_id:
                stop(home)  # repairing the running release: its files must be free to move
            damaged = releases / f'.damaged-{release_id}-{int(time.time())}'
            os.replace(target, damaged)
            shutil.rmtree(damaged, ignore_errors=True)
    if not target.exists():
        incoming = releases / ('.incoming-' + release_id)
        shutil.copytree(source, incoming)
        verify_release(incoming, manifest)
        os.replace(incoming, target)
    personality = home / 'config' / 'personality.txt'
    if not personality.exists():
        shutil.copyfile(target / 'app' / 'personality.txt', personality)
    previous = current['release'] if current and current['release'] != release_id else (current or {}).get('previous')
    if current and current['release'] != release_id:
        stop(home)
    atomic_write(home / 'JARVIS.ps1', LAUNCHER)
    write_current(home, release_id, previous)
    if shortcuts:
        write_shortcuts(home)
        if replace_legacy_shortcuts:  # owner switch-over: the old JARVIS no longer starts at login
            remove_shortcuts(LEGACY_SHORTCUT)
    return {'status': 'installed', 'release': release_id, 'previous': previous, 'home': str(home)}


def rollback(home, stop=stop_running_jarvis):
    home = Path(home)
    current = read_current(home)
    require(current and current.get('previous'), 'No previous release to roll back to.')
    target = home / 'releases' / current['previous']
    verify_release(target)
    stop(home)
    write_current(home, current['previous'], current['release'])
    return {'status': 'rolled_back', 'release': current['previous'], 'previous': current['release']}


def uninstall(home, remove_data=None, shortcuts=True, stop=stop_running_jarvis):
    home = Path(home)
    require(remove_data in (None, CONFIRM_DATA_REMOVAL), f'To delete data too, pass --remove-data {CONFIRM_DATA_REMOVAL}')
    stop(home)
    if shortcuts:
        remove_shortcuts()
    removed = 0
    releases = home / 'releases'
    if releases.is_dir():
        for release in releases.iterdir():
            if release.name.startswith(('.incoming-', '.damaged-')):
                shutil.rmtree(release, ignore_errors=True)
                continue
            try:
                manifest = read_manifest(release)
            except (OSError, ValueError, InstallError):
                continue  # not ours: leave it
            for entry in manifest['files']:  # only files this installer placed
                (release / entry['path']).unlink(missing_ok=True)
                removed += 1
            (release / 'manifest.json').unlink(missing_ok=True)
            for folder in sorted((p for p in release.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                try:
                    folder.rmdir()
                except OSError:
                    pass
            try:
                release.rmdir()
            except OSError:
                pass
        try:
            releases.rmdir()
        except OSError:
            pass
    for name in ('current.json', 'JARVIS.ps1'):
        (home / name).unlink(missing_ok=True)
    kept = [name for name in ('data', 'config', 'profile') if (home / name).exists()]
    if remove_data == CONFIRM_DATA_REMOVAL:
        for name in kept:
            shutil.rmtree(home / name)
        kept = []
    return {'status': 'uninstalled', 'program_files_removed': removed, 'kept': kept}


def status(home):
    home = Path(home)
    current = read_current(home)
    releases = sorted(p.name for p in (home / 'releases').iterdir() if p.is_dir()) if (home / 'releases').is_dir() else []
    return {'home': str(home), 'current': current, 'releases': releases}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['install', 'rollback', 'uninstall', 'verify', 'status'])
    parser.add_argument('--package', help='Release folder containing release\\ (install)')
    parser.add_argument('--home', help='Install location (default %%LOCALAPPDATA%%\\JARVIS)')
    parser.add_argument('--no-shortcuts', action='store_true')
    parser.add_argument('--replace-legacy-shortcuts', action='store_true',
                        help='Switch-over only: also remove the old "JARVIS Desktop" shortcuts')
    parser.add_argument('--remove-data')
    args = parser.parse_args(argv)
    home = Path(args.home) if args.home else default_home()
    try:
        if args.action == 'install':
            result = install(args.package or Path(__file__).resolve().parent, home, shortcuts=not args.no_shortcuts,
                             replace_legacy_shortcuts=args.replace_legacy_shortcuts)
        elif args.action == 'rollback':
            result = rollback(home)
        elif args.action == 'uninstall':
            result = uninstall(home, args.remove_data, shortcuts=not args.no_shortcuts)
        elif args.action == 'verify':
            current = read_current(home)
            require(current, 'JARVIS is not installed here.')
            verify_release(home / 'releases' / current['release'])
            result = {'status': 'verified', 'release': current['release']}
        else:
            result = status(home)
    except InstallError as exc:
        print(json.dumps({'status': 'refused', 'reason': str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
