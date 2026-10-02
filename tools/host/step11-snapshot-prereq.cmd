@echo off
rem Gate 16R step 11: run in the jarvis-s6-val session (double-click) ONLY after Claude reports P2 PASS. The VM stays
rem powered off; nothing is installed between the two snapshots (AMENDMENT-v3 D1: the release needs no prerequisites).
rem Takes the snapshot FRESH-PREREQ and records its identity.
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
if /i not "%VBOX_USER_HOME%"=="D:\JARVIS-S6-FRESHVM\vbox-home" (echo VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window, try again. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Take-FreshVmSnapshot.ps1" -Snapshot FRESH-PREREQ -Description "Gate 16R step 11 (AMENDMENT-v3 D1): equals FRESH-CLEAN-BASELINE; the documented deployment procedure requires no prerequisites, so nothing was installed"
if errorlevel 1 (echo. & echo STEP 11 STOPPED on the message above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Tell Claude "step 11 done". Do not start the VM.
pause
