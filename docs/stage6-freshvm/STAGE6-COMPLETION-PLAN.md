# Stage 6 completion plan (fresh-VM route): owner review draft

Status: **DRAFT FOR OWNER REVIEW, 2026-10-01.** This document authorizes nothing, issues or
requests no token, and changes no control record. It consolidates where Stage 6 stands,
what blocks it, and the decisions needed, so the owner can choose how to finish.

Governing text: `reference/handover-v1/records/authority/corrected-amendment/AMENDMENT-v2.txt`
(route STAGE6-ROUTE-FRESH-VM-20260930-v2, RECORDED_ACTIVE), runbook V1/V2 Gates 16–20,
58bc2bcf (clean-VM option). Prior preparation: `reference/handover-v1/records/stage6-preparation/`
and `records/package-isolation-plan/`, plus the 2026-10-01 VirtualBox source review in
`Documents\Codex\2026-09-07\cr\outputs\stage6-vbox-source-review-20261001-01\REPORT.md`.

## 1. In plain words

- **The JARVIS package is ready to be tested.** The release design is approved, the
  candidate passes every test with its own bundled runtimes, and installing, updating,
  rolling back, uninstalling and reinstalling all work in local rehearsals.
- **The VM set-up is what is stuck.** The route requires proving that a separate Windows
  account running VirtualBox cannot reach the old protected VM. Two parts of that proof
  (VirtualBox's SYSTEM background service, and Windows short file names) could not be
  specified as a test after several review rounds. Under the amendment, an unmet item is
  a FAIL, so Gate 16R cannot pass as written until the owner decides how to treat them.
- Section 6 gives three ways forward. My recommendation is **Option B**.

## 2. Correction to an earlier statement

The "4/5" in the control records is the **Experiment 5 diagnostic budget**, frozen by
AMENDMENT-v2 §10 and not transferable to any gate. It is not a count of Stage 6 attempts.
The real constraint is §6(k): any unmet Gate 16R item is a FAIL, with no silent retry and
no in-place repair; a replacement VM needs an owner decision.

## 3. Where each part stands

| Part | State | Evidence |
|---|---|---|
| Gates 0/0A/1/2 | PASS (historical) | AMENDMENT-v2 §2 |
| Gates 3–15 | Dispositioned by activation | activation record 2026-09-30 |
| Gate pointer | OWNER STOP #1R | control records |
| P0 | **PASS**, sealed (`p0-20260930-01`), under RESUME_STAGE6_FRESH_VM limited to P0 | `D:\JARVIS-S6-FRESHVM\evidence\P0\p0-20260930-01\REPORT.json` |
| Owner freeze | In force: VirtualBox closed under the owner account; no install/upgrade/repair from P0 to Gate 20 | P0 AUTHORIZATION.json |
| O-1 account `jarvis-s6-val` | Created by the owner 2026-09-30; member of Users only | owner declaration; local account metadata |
| §7(b) account qualification | **Not established.** Two credential entries UNRESOLVED (owner's bounded decision); launch path not established | CHAT-CONTEXT.md; VBox source review |
| §7(e) ACL isolation | **Not started.** Bootstrap proposal unapproved; short-name case may be NOT EXERCISED; broker (VBoxSDS) case has no test definition | BOOTSTRAP-PROPOSAL.md; VBox source review |
| Gate 16R VM | Not started | — |
| Gate 17 package | **Ready** (candidate below) | `docs/release-rehearsal-20261001/` |
| Gate 18 recovery | Not started; local rehearsal with the packaged release still to do (section 8) | — |
| Gate 19 update/rollback | Local evidence exists; to be reconciled against FINAL | `docs/release-rehearsal-20261001/` |
| Experiment 5 | UNCONSUMED; budget frozen at 4/5 | AMENDMENT-v2 §10 |

## 4. The package side (Gate 17 readiness)

- Release design **approved by the owner 2026-10-01** (`docs/RELEASE-DESIGN.md`): zip with
  `install.cmd`, bundled models, CPython 3.12.10 embeddable, personality and preferences
  in `config\`. Per user, no administrator rights.
- The three defects reproduced in the 2026-10-01 preparation review (main-desktop header
  casing, delete/admission race, nonfinite percent/conversion) are corrected (60c89f1) and
  now all have regression tests that fail without the fix (15a1ad1).
- Candidate: the next build after 15a1ad1 (1.0.8), to be built with its zip and put through
  the full regression and zip-install rehearsal before it is offered for FINAL selection.
  1.0.7 is superseded only because 15a1ad1 touched `desktop/main.cjs`.
- **Prerequisites: none.** The release carries its own Python 3.12.10, Electron, VC++
  runtime DLLs and voice/wake models. This removes the conflict the earlier resource plan
  flagged (setup tooling leaving a JARVIS installation in FRESH-PREREQ). See decision D1.

## 5. Host facts (read 2026-10-01, non-elevated)

32 GB RAM; AMD Ryzen 7 3700X (8 cores / 16 threads); firmware virtualization enabled;
**Windows hypervisor present** (VirtualBox will run on it, typically slower, which matters
for Gate 17/19 timing; no setting is proposed to change); D: 1,639.9 GB free, above the
proposed 400 GiB Gate 16R reserve; VirtualBox 7.2.18.175117 installed (frozen);
Windows 11 Home ISO present at `D:\C-drive-overflow\Users\jonny\Downloads\Win11_25H2_English_x64_v2.iso`
(8,471,603,200 bytes; acquisition URL/date not recorded; hash not yet compared with
Microsoft's published value).

## 6. Ways forward (owner chooses)

**Option A — continue the route exactly as written.** Next per the records: a read-only
closure review of the installed proxy/registration boundary, then an owner-reviewable
synthetic broker test specification, then the bootstrap exception, then §7(e), storage,
P1 and the VM. Several more approval rounds before a VM exists, and the broker and
short-name cases may still be unprovable at the end.

**Option B — keep the route; dispose of the two unprovable isolation cases explicitly.
(Recommended.)** The owner records, as APPROVED_DISPOSITION with a stated limitation (a
small amendment, v3, under the Gate 20 disposition classes):
- *Broker case:* VirtualBox's SYSTEM service is not proven unable to open files on the
  validation account's behalf. Relied on instead: the separate standard account, its own
  VBOX_USER_HOME on D:, the service keying servers by user SID (source review), the
  §7(e) denial test of the protected paths as `jarvis-s6-val`, and the P0–P5 checks
  that turn any change to the protected original's metadata into a PRESERVATION_FAILURE.
- *Short names:* if 8.3 names are absent on the synthetic fixture, the case is recorded
  NOT EXERCISED with that reason, not enabled.
Everything else in §6–§8 stays, including P0–P5, the freeze and no retries.
Residual risk, stated plainly: the protection of the old VM's *content* rests on Windows
permissions plus before/after metadata checks, not on a full proof about the service.
Given the validation account only ever registers its own new VM in its own home, I judge
that risk low, but it is the owner's to accept.

**Option C — a clean physical PC instead of a VM.** If a spare PC can be reset to a fresh
Windows 11 Home, Gate 17 can run there with no VirtualBox at all, which removes the
isolation problem rather than proving it. Needs an amendment replacing Gate 16R's VM
requirement. Only sensible if such a machine exists.

## 7. Decisions needed before any execution prompt (whichever option)

| # | Decision | Recommendation |
|---|---|---|
| D1 | Prerequisites for FRESH-PREREQ under the approved release design | None: FRESH-PREREQ = FRESH-CLEAN-BASELINE with nothing installed, recorded as "the documented deployment procedure requires no prerequisites"; Python 3.12 x64 is satisfied by the bundled CPython 3.12.10 |
| D2 | Media | The existing 25H2 English x64 ISO, hash compared to Microsoft's published value; acquisition URL/date recorded as a limitation, or a fresh official download if the owner prefers |
| D3 | Guest local account | Use only the setup path the media actually offers; if Home 25H2 offers no supported local-only path, STOP `OWNER_DECISION_REQUIRED_FRESH_VM_ACCOUNT` (§6(c)) |
| D4 | Evidence egress | The earlier proposal: one manually mounted Guest Additions 7.2.18 shared folder mapped only to `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\` |
| D5 | FINAL candidate for Gates 17–19 | 1.0.8 once its regression and zip rehearsal pass (owner-only FINAL selection) |
| D6 | Gate 17 scope for voice and providers | Local STT checked offline from a bundled test recording (no audio device); no provider keys in Stage 6 (AI providers are owner configuration); add keys later only per §9(a) |
| D7 | Executor | Claude Code in place of Codex wherever the amendment names Codex (owner preference recorded in CHAT-CONTEXT.md); Codex reviews only |
| D8 | Gate 18 backup | A backup made inside the VM from synthetic data with `recovery.py`, restored into a second install folder in the same VM; backup file hash before and after (backup-source preservation, R-C); E: never used |
| D9 | Gate 19 timing bound | Measured per phase on the VM; any bound set from evidence, not chosen in advance (58bc2bcf Part 1) |

## 8. Execution model (once a route option and D1–D9 are settled)

- The owner operates VirtualBox only inside the `jarvis-s6-val` Windows session (§7(f):
  never under the owner account). Claude Code runs under the owner account, so it cannot
  and does not operate that VM.
- Everything that runs inside the guest is a reviewed, hash-bound script delivered on the
  read-only package ISO; each writes its results to the single egress folder.
- Claude Code prepares the ISO and scripts, runs the owner-account checkpoints P0–P5
  (enumeration, three control-file hashes, DACL reads, process census; only after the
  route resumes) and checks every evidence file the guest returns.
- Sequence (§7(h), §2): P0 (new run) → (b) → (e) → storage/home → P1 → VM creation →
  registration check → Windows install → Guest Additions → cleanliness checks →
  FRESH-CLEAN-BASELINE → P2 → FRESH-PREREQ → Gate 17 → P3 → OWNER STOP #2 → Gate 18 → P4 →
  Gate 19 → Gate 20 with P5 → STOP (no cutover, no Stage 7).

## 9. Local preparation Claude can do now (no approval needed)

1. Build 1.0.8 with its zip; full release regression; zip-install rehearsal.
2. Gate 18 rehearsal on D: with the packaged release: backup, verify, restore into a second
   sandbox install, data and configuration integrity, backup unchanged.
3. Installer phase timings (copy, verify, stop, switch) for the Gate 19 evidence.
4. Package-ISO builder (Windows' built-in IMAPI, no install) and the guest-side scripts,
   tested against sandbox installs on D:.
5. P0–P5 checkpoint script, written and reviewed but **not run**: reading protected paths
   is not authorized until the route resumes.
