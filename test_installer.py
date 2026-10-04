"""tools/installer.py on synthetic releases in a temporary home (no shortcuts, no processes)."""
import contextlib
import hashlib
import http.server
import io
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
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

    def test_timings_keep_verifying_an_installed_release_out_of_stop(self):
        # Gate 19 G6 and Stage 7 G6 recorded about 95 s as 'stop': it was mostly this check.
        self.install(self.v1)
        self.install(self.v2)
        installer.rollback(self.home, stop=self.stop)
        now = [0]

        def tick():
            now[0] += 1
            return now[0]

        real_verify = installer.verify_release

        def slow_verify(*args, **kw):
            now[0] += 1000  # verifying is the slow part
            return real_verify(*args, **kw)

        with patch.object(installer.time, 'perf_counter', side_effect=tick), \
                patch.object(installer, 'verify_release', side_effect=slow_verify):
            result = self.install(self.v2)  # update again: the release is already installed
        self.assertEqual(set(result['seconds']), {'verify_package', 'verify_installed', 'stop', 'switch'})
        self.assertGreaterEqual(result['seconds']['verify_installed'], 1000)
        self.assertLess(result['seconds']['stop'], 1000)  # stopping only, no verification in it

    def test_rollback_and_uninstall_report_phase_seconds(self):
        self.install(self.v1)
        self.install(self.v2)
        self.assertEqual(set(installer.rollback(self.home, stop=self.stop)['seconds']), {'verify_target', 'stop', 'switch'})
        self.assertEqual(set(installer.uninstall(self.home, shortcuts=False, stop=self.stop)['seconds']), {'stop', 'remove_program'})

    def test_install_rollback_uninstall_refuse_with_the_installed_python(self):
        # Stopping JARVIS ends every program in releases\, which would end the installer itself.
        self.install(self.v1)
        self.install(self.v2)
        self.stops.clear()
        before = (self.current(), sorted(p.relative_to(self.home) for p in self.home.rglob('*')))
        own = self.home / 'releases' / '1.0.0-abc' / 'python' / 'python.exe'
        actions = {'install': lambda: self.install(self.v1),
                   'rollback': lambda: installer.rollback(self.home, stop=self.stop),
                   'uninstall': lambda: installer.uninstall(self.home, shortcuts=False, stop=self.stop)}
        with patch.object(installer.sys, 'executable', str(own)):
            for action, run in actions.items():
                with self.subTest(action=action), self.assertRaises(installer.InstallError) as caught:
                    run()
                self.assertIn("package's Python", str(caught.exception))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(installer.main(['status', '--home', str(self.home)]), 0)  # reading is still allowed
        self.assertEqual(self.stops, [])  # nothing was stopped
        self.assertEqual((self.current(), sorted(p.relative_to(self.home) for p in self.home.rglob('*'))), before)

    def test_another_homes_python_is_not_refused(self):
        other = self.base / 'other-home' / 'releases' / '1.0.0-abc' / 'python' / 'python.exe'
        look_alike = self.base / 'home' / 'releases-old' / 'python.exe'
        for exe in (other, look_alike):
            with self.subTest(exe=exe), patch.object(installer.sys, 'executable', str(exe)):
                self.assertIsNone(installer.running_from_installation(self.home))

    def test_stop_never_ends_the_installers_own_process(self):
        (self.home / 'releases').mkdir(parents=True)
        with patch.object(installer.os, 'name', 'nt'), patch.object(installer.subprocess, 'run') as run:
            installer.stop_running_jarvis(self.home)
        script = run.call_args[0][0][-1]
        self.assertIn(f'$_.ProcessId -ne {os.getpid()}', script)
        self.assertIn(str(self.home / 'releases'), script)

    def test_a_left_over_connection_file_costs_no_wait(self):
        # A Core that crashed or was ended leaves core-connection.json; nothing listens there.
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        (self.home / 'data').mkdir(parents=True)
        link = self.home / 'data' / 'core-connection.json'
        link.write_text(json.dumps({'origin': f'http://127.0.0.1:{port}', 'token': 'a' * 64}), encoding='utf-8')
        started = time.monotonic()
        self.assertFalse(installer.ask_core_to_stop(link))
        installer.stop_running_jarvis(self.home, timeout=30)  # no releases folder: nothing to end
        self.assertLess(time.monotonic() - started, 15)  # was a fixed 30 s wait
        self.assertTrue(link.exists())  # never deleted by the installer

    def test_shutdown_request_reaches_the_core_despite_proxy_settings(self):
        seen = []

        class Core(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Set-Cookie', 'jarvis_session=s1; HttpOnly')
                self.end_headers()

            def do_POST(self):
                seen.append((self.path, self.headers.get('X-Jarvis-Desktop'), self.headers.get('Cookie')))
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(('127.0.0.1', 0), Core)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        (self.home / 'data').mkdir(parents=True)
        link = self.home / 'data' / 'core-connection.json'
        link.write_text(json.dumps({'origin': f'http://127.0.0.1:{server.server_port}', 'token': 't' * 64}), encoding='utf-8')
        dead_proxy = {'HTTP_PROXY': 'http://127.0.0.1:9', 'http_proxy': 'http://127.0.0.1:9', 'NO_PROXY': '', 'no_proxy': ''}
        # Clear urllib's cached global opener too, or a urlopen-based version would reuse proxy settings from earlier tests.
        with patch.dict(os.environ, dead_proxy), patch.object(urllib.request, '_opener', None):
            self.assertTrue(installer.ask_core_to_stop(link))
        self.assertEqual(seen, [('/api/shutdown', 't' * 64, 'jarvis_session=s1')])

    def test_a_busy_core_that_times_out_still_gets_the_wait(self):
        # Only 'nothing listens' skips the wait; a busy or already stopping Core must not be ended at once.
        (self.home / 'data').mkdir(parents=True)
        link = self.home / 'data' / 'core-connection.json'
        link.write_text(json.dumps({'origin': 'http://127.0.0.1:1', 'token': 'a' * 64}), encoding='utf-8')
        for error in (TimeoutError('timed out'), urllib.error.URLError(TimeoutError('timed out')), ConnectionResetError()):
            with self.subTest(error=error), patch.object(urllib.request.OpenerDirector, 'open', side_effect=error):
                self.assertTrue(installer.ask_core_to_stop(link))
        with patch.object(urllib.request.OpenerDirector, 'open', side_effect=TimeoutError('timed out')):
            started = time.monotonic()
            installer.stop_running_jarvis(self.home, timeout=1)  # no releases folder: nothing to end
        self.assertGreaterEqual(time.monotonic() - started, 0.9)
        self.assertTrue(link.exists())


if __name__ == '__main__':
    unittest.main()
