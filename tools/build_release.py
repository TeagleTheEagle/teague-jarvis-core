"""Build a JARVIS release from pinned inputs only (docs/RELEASE-DESIGN.md).

    .venv\\Scripts\\python.exe tools\\build_release.py --version 1.0.0

Requires a clean, committed working tree: application files come from the HEAD commit
(git archive), never from uncommitted edits, so a release is bound to one commit.
Every other input is checked against a pinned SHA-256 before use:
  - CPython 3.12.10 embeddable (python.org; MD5 matches the published value)
  - Python packages from requirements-lock.txt (pip --require-hashes, no index)
  - Electron 44.2.0 (the binary used by the twelve-fix Electron verification)
  - Whisper base.en and openWakeWord models
Microsoft C++ runtime DLLs are deployed app-locally (versions recorded) so a clean PC
needs no administrator-installed prerequisite. Nothing is executed from the inputs.

Output (build/release/, git-ignored):
  JARVIS-<version>-<commit>/            the release tree (installer + release files)
  JARVIS-<version>-<commit>.zip         the distributable
  JARVIS-<version>-<commit>.release.json  release manifest (Stage 7 §16)
"""
import argparse
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'

PYTHON_EMBED = {
    'file': 'python-3.12.10-embed-amd64.zip',
    'url': 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip',
    'sha256': '4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3',
    'md5_published_by_python_org': 'fe8ef205f2e9c3ba44d0cf9954e1abd3',
}
ELECTRON = {'version': '44.2.0', 'sha256': '07b043bf9b0a0ac14a82fac0b612b7b7ed13cde727d706d74e41a45278ab51f1'}
MODELS = {
    'speech-models/base.en/config.json': 'f3bc3821e9fc76a27bae538e11ae5b677dcdd352b4600429ce7951d398569aeb',
    'speech-models/base.en/model.bin': '2a166925539a16005f14ff328359f9b9adb9dc4fb631bb3b227526862e93e2ef',
    'speech-models/base.en/tokenizer.json': '929c5252409436dce1b38a75d1abbcb5e132d170d8e324e4e04ed915fa2d22df',
    'speech-models/base.en/vocabulary.txt': 'ff77588746d3a2595d32ab5b69ffd7b95ce2441ac57533cb66fc3eb575a115cf',
    'wake-models/embedding_model.onnx': '70d164290c1d095d1d4ee149bc5e00543250a7316b59f31d056cff7bd3075c1f',
    'wake-models/hey_jarvis_v0.1.onnx': '94a13cfe60075b132f6a472e7e462e8123ee70861bc3fb58434a73712ee0d2cb',
    'wake-models/melspectrogram.onnx': 'ba2b0e0f8b7b875369a2c89cb13360ff53bac436f2895cced9f479fa65eb176f',
}
CRT = ('msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'concrt140.dll')
# Development-only material that never ships.
EXCLUDED_DIRS = ('tests/', 'docs/', 'review/', 'deployment_test/', '.claude/', 'desktop/test/',
                 'intelligence/test/', 'ios/', 'stage4_native/', 'tools/')
EXCLUDED_NAMES = ('.gitignore', '.env.example')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout


def shipped(path):
    """Application files that ship: production source, assets and config defaults."""
    name = path.rsplit('/', 1)[-1]
    if any(path.startswith(d) for d in EXCLUDED_DIRS) or name in EXCLUDED_NAMES:
        return False
    if name.startswith('test_') or name.endswith('.test.cjs'):
        return False
    return True


def require(condition, message):
    if not condition:
        raise SystemExit('BUILD REFUSED: ' + message)


def build(version):
    require(not git('status', '--porcelain', '--untracked-files=no').strip(), 'commit or stash changes first; a release is built from HEAD only.')
    commit = git('rev-parse', 'HEAD').decode().strip()
    name = f'JARVIS-{version}-{commit[:12]}'
    out_root = BUILD / 'release'
    tree = out_root / name
    require(not tree.exists(), f'{tree} already exists.')
    release = tree / 'release'

    # 1. Application files from the HEAD commit.
    with tarfile.open(fileobj=io.BytesIO(git('archive', '--format=tar', 'HEAD'))) as archive:
        members = [m for m in archive.getmembers() if m.isfile() and shipped(m.name)]
        for m in members:
            target = release / 'app' / m.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(m).read())
    # The installer lives in tools/ (development-only) but ships beside the release.
    installer = git('show', 'HEAD:tools/installer.py')
    (tree / 'installer.py').write_bytes(installer)

    # 2. CPython 3.12.10 embeddable + locked packages + app-local C++ runtime.
    embed = BUILD / 'cache' / PYTHON_EMBED['file']
    require(embed.is_file(), f'download {PYTHON_EMBED["url"]} to {embed}')
    require(file_sha256(embed) == PYTHON_EMBED['sha256'], 'Python embeddable hash mismatch.')
    with zipfile.ZipFile(embed) as z:
        z.extractall(release / 'python')
    # Embeddable Python ignores PYTHONPATH and the script folder: list paths explicitly.
    (release / 'python' / 'python312._pth').write_text(
        'python312.zip\n.\nLib\\site-packages\n..\\app\nimport site\n', encoding='ascii')
    wheels = BUILD / 'wheels'
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--quiet',
                    '--require-hashes', '--no-index', '--find-links', str(wheels), '--only-binary=:all:',
                    '--platform', 'win_amd64', '--python-version', '3.12', '--implementation', 'cp',
                    '--no-compile', '--target', str(release / 'python' / 'Lib' / 'site-packages'),
                    '-r', str(ROOT / 'requirements-lock.txt')], check=True)
    for dll in CRT:
        source = Path(r'C:\Windows\System32') / dll
        require(source.is_file(), f'{dll} not found; install the Microsoft Visual C++ x64 runtime on the build PC.')
        shutil.copyfile(source, release / 'python' / dll)

    # Precompile with unchecked-hash bytecode (PEP 552): Python never rewrites these files,
    # and the launcher runs Python with -B, so the installed release stays byte-identical to
    # its manifest (verification and rollback stay possible after use).
    import compileall, py_compile
    for folder in (release / 'app', release / 'python' / 'Lib' / 'site-packages'):
        compileall.compile_dir(str(folder), quiet=2, workers=0,
                               invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)

    # 3. Electron, verified.
    electron = ROOT / 'desktop' / 'node_modules' / 'electron' / 'dist'
    require(file_sha256(electron / 'electron.exe') == ELECTRON['sha256'], 'Electron identity mismatch.')
    shutil.copytree(electron, release / 'electron')

    # 4. Models, verified.
    for relative, digest in MODELS.items():
        source = ROOT / 'data' / relative
        require(source.is_file() and file_sha256(source) == digest, f'model {relative} missing or changed.')
        target = release / 'models' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    # 5. Release manifest: every file, its hash and size.
    files = [{'path': p.relative_to(release).as_posix(), 'sha256': file_sha256(p), 'bytes': p.stat().st_size}
             for p in sorted(release.rglob('*')) if p.is_file()]
    manifest = {
        'product': 'JARVIS', 'format': 1, 'version': version, 'commit': commit,
        'release_id': f'{version}-{commit[:12]}', 'built_at': time.time(),
        'python': {'version': '3.12.10', 'embeddable_sha256': PYTHON_EMBED['sha256'],
                   'packages_lock_sha256': file_sha256(ROOT / 'requirements-lock.txt')},
        'electron': ELECTRON, 'models': MODELS,
        'crt': {dll: file_sha256(release / 'python' / dll) for dll in CRT},
        'application_files': len(members), 'files': files,
    }
    (release / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    (tree / 'install.cmd').write_text(
        '@echo off\r\n'
        'rem JARVIS installer: per-user, no administrator rights. See installer.py --help.\r\n'
        '"%~dp0release\\python\\python.exe" "%~dp0installer.py" install --package "%~dp0." %*\r\n'
        'if errorlevel 1 pause\r\n', encoding='ascii')

    # 6. Distributable zip and release record.
    archive_path = out_root / (name + '.zip')
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(tree.rglob('*')):
            if p.is_file():
                z.write(p, Path(name) / p.relative_to(tree))
    record = {'release_id': manifest['release_id'], 'version': version, 'commit': commit,
              'zip': archive_path.name, 'zip_sha256': file_sha256(archive_path), 'zip_bytes': archive_path.stat().st_size,
              'manifest_sha256': file_sha256(release / 'manifest.json'), 'files': len(files),
              'release_bytes': sum(f['bytes'] for f in files),
              'canonical_data_path': '%LOCALAPPDATA%\\JARVIS\\data', 'config_path': '%LOCALAPPDATA%\\JARVIS\\config',
              'backup_format': 'recovery.py format 1 (zip + manifest.json)',
              'deferred': ['Qwen/OpenAI provider selection is owner configuration (config\\.env)',
                           'physical glasses integration not included']}
    (out_root / (name + '.release.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', required=True)
    print(json.dumps(build(parser.parse_args().version), indent=2))
