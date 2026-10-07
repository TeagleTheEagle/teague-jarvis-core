@echo off
rem Stage 7 inside the acceptance VM (version 4 scripts): double-click this file on the package disc (account jarvis-s6-guest, a
rem normal window, never "Run as administrator"). It runs whatever step is next and tells you what to do
rem afterwards. To repeat a step after a reset under the 15-minute rule: open a Command Prompt and type the disc
rem letter, a colon, \stage7 rerun   (for example  E:\stage7 rerun).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0guest\Invoke-Stage7Pass.ps1" %*
echo.
pause
