from prepare import *
import subprocess
shutil.copy2(R/'main.cpp',C/'main.cpp')
(C/'protocol_hash.hpp').write_text('static const char* protocolHash="'+sha(C/'protocol.json')+'";\n')
attempt=len(list(R.glob('build-*.log')))+1
lines=['@echo off','call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat"','if errorlevel 1 exit /b %errorlevel%',f'cd /d "{C}"',f'set "TEMP={C / "temp"}"',f'set "TMP={C / "temp"}"']
for arm in 'ABC':lines += [f'cl /nologo /c /EHsc /std:c++17 /O2 /GL- /FAs /Fa{arm}.asm /Fo{arm}.obj /DUNICODE /D_UNICODE {arm}\\arm.cpp','if errorlevel 1 exit /b %errorlevel%']
lines+=['cl /nologo /c /EHsc /std:c++17 /O2 /GL- /FAs /Famain.asm /Fomain.obj /DUNICODE /D_UNICODE main.cpp','if errorlevel 1 exit /b %errorlevel%','link /nologo /OUT:J6FinalQualification.exe /MAP:qualification.map /OPT:NOICF A.obj B.obj C.obj main.obj advapi32.lib tdh.lib','exit /b %errorlevel%']
cmd=R/f'build-{attempt}.cmd';cmd.write_text('\n'.join(lines))
with (R/f'build-{attempt}.log').open('xb') as f:r=subprocess.run(['cmd.exe','/d','/c',str(cmd)],stdout=f,stderr=subprocess.STDOUT,timeout=180)
write(R/f'build-{attempt}.json',dict(exit=r.returncode,command=str(cmd),benchmarkExecuted=False))
print('BUILD',r.returncode)
raise SystemExit(r.returncode)
