@echo off
rem Gate 16R step 4a: run in the OWNER's own session (jonny), normal non-admin window. Double-click it ONCE and
rem leave this window open until it says "Finished OK" (the Windows image is 8.4 GB; allow a few minutes).
rem Creates vbox-home, machines and media under D:\JARVIS-S6-FRESHVM (new folders only), copies the four discs
rem into media and verifies their hashes. Closing the window early leaves a half-made copy behind.
if /i not "%USERNAME%"=="jonny" (echo This step runs in the owner account, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-Stage6Storage.ps1"
if errorlevel 1 (echo. & echo STEP 4a STOPPED on the error above. Nothing more was run. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Photograph this window, then tell Claude "done". (Step 4b runs in the jarvis-s6-val session; if you already ran it, do not repeat it.)
pause
