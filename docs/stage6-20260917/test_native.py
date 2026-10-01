"""Focused real checker tests with controlled Windows module-enumeration inputs."""
from pathlib import Path
import ctypes,importlib.util,json,sys,types,unittest
from unittest.mock import Mock,patch
D=Path(__file__).resolve().parent;S=Path(json.loads((D/'source.json').read_text())['source']);sys.path.insert(0,str(S))
from deployment_test import native as n
PIN={'pid':1,'created':2,'exe_digest':'test-fixture'}
RELEASE=Path(r'C:\TEST-PACKAGE-native')
def inspect(module,paths):
    kernel=types.SimpleNamespace(OpenProcess=Mock(return_value=1),CloseHandle=Mock())
    def enum(h,mods,size,needed,flags):
        for i in range(len(paths)):mods[i]=i+1
        ctypes.cast(needed,ctypes.POINTER(n.w.DWORD)).contents.value=len(paths)*ctypes.sizeof(n.w.HMODULE);return 1
    def filename(h,handle,buffer,size):buffer.value=paths[handle-1];return len(buffer.value)
    psapi=types.SimpleNamespace(EnumProcessModulesEx=Mock(side_effect=enum),GetModuleFileNameExW=Mock(side_effect=filename))
    with patch('deployment_test.contract._transport',return_value=types.SimpleNamespace(identity=lambda pid:PIN)),patch.object(module.c,'WinDLL',side_effect=lambda name,**kw:kernel if name=='kernel32' else psapi),patch.object(module,'verify_native',return_value={'entries':[{'filename':'python.exe'},{'filename':'peer_identity.node'},{'filename':'msvcp140.dll'}]}),patch.object(module,'digest',return_value='fixture-digest'):
        return module.loaded_modules(1,PIN,RELEASE)
class NativeChecks(unittest.TestCase):
    def test_packaged_executable_accepted(self):self.assertEqual(inspect(n,[str(RELEASE/'python/python.exe')])['packaged_modules_external'],0)
    def test_extended_drive_path_accepted(self):self.assertEqual(inspect(n,['\\\\?\\'+str(RELEASE/'native/peer_identity.node')])['packaged_modules_external'],0)
    def test_external_crt_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXTERNAL_PACKAGED_NATIVE'):inspect(n,[r'C:\Windows\System32\msvcp140.dll'])
    def test_external_same_filename_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXTERNAL_PACKAGED_NATIVE'):inspect(n,[r'C:\other\python.exe'])
    def test_windows_system_module_accepted(self):self.assertFalse(inspect(n,[str(Path(n.os.environ['SystemRoot'])/'System32/kernel32.dll')])['modules'][0]['packaged_component'])
    def test_unknown_external_module_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNDECLARED_LOADED_NATIVE'):inspect(n,[r'C:\developer\unknown.dll'])
    def test_original_branch_defect_reproduced(self):
        spec=importlib.util.spec_from_file_location('deployment_test.pending_native',D/'pending/deployment_test/native.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        with self.assertRaisesRegex(ValueError,'UNDECLARED_LOADED_NATIVE'):inspect(old,[str(RELEASE/'python/python.exe')])
if __name__=='__main__':unittest.main()
