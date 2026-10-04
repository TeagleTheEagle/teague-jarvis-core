@echo off
rem Gate 16R step 8, run 4: run in the OWNER's own session (jonny), normal non-admin window, once. Builds the fourth
rem tools disc JARVIS-TOOLS-v4.iso. Its guest check script no longer mistakes things named after the VM's Windows
rem account (jarvis-s6-guest) or computer name (JARVIS-S6-FRESH) for JARVIS itself; otherwise it is the run-3 check.
rem Earlier discs are left unchanged. Takes under a minute.
if /i not "%USERNAME%"=="jonny" (echo This step runs in the owner account, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-ToolsDisc.ps1" -Version 4 -Reason "Step 8 run 3 (gate17-20261004-015834) reported FAIL on the pipe VBoxTrayIPC-jarvis-s6-guest, a VirtualBox Guest Additions pipe named after the VM's Windows account: a harness false positive. This version removes the account name and the computer name from names before testing for 'jarvis' and records account-named pipes separately."
if errorlevel 1 (echo. & echo BUILD STOPPED on the error above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Tell Claude "tools v4 done".
pause
