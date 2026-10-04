# Gate 20: the final Stage 6 review (CLOSED 2026-10-04: all four decisions accepted, P5 PASS, verdict STAGE_6_COMPLETE)

Prepared 2026-10-04 by Claude Code. The full table with every requirement and its record is
`D:\JARVIS-S6-FRESHVM\evidence\gate20\gate20-requirements-draft.json` (repo copy in `gate20-evidence/`).
This page is the plain-language version.

## Where every requirement stands

| Group | Result |
|---|---|
| The build (FINAL 1.0.11): source, files, package and tool versions all tied together by hashes | PASS |
| The old test machinery of Gates 3 to 15 (collector, observers, experiments) | already settled by your amendment of 30 September: accepted or not applicable |
| Fresh VM qualification (Gate 16R) | PASS, with the differences you accepted then |
| Clean install (Gate 17) | PASS |
| Your real backup restored (Gate 18) | PASS, with your four decisions of today |
| Update and rollback (Gate 19) | PASS; timing limit still to be stated (decision 2) |
| Your old VM untouched (checkpoints P0 to P4) | PASS; P5 still to run |
| Clean-up, records and hashes | PASS; final manifest and index after P5 |

Nothing has failed. Four points need your decision, then P5, then the verdict.

## Your four decisions

**1. One small recording gap.** The rules say the Windows build number is recorded at every gate. My Gate 18
script did not record it. The VM's own settings file, saved at the Gate 18 snapshot, shows the same build as
before (26300.9457), and Windows Update was paused. *Recommended: accept this as the record.*

**2. Time limits.** No limit was fixed in advance; it was to be set from what the VM measured. Measured: install
about 200 s, update 307 s, rollback 98 s; stopping a running JARVIS up to 95 s. *Recommended limits: install,
update and rollback each within 600 s; stopping JARVIS within 120 s.* Every measured run is inside them. The four
old limits in the rules (10 s, 13.6 s, 15 s, 20 s) belonged to the old collector machinery, which did not run on
this route; I read them as not applying. If you read the 20 s "cleanup" limit as applying to stopping JARVIS,
the 95 s stops would be a Gate 19 failure for you to rule on: say so if that is your reading.

**3. One limitation of the new build.** If a backup sits on a read-only disc, the new JARVIS hangs instead of
giving an error (found today). It does not affect the switch-over, where the backup is in a normal folder.
*Recommended: accept as a known limitation; I fix it in the first release after the switch-over.*

**4. The test VM and the copies of your data.** The VM (45 GB) and three small copies of your backup on D: now
hold your personal data (no AI keys). *Recommended: keep them until the switch-over is done and has run well for
a while, then delete them.* The other choice is to delete them now. Deleting the VM is done by you in VirtualBox
(jarvis-s6-val); I would give you the steps.

## After your decisions

1. Checkpoint P5, only when you type its go-ahead yourself (the same form as P4, with P5).
2. I write the final table, the manifest and the evidence index, and give the verdict: `STAGE_6_COMPLETE` or
   `STAGE_6_INCOMPLETE` with the exact blocker.
3. I stop. Switching your everyday JARVIS over and Stage 7 remain your separate decisions.

## For your information (no decision needed)

- Your everyday JARVIS cannot start at the moment (the Python it borrowed from Codex is gone). Stage 6 does not
  depend on it, but the switch-over plan's "going back to the old JARVIS" does. I will add this to the
  switch-over plan.
- The "3 memory items" question from Gate 18 is explained: the status page lists only items of the kind
  "memory"; the other rows in the same table are projects, notes and tasks.
- Part of today's records were written by Claude Opus 5.5 after you switched models; each record says which.
