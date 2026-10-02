@echo off
rem Gate 16R step 6b: run in the jarvis-s6-val session (double-click), before the VM is ever started.
rem Turns the VM's audio adapter off: the approved spec says "no audio device", and the creation script left an
rem enabled adapter with the Null driver. Re-records the VM settings and the .vbox hash into the evidence folder.
if /i not "%USERNAME%"=="jarvis-s6-val" (echo This step runs in the jarvis-s6-val session, not %USERNAME%. & pause & exit /b 1)
if /i not "%VBOX_USER_HOME%"=="D:\JARVIS-S6-FRESHVM\vbox-home" (echo VBOX_USER_HOME is not set in this window. Close it, open a NEW File Explorer window, try again. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Disable-FreshVmAudio.ps1"
if errorlevel 1 (echo. & echo STEP 6b STOPPED on the error above. Do not retry. Photograph this window for Claude. & pause & exit /b 1)
echo.
echo Finished OK. Photograph this window, then tell Claude "6b done". Do not start the VM yet.
pause
