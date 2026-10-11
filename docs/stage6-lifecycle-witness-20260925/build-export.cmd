@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul
if errorlevel 1 exit /b %errorlevel%
cd /d "C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-lifecycle-witness-20260925\candidate"
cl /nologo /std:c++17 /EHsc /O2 witness_export_offline.cpp /Fe:"C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-lifecycle-witness-20260925\export-offline\WitnessExportOffline.exe" /link bcrypt.lib
