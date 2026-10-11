@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 > "C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-prospective-pair-20260926\environment-setup.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
"C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B "C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-prospective-pair-20260926\prepare_pair.py" env
