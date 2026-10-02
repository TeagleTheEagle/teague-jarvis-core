@echo off
rem Gate 16R: start the acceptance VM. Run in the jarvis-s6-val session (double-click) for EVERY start of
rem JARVIS-S6-FRESH during Stage 6, first at step 7 and only when Claude says to.
rem Start-FreshVm.ps1 re-applies the "guest cannot reach the host's localhost" setting (VirtualBox 7.2.18 does not
rem keep it in the VM file), confirms it, starts the VM with its window, and records what the running VM received.
rem If a UAC (administrator) prompt appears on the HOST: click No and tell Claude "UAC".
rem If Windows Setup inside the VM demands a Microsoft account: do not work around it; tell Claude "account".
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
if /i not "%VBOX_USER_HOME%"=="D:\JARVIS-S6-FRESHVM\vbox-home" (echo VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window, try again. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-FreshVm.ps1"
if errorlevel 1 (echo. & echo START STOPPED on the message above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo The VM window should now be open. Photograph this window, then follow Claude's instructions inside the VM.
pause
