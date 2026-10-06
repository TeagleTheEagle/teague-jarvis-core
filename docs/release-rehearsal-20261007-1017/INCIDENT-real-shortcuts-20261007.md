# Incident: the Setup rehearsal of 2026-10-07 touched the owner's real shortcuts

The rehearsal recorded in `setup-rehearsal-09fed5f.json` passed every step it checked, but its three installer runs
(`setup-install.log` line 54726 at 01:37:49, `setup-reinstall.log` line 54731 at 01:39:22, `setup-uninstall.log`
line 17 at 01:39:47, all under `D:\JARVIS-release-work\own-app-rehearsal\setup-rehearsal\`) ran `installer.py`
without `--no-shortcuts`: the Setup read its `/NOSHORTCUTS` switch with `{param:}`, which does not see a bare
switch. The install and the reinstall overwrote the owner's real Desktop and Startup `JARVIS.lnk` with links to
the sandbox's `JARVIS.exe`; the uninstall removed them. Found at 06:04 from the owner's screenshot after a
restart (JARVIS had not started at sign-in); the shortcuts were written again at 06:10 with the 1.0.16 launcher
values. The full account and the fixes: `docs/OWN-APP-1.0.17.md` section 6. The JSON records in this folder are
unchanged; the rehearsal itself is superseded and must be run again with the fixed Setup, recording the real
shortcut folders before and after.
