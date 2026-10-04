"""Compare two release manifests: which shipped files changed between builds.

Outside app/, every file must be byte-identical except what records the build folder's path: compiled bytecode
(.pyc) and pip's console-script launchers (site-packages/bin/*.exe) with the RECORD files that list their hashes
(the same 29 files differ between 1.0.10 and 1.0.11). The bundled Python, its locked packages, Electron and the
models are pinned inputs. Inside app/, the changed
source files are listed so they can be checked against the commits between the two builds.
    python compare_manifests.py <old release folder> <new release folder> [--out report.json]
"""
import argparse
import json
import re
from pathlib import Path

BUILD_PATH_FILES = re.compile(r'(\.pyc|^python/Lib/site-packages/bin/[^/]+\.exe|^python/Lib/site-packages/[^/]+\.dist-info/RECORD)$')


def entries(release):
    manifest = json.loads((Path(release) / 'manifest.json').read_text(encoding='utf-8'))
    return manifest, {e['path']: e for e in manifest['files']}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('old')
    parser.add_argument('new')
    parser.add_argument('--out')
    args = parser.parse_args()
    old_manifest, old = entries(args.old)
    new_manifest, new = entries(args.new)
    changed = sorted(p for p in old.keys() & new.keys() if old[p]['sha256'] != new[p]['sha256'])
    added, removed = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())

    def source(paths):
        return [p for p in paths if p.startswith('app/') and not p.endswith('.pyc')]

    pinned_changes = [p for p in changed + added + removed if not p.startswith('app/') and not BUILD_PATH_FILES.search(p)]
    build_path_changes = [p for p in changed if not p.startswith('app/') and not p.endswith('.pyc') and BUILD_PATH_FILES.search(p)]
    report = {
        'old': old_manifest['release_id'], 'new': new_manifest['release_id'],
        'files_old': len(old), 'files_new': len(new),
        'changed': len(changed), 'added': len(added), 'removed': len(removed),
        'app_source_changed': source(changed), 'app_source_added': source(added), 'app_source_removed': source(removed),
        'bytecode_changed': sum(p.endswith('.pyc') for p in changed),
        'launchers_and_records_changed': len(build_path_changes),
        'pinned_inputs_changed': pinned_changes,
        'pinned_inputs_identical': not pinned_changes,
    }
    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    print(text)
    return 0 if report['pinned_inputs_identical'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
