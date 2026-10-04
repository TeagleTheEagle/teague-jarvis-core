@echo off
rem Gate 16R step 8, run 3: run in the OWNER's own session (jonny), normal non-admin window, once. Builds the third
rem tools disc JARVIS-TOOLS-v3.iso. Its guest check script records the full list of the governing text's section 6(f):
rem JARVIS services, scheduled tasks, named pipes and folders, global package folders, default PATH, and the sign-in
rem state, in addition to what run 2 recorded. Earlier discs are left unchanged. Takes under a minute.
if /i not "%USERNAME%"=="jonny" (echo This step runs in the owner account, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-ToolsDisc.ps1" -Version 3 -Reason "Step 8 run 2 passed, but its record did not enumerate every negative of AMENDMENT-v2 section 6(f); this version also records JARVIS services, scheduled tasks, named pipes and folders, global package folders, non-default PATH entries, the account principal source and the OneDrive sign-in state, and the OS caption."
if errorlevel 1 (echo. & echo BUILD STOPPED on the error above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Tell Claude "tools v3 done".
pause
