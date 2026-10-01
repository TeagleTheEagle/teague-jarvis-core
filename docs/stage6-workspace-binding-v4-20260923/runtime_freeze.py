"""Read-only runtime identity capture; writes the new candidate's policy only."""
import pathlib,json,hashlib,sys,ctypes,platform
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
PY=pathlib.Path(sys.executable);PS=pathlib.Path(r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe');SYS=pathlib.Path(r'C:\Windows\System32')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def version(p):
 v=ctypes.WinDLL('version',use_last_error=True);v.GetFileVersionInfoSizeW.argtypes=[ctypes.c_wchar_p,ctypes.c_void_p];v.GetFileVersionInfoW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];v.VerQueryValueW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_uint32)]
 size=v.GetFileVersionInfoSizeW(str(p),None);assert size>0
 b=ctypes.create_string_buffer(size);assert v.GetFileVersionInfoW(str(p),0,size,b)
 out=ctypes.c_void_p();n=ctypes.c_uint32();assert v.VerQueryValueW(b,'\\',ctypes.byref(out),ctypes.byref(n));words=ctypes.cast(out,ctypes.POINTER(ctypes.c_uint32));a,z=words[2:4];return '.'.join(map(str,(a>>16,a&65535,z>>16,z&65535)))
def row(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
executables={k:dict(**row(p),version=version(p)) for k,p in dict(python=PY,pwsh=PS,powershell=SYS/'WindowsPowerShell/v1.0/powershell.exe',logman=SYS/'logman.exe').items()}
paths=set()
for folder in (PY.parent,PY.parent/'DLLs',PS.parent):paths.update(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ('.dll','.pyd','.json','.config'))
paths.update(p for p in (PY.parent/'Lib').rglob('*.py') if 'site-packages' not in p.parts and '__pycache__' not in p.parts)
for name in ('CimCmdlets','Microsoft.PowerShell.Management','Microsoft.PowerShell.Utility','Microsoft.PowerShell.Security','Microsoft.PowerShell.Diagnostics'):
 paths.update(p for p in (PS.parent/'Modules'/name).rglob('*') if p.is_file() and p.suffix.lower() in ('.dll','.psd1','.psm1','.ps1xml'))
for name in ('kernel32.dll','KernelBase.dll','ntdll.dll','advapi32.dll','bcrypt.dll','tdh.dll','ole32.dll','version.dll','user32.dll'):paths.add(SYS/name)
value=dict(schema='stage6-shared-runtime-v4',executables=executables,components=[row(p) for p in sorted(paths)],osIdentity=dict(version=platform.version(),system=platform.system(),architecture=platform.machine(),systemRoot=str(SYS.parent),systemComponentPolicy='Windows-provided components; no copies or substitutions; explicit System32 tools'),moduleRoots=[str(PS.parent/'Modules'),str(SYS/'WindowsPowerShell/v1.0/Modules')],pythonVersion=sys.version.split()[0],coverage='Python stdlib source, native extensions/DLLs; PowerShell root runtime binaries/config and required module files; explicit Windows identity. Site-packages are not used by this TEST entry path.')
with (C/'shared-runtime-v4.json').open('x') as f:json.dump(value,f,sort_keys=True,indent=2)
print(json.dumps(dict(componentFiles=len(paths),executables=executables,policySHA256=sha(C/'shared-runtime-v4.json'))))
