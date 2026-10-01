# Reviewed development changes

Ask JARVIS to read an allowed source file and prepare an exact edit. Python and JavaScript candidates receive syntax checks without executing the candidate. Executable changes remain staged until you approve the displayed diff in Communications or Settings → Pending actions. Approval expires after 30 minutes and can only be used once. Styling and personality retain their existing direct-apply behavior.

After approval, ask “Run the JARVIS test suite.” This runs the fixed Python suite and reports its actual result. It does not validate JavaScript behavior, audible speech, external services, or the visual interface. Refresh for main interface changes; restart for Python and floating-companion changes. Test the affected feature before relying on it.

Use Change History to find the proposal ID, then ask JARVIS to roll it back. Executable rollback also needs approval. Rollback refuses if the file has changed since that proposal, preserving later work. Backups and diffs are local under data/development.

Allowed sources include the main interface, voice pipeline, wake detector, maps and floating companion. Credentials, desktop bridges, launchers and the action gateway are excluded. These tools do not independently implement arbitrary new integrations or grant account access.

Validation: test_development_workflow.py exercises staging, approval, denial, expiry, cancellation, candidate tampering, stale edits and rollback using temporary files. It does not mutate the running application during tests.
