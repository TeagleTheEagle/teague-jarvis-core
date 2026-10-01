@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "D:\JARVIS-STAGE6-LIVE\d45028a56e344926a311c04ba01f6a80\code"
cl /nologo /EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE authority_trace_v3.cpp /Fe:J6AuthorityTraceV3.exe /Fo:authority_trace_v3.obj advapi32.lib tdh.lib ole32.lib bcrypt.lib
if errorlevel 1 exit /b %errorlevel%
cl /nologo /EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE native_handoff_fixture.cpp /Fe:J6HandoffFixture.exe /Fo:native_handoff_fixture.obj advapi32.lib tdh.lib ole32.lib bcrypt.lib
exit /b %errorlevel%
