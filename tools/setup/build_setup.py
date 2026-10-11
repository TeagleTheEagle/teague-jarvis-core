"""JARVIS-Setup-<release id>.exe: one file that installs, updates or reinstalls a release (docs/OWN-APP-PLAN.md 3.4).

    .venv\\Scripts\\python.exe tools\\setup\\build_setup.py --package D:\\JARVIS-release-work\\release\\JARVIS-1.0.17-<commit>

The package is the folder tools/build_release.py made (release\\, installer.py, install.cmd), verified against its
manifest first. The Setup is made by Inno Setup 6 (ISCC.exe), which the owner installs once on this PC (a
system-wide install; this script never installs anything). It unpacks the package into %LOCALAPPDATA%\\JARVIS-package
and runs the package's own installer.py, so install, update, reinstall and the rollback copy behave exactly as the
Stage 7 check has proven them; it registers "JARVIS" in Settings > Apps > Installed apps, whose Uninstall runs the
package's installer with `uninstall` (data kept) and then removes the package folder.

Output, beside the package:
  JARVIS-Setup-<id>.exe          the distributable (per user, no administrator rights; unsigned, decision D3)
  JARVIS-Setup-<id>.iss          the generated Inno Setup script (from JARVIS-Setup.iss.in beside this file)
  JARVIS-Setup-<id>.setup.json   the record: hash and size of the Setup, the package's hashes, the Inno version

Switches of the built Setup: /VERYSILENT /SUPPRESSMSGBOXES /NORESTART (silent, for the Stage 7 check and rehearsals),
/HOME=<folder> (a sandbox install home instead of %LOCALAPPDATA%\\JARVIS, as installer.py --home; needs /DIR as well,
and the run registers as "JARVIS (sandbox)" under its own application id, so a rehearsal on the build PC never touches
the entry of the real JARVIS there), /DIR=<folder> (a sandbox package folder), /NOSHORTCUTS (rehearsals on the build
PC: its real Desktop and Startup are never touched; the installer itself also withholds them from any home that is not
the PC's own install home), /LOG=<file>. The installer's own JSON answer is written to <package folder>\\setup-result.json;
the uninstall's to <package folder>-uninstall-result.json beside it. A silent Setup exits 0 even when the package's
installer refused (Inno Setup has finished its own work by then): setup-result.json is the verdict; on a refusal the
Setup removes the Installed-apps entry it wrote and its finished page says that nothing was installed. The two
application ids are read from the template into the record (app_id, sandbox_app_id).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from installer import verify_release  # noqa: E402
from build_release import version_quad  # noqa: E402  (the same four-number form, and the same refusal, as the build)

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = Path(__file__).resolve().parent / 'JARVIS-Setup.iss.in'
ICON = ROOT / 'desktop' / 'jarvis.ico'
ISCC_CANDIDATES = (Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Inno Setup 6' / 'ISCC.exe',
                   Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'Inno Setup 6' / 'ISCC.exe',
                   Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Inno Setup 6' / 'ISCC.exe')


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def refuse(message):
    raise SystemExit('SETUP BUILD REFUSED: ' + message)


def find_iscc(given=None):
    """Inno Setup's command-line compiler. The owner installs Inno Setup 6 once; nothing is installed here."""
    candidates = [Path(given)] if given else list(ISCC_CANDIDATES)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    refuse('Inno Setup 6 was not found (ISCC.exe). The owner installs it once from jrsoftware.org (a system-wide '
           'install, the owner\'s act); or pass --iscc <path to ISCC.exe>.')


def render(template, values):
    text = template
    for name, value in values.items():
        text = text.replace('@' + name + '@', str(value))
    left = [token for line in text.splitlines() if not line.lstrip().startswith(';')   # comments may mention the form
            for token in re.findall(r'@[A-Z_]+@', line)]
    if left:
        refuse('placeholders left in the Setup script: ' + ', '.join(sorted(set(left))))
    return text


def app_ids(template_text):
    """The two application ids the template defines (the real JARVIS, and a sandbox run with /HOME), in the form
    Windows records them (braces around the GUID): the Stage 7 check and the rehearsals read them from the record."""
    found = dict(re.findall(r'^#define (MyAppGuid|SandboxAppGuid) "([0-9A-Fa-f-]{36})"', template_text, re.M))
    if set(found) != {'MyAppGuid', 'SandboxAppGuid'}:
        refuse('the template does not define MyAppGuid and SandboxAppGuid.')
    return '{' + found['MyAppGuid'].upper() + '}', '{' + found['SandboxAppGuid'].upper() + '}'


def build(package, iscc=None, out_dir=None):
    package = Path(package).resolve()
    if not (package / 'release').is_dir() or not (package / 'installer.py').is_file():
        refuse(f'{package} is not a built package (release\\ and installer.py expected).')
    record_file = package.parent / (package.name + '.release.json')
    if not record_file.is_file():
        refuse(f'{record_file.name} not found beside the package.')
    record = json.loads(record_file.read_text(encoding='utf-8'))
    manifest = verify_release(package / 'release')   # a damaged package never becomes a Setup
    release_id, version = manifest['release_id'], manifest['version']
    if record['release_id'] != release_id:
        refuse('the release record and the manifest name different releases.')
    if not ICON.is_file():
        refuse(f'{ICON} missing.')
    compiler = find_iscc(iscc)
    out_dir = Path(out_dir).resolve() if out_dir else package.parent
    name = f'JARVIS-Setup-{release_id}'
    setup = out_dir / (name + '.exe')
    if setup.exists():
        refuse(f'{setup} already exists.')
    script = out_dir / (name + '.iss')
    template_text = TEMPLATE.read_text(encoding='utf-8')
    app_id, sandbox_app_id = app_ids(template_text)
    script.write_text(render(template_text, {
        'VERSION': version, 'RELEASE_ID': release_id, 'PACKAGE': package, 'ICON': ICON,
        'OUTPUT_DIR': out_dir, 'OUTPUT_NAME': name, 'VERSION_QUAD': version_quad(version),
    }), encoding='utf-8')
    started = time.time()
    done = subprocess.run([str(compiler), '/Qp', str(script)], capture_output=True, text=True, errors='replace')
    if done.returncode != 0 or not setup.is_file():
        refuse('ISCC failed:\n' + (done.stdout + done.stderr)[-3000:])
    summary = {'setup': setup.name, 'setup_sha256': file_sha256(setup), 'setup_bytes': setup.stat().st_size,
               'release_id': release_id, 'version': version, 'commit': record['commit'],
               'package': str(package), 'package_zip': record.get('zip'), 'package_zip_sha256': record.get('zip_sha256'),
               'manifest_sha256': file_sha256(package / 'release' / 'manifest.json'),
               'script': script.name, 'script_sha256': file_sha256(script), 'template_sha256': file_sha256(TEMPLATE),
               'iscc': str(compiler), 'iscc_sha256': file_sha256(compiler), 'seconds': round(time.time() - started, 1),
               'built_at': time.time(), 'signed': False,
               'app_id': app_id, 'sandbox_app_id': sandbox_app_id, 'sandbox_display_name': 'JARVIS (sandbox)',
               'switches': ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
                            '/HOME=<sandbox home> together with /DIR=<sandbox package folder> (registers as "JARVIS (sandbox)" under sandbox_app_id)',
                            '/NOSHORTCUTS', '/LOG=<file>'],
               'silent_exit_code_note': 'a silent Setup exits 0 even when the package installer refused; setup-result.json is the verdict'}
    (out_dir / (name + '.setup.json')).write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--package', required=True, help='the built package folder (contains release\\ and installer.py)')
    parser.add_argument('--iscc', help='path to ISCC.exe when Inno Setup is not in Program Files')
    parser.add_argument('--out', help='output folder (default: beside the package)')
    args = parser.parse_args()
    print(json.dumps(build(args.package, args.iscc, args.out), indent=2))
