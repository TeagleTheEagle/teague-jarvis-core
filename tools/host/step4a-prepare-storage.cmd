@echo off
rem Gate 16R step 4a: run in the OWNER's own session (jonny), normal non-admin window.
rem Creates vbox-home, machines and media under D:\JARVIS-S6-FRESHVM (new folders only), copies the four discs
rem into media and verifies their hashes. Takes a few minutes (the Windows image is 8.4 GB).
if /i not "%USERNAME%"=="jonny" (echo This step runs in the owner account, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-Stage6Storage.ps1"
echo.
echo Finished. Next: in the jarvis-s6-val session, run step4b-set-vbox-home.cmd
pause
