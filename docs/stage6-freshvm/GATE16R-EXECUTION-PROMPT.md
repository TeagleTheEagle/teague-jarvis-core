# Gate 16R execution prompt: DRAFT for owner approval

Status: **DRAFT 2026-10-01 (Claude Code), not approved.** Under AMENDMENT-v2 §3(c), Gate 16R
runs only when the owner issues `RESUME_STAGE6_FRESH_VM` **together with** an approved
execution prompt. This is the proposed prompt. Approving it does not issue the token; the
owner issues the token separately, when ready. Governing text: AMENDMENT-v2 §6–§8 and
AMENDMENT-v3 (approved 2026-10-01, `governance/STAGE6-AMENDMENT-v3-RECORD.json`).

## In plain words

Gate 16R builds the fresh test machine and proves it is clean and separate from your old
VM. It ends with two snapshots and a pass/fail. It does **not** install or test JARVIS; that
is Gate 17, which gets its own prompt after you select the FINAL build. Budget about half a
day of your time, most of it waiting for Windows to install. Any failure stops; nothing is
retried quietly; a replacement VM would be your decision.

Roles: **you** do everything in VirtualBox and inside the VM, signed in as `jarvis-s6-val`.
**Claude Code** (under your own account) prepares the discs and scripts, runs the three
checkpoints when you say so, and checks every evidence file. Claude cannot see or operate
the `jarvis-s6-val` session.

## Step 0: preparation (Claude Code, owner account, before the token)

Nothing here touches the protected paths or VirtualBox.

0.1 Confirm the freeze still holds: no VirtualBox process under the owner account;
    installed VirtualBox 7.2.18.175117 (static file metadata only).
0.2 Confirm D: free space ≥ 400 GiB (the Gate 16R reserve).
0.3 Compute the SHA-256 of `Win11_25H2_English_x64_v2.iso` and compare it with Microsoft's
    published value for that download (D2). Record the result; a mismatch means the owner
    downloads fresh official media before the token.
0.4 Build the discs with `tools\New-PackageIso.ps1` (each hash recorded, each read back):
    - `JARVIS-TOOLS.iso`: the guest-side scripts (`Invoke-Gate17.ps1` for its Baseline
      phase) and a README. (The JARVIS package itself ships at Gate 17.)
    - `UNATTEND.iso`: `autounattend.xml` creating one local standard account, no Microsoft
      account, no network sign-in, English, Windows Update not touched; text recorded verbatim.
0.5 Write the host-side scripts the owner will run, each hash-recorded:
    - `tools\host\Invoke-ValidationAccountCheck.ps1` (run inside the `jarvis-s6-val` session):
      §7(b) checks, no elevation, no password handling.
    - `tools\host\New-IsolationFixtures.ps1` (owner account): the §7(e) synthetic fixtures
      under `D:\JARVIS-S6-FRESHVM\synthetic\isolation-01\` with the DACLs of
      BOOTSTRAP-PROPOSAL.md; new objects only; no change to any existing folder.
    - `tools\host\Invoke-IsolationCheck.ps1` (validation session): the §7(e) cases against the
      fixtures, the positive scratch control, and the expected-denial enumeration of both
      protected paths; writes results only.
    - `tools\host\New-FreshVm.ps1` (validation session): the VBoxManage commands of step 6,
      so the VM is created the same way every time; the GUI is the equivalent.
0.6 Create `D:\JARVIS-S6-FRESHVM\evidence\gate16r-<date>\` (owner account). All 16R evidence
    goes there, with `MANIFEST.json` (every file's SHA-256) written at the end.

## Step 1: P0 checkpoint (Claude Code, after the token and the owner's "run P0")

`tools\host\Invoke-PreservationCheckpoint.ps1 -Checkpoint P0 -OwnerAuthorized`: permitted
reads only (§8(c)), census before and after. PASS required. A mismatch is pre-existing:
STOP, owner decision, no route action. (This prompt authorises P0, P1 and P2 at their
sequence points; P3–P5 belong to later prompts.)

## Step 2: §7(b) account (owner, in the `jarvis-s6-val` session)

Sign in as `jarvis-s6-val` and run `Invoke-ValidationAccountCheck.ps1` from
`D:\JARVIS-S6-FRESHVM\tools\`. It records: SID; group memberships (must not include
Administrators, Backup Operators or Hyper-V Administrators, nor any privileged group); token
privileges (SeBackup, SeRestore, SeTakeOwnership, SeDebug must be absent); `cmdkey /list`
(no saved owner or administrator credentials); profile creation time (fresh). The password is
never typed into a script or recorded. Claude reviews the JSON. The two credential entries
of 2026-09-30 stay UNRESOLVED (v3 A3). Any other unmet item: STOP.

## Step 3: §7(e) isolation (owner, both sessions)

3.1 Owner account: `New-IsolationFixtures.ps1` creates the synthetic roots and sentinels,
    hard link, junction and scratch folder; writes `owner-preflight.json` (hashes, DACLs).
3.2 Validation session: `Invoke-IsolationCheck.ps1` attempts, on the synthetic restricted
    fixture only: enumerate, read, open for write, create, delete, rename, change permission,
    change owner; the same through the hard link, the junction, the extended canonical path
    (`\\?\`) and `.`/`..` paths; expects ACCESS_DENIED with no mutation. Positive control:
    create/read/delete in scratch must succeed. Then enumerates both protected paths
    expecting ACCESS_DENIED (nothing is read). Short names: `dir /x` on the fixture and the
    `NtfsDisable8dot3NameCreation` registry value are recorded; if no short name exists the
    case is NOT_APPLICABLE_WITH_EVIDENCE (v3 A2); nothing is enabled.
3.3 Owner account: postflight compares fixture hashes and DACLs with the preflight.
    Any mutation, any success where denial was expected, or any access to a protected path:
    FIRST FAIL, STOP, record, no repair. Broker case: dispositioned (v3 A1), not tested.

## Step 4: §7(c),(d) storage and VirtualBox home (owner account)

Create `D:\JARVIS-S6-FRESHVM\vbox-home\`, `machines\`, `media\` and grant `jarvis-s6-val`
modify rights on those three new folders only (new-object DACLs; no change to the existing
parent or to `evidence\`). Copy the Windows ISO, `UNATTEND.iso`, `JARVIS-TOOLS.iso` and the
host's `VBoxGuestAdditions.iso` into `media\`; record their hashes. In the validation
session set the **user** environment variable `VBOX_USER_HOME=D:\JARVIS-S6-FRESHVM\vbox-home`
(that account only; never the owner account). Nothing under `C:\Users\jonny`; E: not used.

## Step 5: P1 checkpoint (Claude Code, owner's "run P1")

As step 1, compared exactly with P0. Mismatch = PRESERVATION_FAILURE: STOP, no retry.

## Step 6: VM creation (owner, validation session)

Start VirtualBox normally in that session (v3 A4). Run `New-FreshVm.ps1` or do the same in
the GUI: new VM `JARVIS-S6-FRESH`, Windows 11 (64-bit), 4 vCPU, 8192 MiB, new 96 GiB
dynamic disk in `machines\`, EFI with Secure Boot and TPM 2.0, NAT only with
`--nat-localhostreachable1 off`, shared clipboard and drag-and-drop disabled, no USB
passthrough, no port forwarding, no host-only or bridged adapter, no audio device; optical
drives: Windows ISO, `UNATTEND.iso`. One shared folder `guest-egress-01` →
`D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\`, **not** auto-mounted, writable.
Then record: VM UUID, `.vbox` path and SHA-256, and confirm the VM is registered only in
`D:\JARVIS-S6-FRESHVM\vbox-home\VirtualBox.xml` (Claude reads that one file and the
`.vbox`; it never opens VirtualBox). A UAC prompt at any point: STOP.

## Step 7: Windows installation (owner, inside the VM)

Boot the VM. Setup reads `autounattend.xml`; a local standard account is created with no
Microsoft account. If Setup demands a Microsoft account or refuses the answer file: STOP,
`OWNER_DECISION_REQUIRED_FRESH_VM_ACCOUNT`; no bypass commands. After first sign-in: pause
Windows Update for the longest period offered (record it); attach `VBoxGuestAdditions.iso`
and install Guest Additions 7.2.18 (record version); reboot; mount the egress folder
manually; attach `JARVIS-TOOLS.iso`.

## Step 8: cleanliness and baseline record (owner, inside the VM)

Run `Invoke-Gate17.ps1 -Phase Baseline -Package <tools disc> -Evidence <egress>`. It writes
the §6(f) negative checks (no JARVIS, no Python/Node/Git/Visual Studio/build tools, default
PATH, no `.env`, no credential entries, no signed-in accounts), edition and build.UBR,
activation status, Windows Update pause, installed programs, services and PATH. Any
positive finding: FAIL, STOP.

## Step 9: FRESH-CLEAN-BASELINE snapshot (owner, validation session)

Shut the VM down cleanly. `VBoxManage snapshot JARVIS-S6-FRESH take FRESH-CLEAN-BASELINE`.
Record the snapshot UUID and the `.vbox` SHA-256. Claude writes the §6(h)1 manifest from
the step 8 evidence plus those identities.

## Step 10: P2 checkpoint (Claude Code, owner's "run P2")

As step 5.

## Step 11: FRESH-PREREQ snapshot (owner, validation session)

Per v3 D1 nothing is installed: take snapshot `FRESH-PREREQ` immediately, with the same
manifest fields and the recorded statement "the documented deployment procedure requires
no prerequisites; the release carries CPython 3.12.10, Electron, the VC++ runtime and
models". Record the §6(i) identity record: VirtualBox host version, ISO hash, VM UUID,
`.vbox` path and hash, both snapshot UUIDs, guest edition and build, the account name the
VM runs under.

## Step 12: result (Claude Code)

Check every §6(k) item against the evidence: (a)–(j), §7, P0–P2, the continuity list
(account boundary, ACL boundary, isolated VirtualBox configuration, registry/config
separation, disk identity, snapshot lineage rooted at FRESH-CLEAN-BASELINE, networking,
LocalhostReachable=0, no path back to the protected original). All met:
`FRESH_VM_QUALIFICATION_PASS`, evidence `MANIFEST.json` written, report to the owner,
**STOP before Gate 17**. Any unmet item: FAIL, STOP, owner decision; no silent retry, no
in-place repair.

## Not authorised by this prompt

Gate 17 and later; FINAL selection; any read of the protected paths outside P0–P2; any
VirtualBox operation under the owner account; installing, upgrading or repairing
VirtualBox; Experiment 5; provider credentials; production; Stage 7.

## How to approve

Reply that you approve the Gate 16R execution prompt (name any step you want changed).
Claude then finishes step 0, reports its results, and waits for `RESUME_STAGE6_FRESH_VM`.
