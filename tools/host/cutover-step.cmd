@echo off
rem JARVIS switch-over: the one launcher. Double-click it in your own account (jonny), a normal window.
rem It works out the next step from its records and does only that one step. It does nothing until Claude has
rem recorded your approval of the plan. If a UAC (administrator) prompt appears at any time: click No and tell
rem Claude "UAC". Plan: docs\CUTOVER-BLUEPRINT.md in the repo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-Cutover.ps1"
echo.
pause
