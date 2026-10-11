# Owner amendment STAGE6-ROUTE-FRESH-VM-20261001-v3 (APPROVED)

Status: **APPROVED by the owner on 2026-10-01 in a direct chat message: "i approve everything".** Drafted by Claude Code the same day at the owner's request (option B); approved as drafted, every D-item at its recommended selection.
Recorded and active from the moment of approval (see STAGE6-AMENDMENT-v3-RECORD.json).
It issues no token and authorises no execution. Everything in AMENDMENT-v2 not named here is
unchanged, including P0–P5, the owner freeze, no retries, and all of §13 (not authorised).

## What you are deciding (plain words)

1. Two parts of the VirtualBox isolation proof could not be turned into a test after several
   reviews. You would **accept them with a written limitation** instead of proving them,
   while keeping every real protection. Section A below says exactly what is accepted and
   what still protects the old VM.
2. Nine practical choices for the VM test (which Windows image, how packages get in, how
   evidence gets out, what gets tested, who runs what). Section B lists each with the
   recommended answer. Change any you disagree with.
3. After approval, the next owner acts are still separate: the `RESUME_STAGE6_FRESH_VM`
   token with an execution prompt for Gate 16R, and later `RESUME_STAGE6_RECOVERY`.

---

## Section A: dispositions of the unresolved isolation items (§7(b), §7(e))

Made under the Gate 20 disposition classes. Each is **APPROVED_DISPOSITION** or
**NOT_APPLICABLE_WITH_EVIDENCE**, never PASS.

### A1. Broker case (VBoxSDS / VBoxSVC acting on the validation account's behalf): APPROVED_DISPOSITION

"Not proven. The 2026-10-01 source review established the call chain at component level
but could not specify an execution-ready, non-elevated test of whether VirtualBox's SYSTEM
service (VBoxSDS) or the per-user VBoxSVC can open files outside the validation account's
own authority. The owner accepts this as a stated limitation and relies instead on:
(i) the standard, non-administrator validation account `jarvis-s6-val` with no saved owner
or administrator credentials; (ii) VirtualBox running under that account only, with
`VBOX_USER_HOME` and the machine folder on `D:\JARVIS-S6-FRESHVM\`, so the only VM it ever
registers is its own new one; (iii) the source-review finding that the service keys servers
by user SID (evidence against user-name routing, not proof of isolation); (iv) the §7(e)
expected-denial test of both protected paths as `jarvis-s6-val`; (v) checkpoints P0–P5,
which turn any change to the protected original's metadata or control-file hashes into a
PRESERVATION_FAILURE that stops the route. Residual risk, stated: protection of the
protected original's content rests on Windows permissions plus before/after metadata
checks, not on a proof about the service. Any observed access to a protected path by any
VirtualBox process is a FAIL regardless of this disposition."

### A2. Short-name (8.3) alias case of §7(e): NOT_APPLICABLE_WITH_EVIDENCE when absent

"If `fsutil 8dot3name query D:` reports short-name creation disabled for the volume and
the synthetic fixture under `D:\JARVIS-S6-FRESHVM\synthetic\` has no short name
(`cmd /c dir /x` shows none), the short-name alias case is dispositioned
NOT_APPLICABLE_WITH_EVIDENCE with those two outputs as the evidence. Short names are never
enabled or created to exercise it. §7(e) PASS may then be declared on the remaining cases
(enumeration, read, write, create, delete, rename, permission and ownership change, hard
link, junction, extended canonical path, `.`/`..` paths) plus the positive scratch control."

### A3. The two credential entries of §7(b): APPROVED_DISPOSITION (unchanged from 2026-09-30)

"The two credential entries remain UNRESOLVED under the owner's bounded evidence decision
of 2026-09-30. §7(b) is otherwise verified as written (standard user; not in Administrators,
Backup Operators or Hyper-V Administrators; no privileged group; no automatic elevation;
fresh profile; SeBackup/SeRestore/SeTakeOwnership/SeDebug absent; password never emitted).
This does not establish full account qualification beyond those checks."

### A4. §7(b) launch path: APPROVED_DISPOSITION

"VirtualBox is started under `jarvis-s6-val` through its normal user interface in that
account's interactive session, with `VBOX_USER_HOME=D:\JARVIS-S6-FRESHVM\vbox-home` set for
that session only. VirtualBox's own first-use COM registration under that account is its
ordinary behaviour, not an installation change under §7(g); the §7(g) freeze is judged by
the installed binaries' version and hashes at P0 and P5. No elevation, no UAC prompt may be
accepted; a prompt is a STOP."

### A5. Executor

"Claude Code performs the engineer role wherever AMENDMENT-v2 names Codex (owner
preference recorded 2026-10-01). Codex is an independent reviewer only, on owner request.
Claude Code runs under the owner account and therefore never operates VirtualBox or the
VM; the owner does, in the `jarvis-s6-val` session. Everything that runs inside the guest is
a hash-bound script delivered on the package ISO and run by the owner."

---

## Section B: selections under §6 (D1–D9)

| # | Decision | Selection (change anything you disagree with) |
|---|---|---|
| D1 | §6(h)2 prerequisites | **None.** The approved release (docs/RELEASE-DESIGN.md) carries its own CPython 3.12.10, Electron, VC++ runtime DLLs and models; nothing is installed system-wide. FRESH-PREREQ = FRESH-CLEAN-BASELINE with the recorded statement "the documented deployment procedure requires no prerequisites". Gate 17 "prerequisites" is satisfied by re-running the cleanliness checks after JARVIS is installed: still no Python, Node, Git or build tools on the machine. Python 3.12 x64 (the known baseline) is the bundled interpreter; the 3.11 path is not used. |
| D2 | §6(a) media | The owner's existing official ISO `Win11_25H2_English_x64_v2.iso` (8,471,603,200 bytes, in `D:\C-drive-overflow\Users\jonny\Downloads\`), SHA-256 computed and compared with Microsoft's published value for that download; acquisition date not recorded at download time, recorded as a LIMITATION. If the hash is not published or does not match: a fresh download from microsoft.com by the owner, recorded in full. |
| D3 | §6(c) local account | A Microsoft-documented unattended-setup answer file (`autounattend.xml`) on a second read-only ISO, creating one local standard account with no Microsoft account and no network sign-in; the file is recorded verbatim in evidence. This is a supported Windows Setup path, not modified media and not a third-party tool. If Windows 11 Home 25H2 setup refuses it or demands a Microsoft account: STOP `OWNER_DECISION_REQUIRED_FRESH_VM_ACCOUNT` (§6(c)); no bypass scripts. |
| D4 | §6(e) egress and Guest Additions | Guest Additions 7.2.18 from the ISO shipped inside the installed VirtualBox (`C:\Program Files\Oracle\VirtualBox\VBoxGuestAdditions.iso`, hash recorded; version equals the frozen host), installed before FRESH-CLEAN-BASELINE and counted in it. Exactly one egress: a shared folder mapped only to `D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01\`, mounted manually, no automount, no clipboard, no drag-and-drop, no second channel. |
| D5 | FINAL candidate for Gates 17–19 | **1.0.10-915e906516dc** if its regression, zip-install, Gate 18 and Gate 17 rehearsals all pass (docs/release-rehearsal-20261001/README.md §6); otherwise the next build that does. FINAL selection itself remains the owner's separate act. |
| D6 | Gate 17 voice and providers | Local speech recognition checked offline inside the guest with the bundled model and Windows synthetic speech (`check_voice_offline.py`, network blocked by the check); no audio device is added to the VM. No AI-provider keys enter the VM in Stage 6 (providers are owner configuration; §9(a) governs any later supply). |
| D7 | Who runs what | Owner: VirtualBox and everything inside the VM, in the `jarvis-s6-val` session; the manual steps the scripts cannot do (tray "Quit JARVIS completely", Windows restart). Claude Code (owner account): builds the package ISO, prepares and reviews the guest scripts, runs the P0–P5 checkpoints only when the owner authorises each one, and checks every evidence file the guest returns. |
| D8 | Gate 18 backup | **Recommended: the owner's real verified backup**, copied by the owner from `E:` (read-only; hash recorded before and after; E: never written) onto the package ISO, restored inside the guest into a second install folder (the disposable target) with the shipped `switch_over.py`; the VM then holds personal data: its storage never leaves `D:\JARVIS-S6-FRESHVM\` and its disposal is the Gate 20 owner decision. Alternative if the owner prefers no personal data in the VM: a backup made inside the guest from synthetic data (the exact flow rehearsed locally on 2026-10-01). |
| D9 | Gate 19 timing bound | No bound is chosen in advance. The installer reports per-phase seconds (verify, copy, verify copy, stop, switch); the bound for the final evidence is set from the measured values on the VM (58bc2bcf Part 1), and a genuine hang is investigated, never papered over by a larger bound. |

---

## Section C: unchanged and not authorised

- P0–P5, §8 reference values, the owner freeze (§7(f), §7(g)), zero silent retries, no UAC,
  secrets never emitted, no production, no Stage 7: unchanged.
- Both R-C obligations remain mandatory: the protected original and the backup/restore
  source are each preserved and checked.
- This amendment authorises nothing: no `RESUME_STAGE6_FRESH_VM`, no account, VM, download,
  VirtualBox operation, protected-path read, Experiment 5, gate execution, cutover or Stage 7.

## Section D: how to approve

Reply in your own words that you approve amendment v3 (optionally naming any D-item you
changed). Claude Code will then record it as a control record under `governance/` with the
hash of this file, update the route status, and draft the Gate 16R execution prompt for
your separate approval. A `RESUME_STAGE6_FRESH_VM` token is never requested; you issue it
when you are ready.
