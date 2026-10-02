@echo off
rem Gate 16R step 3b: run in the jarvis-s6-val session (double-click). Attempts the denied operations on the synthetic
rem fixtures only, the positive control, and the expected-denial listing of the two protected paths. Changes nothing.
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-IsolationCheck.ps1" -Evidence "D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\isolation"
echo.
echo Finished. Next: back in the owner account, run step3c-postflight.cmd
pause
