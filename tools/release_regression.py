"""Release regression (docs/RELEASE-DESIGN.md, Stage 7 "release regression").

Runs the JARVIS test suites against a built release using the release's own bundled Python
and Electron, never the development .venv or a system node. The release folder is not
changed: it is verified against its manifest, copied to a scratch folder, the copy is
verified again, and only then are the tests from the release's own commit added to the copy.
Owner folders are pointed at the scratch folder, so no real data or config is read.

    python tools/release_regression.py --package <JARVIS-x.y.z-commit> --work <scratch folder>
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from installer import verify_release  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
TEST_PATH = re.compile(r'^(test_[^/]+\.(py|cjs)|(desktop|intelligence)/test/.+)$')


def release_commit(package):
    record = package.parent / (package.name + '.release.json')
    return json.loads(record.read_text(encoding='utf-8'))['commit']


def overlay_tests(commit, app):
    names = subprocess.run(['git', 'ls-tree', '-r', '--name-only', commit], cwd=REPO, check=True,
                           capture_output=True, text=True).stdout.splitlines()
    added = []
    for name in names:
        if not TEST_PATH.match(name):
            continue
        target = app / name
        if target.exists():
            raise SystemExit(f'Refusing to overwrite a shipped file with a test file: {name}')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.run(['git', 'show', f'{commit}:{name}'], cwd=REPO, check=True,
                                          capture_output=True).stdout)
        added.append(name)
    return added


def run(label, command, cwd, env, logs, timeout=3600):
    started = time.time()
    proc = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=timeout)
    output = proc.stdout + proc.stderr
    log = logs / (re.sub(r'[^A-Za-z0-9_.-]+', '_', label) + '.log')
    log.write_text(output, encoding='utf-8')
    return {'suite': label, 'exit_code': proc.returncode, 'seconds': round(time.time() - started, 1),
            'log': log.name, 'tail': output.strip().splitlines()[-25:]}


def main(argv=None):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--package', required=True, help='built release folder (contains release\\)')
    parser.add_argument('--work', required=True, help='empty scratch folder for the copy and the report')
    args = parser.parse_args(argv)
    package, work = Path(args.package), Path(args.work)
    if work.exists() and any(work.iterdir()):
        raise SystemExit(f'{work} is not empty')
    manifest = verify_release(package / 'release')
    commit = release_commit(package)

    copy = work / 'release'
    shutil.copytree(package / 'release', copy)
    verify_release(copy, manifest)  # the copy under test is byte-identical to the release
    app = copy / 'app'
    added = overlay_tests(commit, app)
    (app / 'tools').mkdir(exist_ok=True)  # test_installer.py tests the installer shipped with the release
    shutil.copyfile(package / 'installer.py', app / 'tools' / 'installer.py')
    # test_own_app.py tests the build's helpers; the build script never ships, so it comes from the release's commit
    # like the tests themselves (1.0.17).
    (app / 'tools' / 'build_release.py').write_bytes(subprocess.run(['git', 'show', f'{commit}:tools/build_release.py'], cwd=REPO, check=True,
                                                                   capture_output=True).stdout)
    # Two Python tests evaluate JavaScript with `node`: give them the release's own Electron as node.
    shim = work / 'node-shim'
    shutil.copytree(copy / 'electron', shim)
    shutil.copyfile(shim / 'JARVIS.exe', shim / 'node.exe')   # the release's Electron is JARVIS.exe (1.0.17)

    # A brand-new Windows account, laid out as Windows lays it out (one shared folder for
    # profile, AppData and Temp is not realistic and makes browsers refuse to start).
    home = work / 'home'
    local, roaming, temp = home / 'AppData' / 'Local', home / 'AppData' / 'Roaming', home / 'AppData' / 'Local' / 'Temp'
    for folder in (work / 'data', work / 'config', roaming, temp):
        folder.mkdir(parents=True, exist_ok=True)
    python, electron = copy / 'python' / 'python.exe', copy / 'electron' / 'JARVIS.exe'
    keep = ('SYSTEMROOT', 'SYSTEMDRIVE', 'WINDIR', 'COMSPEC', 'PATHEXT', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE',
            'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PROGRAMW6432', 'PROGRAMDATA', 'ALLUSERSPROFILE',
            'COMMONPROGRAMFILES', 'COMMONPROGRAMFILES(X86)', 'COMMONPROGRAMW6432')  # Windows itself (Edge lives here)
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    env.update({'PATH': os.pathsep.join([str(python.parent), str(Path(os.environ['SYSTEMROOT']) / 'System32'),
                                         str(Path(os.environ['SYSTEMROOT']) / 'System32' / 'WindowsPowerShell' / 'v1.0')]),
                'TEMP': str(temp), 'TMP': str(temp), 'USERPROFILE': str(home),
                'LOCALAPPDATA': str(local), 'APPDATA': str(roaming),
                'JARVIS_DATA_DIR': str(work / 'data'), 'JARVIS_CONFIG_DIR': str(work / 'config'),
                'JARVIS_MODELS_DIR': str(copy / 'models'), 'JARVIS_PYTHON': str(python),
                'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'})
    node = {**env, 'ELECTRON_RUN_AS_NODE': '1'}
    python_env = {**node, 'PATH': str(shim) + os.pathsep + env['PATH']}
    logs = work / 'logs'
    logs.mkdir()

    results = [run('python unittest', [str(python), '-m', 'unittest', 'discover', '-s', '.', '-p', 'test_*.py'], app, python_env, logs)]
    for folder in ('desktop', 'intelligence'):
        tests = sorted(str(p.relative_to(app / folder)) for p in (app / folder / 'test').glob('*.test.cjs'))
        results.append(run(f'{folder} node --test', [str(electron), '--test', *tests], app / folder, node, logs))
    for script in sorted(p.name for p in app.glob('test_*.cjs')):
        results.append(run(script, [str(electron), script], app, node, logs, timeout=900))

    report = {'release_id': manifest['release_id'], 'commit': commit, 'package': str(package),
              'release_verified_before_and_after_copy': True, 'test_files_added_to_copy': len(added),
              'runtime': {'python': str(python.relative_to(work)), 'node': 'bundled electron (ELECTRON_RUN_AS_NODE)',
                          'system_node_used': False, 'dev_venv_used': False},
              'passed': all(r['exit_code'] == 0 for r in results), 'suites': results}
    verify_release(package / 'release', manifest)  # the release itself is unchanged by the run
    (work / 'regression-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'suites'}, indent=2))
    for r in results:
        print(f"{'PASS' if r['exit_code'] == 0 else 'FAIL'}  {r['suite']:<34} {r['seconds']:>7}s  {r['tail'][-1] if r['tail'] else ''}")
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
