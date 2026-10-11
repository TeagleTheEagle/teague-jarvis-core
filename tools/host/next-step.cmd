@echo off
rem Stage 6 Gates 17 and 19: the one launcher. Double-click it in whichever account you are in (jonny or
rem jarvis-s6-val). It works out what is next from the records, runs it when it belongs to this account, and
rem otherwise says where the next step is. It never skips ahead and never repeats a step that failed.
rem If a UAC (administrator) prompt appears at any time: click No and tell Claude "UAC".
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-NextStep.ps1"
if errorlevel 1 (echo. & echo NEXT-STEP STOPPED on the message above. Photograph this window for Claude. & pause & exit /b 1)
echo.
pause
