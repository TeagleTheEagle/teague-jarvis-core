@echo off
rem Stage 7 check of a release (version 2): the one launcher on the PC. Double-click it in whichever account you
rem are in (jonny or jarvis-s6-val). It works out what is next from the records, runs it when it belongs to this
rem account, and otherwise says where the next step is. It does nothing until Claude has recorded your approval
rem of this check. If a UAC (administrator) prompt appears at any time: click No and tell Claude "UAC".
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-Stage7Step.ps1"
echo.
pause
