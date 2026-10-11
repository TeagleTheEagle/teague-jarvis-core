@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul
if errorlevel 1 exit /b %errorlevel%
cd /d "C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-authority-independent-20260925\candidate"
cl /nologo /std:c++17 /EHsc /O2 /W4 "authority_trace_v3.cpp" /Fe:"J6AuthorityTraceV3.exe" /link advapi32.lib tdh.lib ole32.lib bcrypt.lib
exit /b %errorlevel%
