@echo off
rem Gate 16R step 3a: run in the OWNER's own session (jonny), normal non-admin window.
rem Creates the synthetic isolation fixtures as new objects under D:\JARVIS-S6-FRESHVM\synthetic\isolation-01 and writes owner-preflight.json.
if /i not "%USERNAME%"=="jonny" (echo This step runs in the owner account, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-IsolationFixtures.ps1" -Phase Create -Evidence "D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\isolation"
echo.
echo Finished. Next: in the jarvis-s6-val session, run step3b-isolation-check.cmd
pause
