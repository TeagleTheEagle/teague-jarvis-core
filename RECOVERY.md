# Backup and recovery

Open **Settings → Backup & recovery**. Choose **Create verified backup**, then **Test restore in temporary folder**. A passing rehearsal confirms extraction, all file checksums, SQLite integrity and table row counts. It does not prove microphone, model or full application behaviour.

Backups are saved beside the app in `outputs/jarvis-backups`. They contain saved personal information and are not encrypted. They are not uploaded, and no automatic deletion or retention rotation is enabled. Keep a protected copy on another disk for disk-loss recovery; a backup on this disk cannot provide that protection.

Included: the complete SQLite database (all tables), generated documents, inspection archives when present, development proposals and backups, update-history records, source files, launch/setup scripts, desktop preferences, requirements and Node lockfile. SQLite online backup includes committed WAL data; a bounded write reservation prevents database mutations during the snapshot. Source/data files are hashed before and after copying; concurrent changes abort publication. Finish activity and stop editing before backup. Other processes may briefly wait on the database lock.

Excluded: `.env` and API credentials; Python/Node installed dependencies; downloaded speech/wake model caches; Windows shortcuts; Electron/browser cache and unsaved drafts; review/test artifacts outside saved data. Imported document text is in SQLite; external original files not copied into JARVIS remain outside the backup. This is a source/data recovery bundle, not a self-contained installer. Preserve/reconfigure credentials separately. Do not delete your current installation after making a backup.

## Recovery without overwriting the working app

Select a backup and choose **Recover to separate folder**. This creates `outputs/jarvis-backups/recovered-<backup-id>` with source at its root and saved data under `data`. Existing recovered folders are never overwritten. Nothing is launched. Verification happens before publication and the working application is unchanged.

To use a recovered copy, first quit the original JARVIS from its tray menu. Recreate its Python environment and install the included requirements. Install the pinned desktop dependencies using its lockfile, configure credentials locally, and recreate downloaded voice models using the included setup instructions. Follow `README.md`, `desktop/README.md` and the voice setup documentation in the recovered copy. Check recovered data and features before moving shortcuts. A recovered preference may enable microphone-on-launch; review preferences before first launch. Do not run original and recovered copies concurrently against the same data.

No one-click replacement of the live installation is provided. Restore the separate copy first so the current app remains available for comparison and rollback. Code in a backup is never executed by verification or restoration. Only restore your own trusted backups: hashes detect accidental changes, not a malicious archive whose manifest was also replaced.

## Command-line use

From the JARVIS folder with its existing Python environment:

```powershell
.\.venv\Scripts\python.exe recovery.py create
.\.venv\Scripts\python.exe recovery.py list
.\.venv\Scripts\python.exe recovery.py verify --id BACKUP_ID
.\.venv\Scripts\python.exe recovery.py rehearse --id BACKUP_ID
.\.venv\Scripts\python.exe recovery.py restore --id BACKUP_ID
```

Rehearsals remove their own disposable extraction folders after checking them and retain a small receipt beside the archive. Backups have a 2 GiB uncompressed / 20,000-entry limit. Duplicate paths, path traversal, reserved Windows names, linked files, checksum failures, unsupported manifests and existing destinations are rejected. If a backup fails, retry when activity is idle; no success is reported and no partial ZIP is published.
