@echo off
rem Gate 16R step 6: run in the jarvis-s6-val session (double-click) ONLY after Claude reports P1 PASS.
rem Creates the acceptance VM JARVIS-S6-FRESH with VBoxManage under this account (New-FreshVm.ps1: new VM, new
rem 96 GiB disk in machines\, EFI + Secure Boot + TPM 2.0, NAT only, no clipboard/drag-drop/USB/audio, Windows and
rem UNATTEND discs attached, one shared folder guest-egress-01 not auto-mounted) and writes vm\vm-creation.json.
rem If Windows shows a UAC (administrator) prompt at any point: click No, and tell Claude "UAC". That is a STOP.
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
if /i not "%VBOX_USER_HOME%"=="D:\JARVIS-S6-FRESHVM\vbox-home" (echo VBOX_USER_HOME is not set in this window. Step 4b must have run in this account; close this window and open a NEW one, then try again. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0New-FreshVm.ps1" -Evidence "D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002\vm"
if errorlevel 1 (echo. & echo STEP 6 STOPPED on the error above. Do not retry. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Photograph this window, then tell Claude "done". Do not start the VM yet.
pause
