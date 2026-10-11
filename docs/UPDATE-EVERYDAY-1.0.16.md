# Updating your everyday JARVIS to 1.0.16

Status: **APPROVED BY THE OWNER 2026-10-06** ("I approve the update of my everyday JARVIS to 1.0.16", first clock
reading 2026-10-06T09:11:04Z; record `../governance/UPDATE-1.0.16-APPROVAL-RECORD.json`, repo copy
`docs/update-1.0.16-evidence/`; the launcher placed in `D:\JARVIS-update-1.0.16\tools\` with `update-authorized.json`).
Rehearsed in a sandbox: see "This launcher, rehearsed" below. Updating the everyday JARVIS is your decision (`CLAUDE.md`). 1.0.16
passed its Stage 7 check in the test VM on 2026-10-06 (`STAGE_7_COMPLETE`, 27 of 27 checks,
`docs/stage7-1.0.16-evidence/`).

## In plain words

Your everyday JARVIS (1.0.15, installed at `%LOCALAPPDATA%\JARVIS` since 2026-10-06 midday) gets the new program
version 1.0.16, "the phone release". Your memories, conversations, personality, preferences and keys stay exactly
where they are: an update only adds the new program beside the old one and switches to it. 1.0.15 stays installed
beside it, so going back is one step. Before anything changes, a fresh backup of your data is made and tested.

## What 1.0.16 brings

The 1.0.16 entry of `release-notes.json`, in short:

- **The PC side of the iPhone app** (`docs/PHONE-PLAN.md`): a new switch in Settings > Devices, **Private network,
  off until you turn it on**. With it on, and Tailscale running and signed in on this PC, JARVIS opens a second door
  at this PC's Tailscale address (port 8790 unless you change it) for paired devices only; through it only the device
  routes are served, each request with the device's own key. JARVIS itself still listens on this PC's own address as
  before. Until you turn the switch on, nothing is open and nothing changes.
- **Pairing limits:** wrong codes and wrong keys are counted per caller; a caller that tries too many is locked out
  for fifteen minutes while your pairing keeps waiting for the right device.
- **What a paired device may do:** read its own conversations, the PC's health as the dashboard shows it, an
  overview of open tasks, projects and the next day's reminders; wait for an answer instead of asking every tenth
  of a second; a recording from a device is refused while the emergency stop holds. A tick per device, **May save
  memories and tasks**, off for every new device, lets your own phone save a memory, note, task or timer under the
  same switches as the PC.
- **Music from your own files** (Settings > Music): MP3 files in the music folder JARVIS shows you, a nickname per
  song, "Jarvis, play ..."; pause, resume, volume, "what is playing"; answered by JARVIS itself, played on this PC's
  speakers whether the window is open or not; its own switch in Settings > Permissions; the emergency stop stops
  the music too.
- **The Qwen cloned voice speaks:** Alibaba hands the finished sound out as a plain http link on its own file
  server, which JARVIS refused until now; it is now fetched over https from that same Alibaba server. Your voice ID
  is already in your key file; after the update you choose Qwen under Settings > Voice > VOICE PREVIEW if you want it.

## Two things only you can check before approving

1. **Your key file** needs no change for 1.0.16: `JARVIS_PROVIDER` stays openai or qwen as for 1.0.15; the Qwen voice
   uses the `QWEN_TTS_VOICE` line you already have. I never read or edit the key file.
2. **Space on C:.** 15.7 GB free today; 1.0.16 adds about 1.2 GB; the launcher refuses below 4 GB free. After the
   update four releases are installed (1.0.11, 1.0.14, 1.0.15, 1.0.16). Removing 1.0.11 and 1.0.14 later is a separate
   step on your word and frees about 2.4 GB.

## What is proven first

- On this PC: the build compared with 1.0.15 (the same pinned parts; 14 changed and 4 added source files, exactly
  the work since 1.0.15), its full test suite with its own Python and Electron (664 Python with 1 skipped as always,
  52 desktop, 18 Intelligence, 24 interface scripts), the zip install (70 s), and the whole Stage 7 pass in a
  sandbox (`docs/release-rehearsal-20261006-1016/README.md`: install 27.6 s, update while running, rollback, update
  again, an update killed mid-copy then rerun, all passed).
- In the test VM (`docs/stage7-1.0.16-evidence/stage7-evaluation.json`): the Stage 7 check passed (install, restart
  with automatic start, uninstall and reinstall, update from 1.0.15 while running, rollback, update again, an update
  killed mid-copy then rerun; 27 of 27 checks; update 334 s, rollback 95 s, update again 192 s, update after the
  interruption 223 s, stopping JARVIS at most 5 s). The first install in that VM took 646 s, above the 600-second
  bound, which the records show to be the VM's disk (the same files copied three times faster later in the same
  pass, and in 28 s on this PC): a VM limitation under your rule of 2026-10-06, and it does not bear on this update,
  whose timings on the real PC are quoted below.
- **Your data and a rollback.** 1.0.16 adds one table to the same database (`music`: your nicknames), one column to
  the devices table (the per-device tick; an older database gets it), and keeps the Private network switch's state
  in the `control` table beside the emergency stop; it creates the folder `config\music` (empty) beside your key
  file. Every table 1.0.15 uses is unchanged. If you ever roll back, 1.0.15 runs on the same data and leaves the new
  table and column alone: the VM's rollback step did exactly that with both test memories present. What 1.0.15 does
  not know it does not enforce: the switch (the door stays closed), the tick (devices only read), the music commands;
  and its Qwen voice does not speak (said in the release notes).
- **The personality text** shipped with 1.0.16 is the same as 1.0.15's; nothing of yours is touched.
- **This launcher, rehearsed** (`docs/release-rehearsal-20261006-1016/rehearse-everyday-update-1016.ps1`, records in
  `update-rehearsal/`, 2026-10-06 20:06-20:09 local): 1.0.15 installed into a sandbox folder on D: and started once;
  refused without approval; refused while JARVIS was running; step 1 PASS (package hash equal, 1.0.15 verified,
  unpack 18 s); step 2 PASS (backup made with 1.0.15's own backup code, 174 files, verified, test restore passed,
  copy on D: hash-checked, program still verifies); step 3 PASS (update 28.5 s: verify package 8.1 s, copy 11.0 s,
  verify copy 7.8 s, stop 0.7 s, switch 0.7 s; verified; database file byte-for-byte unchanged; shortcuts kept; JARVIS
  not started); 1.0.16 started on the same data; a rerun changed nothing; rollback (only with its approval file) PASS,
  1.0.15 verified (7.4 s); a rerun after the rollback changed nothing; **13 of 13 checks**. Your real JARVIS was not
  running at the time (0 processes before and after) and was never addressed; no sandbox process was left.
- **Not rehearsable by me:** your real data (the sandbox database was new; the same backup code made and test-restored
  your real data at Gate 18, the switch-over and the 1.0.14 and 1.0.15 updates, every count equal), your real install
  folder, and your real restart.
- **The launcher** is the 1.0.15 launcher (itself the 1.0.14 one) copied unchanged except its folder and the plan it
  names (`tools/host/update-1.0.16/`; the 1.0.14 and 1.0.15 files stay as their approvals recorded them). sha256:
  `Invoke-EverydayUpdate.ps1` `1abb0be581ee425dcbfdbbae4835511158a8950d96fbb5ae83a0d3626532b20a`, `update-step.cmd`
  `9c469bd44002e59066f5b8e7e2b077173826780840b37e7f4151e99be86d3388` (identical to 1.0.14's and 1.0.15's); the 1.0.16
  package zip sha256 `58bba7423cf0668ff7684e9370865b9951e473eb1e0818c9437bf4287032d23a`.

## The steps

You double-click one launcher, `D:\JARVIS-update-1.0.16\tools\update-step.cmd`, once per step, in your own account
(jonny), with JARVIS **quit** (right-click its icon near the clock > Quit JARVIS completely). Each step writes a
record and stops; you tell me "step N done" and I check the record before the next. No administrator rights; a UAC
prompt is a STOP. Nothing is deleted anywhere.

| # | Who | What happens | Undo |
|---|---|---|---|
| 1 | Launcher | Checks: the 1.0.16 package against its hash; your JARVIS is 1.0.15 and every program file verifies; JARVIS is not running; 4 GB free on C:. Unpacks the package to `D:\JARVIS-update-1.0.16\package`. Changes nothing in your JARVIS. | nothing changed |
| 2 | Launcher | A fresh backup of your JARVIS with its own backup code (the same as Settings > Backups: "Create verified backup", then "Test restore"); the backup lands in `%LOCALAPPDATA%\JARVIS\data-backups` and a hash-checked copy in `D:\JARVIS-update-1.0.16\backup`. The program still verifies afterwards. | nothing changed |
| 3 | Launcher | The 1.0.16 installer adds 1.0.16 beside 1.0.15, checks every file, and switches your JARVIS to it in one step. Data, settings, keys, profile and shortcuts are not touched (the record proves the database file is byte-for-byte the same before and after). JARVIS is not started. | step R |
| 4 | You | Start JARVIS from its Desktop icon and check (list below). | |
| 5 | You | Restart the PC once (Start > Power > Restart, jonny) and check JARVIS starts by itself after you sign in (for 1.0.15 it did, 5.4 minutes after sign-in). | |
| R | Launcher, **only on your word** | If anything is wrong in step 4 or 5: tell me; I record your word and one more double-click switches your JARVIS back to 1.0.15 (still installed). | update again later |

**Your check in step 4** (10 minutes): Settings > About shows `Version 1.0.16-fccde24e2cc6 (installed)`; your
memories and recent conversations are there; ask something and JARVIS answers; say something and voice works;
Settings > Devices shows the **Private network** switch off with a line saying Tailscale is not running (expected:
it is not installed yet); Settings > Music shows the music folder and an empty list; Settings > Voice > VOICE PREVIEW
offers Qwen (choose it if you want the cloned voice; it should speak the preview); then quit from the icon near the
clock: no "Core stopped" box.

## Records

`D:\JARVIS-update-1.0.16\evidence\` (check.json, backup.json, update.json, rollback.json if used); I copy them to
`docs/update-1.0.16-evidence/` with a manifest. The records hold hashes, counts per database table and timings, never
your messages or keys. I never read your key file or the contents of the backup.

## What you accept by approving

1. **The update runs on your real JARVIS** (owner-only), started by you, one step at a time.
2. **Keys and provider stay as they are.** Nothing about keys changes.
3. **The Private network switch stays off** until you turn it on yourself after Tailscale is set up
   (`docs/PHONE-TAILSCALE-STEPS.md`); I never turn it on.
4. **A rollback to 1.0.15 keeps your data** (paired devices and nicknames included) but 1.0.15 knows neither the
   switch, the tick nor the music commands, and its Qwen voice does not speak.
5. **Known limits that remain:** install under a non-administrator Windows account is untested (your account is an
   administrator; the update itself needs no administrator rights); a program JARVIS opened should be closed before
   an update; the private-network door, a paired phone and music through speakers were tested with stand-ins in the
   suites and once on this PC, not in the VM (no network, phone or audio device there).
6. **Space:** about 1.2 GB more on C:; 1.0.15 stays as the rollback copy, 1.0.14 and 1.0.11 stay until you say
   otherwise.

## After the update

Tailscale on the PC and the phone and the switch on, then the pairing (steps 6 and 8 of the phone plan,
`docs/PHONE-TAILSCALE-STEPS.md`); the look of the iPhone app on the Mac if not done; then release 1.0.17, JARVIS as
his own app (`docs/OWN-APP-PLAN.md`, approved).

## Approval

Reply in your own words, for example: "I approve the update of my everyday JARVIS to 1.0.16". I then record it, put
the launcher in `D:\JARVIS-update-1.0.16\tools\` with its hashes and `update-authorized.json`, and you start with
step 1.
