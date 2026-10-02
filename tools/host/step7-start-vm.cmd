@echo off
rem Gate 16R step 7: run in the jarvis-s6-val session (double-click) ONLY when Claude says step 6 is complete.
rem Starts the acceptance VM JARVIS-S6-FRESH with its window (VBoxManage startvm --type gui); Windows Setup then
rem runs on its own from the answer file disc.
rem If a UAC (administrator) prompt appears on the HOST: click No and tell Claude "UAC".
rem If Windows Setup inside the VM demands a Microsoft account: do not work around it; tell Claude "account".
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
if /i not "%VBOX_USER_HOME%"=="D:\JARVIS-S6-FRESHVM\vbox-home" (echo VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window, try again. & pause & exit /b 1)
"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" startvm JARVIS-S6-FRESH --type gui
if errorlevel 1 (echo. & echo START FAILED. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo The VM window should now be open. Follow Claude's step-7 instructions inside it. You can close this window.
pause
