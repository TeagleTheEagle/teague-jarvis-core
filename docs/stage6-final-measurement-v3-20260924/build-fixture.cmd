@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code"
set "TEMP=D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\build-temp"
set "TMP=D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\build-temp"
cl /nologo /EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE loss_measurement_fixture_v3.cpp /Fe:J6MeasurementFixtureV3.exe /Fo:loss_measurement_fixture_v3.obj advapi32.lib tdh.lib psapi.lib
exit /b %errorlevel%
