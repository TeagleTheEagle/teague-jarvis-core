@echo off
rem Gate 16R step 9: run in the jarvis-s6-val session (double-click) AFTER step 8 passed and AFTER Windows inside the
rem VM was shut down cleanly (Start > Power > Shut down; wait for the VM window to close). Takes the snapshot
rem FRESH-CLEAN-BASELINE and records its identity. Refuses if the VM is still running.
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
if /i not "%VBOX_USER_HOME%"=="D:\JARVIS-S6-FRESHVM\vbox-home" (echo VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window, try again. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Take-FreshVmSnapshot.ps1" -Snapshot FRESH-CLEAN-BASELINE -Description "Gate 16R step 9: clean Windows 11 Home from the answer file, Guest Additions 7.2.18, Windows Update paused, nothing else installed; baseline checks passed in step 8"
if errorlevel 1 (echo. & echo STEP 9 STOPPED on the message above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Tell Claude "step 9 done". Do not start the VM.
pause
