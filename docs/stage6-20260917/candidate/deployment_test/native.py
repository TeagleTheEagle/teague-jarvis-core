"""Bounded native package inventory and read-only loaded-module evidence (TEST)."""
import ctypes as c
from ctypes import wintypes as w
import os
from pathlib import Path
import re
import subprocess
from .contract import digest, exclusive_json, need, read_json, safe_path

CRT = ('msvcp140.dll','vcruntime140.dll','vcruntime140_1.dll')
CRT_VERSION = '14.44.35211.0'
REDIST = Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Redist\MSVC\14.44.35112\x64\Microsoft.VC143.CRT')
DUMPBIN = Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe')

def version(path):
    api=c.WinDLL('version',use_last_error=True)
    api.GetFileVersionInfoSizeW.argtypes=[w.LPCWSTR,c.POINTER(w.DWORD)]
    api.GetFileVersionInfoW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p]
    api.VerQueryValueW.argtypes=[c.c_void_p,w.LPCWSTR,c.POINTER(c.c_void_p),c.POINTER(w.UINT)]
    size=api.GetFileVersionInfoSizeW(str(path),None)
    if not size:return None
    data=c.create_string_buffer(size);need(api.GetFileVersionInfoW(str(path),0,size,data),'NATIVE_VERSION_READ')
    ptr=c.c_void_p();length=w.UINT()
    if not api.VerQueryValueW(data,'\\',c.byref(ptr),c.byref(length)):return None
    values=c.cast(ptr,c.POINTER(w.DWORD))
    need(values[0]==0xFEEF04BD,'NATIVE_VERSION_RESOURCE')
    return '.'.join(map(str,(values[2]>>16,values[2]&65535,values[3]>>16,values[3]&65535)))

def build_manifest(release,sources):
    entries=[]
    for file in sorted(release.rglob('*')):
        if file.suffix.lower() not in ('.exe','.dll','.pyd','.node'):continue
        rel=file.relative_to(release).as_posix()
        output=subprocess.run([str(DUMPBIN),'/dependents',str(file)],capture_output=True,text=True,check=True).stdout
        imports=sorted(set(re.findall(r'^\s+([\w.-]+\.(?:dll|exe))\s*$',output,re.M|re.I)),key=str.lower)
        entries.append(dict(filename=file.name,path=rel,source=sources[rel],purpose='Packaged '+rel.split('/')[0]+' native runtime',
            version=version(file),sha256=digest(file),classification='required',loading_component=rel.split('/')[0],imports=imports))
    packaged={x['filename'].lower() for x in entries}
    system=Path(os.environ['SystemRoot'])/'System32';platform={}
    for entry in entries:
        for name in entry['imports']:
            if name.lower() in packaged:continue
            need(name.lower() not in ('msvcp140.dll','vcruntime140.dll','vcruntime140_1.dll'),'UNBUNDLED_CRT')
            need(name.lower().startswith(('api-ms-win-','ext-ms-win-')) or (system/name).is_file(),'UNDECLARED_NATIVE_IMPORT:'+name)
            platform[name]=dict(filename=name,source=str(system/name) if (system/name).is_file() else 'Windows API-set contract',
                purpose='Operating system native API',version=version(system/name) if (system/name).is_file() else None,
                observed_host_sha256=digest(system/name) if (system/name).is_file() else None,
                hash_policy='OS-managed prerequisite; observed host hash is evidence, not a portable release pin',classification='required OS prerequisite',
                loading_components=sorted({x['path'] for x in entries if name in x['imports']}))
    exclusive_json(release/'native-manifest.json',dict(version=1,architecture='x64',crt_version=CRT_VERSION,entries=entries,
        windows_dependencies=platform,optional_excluded=['physical audio capture','ML/voice models','third-party Python packages'],
        delay_node_exe='Electron native module delay-load hook; bundled node.exe is the separate trusted launcher'))

def verify_native(release):
    manifest=read_json(release/'native-manifest.json',4194304)
    need(manifest['version']==1 and manifest['architecture']=='x64' and manifest['crt_version']==CRT_VERSION,'NATIVE_CONTRACT')
    actual={p.relative_to(release).as_posix() for p in release.rglob('*') if p.suffix.lower() in ('.exe','.dll','.pyd','.node')}
    need(actual=={x['path'] for x in manifest['entries']},'NATIVE_INVENTORY')
    for entry in manifest['entries']:
        file=safe_path(release/entry['path'],directory=False)
        need(file.is_relative_to(release) and digest(file)==entry['sha256'] and version(file)==entry['version'],'NATIVE_IDENTITY_OR_VERSION')
        with file.open('rb') as stream:need(stream.read(2)==b'MZ','NATIVE_PE_REQUIRED')
        if file.name.lower() in CRT:need(entry['version']==CRT_VERSION,'NATIVE_CRT_VERSION')
    for component in ('python','electron','node','native'):
        for name in CRT:need((release/component/name).is_file(),'APP_LOCAL_CRT_REQUIRED')
    return manifest

def loaded_modules(pid,expected_peer,release):
    """Evidence helper for a previously authenticated, exact TEST process only."""
    from .contract import _transport
    pt=_transport();need(pt.identity(pid)==expected_peer,'MODULE_PROCESS_IDENTITY')
    kernel=c.WinDLL('kernel32',use_last_error=True);psapi=c.WinDLL('psapi',use_last_error=True)
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];kernel.OpenProcess.restype=w.HANDLE
    kernel.CloseHandle.argtypes=[w.HANDLE]
    psapi.EnumProcessModulesEx.argtypes=[w.HANDLE,c.POINTER(w.HMODULE),w.DWORD,c.POINTER(w.DWORD),w.DWORD]
    psapi.GetModuleFileNameExW.argtypes=[w.HANDLE,w.HMODULE,w.LPWSTR,w.DWORD]
    handle=kernel.OpenProcess(0x410,False,pid);need(handle,'MODULE_PROCESS_ACCESS')
    try:
        mods=(w.HMODULE*4096)();needed=w.DWORD()
        need(psapi.EnumProcessModulesEx(handle,mods,c.sizeof(mods),c.byref(needed),3) and needed.value<=c.sizeof(mods),'MODULE_ENUMERATION')
        paths=[]
        for module in mods[:needed.value//c.sizeof(w.HMODULE)]:
            path=c.create_unicode_buffer(32768)
            need(psapi.GetModuleFileNameExW(handle,module,path,len(path)),'MODULE_PATH')
            raw=path.value
            # Windows may return the same local path in extended-length syntax.
            # Normalize only a drive-qualified \\?\ prefix, never UNC/device paths.
            normalized=raw[4:] if re.match(r'^\\\\\?\\[A-Za-z]:\\',raw) else raw
            paths.append((Path(normalized),raw))
        need(pt.identity(pid)==expected_peer,'MODULE_PROCESS_CHANGED')
        native=verify_native(release);by_name={e['filename'].lower() for e in native['entries']}
        records=[];external=[]
        for path,raw in paths:
            package_name=path.name.lower() in by_name
            if package_name and not path.is_relative_to(release):external.append(str(path))
            elif not package_name:need(path.is_relative_to(Path(os.environ['SystemRoot'])),'UNDECLARED_LOADED_NATIVE:'+str(path))
            records.append(dict(path=str(path),windows_reported_path=raw,sha256=digest(path) if package_name else None,packaged_component=package_name))
        need(not external,'EXTERNAL_PACKAGED_NATIVE:'+str(dict(external=external,all_loaded=records)))
        return dict(identity=expected_peer,modules=records,packaged_modules_external=0)
    finally:kernel.CloseHandle(handle)

def mark_test_build(executable,application_version):
    """Only a newly copied, unsigned TEST Electron PE resource is changed."""
    kernel=c.WinDLL('kernel32',use_last_error=True)
    kernel.BeginUpdateResourceW.argtypes=[w.LPCWSTR,w.BOOL];kernel.BeginUpdateResourceW.restype=w.HANDLE
    kernel.UpdateResourceW.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,w.WORD,c.c_void_p,w.DWORD]
    kernel.EndUpdateResourceW.argtypes=[w.HANDLE,w.BOOL]
    handle=kernel.BeginUpdateResourceW(str(executable),False);need(handle,'TEST_RESOURCE_OPEN')
    marker=('STAGE4_TEST deployment application version '+str(application_version)).encode()
    data=c.create_string_buffer(marker)
    ok=kernel.UpdateResourceW(handle,c.c_void_p(10),c.c_void_p(41000),0,data,len(marker))
    need(kernel.EndUpdateResourceW(handle,not ok) and ok,'TEST_RESOURCE_PUBLICATION')
