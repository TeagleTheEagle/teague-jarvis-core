"""tools/installer.py on synthetic releases in a temporary home (no shortcuts, no processes)."""
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools'))
import installer  # noqa: E402


def make_package(base, version, files):
    package = Path(base) / f'pkg-{version}'
    release = package / 'release'
    for path, data in files.items():
        (release / path).parent.mkdir(parents=True, exist_ok=True)
        (release / path).write_bytes(data)
    manifest = {'product': 'JARVIS', 'format': 1, 'version': version, 'release_id': f'{version}-abc',
                'files': [{'path': p, 'sha256': hashlib.sha256(d).hexdigest(), 'bytes': len(d)} for p, d in sorted(files.items())]}
    (release / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    return package


APP = {'app/server.py': b'# server', 'app/personality.txt': b'Default personality.', 'python/python.exe': b'MZ',
       'electron/electron.exe': b'MZ', 'models/wake-models/hey.onnx': b'model'}


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.home = self.base / 'home'
        self.v1 = make_package(self.base, '1.0.0', APP)
        self.v2 = make_package(self.base, '1.1.0', {**APP, 'app/server.py': b'# server v2'})
        self.stops = []
        self.stop = lambda home: self.stops.append(home)

    def install(self, package, **kw):
        return installer.install(package, self.home, shortcuts=False, stop=self.stop, **kw)

    def current(self):
        return installer.read_current(self.home)

    def test_first_install_lays_out_program_and_owner_folders(self):
        result = self.install(self.v1)
        self.assertEqual(result['release'], '1.0.0-abc')
        self.assertEqual(self.current()['release'], '1.0.0-abc')
        self.assertIsNone(self.current()['previous'])
        for folder in ('data', 'config', 'profile'):
            self.assertTrue((self.home / folder).is_dir())
        self.assertEqual((self.home / 'config' / 'personality.txt').read_bytes(), b'Default personality.')
        self.assertIn('JARVIS_DATA_DIR', (self.home / 'JARVIS.ps1').read_text(encoding='utf-8'))
        self.assertEqual(self.stops, [])  # nothing to stop on a first install

    def test_damaged_or_padded_package_is_refused_before_any_change(self):
        (self.v1 / 'release' / 'app' / 'server.py').write_bytes(b'# tampered')
        with self.assertRaises(installer.InstallError):
            self.install(self.v1)
        self.assertFalse(self.home.exists())
        self.v2.joinpath('release', 'app', 'extra.py').write_bytes(b'unlisted')
        with self.assertRaises(installer.InstallError):
            self.install(self.v2)

    def test_update_switches_atomically_keeps_previous_and_never_touches_data(self):
        self.install(self.v1)
        (self.home / 'data' / 'jarvis.sqlite3').write_bytes(b'memory')
        (self.home / 'config' / 'personality.txt').write_bytes(b'Owner personality.')
        result = self.install(self.v2)
        self.assertEqual(result['previous'], '1.0.0-abc')
        self.assertEqual(set(result['seconds']), {'verify_package', 'copy', 'verify_copy', 'stop', 'switch'})  # update-timing evidence
        self.assertEqual(self.current(), {**self.current(), 'release': '1.1.0-abc', 'previous': '1.0.0-abc'})
        self.assertEqual(len(self.stops), 1)  # the running JARVIS is stopped before the switch
        self.assertEqual((self.home / 'data' / 'jarvis.sqlite3').read_bytes(), b'memory')
        self.assertEqual((self.home / 'config' / 'personality.txt').read_bytes(), b'Owner personality.')
        self.assertTrue((self.home / 'releases' / '1.0.0-abc').is_dir())  # kept for rollback

    def test_interrupted_update_leaves_the_previous_release_current(self):
        self.install(self.v1)
        with patch.object(installer.shutil, 'copytree', side_effect=OSError('power cut')), self.assertRaises(OSError):
            self.install(self.v2)
        self.assertEqual(self.current()['release'], '1.0.0-abc')
        (self.home / 'releases' / '.incoming-1.1.0-abc').mkdir()  # debris of an interrupted copy
        self.install(self.v2)
        self.assertEqual(self.current()['release'], '1.1.0-abc')
        self.assertFalse((self.home / 'releases' / '.incoming-1.1.0-abc').exists())

    def test_a_crash_at_any_update_step_leaves_a_startable_jarvis_and_a_rerun_finishes(self):
        real_copytree, real_replace = shutil.copytree, installer.os.replace

        def half_copy(src, dst, **kw):  # power cut part-way through copying the new release
            files = sorted(p for p in Path(src).rglob('*') if p.is_file())
            for p in files[:len(files) // 2]:
                (Path(dst) / p.relative_to(src)).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, Path(dst) / p.relative_to(src))
            raise OSError('power cut')

        def replace_fails_for(suffix):  # crash just before one rename (flushed side file already written)
            def replace(src, dst):
                if str(src).endswith(suffix):
                    raise OSError('power cut')
                return real_replace(src, dst)
            return patch.object(installer.os, 'replace', side_effect=replace)

        def crash(exc=OSError('power cut')):
            raise exc

        faults = {
            'part-way through copying': lambda: patch.object(installer.shutil, 'copytree', side_effect=half_copy),
            'before the release folder is renamed into place': lambda: replace_fails_for('.incoming-1.1.0-abc'),
            'while stopping the running JARVIS': lambda: patch.object(self, 'stop', side_effect=lambda h: crash()),
            'while writing the launcher': lambda: replace_fails_for('JARVIS.ps1.pending'),
            'while switching current.json': lambda: replace_fails_for('current.json.pending'),
            'while writing shortcuts': lambda: patch.object(installer, 'write_shortcuts', side_effect=lambda h: crash()),
        }
        for step, fault in faults.items():
            with self.subTest(step=step):
                shutil.rmtree(self.home, ignore_errors=True)
                self.install(self.v1)
                (self.home / 'data' / 'jarvis.sqlite3').write_bytes(b'memory')
                with patch.object(installer, 'write_shortcuts'), fault(), self.assertRaises(OSError):  # never real shortcuts
                    installer.install(self.v2, self.home, shortcuts=True, stop=lambda h: self.stop(h))
                current = self.current()['release']
                self.assertIn(current, ('1.0.0-abc', '1.1.0-abc'))
                installer.verify_release(self.home / 'releases' / current)  # whichever is current is intact
                self.assertEqual((self.home / 'JARVIS.ps1').read_text(encoding='utf-8'), installer.LAUNCHER)
                self.assertEqual((self.home / 'data' / 'jarvis.sqlite3').read_bytes(), b'memory')
                self.install(self.v2)  # running the installer again completes the update
                self.assertEqual((self.current()['release'], self.current()['previous']), ('1.1.0-abc', '1.0.0-abc'))
                installer.verify_release(self.home / 'releases' / '1.1.0-abc')
                self.assertEqual([p.name for p in (self.home / 'releases').iterdir() if p.name.startswith('.')], [])
                self.assertEqual((self.home / 'data' / 'jarvis.sqlite3').read_bytes(), b'memory')
        self.assertIs(installer.shutil.copytree, real_copytree)

    def test_a_damaged_installed_release_is_repaired_by_reinstalling(self):
        self.install(self.v1)
        self.install(self.v2)
        (self.home / 'releases' / '1.1.0-abc' / 'app' / 'server.py').write_bytes(b'# damaged')
        self.stops.clear()
        self.install(self.v2)  # the running release: JARVIS is stopped, then the folder is replaced
        installer.verify_release(self.home / 'releases' / '1.1.0-abc')
        self.assertEqual(len(self.stops), 1)
        self.assertEqual((self.current()['release'], self.current()['previous']), ('1.1.0-abc', '1.0.0-abc'))
        (self.home / 'releases' / '1.0.0-abc' / 'app' / 'server.py').unlink()
        self.install(self.v1)  # a damaged older release is repaired too
        installer.verify_release(self.home / 'releases' / '1.0.0-abc')
        self.assertEqual(self.current()['release'], '1.0.0-abc')
        self.assertEqual([p.name for p in (self.home / 'releases').iterdir() if p.name.startswith('.')], [])

    def test_rollback_and_refusals(self):
        self.install(self.v1)
        with self.assertRaises(installer.InstallError):
            installer.rollback(self.home, stop=self.stop)  # nothing to roll back to
        self.install(self.v2)
        result = installer.rollback(self.home, stop=self.stop)
        self.assertEqual((result['release'], result['previous']), ('1.0.0-abc', '1.1.0-abc'))
        (self.home / 'releases' / '1.1.0-abc' / 'app' / 'server.py').write_bytes(b'# changed')
        with self.assertRaises(installer.InstallError):
            installer.rollback(self.home, stop=self.stop)  # a damaged release is never activated
        self.assertEqual(self.current()['release'], '1.0.0-abc')

    def test_uninstall_keeps_data_and_reinstall_reuses_it(self):
        self.install(self.v1)
        self.install(self.v2)
        (self.home / 'data' / 'jarvis.sqlite3').write_bytes(b'memory')
        (self.home / 'releases' / '1.0.0-abc' / 'app' / 'owner-note.txt').write_bytes(b'not ours')
        result = installer.uninstall(self.home, shortcuts=False, stop=self.stop)
        self.assertEqual(sorted(result['kept']), ['config', 'data', 'profile'])
        self.assertFalse((self.home / 'current.json').exists())
        self.assertFalse((self.home / 'JARVIS.ps1').exists())
        self.assertFalse((self.home / 'releases' / '1.1.0-abc').exists())
        self.assertTrue((self.home / 'releases' / '1.0.0-abc' / 'app' / 'owner-note.txt').exists())  # unlisted file left
        self.install(self.v2)
        self.assertEqual((self.home / 'data' / 'jarvis.sqlite3').read_bytes(), b'memory')
        self.assertEqual(self.current()['release'], '1.1.0-abc')

    def test_data_is_removed_only_with_the_exact_confirmation(self):
        self.install(self.v1)
        (self.home / 'data' / 'jarvis.sqlite3').write_bytes(b'memory')
        with self.assertRaises(installer.InstallError):
            installer.uninstall(self.home, remove_data='yes', shortcuts=False, stop=self.stop)
        self.assertTrue((self.home / 'data' / 'jarvis.sqlite3').exists())
        result = installer.uninstall(self.home, remove_data=installer.CONFIRM_DATA_REMOVAL, shortcuts=False, stop=self.stop)
        self.assertEqual(result['kept'], [])
        self.assertFalse((self.home / 'data').exists())

    def test_reinstalling_the_same_release_is_idempotent(self):
        self.install(self.v1)
        self.install(self.v1)
        self.assertEqual(self.current()['release'], '1.0.0-abc')
        self.assertIsNone(self.current()['previous'])
        self.assertEqual(self.stops, [])

    def test_unsafe_manifest_paths_are_refused(self):
        manifest = json.loads((self.v1 / 'release' / 'manifest.json').read_text(encoding='utf-8'))
        manifest['files'].append({'path': '../escape.txt', 'sha256': '0' * 64, 'bytes': 0})
        (self.v1 / 'release' / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaises(installer.InstallError):
            self.install(self.v1)

    def test_powershell_quoting(self):
        self.assertEqual(installer.ps_quote("C:\\Users\\O'Brien\\JARVIS"), "'C:\\Users\\O''Brien\\JARVIS'")


if __name__ == '__main__':
    unittest.main()
