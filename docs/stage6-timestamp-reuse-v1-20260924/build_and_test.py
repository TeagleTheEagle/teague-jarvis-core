from prepare import *
import subprocess,time,os
ref=C.parent/'reference'
for root in [C,ref]:
 shutil.copy2(R/'loss_measurement_fixture_v3.cpp',root/'loss_measurement_fixture_v3.cpp')
 if root==ref:shutil.copy2(C/'callback-bodies.inc',root/'callback-bodies.inc')
attempt=len(list(R.glob('build-attempt-*.log')))+1
cmd=['@echo off','call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat"','if errorlevel 1 exit /b %errorlevel%',f'set "TEMP={C.parent / "build-temp"}"',f'set "TMP={C.parent / "build-temp"}"']
for root,label in [(C,'reuse'),(ref,'reference')]:
 flag='/DJ6_REFERENCE_TEST' if label=='reference' else ''
 cmd += [f'cd /d "{root}"',f'cl /nologo /EHsc /std:c++17 /O2 /FAs /Fafixture-final.asm {flag} /DUNICODE /D_UNICODE loss_measurement_fixture_v3.cpp /Fe:J6Timestamp{label}.exe /Fo:fixture.obj advapi32.lib tdh.lib psapi.lib','if errorlevel 1 exit /b %errorlevel%']
cmd += [f'cd /d "{C}"']
for name in ['authority_trace_v3','startup_trace']:
 cmd += [f'cl /nologo /EHsc /std:c++17 /O2 /FAs /Fa{name}-final.asm /DUNICODE /D_UNICODE {name}.cpp /Fe:{name}-OFFLINE-NOT-LIVE.exe /Fo:{name}.obj advapi32.lib tdh.lib bcrypt.lib ole32.lib','if errorlevel 1 exit /b %errorlevel%']
cmd+=['exit /b 0']
build=R/f'build-attempt-{attempt}.cmd';build.write_text('\n'.join(cmd))
with (R/f'build-attempt-{attempt}.log').open('xb') as log:
 result=subprocess.run(['cmd.exe','/d','/c',str(build)],stdout=log,stderr=subprocess.STDOUT,timeout=240)
write(R/f'build-attempt-{attempt}.json',dict(exit=result.returncode))
print('BUILD',result.returncode,flush=True)
if result.returncode:raise SystemExit(result.returncode)
for root,label in [(C,'reuse'),(ref,'reference')]:
 exe=root/f'J6Timestamp{label}.exe';before=sha(exe);start=time.monotonic()
 with (R/f'tests-{label}-{attempt}.stdout').open('xb') as out,(R/f'tests-{label}-{attempt}.stderr').open('xb') as err:
  p=subprocess.Popen([str(exe)],cwd=root,stdout=out,stderr=err)
  pid=p.pid;code=p.wait(timeout=60)
 write(R/f'tests-{label}-{attempt}.json',dict(pid=pid,exe=str(exe),sha256=before,exit=code,duration=time.monotonic()-start,exited=True,benchmark=False))
 assert sha(exe)==before
 print(label,code,flush=True)
 if code:raise SystemExit(code)
