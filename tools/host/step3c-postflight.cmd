@echo off
rem Gate 16R step 3c: run in the OWNER's own session (jonny). Re-hashes the fixtures and their permissions and writes owner-postflight.json.
if /i not "%USERNAME%"=="jonny" (echo This step runs in the owner account, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-IsolationFixtures.ps1" -Phase Postflight -Evidence "D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\isolation"
echo.
echo Finished. Tell Claude "done"; the results are read from the evidence folder.
pause
