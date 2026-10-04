"""Bring saved JARVIS data from a verified backup into this installation (the switch-over).

Owner-run steps (see docs/SWITCH-OVER-PLAN.md):
  1. Quit the old JARVIS completely (tray menu).
  2. In the OLD installation:  python recovery.py create   then   python recovery.py rehearse --id <ID>
  3. Here (dry run, changes nothing):  .venv\\Scripts\\python.exe switch_over.py --archive <backup.zip>
  4. Here, to import:                   .venv\\Scripts\\python.exe switch_over.py --archive <backup.zip> --apply

Only the archive's data/ part (memory database, generated documents and other saved data)
is imported; this installation's code is kept. Entries that would be replaced are moved to
data/pre-switchover-<time>/, never deleted. Speech/wake models, logs, Core files and the
Electron profile here are never touched. Refuses while this installation's Core is running,
and holds the Core lock for the whole import so JARVIS cannot start mid-copy. Any failure
restores the previous state. The archive itself is never executed.
"""
from contextlib import closing
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import time
import zipfile

import core_lock
import recovery
import runtime_paths

ROOT = Path(__file__).resolve().parent
DATA_FOLDER_REFUSED = ('The JARVIS data folder does not allow creating folders, so nothing was imported. '
                       'Check that the drive is not write-protected, then try again.')
# Present only in this installation; an import never replaces them.
PROTECTED = {core_lock.LOCK_NAME, core_lock.OWNER_NAME, core_lock.CONNECTION_NAME, 'speech-models',
             'wake-models', 'logs', 'dev-electron-profile'}
DATABASE_SIDE_FILES = ('jarvis.sqlite3-wal', 'jarvis.sqlite3-shm')
PERSONAL_CONFIG = {'app/personality.txt': 'personality.txt', 'app/desktop/preferences.json': 'desktop/preferences.json'}


def personal_config_targets(root):
    """Where the owner's personality and desktop preferences live: the config folder in an
    installed release (never inside the verified program files), beside the code in development."""
    config = runtime_paths.config_dir_for(root)
    if config != Path(root).resolve():
        return {'app/personality.txt': config / 'personality.txt', 'app/desktop/preferences.json': config / 'preferences.json'}
    return {name: Path(root) / target for name, target in PERSONAL_CONFIG.items()}


def plan(archive, data_dir, root=ROOT):
    data_dir = Path(data_dir)
    # Checksums, safe paths, database integrity and counts. A backup on read-only media (a disc)
    # is checked in this installation's own backup folder, which is then created if needed.
    manifest = recovery.verify(archive, fallback=recovery.default_folder(root, data_dir))
    imported, skipped = {}, []
    for name, entry in manifest['files'].items():
        parts = recovery.safe_name(name).parts
        if parts[0] != 'data':
            continue
        if parts[1] in PROTECTED:
            skipped.append(name)
            continue
        imported[name] = entry
    tops = sorted({recovery.safe_name(n).parts[1] for n in imported})
    replaced = sorted(t for t in tops if (data_dir / t).exists()) + [s for s in DATABASE_SIDE_FILES if (data_dir / s).exists()]
    config, targets = {}, personal_config_targets(root)
    for name, target in PERSONAL_CONFIG.items():
        if name in manifest['files']:
            current = targets[name]
            same = current.is_file() and recovery.digest(current) == manifest['files'][name]['sha256']
            config[target] = 'same' if same else 'differs'
    return manifest, imported, skipped, replaced, config


def apply(archive, data_dir, root=ROOT, include_personal_config=False):
    data_dir = Path(data_dir)
    manifest, imported, skipped, replaced, config = plan(archive, data_dir, root)
    ownership = core_lock.CoreLock(data_dir)  # raises CoreAlreadyRunning if JARVIS is running
    aside = data_dir / ('pre-switchover-' + time.strftime('%Y%m%d-%H%M%S'))
    moved, placed = [], []
    try:
        with recovery.work_folder('.switchover-', [data_dir], DATA_FOLDER_REFUSED) as stage:
            with zipfile.ZipFile(archive) as z:
                for name, entry in imported.items():
                    target = stage.joinpath(*recovery.safe_name(name).parts[1:])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(name) as src, target.open('xb') as out:
                        shutil.copyfileobj(src, out)
                    if recovery.digest(target) != entry['sha256']:
                        raise ValueError('Imported file mismatch: ' + name)
            if replaced:
                aside.mkdir()
            for name in replaced:
                (data_dir / name).rename(aside / name)
                moved.append(name)
            for item in sorted(p.name for p in stage.iterdir()):
                (stage / item).rename(data_dir / item)
                placed.append(item)
        counts = recovery.check_database(data_dir / 'jarvis.sqlite3')
        if counts != manifest['database_counts']:
            raise ValueError('Imported database does not match the backup.')
        written = []
        if include_personal_config:
            with zipfile.ZipFile(archive) as z:
                for name, target in PERSONAL_CONFIG.items():
                    if config.get(target) == 'differs':
                        destination = personal_config_targets(root)[name]
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(z.read(name))
                        written.append(target)
    except BaseException:
        for item in placed:  # undo: remove what was placed, put back what was moved aside
            path = data_dir / item
            shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)
        for name in moved:
            (aside / name).rename(data_dir / name)
        if aside.exists() and not any(aside.iterdir()):
            aside.rmdir()
        raise
    finally:
        ownership.release()
    return {'status': 'switch_over_imported', 'backup_id': manifest['id'], 'files_imported': len(imported),
            'database_counts': counts, 'previous_data_moved_to': str(aside) if moved else None,
            'skipped_protected': skipped, 'personal_config_written': written}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--archive', required=True, help='Verified backup .zip created by recovery.py in the old installation')
    parser.add_argument('--data', default=str(runtime_paths.data_dir()),
                        help='saved-data folder (default: the installed data folder, else <app>/data)')
    parser.add_argument('--apply', action='store_true', help='Import (default is a dry run that changes nothing)')
    parser.add_argument('--include-personal-config', action='store_true',
                        help='Also take personality.txt and desktop/preferences.json from the backup where they differ')
    args = parser.parse_args(argv)
    try:
        if args.apply:
            result = apply(Path(args.archive), Path(args.data), include_personal_config=args.include_personal_config)
        else:
            manifest, imported, skipped, replaced, config = plan(Path(args.archive), Path(args.data))
            result = {'status': 'dry_run_only', 'backup_id': manifest['id'], 'backup_verified': True,
                      'files_to_import': len(imported), 'database_counts': manifest['database_counts'],
                      'would_move_aside': replaced, 'skipped_protected': skipped, 'personal_config': config}
    except recovery.NoWorkFolder as exc:  # a plain answer instead of a traceback, as the installer gives
        print(json.dumps({'status': 'refused', 'reason': str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
