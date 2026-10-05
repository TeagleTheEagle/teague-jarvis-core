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

## After Stage 6

| What | Result | Records | Manifest (SHA-256) |
|---|---|---|---|
| Switch-over of the everyday JARVIS to 1.0.11 | `SWITCH_OVER_COMPLETE` (2026-10-04) | `../governance/CUTOVER-APPROVAL-RECORD.json`; `D:\JARVIS-cutover\evidence\cutover-evaluation.json`; repo `docs/cutover-evidence/` | `D:\JARVIS-cutover\evidence\MANIFEST.json` 82ff8be6… |
| Stage 7 (packaged-app acceptance, 1.0.10 -> 1.0.11) | `STAGE_7_COMPLETE` (2026-10-04) | `../governance/STAGE7-APPROVAL-RECORD.json`; `D:\JARVIS-stage7\evidence\stage7-evaluation.json`; guest `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7\`; repo `docs/stage7-evidence/` | `D:\JARVIS-stage7\evidence\MANIFEST.json` 69f04661…; guest `stage7\MANIFEST.json` 06627a14… |
| Stage 7 check of release 1.0.14 (1.0.11 -> 1.0.14, version 2 scripts) | `STAGE_7_COMPLETE` (2026-10-05; 27 of 27 checks; incidents 01-02 with owner decision 01) | `../governance/STAGE7-1.0.14-APPROVAL-RECORD.json`; `D:\JARVIS-stage7\1.0.14-e03872680e1d\evidence\stage7-evaluation.json`; guest `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\stage7-1.0.14-e03872680e1d\`; repo `docs/stage7-1.0.14-evidence/` | `D:\JARVIS-stage7\1.0.14-e03872680e1d\evidence\MANIFEST.json` 93a71864…; guest `stage7-1.0.14-e03872680e1d\MANIFEST.json` df9e417d… |

The VM now also holds snapshots STAGE7-PASS `2503a110-bd71-49d8-8ff1-3193c2c20cd3` (child of FRESH-PREREQ) and
STAGE7-PASS-1.0.14-e03872680e1d `0b7c12fa-5067-4f3d-b24f-ee43b6c42257` (child of FRESH-PREREQ; current).

## Limitations carried forward

Listed in `gate20-evaluation.json` (`stated_limitations_carried_forward`).
