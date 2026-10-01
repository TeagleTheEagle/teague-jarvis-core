@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "D:\JARVIS-STAGE6-LIVE\component-attribution-20260924-7f29a680"
set "TEMP=D:\JARVIS-STAGE6-LIVE\component-attribution-20260924-7f29a680\build-temp"
set "TMP=D:\JARVIS-STAGE6-LIVE\component-attribution-20260924-7f29a680\build-temp"
cl /nologo /EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE attribution_fixture.cpp /Fe:J6AttributionFixture.exe /Fo:attribution_fixture.obj advapi32.lib tdh.lib psapi.lib
exit /b %errorlevel%
