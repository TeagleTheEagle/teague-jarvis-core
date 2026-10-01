"""One invocation only; original launcher controls all observer lifetimes."""
import pathlib,subprocess,json,os
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\2d922197cf7d4bb098d8da6e070cbff2\code')
RUN='protected-8145cedf8db843959b8ba58dfd62717b'
L=C.parent/('live-'+RUN);L.mkdir(exist_ok=False)
pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
command=[pwsh,'-NoProfile','-File',str(C/'small_launch_v2.ps1'),'-Run',RUN]
with (L/'launch-command.json').open('x') as f:json.dump(command,f,indent=2)
with (L/'launch.stdout').open('xb') as out,(L/'launch.stderr').open('xb') as err:
 p=subprocess.Popen(command,cwd=C,stdout=out,stderr=err,creationflags=0x08000000)
 print('LAUNCHER_STARTED '+str(p.pid),flush=True)
 code=p.wait()
 out.flush();err.flush();os.fsync(out.fileno());os.fsync(err.fileno())
with (L/'launcher-exit.json').open('x') as f:json.dump(dict(pid=p.pid,exitCode=code),f)
if hasattr(p,'_handle'):p._handle.Close()
print('LAUNCHER_EXIT '+str(code),flush=True)
raise SystemExit(code)
