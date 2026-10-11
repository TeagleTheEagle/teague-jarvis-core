# Reviewed development changes

Ask JARVIS to read an allowed file and prepare an exact edit. Python and JavaScript candidates receive syntax checks without executing the candidate. Every change stays staged until you approve the displayed difference in Chat or Settings → Developer → Pending actions. Approval expires after 30 minutes and can only be used once. Since release 1.0.15 this includes style and personality changes, which used to apply directly (docs/PERMISSIONS.md).

Two kinds of file. Your own files, `personality.txt` and `owner-style.css` (your style sheet, loaded after every other style), are kept in the config folder beside the key file, so an update, a rollback or a reinstall keeps them. Program files (the interface, voice pipeline, wake detector, maps and floating companion sources) can be changed after approval only when JARVIS runs from the source folder. An installed JARVIS never changes its program files: such a change is saved as a proposal only, for the engineer and a later release.

After approving a change to a program file, ask “Run the JARVIS test suite.” This runs the fixed Python suite and reports its actual result. It does not validate JavaScript behavior, audible speech, external services, or the visual interface. Refresh for main interface changes; restart for Python and floating-companion changes. Test the affected feature before relying on it. A personality change applies from the next question; reload the window to see a style change.

Use Release History to find the proposal ID, then ask JARVIS to roll it back (or press UNDO CHANGE there). A rollback also needs approval. Rollback refuses if the file has changed since that proposal, preserving later work. Backups and diffs are local under the data folder, in `development`.

Credentials, permission enforcement, desktop bridges, launchers and the action gateway are excluded. These tools do not independently implement arbitrary new integrations or grant account access.

Validation: test_development_workflow.py exercises staging, approval, denial, expiry, cancellation, candidate tampering, stale edits and rollback using temporary files, for the source folder and for the installed layout (program files never written, your two files in the config folder). It does not mutate the running application during tests.
