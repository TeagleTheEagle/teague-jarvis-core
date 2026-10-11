@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
set "TEMP=D:\JARVIS-STAGE6-LIVE\timestamp-reuse-v1-20260924\build-temp"
set "TMP=D:\JARVIS-STAGE6-LIVE\timestamp-reuse-v1-20260924\build-temp"
cd /d "D:\JARVIS-STAGE6-LIVE\timestamp-reuse-v1-20260924\code"
cl /nologo /EHsc /std:c++17 /O2 /FAs /Fa:fixture.asm /DUNICODE /D_UNICODE loss_measurement_fixture_v3.cpp /Fe:J6Timestampreuse.exe /Fo:fixture.obj advapi32.lib tdh.lib psapi.lib
if errorlevel 1 exit /b %errorlevel%
cd /d "D:\JARVIS-STAGE6-LIVE\timestamp-reuse-v1-20260924\reference"
cl /nologo /EHsc /std:c++17 /O2 /FAs /Fa:fixture.asm /DUNICODE /D_UNICODE loss_measurement_fixture_v3.cpp /Fe:J6Timestampreference.exe /Fo:fixture.obj advapi32.lib tdh.lib psapi.lib
if errorlevel 1 exit /b %errorlevel%
cd /d "D:\JARVIS-STAGE6-LIVE\timestamp-reuse-v1-20260924\code"
cl /nologo /EHsc /std:c++17 /O2 /FAs /Fa:authority_trace_v3.asm /DUNICODE /D_UNICODE authority_trace_v3.cpp /Fe:authority_trace_v3-OFFLINE-NOT-LIVE.exe /Fo:authority_trace_v3.obj advapi32.lib tdh.lib bcrypt.lib ole32.lib
if errorlevel 1 exit /b %errorlevel%
cl /nologo /EHsc /std:c++17 /O2 /FAs /Fa:startup_trace.asm /DUNICODE /D_UNICODE startup_trace.cpp /Fe:startup_trace-OFFLINE-NOT-LIVE.exe /Fo:startup_trace.obj advapi32.lib tdh.lib bcrypt.lib ole32.lib
if errorlevel 1 exit /b %errorlevel%
exit /b 0