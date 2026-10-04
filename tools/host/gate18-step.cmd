@echo off
rem Stage 6 Gate 18: the one launcher. Double-click it in whichever account you are in (jonny or jarvis-s6-val).
rem It works out what is next from the records, runs it when it belongs to this account, and otherwise says where
rem the next step is. It does nothing until Claude has recorded your RESUME_STAGE6_RECOVERY, and it never touches
rem the backup drive. If a UAC (administrator) prompt appears at any time: click No and tell Claude "UAC".
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-Gate18Step.ps1"
if errorlevel 1 (echo. & echo GATE18-STEP STOPPED on the message above. Photograph this window for Claude. & pause & exit /b 1)
echo.
pause
