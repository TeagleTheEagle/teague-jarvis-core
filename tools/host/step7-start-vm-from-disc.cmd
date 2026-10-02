@echo off
rem Gate 16R step 7, FIRST INSTALLATION ONLY: run in the jarvis-s6-val session (double-click) with the VM powered off,
rem after step7a-reset-boot-list.cmd. Same as step7-start-vm.cmd (re-applies the localhost setting, starts the VM,
rem records the running VM's log value) and additionally answers the Windows disc's "Press any key" prompt from the
rem host for 25 seconds, so the disc boots without any typing. Do NOT use it once Windows is installed: it would boot
rem the installer again. Use step7-start-vm.cmd for every later start.
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
if /i not "%VBOX_USER_HOME%"=="D:\JARVIS-S6-FRESHVM\vbox-home" (echo VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window, try again. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-FreshVm.ps1" -BootFromDisc
if errorlevel 1 (echo. & echo START STOPPED on the message above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo The VM should now be booting the Windows disc (VirtualBox logo, then the blue Installing screen). Leave it alone.
pause
