# Release 1.0.17: build and checks on this PC (2026-10-07)

Owner, 2026-10-07: "take the handoff ... continue with 1.0.17's release work in the order the status doc gives". This
folder is the record of the checks of release 1.0.17 ("JARVIS as his own app", `docs/OWN-APP-PLAN.md`, with the access
items of `docs/PHONE-ACCESS-PLAN.md`, the three phone-check fixes, the music stop fix and the start-up song). The
owner's installed JARVIS (`%LOCALAPPDATA%\JARVIS`, 1.0.16, running with 8 processes throughout) was never addressed:
every rehearsal counts processes by their program folder and stops only those from its own sandbox folder, and from
today every Setup rehearsal records the owner's real Desktop and Startup shortcuts before and after. The check in the
test VM (Stage 7) is a separate owner-approved step: `docs/STAGE7-CHECK-1.0.17.md`.

## Earlier in this folder (2026-10-07, 01:00 to 06:30)

- `own-app-rehearsal-09fed5f.json`, `rehearse-own-app.ps1`: items 3.1 to 3.3 rehearsed on the rehearsal build
  `1.0.17-09fed5f54c31` (five steps, all as expected; `docs/OWN-APP-1.0.17.md` section 1).
- `setup-rehearsal-09fed5f.json`, `rehearse-setup.ps1`, `JARVIS-Setup-1.0.17-09fed5f54c31.setup.json`: the first
  Setup rehearsal, **superseded**: it passed every step it checked and still wrote and then removed the owner's real
  shortcuts (`INCIDENT-real-shortcuts-20261007.md`; `docs/OWN-APP-1.0.17.md` section 6). That Setup carries the old
  script and must not be run again on this PC.
- `test-stage7-step-v4.output.json`, `test-stage7-pass-v4.output.json`: the version 4 Stage 7 tools' decision tests
  (19 launcher cases, 21 driver cases, all pass; `docs/STAGE7-DRIVER-V4.md`).

## The rehearsal build `1.0.17-b848d70e784d` and the Setup rehearsal, version 2 (13:05 to 13:15)

Made from commit b848d70 (the version 4 scripts, the review of item 3.4 applied, the music items) to prove the fixed
Setup against the real shortcut folders **before** the real build. Not a release: no zip, never offered.

- `JARVIS-1.0.17-b848d70e784d.release.json`: 10,768 files, 1,186,122,121 bytes, built in
  `D:\JARVIS-release-work\own-app-rehearsal`.
- `JARVIS-Setup-1.0.17-b848d70e784d.setup.json`: the Setup built by `tools/setup/build_setup.py` with Inno Setup
  6.7.3 in 130.9 s: 406,946,014 bytes, sha256 `6d378884…`; the record carries both application ids (`app_id`
  `{DC2C8033-…}` for the real JARVIS, `sandbox_app_id` `{7A3F1C52-…}` for a run with `/HOME`).
- `setup-rehearsal-v2-b848d70.json` (`rehearse-setup-v2.ps1`): **PASS, 13:11 to 13:15.** The owner's real Desktop and
  Startup `JARVIS.lnk` carry the same sha256 before, after every step and at the end (desktop `1829581c…`, startup
  `0be9b25f…`: the 1.0.16 launcher values as restored at 06:10); the live JARVIS had 8 processes before and after;
  no Installed-apps entry existed before. Steps: the silent install with `/DIR`, `/HOME` and `/NOSHORTCUTS` in
  101.8 s (the installer: verify package 9.6 s, copy 12.2 s, verify copy 25.1 s, switch 0.1 s), the installer's own
  word `withheld (the home is not this PC's own install home)`, the Setup's logged command carrying `--no-shortcuts`,
  the entry **"JARVIS (sandbox)" 1.0.17, Teague Industries** under the sandbox id with the sandbox uninstaller, no
  `JARVIS.ps1`; JARVIS.exe started (the Core up in 60.4 s; `JARVIS.exe` and `python.exe` only) and shut down cleanly;
  the same Setup again as a reinstall in 65.3 s (verified, nothing copied twice, `withheld` again); the uninstall
  through the entry's own uninstaller in 11.8 s: 10,768 program files removed, data, config and profile kept, the
  entry gone, the package folder gone, 0 processes, `withheld` and `--no-shortcuts` in the uninstall's command too.
  (The version 1 record of 01:40 was 7.9 MB because one field carried a PowerShell provider graph; this one is 8 KB.)

## The real build of 1.0.17 and its checks

(Appended as each check completes.)
