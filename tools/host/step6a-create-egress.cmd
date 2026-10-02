@echo off
rem Gate 16R step 6a: run in the OWNER's own session (jonny), normal non-admin window, any time before step 6.
rem Creates the host folder of the VM's single shared folder, D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01
rem (new object only) and grants jarvis-s6-val modify on it. Writes step6-egress-folder.json. Quick.
if /i not "%USERNAME%"=="jonny" (echo This step runs in the owner account, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-GuestEgressFolder.ps1"
if errorlevel 1 (echo. & echo STEP 6a STOPPED on the error above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Tell Claude "6a done".
pause
