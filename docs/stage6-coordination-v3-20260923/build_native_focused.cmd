@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code"
cl /nologo /EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE authority_trace_v3.cpp /Fe:J6AuthorityTraceV3.exe /Fo:authority_trace_v3.obj advapi32.lib tdh.lib ole32.lib bcrypt.lib
if errorlevel 1 exit /b %errorlevel%
cl /nologo /EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE native_receipt_fixture.cpp /Fe:J6ReceiptFixtureV3.exe /Fo:native_receipt_fixture.obj advapi32.lib tdh.lib ole32.lib bcrypt.lib
exit /b %errorlevel%
