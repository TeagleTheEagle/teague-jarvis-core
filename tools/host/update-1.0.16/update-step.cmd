@echo off
rem Update of your everyday JARVIS: double-click this file in your own account (jonny), once per step. It does the
rem next step, writes a record and tells you what to do next. It does nothing until Claude has recorded your
rem approval of the update plan. If a UAC (administrator) prompt appears at any time: click No and tell Claude "UAC".
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-EverydayUpdate.ps1"
echo.
pause
