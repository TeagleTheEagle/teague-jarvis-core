@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "D:\JARVIS-STAGE6-LIVE\qualification-harness-v1-20260924"
set "TEMP=D:\JARVIS-STAGE6-LIVE\qualification-harness-v1-20260924\temp"
set "TMP=D:\JARVIS-STAGE6-LIVE\qualification-harness-v1-20260924\temp"
cl /nologo /c /EHsc /std:c++17 /O2 /GL- /FAs /FaA.asm /FoA.obj /DUNICODE /D_UNICODE A\arm.cpp
if errorlevel 1 exit /b %errorlevel%
cl /nologo /c /EHsc /std:c++17 /O2 /GL- /FAs /FaB.asm /FoB.obj /DUNICODE /D_UNICODE B\arm.cpp
if errorlevel 1 exit /b %errorlevel%
cl /nologo /c /EHsc /std:c++17 /O2 /GL- /FAs /FaC.asm /FoC.obj /DUNICODE /D_UNICODE C\arm.cpp
if errorlevel 1 exit /b %errorlevel%
cl /nologo /c /EHsc /std:c++17 /O2 /GL- /FAs /Famain.asm /Fomain.obj /DUNICODE /D_UNICODE main.cpp
if errorlevel 1 exit /b %errorlevel%
link /nologo /OUT:J6FinalQualification.exe /MAP:qualification.map /OPT:NOICF A.obj B.obj C.obj main.obj advapi32.lib tdh.lib
exit /b %errorlevel%