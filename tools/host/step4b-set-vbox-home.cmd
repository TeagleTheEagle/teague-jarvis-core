@echo off
rem Gate 16R step 4b: run in the jarvis-s6-val session (double-click). Sets VBOX_USER_HOME for THIS account only
rem (user scope, AMENDMENT-v2 7(d)) and re-runs the 7(b) account check so its record shows the variable set.
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
setx VBOX_USER_HOME "D:\JARVIS-S6-FRESHVM\vbox-home" >nul
if errorlevel 1 (echo setx failed & pause & exit /b 1)
set "VBOX_USER_HOME=D:\JARVIS-S6-FRESHVM\vbox-home"
echo VBOX_USER_HOME set for this account to %VBOX_USER_HOME%
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-ValidationAccountCheck.ps1" -Evidence "D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\account"
echo.
echo Finished. Tell Claude "done". (Any VirtualBox window opened later in this account must be opened AFTER this, so it sees the variable.)
pause
