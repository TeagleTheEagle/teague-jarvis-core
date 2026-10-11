"""Explicit Windows TEST deployment binding. No production discovery or defaults."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

MODE = 'STAGE4_TEST_DEPLOYMENT'
SCHEMA = 2

def compatible_manifest(manifest):
    need(set(manifest) == {'mode','version','application_version','enrollment_format','bootstrap_contract',
         'build','protocol','data_schema','files','capabilities'} and manifest['mode'] == MODE and
         manifest['version'] == 2 and manifest['bootstrap_contract'] == 2 and
         manifest['enrollment_format'] == 1 and manifest['protocol'] == [2,3] and
         manifest['data_schema'] == 1 and type(manifest['application_version']) is int and
         manifest['application_version'] >= 1, 'PACKAGE_COMPATIBILITY')

def need(ok, reason):
    if not ok:
        raise ValueError(reason)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf8')

def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def safe_path(value, *, directory=None):
    need(isinstance(value, (str, Path)), 'PATH_TYPE')
    path = Path(value)
    need(path.is_absolute() and not str(path).startswith(('\\\\', '//')) and
         '..' not in path.parts and ':' not in str(path)[2:], 'ABSOLUTE_LOCAL_PATH_REQUIRED')
    for item in (path, *path.parents):
        st = item.lstat()
        need(not item.is_symlink() and not getattr(st, 'st_file_attributes', 0) & 0x400, 'REPARSE_DENIED')
    if directory is not None:
        need(path.is_dir() == directory, 'PATH_KIND')
    return path

def read_json(path, limit=1048576):
    path = safe_path(path, directory=False)
    need(path.stat().st_size <= limit, 'RECORD_LIMIT')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'AMBIGUOUS_JSON')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf8'), object_pairs_hook=unique)

def exclusive_json(path, value):
    safe_path(Path(path).parent, directory=True)
    with Path(path).open('xb') as stream:
        stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())

# Current-user DPAPI; no machine-wide flag, no registry/security-policy changes.
class Blob(c.Structure):
    _fields_ = [('length', w.DWORD), ('data', c.POINTER(c.c_ubyte))]

def protect(data, *, decrypt=False):
    need(os.name == 'nt' and isinstance(data, bytes) and len(data) <= 1048576, 'WINDOWS_BOUNDED_SECRET')
    crypto = c.WinDLL('crypt32', use_last_error=True)
    kernel = c.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [c.c_void_p]
    raw = c.create_string_buffer(data)
    source = Blob(len(data), c.cast(raw, c.POINTER(c.c_ubyte))); target = Blob()
    if decrypt:
        fn = crypto.CryptUnprotectData
        fn.argtypes = [c.POINTER(Blob), c.c_void_p, c.c_void_p, c.c_void_p, c.c_void_p, w.DWORD, c.POINTER(Blob)]
        ok = fn(c.byref(source), None, None, None, None, 1, c.byref(target))
    else:
        fn = crypto.CryptProtectData
        fn.argtypes = [c.POINTER(Blob), w.LPCWSTR, c.c_void_p, c.c_void_p, c.c_void_p, w.DWORD, c.POINTER(Blob)]
        ok = fn(c.byref(source), MODE, None, None, None, 1, c.byref(target))
    if not ok:
        raise OSError(c.get_last_error(), 'TEST protected record unavailable')
    try:
        return c.string_at(target.data, target.length)
    finally:
        c.memset(target.data, 0, target.length); kernel.LocalFree(target.data)

def _transport():
    import sys
    app = Path(__file__).resolve().parents[1]
    location = str(app/'tests/lifecycle_stage2')
    if location not in sys.path:
        sys.path.insert(0, location)
    import pipe_transport
    return pipe_transport

def current_sid():
    return _transport().current_sid()

def private_directory(path):
    """Create a new TEST directory with owner-only inheritable access."""
    path = Path(path); safe_path(path.parent, directory=True)
    pt = _transport(); sd = c.c_void_p()
    sddl = 'D:P(A;OICI;FA;;;' + current_sid() + ')'
    pt.check(pt.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, c.byref(sd), None))
    try:
        sa = pt.SA(c.sizeof(pt.SA), sd, False)
        fn = pt.k.CreateDirectoryW
        fn.argtypes = [w.LPCWSTR, c.POINTER(pt.SA)]; fn.restype = w.BOOL
        pt.check(fn(str(path), c.byref(sa)))
    finally:
        pt.k.LocalFree(sd)
    return safe_path(path, directory=True)

def write_protected(path, value):
    safe_path(Path(path).parent, directory=True)
    pending = Path(path).with_name('.pending-'+uuid.uuid4().hex)
    with pending.open('xb') as stream:
        stream.write(protect(canonical(value))); stream.flush(); os.fsync(stream.fileno())
    # Publish a new immutable name only. Windows rename refuses an existing
    # destination; readers never observe a partially written generation.
    os.rename(pending, path)

def read_protected(path):
    path = safe_path(path, directory=False)
    need(path.stat().st_size <= 1048576, 'SECRET_RECORD_LIMIT')
    return json.loads(protect(path.read_bytes(), decrypt=True))

class Binding:
    FIELDS = {'schema','mode','installation_id','data_id','owner_sid','install_root',
              'state_root','release_root','package_hash','protocol','data_schema'}

    def __init__(self, descriptor, *, maintenance=False):
        self.maintenance = maintenance
        self.descriptor = safe_path(descriptor, directory=False)
        need(self.descriptor.name == 'binding.dpapi', 'EXPLICIT_BINDING_REQUIRED')
        self.seal = digest(self.descriptor)
        self.record = read_protected(self.descriptor)
        self.base_record = dict(self.record)
        r = self.record
        need(type(r) is dict and set(r) == self.FIELDS and r['schema'] == SCHEMA and
             r['mode'] == MODE and r['protocol'] == [2,3] and r['data_schema'] == 1, 'BINDING_SCHEMA')
        need(r['owner_sid'] == current_sid(), 'OWNER_SID')
        need(re.fullmatch(r'TEST-INSTALL-[a-f0-9]{32}', r['installation_id']) is not None and
             re.fullmatch(r'TEST-[a-f0-9]{32}', r['data_id']) is not None, 'SYNTHETIC_IDENTITY')
        self.install = safe_path(r['install_root'], directory=True)
        self.state = safe_path(r['state_root'], directory=True)
        self.release = safe_path(r['release_root'], directory=True)
        need(self.install.name == r['installation_id'] and self.descriptor == self.install/'binding.dpapi', 'COPIED_BINDING')
        need(self.state.parent == self.install/'state' and re.fullmatch(r'TEST-STAGE4-[a-f0-9]{32}', self.state.name), 'STATE_BINDING')
        need(self.release.parent == self.install/'releases' and self.state != self.release, 'RELEASE_BINDING')
        self.app = self.release/'app'
        self.handles = []
        self.activation = 0
        self.enrollment_directory = self.state/'enrollment'
        self.pending_update = None
        self._activation_history()
        self.check_root(self.state)

    def _activation_history(self):
        """Immutable, DPAPI-protected decisions; an unfinished intent fences startup."""
        directory = safe_path(self.state/'updates', directory=True)
        files = sorted(directory.glob('intent-*.dpapi'))
        need(len(files) <= 128 and [p.name for p in files] ==
             [f'intent-{i:06d}.dpapi' for i in range(1,len(files)+1)], 'UPDATE_HISTORY_GAP')
        for prefix in ('commit','abort','enrolled'):
            for record in directory.glob(prefix+'-*.dpapi'):
                suffix=record.name[len(prefix):]
                need((directory/('intent'+suffix)).is_file(),'ORPHAN_UPDATE_RECORD')
        for index, file in enumerate(files, 1):
            intent = read_protected(file)
            need(intent['binding'] == self.seal and intent['sequence'] == index and
                 intent['previous_package'] == self.record['package_hash'] and
                 intent['data_id'] == self.record['data_id'], 'UPDATE_IDENTITY')
            commit = directory/f'commit-{index:06d}.dpapi'
            abort = directory/f'abort-{index:06d}.dpapi'
            need(not (commit.exists() and abort.exists()), 'CONTRADICTORY_UPDATE')
            if abort.exists():
                result = read_protected(abort)
                need(result['binding'] == self.seal and result['intent_hash'] == digest(file), 'UPDATE_ABORT')
                continue
            if not commit.exists():
                need(index == len(files), 'UPDATE_AFTER_PENDING')
                self.pending_update = index
                need(self.maintenance, 'UPDATE_RECOVERY_REQUIRED')
                continue
            result = read_protected(commit)
            enrolled = directory/f'enrolled-{index:06d}.dpapi'
            registered = read_protected(enrolled)
            need(result['binding'] == self.seal and result['intent_hash'] == digest(file) and
                 result['enrollment_hash'] == registered['enrollment_hash'] and
                 registered['binding'] == self.seal and registered['intent_hash'] == digest(file) and
                 result['enrollment_authority_hash'] == digest(enrolled), 'UPDATE_COMMIT')
            release = safe_path(intent['release'], directory=True)
            need(release.parent == self.install/'releases' and
                 digest(release/'manifest.json') == intent['package_hash'], 'UPDATE_RELEASE')
            manifest = read_json(release/'manifest.json',4194304); compatible_manifest(manifest)
            enroll = safe_path(directory/f'enrollment-{index:06d}',directory=True)
            need(digest(enroll/'generation-000001.dpapi') == result['enrollment_hash'], 'UPDATE_ENROLLMENT')
            self.record.update(release_root=str(release),package_hash=intent['package_hash'])
            self.release = release; self.app = release/'app'
            self.enrollment_directory = enroll; self.activation = index

    def check_root(self, root):
        need(Path(root) == self.state and digest(self.descriptor) == self.seal, 'CONFLICTING_BINDING')
        safe_path(self.state, directory=True); safe_path(self.release, directory=True)
        marker = safe_path(self.state/'TEST_ONLY', directory=False)
        need(marker.read_text() == 'NO PRODUCTION SERVICES', 'TEST_MARKER')
        if not self.maintenance:
            if (self.state/'deployment-fence.json').exists():
                fence=read_json(self.state/'deployment-fence.json')
                ready_path=self.state/'reinstall-ready.dpapi'
                need(fence['action']=='prepare-uninstall' and ready_path.exists(),'DEPLOYMENT_FENCED')
                ready=read_protected(ready_path)
                need(ready['binding']==self.seal and ready['operation']==fence['operation'] and
                     ready['package_hash']==self.record['package_hash'] and ready['revision']==2,'REINSTALL_AUTHORIZATION')
        return self.state

    def verify_package(self, *, hold=False):
        manifest_path = safe_path(self.release/'manifest.json', directory=False)
        need(digest(manifest_path) == self.record['package_hash'], 'PACKAGE_PIN')
        manifest = read_json(manifest_path, 4194304)
        compatible_manifest(manifest)
        need(1 <= len(manifest['files']) <= 8000, 'PACKAGE_LIMIT')
        expected = {'manifest.json'}
        pt = _transport()
        try:
            for entry in manifest['files']:
                need(set(entry) == {'path','sha256','bytes'} and entry['path'] not in expected, 'PACKAGE_ENTRY')
                relative = Path(entry['path'])
                need(not relative.is_absolute() and '..' not in relative.parts and ':' not in str(relative), 'PACKAGE_ESCAPE')
                file = safe_path(self.release/relative, directory=False)
                need(file.is_relative_to(self.release), 'PACKAGE_ESCAPE')
                if hold:
                    handle = pt.k.CreateFileW(str(file), 0x80000000, 1, None, 3, 0x00200080, None)
                    need(handle != c.c_void_p(-1).value, 'PACKAGE_FILE_BUSY')
                    self.handles.append(handle)
                need(file.stat().st_size == entry['bytes'] and digest(file) == entry['sha256'], 'PACKAGE_FILE_IDENTITY')
                expected.add(relative.as_posix())
            actual = {p.relative_to(self.release).as_posix() for p in self.release.rglob('*') if p.is_file()}
            need(actual == expected, 'UNMANIFESTED_PACKAGE_FILE')
            from .native import verify_native
            verify_native(self.release)
        except BaseException:
            self.close(); raise
        self.manifest = manifest
        return manifest

    def close(self):
        for handle in self.handles:
            _transport().k.CloseHandle(handle)
        self.handles = []

    def audit_identity(self):
        return {**self.record, 'binding_sha256': self.seal}

    def python_command(self, role):
        need(role in ('--core','--coordinator','--control'), 'BOOTSTRAP_ROLE')
        return [str(self.release/'python/python.exe'), '-I', '-S', '-B',
                str(self.app/'deployment_test/bootstrap.py'), role, str(self.descriptor)]
