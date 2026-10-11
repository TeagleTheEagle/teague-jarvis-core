"""Trusted TEST updater data operations, never an incoming-code execution grant.

Not a sandbox against arbitrary code already running as the Windows owner.
No API is exported to a renderer. Existing owner authentication is mandatory.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import ctypes, os, sys
from .contract import need, safe_path, digest, read_json, compatible_manifest, _transport

_installed = None
_control = False
_authority = ContextVar('update_authority', default=None)
_phase = ContextVar('update_io_phase', default=None)
_CODE = {'.py', '.pyc', '.pyd'}
_SPAWN = {'subprocess.Popen','os.system','os.posix_spawn','os.spawn','os.startfile','os.startfile/2'}

def install(release, *, update_control=True):
    global _installed, _control
    need(_installed is None, 'UPDATE_GUARD_ALREADY_INSTALLED')
    _installed = safe_path(release, directory=True)
    _control = update_control
    sys.addaudithook(audit)

def audit(event, args):
    phase = _phase.get()
    if not _control and event != 'open':return
    if event in _SPAWN or event=='os.exec':
        raise ValueError('UPDATE_EXECUTION_DENIED')
    # The fixed control program is fully imported before installation. No new
    # Python code is needed, including after a read capability has ended.
    if event in ('compile','exec','function.__new__','code.__new__'):
        raise ValueError('UPDATE_EXECUTION_DENIED')
    if event == 'import' and len(args)>1 and args[1]:
        need(Path(args[1]).resolve().is_relative_to(_installed), 'EXTERNAL_IMPORT_DENIED')
    if event == 'ctypes.dlopen':
        # Fixed Windows APIs already used by package verification; never incoming DLLs.
        name=args[0]
        need(name in ('version','kernel32','advapi32','crypt32','psapi'), 'UPDATE_NATIVE_EXECUTION_DENIED')
    if event == 'open' and isinstance(args[0], (str, bytes)):
        path=Path(os.fsdecode(args[0])).resolve()
        if phase is not None and not path.is_relative_to(_installed):
            mode, flags=args[1],args[2]
            writing=flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
            if writing:
                need(path in phase['write'] and flags & os.O_EXCL and not flags & (os.O_TRUNC|os.O_APPEND), 'UPDATE_WRITE_DENIED')
                safe_path(path.parent,directory=True)
            else:
                need(path in phase['read'], 'UPDATE_READ_DENIED')
                safe_path(path,directory=False)
        elif path.suffix.lower() in _CODE:
            need(path.is_relative_to(_installed), 'SOURCE_TREE_EXECUTION_DENIED')

@contextmanager
def authorized(binding, request):
    from .enrollment import authorize
    need(_authority.get() is None, 'NESTED_UPDATE_AUTHORITY')
    body=authorize(binding,request)
    need(body['action'] in ('stage-update','stage-rollback','enroll-update','commit-update','abort-update'), 'UPDATE_ACTION')
    token=_authority.set((binding,body))
    try:yield body
    finally:_authority.reset(token)

def _target(release, pin):
    auth=_authority.get();need(auth is not None,'UPDATE_AUTHORITY_REQUIRED')
    binding,body=auth;release=safe_path(release,directory=True)
    incoming=body['args'].get('package')
    if incoming is not None and release==Path(incoming):
        need(pin==body['args'].get('package_hash'),'UPDATE_PIN_REQUIRED')
    else:
        need(release.parent==binding.install/'releases','UPDATE_LOCATION_DENIED')
        # Internal destination must be named by the current durable pending intent.
        from .contract import Binding, read_protected
        fresh=Binding(binding.descriptor,maintenance=True)
        need(fresh.pending_update is not None,'UPDATE_INTENT_REQUIRED')
        intent=read_protected(fresh.state/'updates'/f'intent-{fresh.pending_update:06d}.dpapi')
        need(Path(intent['release'])==release and intent['package_hash']==pin,'UPDATE_INTENT_TARGET')
    return release

@contextmanager
def verification(release, pin):
    # Offline source-owned manifest tooling has no installed audit exception.
    if _installed is None:
        yield;return
    need(_phase.get() is None,'NESTED_UPDATE_IO')
    release=_target(release,pin);manifest_path=safe_path(release/'manifest.json',directory=False)
    pt=_transport();handle=pt.k.CreateFileW(str(manifest_path),0x80000000,1,None,3,0x00200080,None)
    need(handle!=ctypes.c_void_p(-1).value,'UPDATE_MANIFEST_BUSY')
    try:
        need(digest(manifest_path)==pin,'PACKAGE_PIN')
        manifest=read_json(manifest_path,4194304);compatible_manifest(manifest)
        need(1<=len(manifest['files'])<=8000,'PACKAGE_LIMIT')
        paths={manifest_path}
        for entry in manifest['files']:
            need(set(entry)=={'path','bytes','sha256'},'PACKAGE_ENTRY')
            rel=Path(entry['path'])
            need(not rel.is_absolute() and '..' not in rel.parts and ':' not in str(rel),'PACKAGE_ESCAPE')
            p=safe_path(release/rel,directory=False)
            need(p.is_relative_to(release) and p not in paths,'PACKAGE_ESCAPE')
            paths.add(p)
        token=_phase.set({'read':frozenset(paths),'write':frozenset()})
        try:yield
        finally:_phase.reset(token)
    finally:pt.k.CloseHandle(handle)

def stage_copy(verified, target):
    """Copy already verified, held source files exclusively; no overwrite or code load."""
    from .contract import private_directory, read_protected, Binding
    auth=_authority.get();need(auth is not None and _phase.get() is None,'UPDATE_AUTHORITY_REQUIRED')
    binding,body=auth
    need(body['action'] in ('stage-update','stage-rollback'),'UPDATE_ACTION')
    fresh=Binding(binding.descriptor,maintenance=True)
    need(fresh.pending_update is not None,'UPDATE_INTENT_REQUIRED')
    intent=read_protected(fresh.state/'updates'/f'intent-{fresh.pending_update:06d}.dpapi')
    target=Path(target)
    need(target==Path(intent['release']) and target.parent==binding.install/'releases' and not target.exists(),'UPDATE_STAGE_TARGET')
    need(verified.record['package_hash']==intent['package_hash'] and verified.handles,'UPDATE_VERIFIED_HANDLES_REQUIRED')
    private_directory(target)
    entries=list(verified.manifest['files'])+[{'path':'manifest.json','sha256':verified.record['package_hash']}]
    for entry in entries:
        rel=Path(entry['path']);src=safe_path(verified.release/rel,directory=False);dst=target/rel
        need(src.is_relative_to(verified.release) and dst.is_relative_to(target) and '..' not in rel.parts,'PACKAGE_ESCAPE')
        dst.parent.mkdir(parents=True,exist_ok=True);safe_path(dst.parent,directory=True)
        token=_phase.set({'read':frozenset({src}),'write':frozenset({dst})})
        try:
            import hashlib
            hashed=hashlib.sha256()
            with src.open('rb') as inp, dst.open('xb') as out:
                while block:=inp.read(1024*1024):
                    hashed.update(block);out.write(block)
                out.flush();os.fsync(out.fileno())
            need(hashed.hexdigest()==entry['sha256'],'STAGED_FILE_IDENTITY')
        finally:_phase.reset(token)
        yield entry['path']
