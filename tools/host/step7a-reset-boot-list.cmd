@echo off
rem Gate 16R step 7 recovery: run in the jarvis-s6-val session (double-click) with the VM POWERED OFF
rem (VM window: Machine > Close > Power off the machine). Resets the VM's firmware boot list so the Windows disc is
rem tried first again (the first Setup attempt had put the half-installed disk ahead of it) and re-enrols the
rem Secure Boot keys as at creation. Then run step7-start-vm-from-disc.cmd.
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
if /i not "%VBOX_USER_HOME%"=="D:\JARVIS-S6-FRESHVM\vbox-home" (echo VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window, try again. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Reset-FreshVmNvram.ps1"
if errorlevel 1 (echo. & echo STEP 7a STOPPED on the message above. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Now double-click step7-start-vm-from-disc.cmd.
pause
