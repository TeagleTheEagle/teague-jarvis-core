@echo off
rem Stage 6 Gate 18 inside the acceptance VM: double-click this file on the recovery disc (account jarvis-s6-guest,
rem a normal window, never "Run as administrator"). It restores the backup on this disc into a second, disposable
rem JARVIS install and checks it. It runs once; if it stops, photograph the window for Claude.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-Gate18.ps1"
echo.
pause
