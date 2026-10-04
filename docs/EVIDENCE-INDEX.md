# Stage 6 evidence index (fresh-VM route)

Written 2026-10-04 at Gate 20 by Claude Code. Verdict: **`STAGE_6_COMPLETE`**, `PRODUCTION_CUTOVER_NOT_AUTHORIZED`,
`STAGE_7_NOT_STARTED`. FINAL = `1.0.11-60d406fb6398` (commit `60d406fb6398b95345aa50bafead369dc0f41d25`, zip SHA-256
`1923651176dd3095e84b0628a5c7a90608b6db57fe06986670e0ea8246225a58`).

Evidence root: `D:\JARVIS-S6-FRESHVM\evidence\`. Repo copies: `docs/stage6-freshvm/`. Integrity rests on the hash
manifests and the repo copies (the D: tree is modifiable by any signed-in account). The sealed folder
`evidence\P0\` (2026-09-30) is owner-only and is in no manifest. Nothing is uploaded or synced.

## Authority

| What | Record |
|---|---|
| Runbook V1 / V2, governing texts | `../reference/governing/` |
| AMENDMENT-v2 (fresh-VM route) and its activation | `../reference/handover-v1/records/authority/corrected-amendment/`, `.../stage6-route-fresh-vm-activation-20260930-063614-v1.json` |
| AMENDMENT-v3 (dispositions A1–A5, selections D1–D9) | `../governance/STAGE6-AMENDMENT-v3.md`, `-RECORD.json` |
| Gate 16R prompt and token `RESUME_STAGE6_FRESH_VM` | `../governance/STAGE6-GATE16R-EXECUTION-PROMPT.md`, `-PROMPT-APPROVAL.json`, `STAGE6-RESUME-FRESH-VM-RECORD.json` |
| Simplified acceptance | `../governance/STAGE6-SIMPLIFIED-ACCEPTANCE-RECORD.json` |
| FINAL selection, Gates 17–20 plan | `../governance/STAGE6-FINAL-SELECTION-RECORD.json`, `STAGE6-GATES17-20-EXECUTION-PROMPT.md`, `-PROMPT-APPROVAL.json` |
| Token `RESUME_STAGE6_RECOVERY` | `../governance/STAGE6-RESUME-RECOVERY-RECORD.json` |

## Gates

| Gate | Result | Result record | Folder (under the evidence root) | Manifest (SHA-256) |
|---|---|---|---|---|
| 16R fresh VM qualification | `FRESH_VM_QUALIFICATION_PASS` | `step12-evaluation.json`, `step12-owner-dispositions.json` | `gate16r-20261002\` | `MANIFEST.json` 38d487a6…, `MANIFEST-addendum-1.json` |
| 17 clean Windows deployment | `CLEAN_WINDOWS_DEPLOYMENT_PASS` | `gate17-evaluation.json` | `gate17\` | `MANIFEST.json` 53ac88ff…, `MANIFEST-guest-egress-01.json` aa3e8a30… |
| 19 update / rollback | `UPDATE_ROLLBACK_RECONCILED` | `gate19-evaluation.json` | `gate17\` | same |
| 18 backup / restore / recovery | `BACKUP_RESTORE_RECOVERY_PASS` | `gate18-evaluation.json`, `p4-evaluation.json`; incidents 01–04, owner decisions 01–04 | `gate18\` | `MANIFEST.json` 603605cf…, `MANIFEST-guest-egress-01.json` c42af0f1… |
| 20 final review | `STAGE_6_COMPLETE` | `gate20-evaluation.json`, `gate20-requirements-draft.json`, `gate20-owner-decisions.json`, `p5-evaluation.json` | `gate20\` | `MANIFEST.json` fd2fddf6… |

Guest-side records (written inside the VM): `guest-egress-01\` (baseline runs, Gate 17 phases, Gate 19, Gate 18 run
`gate18-20261004-074554`, and the two stopped Gate 18 runs under `incident-03-run1\` and `incident-04-run2\`).

## Preservation checkpoints (all PASS, all equal)

| | Run folder |
|---|---|
| P0 | `gate16r-20261002\checkpoints\p0-20261002-012032` |
| P1 | `gate16r-20261002\checkpoints\p1-20261002-025102` |
| P2 | `gate16r-20261002\checkpoints\p2-20261004-030308` |
| P3 | `gate17\checkpoints\p3-20261004-051026` |
| P4 | `gate18\checkpoints\p4-20261004-075914` |
| P5 | `gate20\checkpoints\p5-20261004-080906` |

## The acceptance VM

`JARVIS-S6-FRESH`, uuid `4ef16bdd-2a1b-46af-83db-ee69c2f868bb`, under `D:\JARVIS-S6-FRESHVM\machines\`. Snapshots:
FRESH-CLEAN-BASELINE `0da943df-…`, FRESH-PREREQ `9f1d7bec-…`, GATE17-19-PASS `3023e9a7-…`, GATE18-PASS
`5dcbb9f0-0d6c-4311-8b57-7ba329290edf` (current; holds the owner's personal data). Owner decision at Gate 20: keep
until the switch-over has run well, then delete on the owner's word.

## Build and media

`D:\JARVIS-release-work\release\` (FINAL and previous build with release records);
`D:\JARVIS-S6-FRESHVM\media\` (Windows ISO, answer-file, tools, package and recovery discs, each with a hash record).
Rehearsals: `docs/release-rehearsal-20261001/`, `docs/release-rehearsal-20261004/`.

## Limitations carried forward

Listed in `gate20-evaluation.json` (`stated_limitations_carried_forward`).
