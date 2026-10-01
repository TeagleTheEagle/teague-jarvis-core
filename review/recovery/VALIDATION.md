# Backup and recovery validation — 2026-09-09

## Desktop follow-up

RESOLVED after direct desktop reproduction: ZIP 03f021f6a4ba4a96995b1318ba18f32c inherited owner-only ACLs from TemporaryDirectory (OWNER RIGHTS, SYSTEM, Administrators; owner CodexSandboxOffline). Receipt/folder ACLs did include jonny, so the earlier inference from receipt permissions was insufficient. publish_backup now creates a new sibling file with normal inherited permissions, verifies it and renames it for publication; it does not modify ACLs. Verification temp files stay beside the archive. Rehearsal reports its stage on OS errors.

14 recovery/HTTP tests passed. Get-Acl confirmed replacement 50fe5f453d084b32aec90bad88b4edd0.zip inherited jonny access. Using Computer Use, applied the stage-diagnostic update, opened Settings, muted runtime mic, listed backups and tested replacement dated 3:56:25 PM. Actual desktop UI returned restore rehearsal passed. Its receipt beside the backup confirms 164 file hashes plus SQLite integrity/count checks; working data was not restored over. The publication-code update remains pending in the desktop at this observation. The original inaccessible ZIP is retained, not deleted. No full recovered application launch/hardware test claimed.

User screenshot at 15:43 showed a generic API failure during recovery. The same saved backup passed a fresh CLI rehearsal and a real authenticated HTTP rehearsal using an isolated server (test_http_real.py). Those checks do not reproduce the running desktop process. Added operation/type/OS-error-code reporting without private exception text; 12 recovery/HTTP checks passed, including failure-message privacy. Root cause remains unconfirmed. Retry in the updated desktop app is required; no repair success claimed.

Implemented recovery.py, static/recovery.js and RECOVERY.md. Wired the authenticated recovery endpoint and static asset in server.py, script loading in static/index.html, and the inert inspection copy in inspection_runtime.py. Updated README and release notes. Fixed a reproduced same-clock-tick collision in update_history.py with unique filenames and ordered observation timestamps.

## Completed checks

- 37 Python tests passed across test_recovery, test_jarvis and test_update_evidence.
- One additional HTTP recovery test passed: missing session rejected, arbitrary path field rejected, and valid rehearsal routed to the requested backup ID. Total: 38 checks.
- Six recovery tests cover complete saved-data capture, committed WAL data, checksums, corrupt archives, unsafe paths/IDs, lock overlap, failed backup publication, separate-folder recovery and refusal to overwrite.
- One isolated Chrome UI test passed for create/list/rehearse/error display. The test uses synthetic API responses and saved data. It does not prove the running Electron app loaded the update. preview.png was visually reviewed.
- JavaScript syntax and Python compilation checks passed; these are separate from runtime tests.

## Real-data verification

Completed recovery.create and recovery.rehearse against the real local saved database. Backup ID: 03f021f6a4ba4a96995b1318ba18f32c. Result: 161 archived files, 2,093,277 bytes, 16 database tables, restore_rehearsal_passed. Results are in real-backup-result.json; the ZIP and restore-check receipt are in outputs/jarvis-backups. Every extracted file hash, SQLite integrity and table counts matched. The temporary restore directory was removed. Restored code was not started.

## Limitations and rollback

API credentials, installed dependencies, downloaded voice/wake models, OS shortcuts and browser-only unsaved state are excluded. Backups contain private saved data, remain unencrypted locally and need a separately stored copy for disk-loss protection. No automatic schedule or deletion is added. Hashes detect corruption, not malicious replacement of an entire backup and manifest.

The running app is not overwritten or restarted by recovery operations. Recovery only creates a new folder. No full recovered runtime/device/cloud validation is claimed. To roll back this feature, remove its Settings script include and server endpoint/static mapping, revert the inspection asset addition and remove the new recovery source/assets; retain backup ZIPs and receipts. Do not restore a backup over a running app.
