# JARVIS as his own app: release 1.0.17 (proposal for your approval)

Status: **APPROVED BY THE OWNER 2026-10-06** ("I approve the own app plan can we make the app icon this image as well
as the app icon for the ios app", then the exact wording "I approve the own-app plan"; first clock reading
2026-10-06T08:23:24Z; record `../governance/OWN-APP-PLAN-APPROVAL-RECORD.json`, repo copy `docs/own-app-evidence/`).
Decisions D1 Inno Setup (installed by the owner), D2 yes, D3 later, D4 no, D6 dropped, as recommended; **D5 changed by
the owner: the icon is the Teague Industries badge the owner supplied** (`static/assets/branding/teague/
teague-industries-badge.png`, sha256 2e64494c…), from which `desktop/jarvis.ico`, `desktop/tray.png` and
`phone/ios/AppIcon-1024.png` were made the same day (section 3.1). Nothing else of it is built: the building starts
after 1.0.16 is the everyday JARVIS and the phone is paired (the approved `docs/PHONE-PLAN.md` steps 4 to 8); it does
not touch 1.0.16. Written on the owner's "write the own-app plan".

What you said: "when can we make jarvis been his own app, launched by himself not electron" and "so how can we make
jarvis his own app". The `docs/CAPABILITY-PLAN.md` section 5 proposal of `JARVIS-Setup.exe` ("a download app not a
short cut", asked for twice) is folded into this release; `docs/PHONE-PLAN.md` decision D6 put it after the phone.

## 1. What is wrong today

- The Desktop and Startup shortcuts start **PowerShell**, which runs a hidden script (`JARVIS.ps1`), which starts a bare
  **`electron.exe`** from the current release folder. Task Manager says "Electron"; the shortcuts carry the PowerShell
  icon; the window has Electron's default icon; a double-click on the program file itself opens Electron's welcome
  window, not JARVIS.
- The tray icon file the desktop code points at (`desktop/tray.png`) does not exist in the repo, so the icon near the
  clock carries no JARVIS mark.
- Installing JARVIS means unpacking a zip and double-clicking `install.cmd` inside it; there is no entry in Windows
  Settings > Apps > Installed apps.

## 2. What you get

| Today | After 1.0.17 |
|---|---|
| Shortcut > PowerShell > electron.exe | Shortcut > `JARVIS.exe`, nothing in between |
| "Electron" in Task Manager, the PowerShell icon on the shortcut, Electron's icon on the window | "JARVIS" with the JARVIS mark everywhere: Task Manager, taskbar, window, shortcuts, tray, notifications |
| Double-click on the program file opens Electron's welcome window | Double-click on `JARVIS.exe` opens JARVIS |
| A zip and `install.cmd` | `JARVIS-Setup-1.0.17-<commit>.exe`: one file, double-click, Next, done; the same file installs, updates and reinstalls |
| No entry in Installed apps | An entry "JARVIS 1.0.17, Teague Industries" with Uninstall (data kept) |
| Starts by itself at sign-in (Startup shortcut) | The same, through `JARVIS.exe` |

What stays exactly as it is: the Core in Python; one JARVIS, one memory; your data, config and profile folders; the
rollback copies of earlier releases; the zip package (still built and still the artefact the Stage 7 check and the
everyday update use); the Stage 7 way of checking a release; the update of your everyday JARVIS on your word.

## 3. How it is built

### 3.1 JARVIS.exe

Electron's program file is a plain `electron.exe` with Electron's icon and name stamped into it. The release build
(`tools/build_release.py`) copies it as `release\electron\JARVIS.exe` and stamps it with the JARVIS icon and the
program's name, description, company and version (the stamping tool is `rcedit`, published by the Electron team on the
npm registry; installed project-locally into `desktop/node_modules`, nothing system-wide). `electron.exe` is not
shipped any more (one program file). The source `electron.exe` is still verified against its recorded hash before it is
copied (as today), and the stamped `JARVIS.exe` gets its own hash in the release manifest like every other file.

Beside it, `release\electron\resources\app\` holds a four-line bootstrap (`package.json` and `main.cjs`) that loads
the desktop app from `release\app\desktop\`. Electron starts that bootstrap whenever `JARVIS.exe` is started with no
arguments, so a double-click on `JARVIS.exe` opens JARVIS, never Electron's welcome window.

The icon (decision D5, decided by the owner on approval): the Teague Industries badge the owner supplied, kept byte for
byte at `static/assets/branding/teague/teague-industries-badge.png`. Made from it on 2026-10-06 with Pillow and
checked into the repo: `desktop/jarvis.ico` (256 and 128 px the whole badge; 64, 48, 32, 24 and 16 px the chrome T
centred on the badge's dark ground, because the lettering cannot be read at those sizes), `desktop/tray.png` (32 px,
the chrome T) and `phone/ios/AppIcon-1024.png` (the whole badge, 1024 px, no transparency, for Xcode's Assets >
AppIcon). The owner may swap any of them for other renderings of the same badge.

### 3.2 The app knows where it lives

Today `JARVIS.ps1` tells Electron which release is current and where the data, config and models folders are
(environment variables). After 1.0.17 the desktop app works that out itself when it runs from an installation
(`<home>\releases\<id>\electron\JARVIS.exe`: the home is three folders up, exactly the rule `runtime_paths.install_home`
already uses on the Core side) and sets the same values before starting the Core. In development (the repo) nothing
changes. `JARVIS.ps1` is no longer written (decision D6).

**Stale starts.** After an update the current release lives in a new folder; the installer rewrites the shortcuts, but
a taskbar pin or a Windows "recent" entry may still point at the old `JARVIS.exe` (kept as the rollback copy). So every
`JARVIS.exe` reads `current.json` at start: if it is not the current release and the current one exists, it starts
the current release's `JARVIS.exe` with the same arguments and quits. A second start of the current release still just
brings the running JARVIS forward (unchanged single-instance rule).

### 3.3 Shortcuts

The installer's Desktop and Startup shortcuts point straight at the current release's `JARVIS.exe` with its icon; the
Startup one carries `--login-launch` as today. They are rewritten on install and update (as today) and now also on
rollback (new: today rollback need not touch them because `JARVIS.ps1` never moved).

### 3.4 JARVIS-Setup.exe

One file, `JARVIS-Setup-<version>-<commit>.exe` (about 500 MB, the whole release inside, compressed), built on this PC
from a script kept in the repo (`tools/setup/`). It:

1. installs **per user, without administrator rights** (the same `%LOCALAPPDATA%\JARVIS` home as today; a UAC prompt
   would be a defect);
2. unpacks the package into `%LOCALAPPDATA%\JARVIS-package` (the same staging the Stage 7 check and the everyday
   update use today) and runs the package's own installer (`installer.py`), so install, update, reinstall and the
   rollback copy behave exactly as the Stage 7 check has proven them: nothing of the install engine changes;
3. shows the result and offers to start JARVIS;
4. registers the entry in Settings > Apps > Installed apps (decision D2); its Uninstall runs the package's installer
   with `uninstall` (program removed, data kept, as today) and then removes the package folder;
5. runs silently with a switch for the Stage 7 check and for rehearsals, with a parameter for a sandbox home (as
   `--home` today).

**The tool that makes it (decision D1):** Inno Setup (free, the standard Windows installer maker; per-user installs,
silent mode, the Installed-apps entry, large files). It is a system-wide install, so **you install it once** on this PC
(about two minutes; I never install system-wide). The alternative that needs no install, a self-extracting stub made
with PyInstaller from PyPI, is known for antivirus and SmartScreen false alarms on the result; not recommended.

**Signing (decision D3):** the first Setup.exe is unsigned. On this PC a file you built yourself shows no warning. A
copy downloaded on another PC shows Windows' "unknown publisher" warning until it is signed; signing needs a
code-signing certificate in your name (a yearly cost, identity checks, nowadays a hardware key or a cloud signing
service). Priced and set up only when you decide to put the file online; nothing in this release depends on it.

### 3.5 Updates and rollback

Running a newer Setup.exe over an installed JARVIS performs the update (the previous release kept, data untouched),
the same engine as today. Rollback stays what it is today (the installer's `rollback` command; a button in Settings is
not in this release). The interrupted-update safety is unchanged and checked again in Stage 7.

### 3.6 The checks learn the new shape

- **Unit tests** for the new pieces: the stamped file in the build, the bootstrap, the "where do I live" rule, the
  stale-start redirect, the shortcut targets, the Installed-apps entry written and removed.
- **Release regression** (`tools/release_regression.py`): it runs the Electron tests with the release's own Electron;
  it learns the name `JARVIS.exe`. Same suites, same counts.
- **Zip install rehearsal and a Setup.exe rehearsal** into a sandbox home on D:.
- **Stage 7 version 4 scripts** (copies of version 3, the version 3 files untouched as their approvals recorded them):
  the Install phase installs from `JARVIS-Setup-<id>.exe` silently instead of `install.cmd` and checks the
  Installed-apps entry; the launch is still the Desktop shortcut (the fallback without shortcuts starts `JARVIS.exe`
  directly); the uninstall checks the entry is gone; the update, rollback, update-again and interrupted-update phases
  run on the package's installer exactly as today, plus one update through the Setup.exe to prove that path. The disc
  carries the Setup.exe and the zip. Sandbox rehearsal first, decision tests, then your VM check on a new approval.
- **Everyday update:** on your approval, as for 1.0.15 and 1.0.16, from the Setup.exe this time.

## 4. What stays outside this release

- A native shell instead of Electron: not proposed. The tray, screen capture, hotkeys, floating JARVIS, microphone
  and Core watching are desktop code that has passed Stage 7 in Electron; after this release the difference is
  invisible, and a rewrite is months plus a fresh acceptance.
- A faster start at sign-in (decision D4): Windows itself delays Startup-folder programs (5 to 6 minutes seen on this
  PC). A logon task would start him within seconds, but it is a system change and a separate decision; the Startup
  shortcut stays in this release.
- A rollback button in Settings; signing; putting the file online. Each on your word later.

## 5. Decisions for you

| | Decision | Recommended |
|---|---|---|
| D1 | The installer maker: Inno Setup (you install it once, system-wide) or a PyInstaller stub (no install, false alarms likely) | Inno Setup |
| D2 | An entry in Settings > Apps > Installed apps with Uninstall (data kept) | yes |
| D3 | Signing the Setup.exe now (certificate in your name, yearly cost) or later | later, when the file goes online |
| D4 | A faster start at sign-in (logon task; a system change) in this release | no, a separate decision |
| D5 | The icon: made from the JARVIS mark, or an icon file from you | **decided: the Teague Industries badge the owner supplied** |
| D6 | `JARVIS.ps1` dropped (one way to start him) | dropped |

Names shown by Windows: product "JARVIS", company "Teague Industries", version 1.0.17. Say if you want other words.

## 6. Order of work and size

1. You: 1.0.16 lands (the VM check, the everyday update), Tailscale and the pairing, the phone's section 10 checks.
2. You: approve this plan (section 9); install Inno Setup (D1); answer D2 to D6 or accept the recommendations.
3. Claude, about two sessions: JARVIS.exe and the icon in the build; the app's "where do I live" rule and the stale-start
   redirect; shortcuts; the Setup script and the Installed-apps entry; the version 4 Stage 7 scripts; tests; one
   independent review per item; build 1.0.17; comparison with 1.0.16; release regression; zip and Setup rehearsals;
   sandbox Stage 7; the Stage 7 check plan for your approval.
4. You: the Stage 7 check of 1.0.17 in the VM (your day, about 90 minutes), then the everyday update, each on its own
   approval as always.

## 7. Risks and limits, stated plainly

- Unsigned Setup.exe: "unknown publisher" on other PCs until signed (D3). No effect on this PC.
- The Setup.exe is about 500 MB because the release carries its own Python, Electron and models (offline install, no
  hidden dependency on this PC, the Stage 6 rule). Same as the zip today.
- Inno Setup is a system-wide install on the build PC (your act). The built Setup.exe needs nothing installed on the
  target PC.
- The stale-start redirect costs one or two seconds when an old pin is used once; the pin is then best re-made.
- Two programs may show in Task Manager while JARVIS runs: `JARVIS.exe` (the window) and `python.exe` (the Core).
  Naming the Core's process is possible but not in this release.
- Old 1.0.16 shortcuts are replaced by the update, as every update does today.

## 8. Rules kept

One writer; every item independently reviewed; nothing claimed that was not seen or tested; the live installation,
VirtualBox, system-wide installs, registry, signing certificates, uploads: yours. The Setup.exe's Installed-apps entry
is written by the installer the owner runs, on the owner's PC, as part of the approved product; Claude writes no
registry entry on this PC outside a sandbox test that cleans up after itself.

## 9. Approval

If you approve, type exactly:

```
I approve the own-app plan
```

With any changes to the decisions in the same message (for example "I approve the own-app plan, D4 yes"). I record it
in `../governance/` with this file's hash, and the building starts after 1.0.16 and the phone are done.
