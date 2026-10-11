@echo off
rem Stage 6 Gates 17 and 19 inside the acceptance VM: double-click this file on the package disc (account
rem jarvis-s6-guest, a normal window, never "Run as administrator"). It runs whatever step is next and tells you
rem what to do afterwards. To repeat a step after a reset under the 15-minute rule: open a Command Prompt and type
rem the disc letter, a colon, \gate rerun   (for example  E:\gate rerun).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0guest\Invoke-Gate.ps1" %*
echo.
pause
