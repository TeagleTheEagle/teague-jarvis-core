@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul
if errorlevel 1 exit /b %errorlevel%
cd /d "C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-authority-independent-20260925"
cl /nologo /std:c++17 /Zs /W4 configuration-proof.cpp
if errorlevel 1 exit /b %errorlevel%
cl /nologo /std:c++17 /EHsc /Zs /W4 candidate\authority_trace_v3.cpp
exit /b %errorlevel%
