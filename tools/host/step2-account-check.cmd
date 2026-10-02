@echo off
rem Gate 16R step 2: run in the jarvis-s6-val session (double-click, or type its path in PowerShell).
rem Runs the 7(b) account check with a normal, non-elevated PowerShell; asks for no password.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-ValidationAccountCheck.ps1" -Evidence "D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\account"
echo.
echo Finished. The result is in D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\account (Claude reads it from the owner session).
pause
