@echo off
rem Stage 6 Gate 17 preparation: run in the OWNER's own session (jonny), normal non-admin window. Click ONCE and
rem leave the window open until it says Finished (it copies the 500 MB release, hashes it, images the disc and
rem mounts the result once to verify it; a few minutes). Builds JARVIS-PACKAGE-1.0.11-60d406fb6398.iso under
rem D:\JARVIS-release-work\stage6-media. Building the disc does not make 1.0.11 FINAL.
if /i not "%USERNAME%"=="jonny" (echo This step runs in the owner account, not %USERNAME%. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-Gate17PackageDisc.ps1"
if errorlevel 1 (echo. & echo BUILD STOPPED on the error above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Tell Claude "disc done".
pause
