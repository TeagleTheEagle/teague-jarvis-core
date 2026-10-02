@echo off
rem Gate 16R step 8 rerun: run in the OWNER's own session (jonny), normal non-admin window, once. Builds the second
rem tools disc JARVIS-TOOLS-v2.iso (corrected guest check script), hash-verified, and copies it with its hash record
rem into D:\JARVIS-S6-FRESHVM\media. The first tools disc is left unchanged. Takes under a minute.
if /i not "%USERNAME%"=="jonny" (echo This step runs in the owner account, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-ToolsDiscV2.ps1"
if errorlevel 1 (echo. & echo BUILD STOPPED on the error above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Tell Claude "tools v2 done".
pause
