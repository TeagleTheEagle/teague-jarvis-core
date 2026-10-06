"""tools/installer.py on synthetic releases in a temporary home (no shortcuts, no processes)."""
import contextlib
import hashlib
import http.server
import io
import json
import os
import shutil
import socket
import subprocess
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
# A release of 1.0.17 or later: its own program file, no electron.exe (docs/OWN-APP-PLAN.md 3.1).
APP_EXE = {**{k: v for k, v in APP.items() if k != 'electron/electron.exe'}, 'electron/JARVIS.exe': b'MZ-JARVIS',
           'electron/resources/app/main.cjs': b'// bootstrap', 'electron/resources/app/package.json': b'{"main": "main.cjs"}'}


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
        # Never the real Desktop and Startup folders of this PC: every shortcut write is recorded instead.
        self.shortcut_writes = []
        guard = patch.object(installer, 'write_shortcuts', side_effect=lambda home, release_id: self.shortcut_writes.append((str(home), release_id)))
        guard.start()
        self.addCleanup(guard.stop)
        removal = patch.object(installer, 'remove_shortcuts', side_effect=lambda name=installer.SHORTCUT: self.shortcut_writes.append(('remove', name)))
        removal.start()
        self.addCleanup(removal.stop)

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
            'while writing shortcuts': lambda: patch.object(installer, 'write_shortcuts', side_effect=lambda h, r: crash()),
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
        self.assertEqual(installer.ps_quote('D\u2019Arcy \u2018\u201a\u201b'), "'D\u2019\u2019Arcy \u2018\u2018\u201a\u201a\u201b\u201b'")

    @unittest.skipUnless(os.name == 'nt', 'Windows PowerShell')
    def test_powershell_quoting_round_trips_every_single_quote_mark(self):
        # PowerShell also reads the typographic single quotes as quote marks: a folder named D'Arcy with a curly
        # apostrophe broke the process-ending script (independent review of the 1.0.13 installer change).
        text = "C:\\Users\\D\u2019Arcy \u2018x\u2019 \u201ay\u201b O'Brien\\JARVIS"
        done = installer.subprocess.run(['powershell', '-NoProfile', '-Command',
                                         '(' + installer.ps_quote(text) + ').ToCharArray() | ForEach-Object { [int]$_ }'],
                                        capture_output=True, text=True, timeout=60)
        self.assertEqual([int(n) for n in done.stdout.split()], [ord(c) for c in text])

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
        self.assertEqual(set(installer.rollback(self.home, stop=self.stop, shortcuts=False)['seconds']), {'verify_target', 'stop', 'switch'})
        self.assertEqual(set(installer.rollback(self.home, stop=self.stop, shortcuts=True)['seconds']), {'verify_target', 'stop', 'switch', 'shortcuts'})  # 1.0.17: the shortcuts follow the program
        self.assertEqual(set(installer.rollback(self.home, stop=self.stop)['seconds']), {'verify_target', 'stop', 'switch'})  # the default: a home that is not this PC's own gets none
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
        done = installer.subprocess.CompletedProcess([], 0, stdout='remaining=0\n')
        with patch.object(installer.os, 'name', 'nt'), patch.object(installer.subprocess, 'run', return_value=done) as run:
            installer.stop_running_jarvis(self.home)
        script = run.call_args[0][0][-1]
        self.assertIn(f'$own={os.getpid()};', script)
        self.assertIn('$_.ProcessId -ne $own', script)
        self.assertIn(str(self.home / 'releases'), script)

    def test_stop_refuses_when_jarvis_is_still_running_afterwards(self):
        # Nothing may be switched or deleted while a program file is in use (Stage 7 rehearsal of 1.0.12:
        # an uninstall reached electron.exe while a closing JARVIS window still ran).
        (self.home / 'releases').mkdir(parents=True)
        for stdout in ('remaining=2\n', 'remaining=\n'):  # 'remaining=' alone: one process left (PowerShell 5.1 .Count)
            done = installer.subprocess.CompletedProcess([], 0, stdout=stdout)
            with self.subTest(stdout=stdout), patch.object(installer.os, 'name', 'nt'), \
                    patch.object(installer.subprocess, 'run', return_value=done), self.assertRaises(installer.InstallError) as caught:
                installer.stop_running_jarvis(self.home)
            self.assertIn('could not be stopped', str(caught.exception))

    def test_stop_refuses_when_the_check_itself_fails(self):
        # A failed process search must never pass as "nothing running" (independent review of the 1.0.13 change).
        (self.home / 'releases').mkdir(parents=True)
        outcomes = {'script error, then remaining=0': installer.subprocess.CompletedProcess([], 1, stdout='remaining=0\n'),
                    'no answer': installer.subprocess.CompletedProcess([], 0, stdout='garbage\n'),
                    'nothing printed': installer.subprocess.CompletedProcess([], 0, stdout=''),
                    'timed out': installer.subprocess.TimeoutExpired('powershell', 180),
                    'no PowerShell': FileNotFoundError(2, 'not found')}
        for name, outcome in outcomes.items():
            run = {'side_effect': outcome} if isinstance(outcome, BaseException) else {'return_value': outcome}
            with self.subTest(name), patch.object(installer.os, 'name', 'nt'), \
                    patch.object(installer.subprocess, 'run', **run), self.assertRaises(installer.InstallError) as caught:
                installer.stop_running_jarvis(self.home)
            self.assertIn('could not check', str(caught.exception))

    @unittest.skipUnless(os.name == 'nt', 'Windows PowerShell')
    def test_a_failed_process_search_never_reads_as_nothing_running(self):
        releases = self.home / 'releases'
        releases.mkdir(parents=True)
        script = installer.end_processes_script(releases, os.getpid())
        run = lambda text: installer.subprocess.run(['powershell', '-NoProfile', '-Command', text], capture_output=True,
                                                    text=True, errors='replace', timeout=120)
        done = run(script)  # nothing runs from this test folder
        self.assertEqual((done.returncode, done.stdout.strip()), (0, 'remaining=0'))
        self.assertIn('Get-CimInstance Win32_Process', script)
        done = run(script.replace('Get-CimInstance Win32_Process', 'Get-CimInstance Win32_NoSuchClass'))
        self.assertNotEqual(done.returncode, 0)
        self.assertNotIn('remaining=', done.stdout)

    def test_repairing_a_release_that_is_still_in_use_is_refused_plainly(self):
        self.install(self.v1)
        (self.home / 'releases' / '1.0.0-abc' / 'app' / 'server.py').write_bytes(b'# damaged')
        real_replace = installer.os.replace

        def replace(src, dst):
            if Path(dst).name.startswith('.damaged-'):  # a folder in the release is some program's working folder
                raise PermissionError(5, 'Access is denied', str(src))
            return real_replace(src, dst)

        with patch.object(installer.os, 'replace', side_effect=replace), self.assertRaises(installer.InstallError) as caught:
            self.install(self.v1)
        self.assertIn('still in use', str(caught.exception))
        self.assertEqual(self.current()['release'], '1.0.0-abc')

    @unittest.skipUnless(os.name == 'nt', 'Windows process handling')
    def test_stop_ends_every_program_of_this_home_and_waits_until_they_are_gone(self):
        # Stand-ins for JARVIS programs: copies of Windows' own PING.EXE running from this test home's releases.
        # Only processes whose executable lives there can be ended; nothing else on the PC is touched.
        folder = self.home / 'releases' / '1.0.0-abc' / 'electron'
        folder.mkdir(parents=True)
        ping = folder / 'ping.exe'
        shutil.copyfile(Path(os.environ['SYSTEMROOT']) / 'System32' / 'PING.EXE', ping)
        outside = self.base / 'elsewhere'
        outside.mkdir()
        shutil.copyfile(ping, outside / 'ping.exe')
        flags = getattr(installer.subprocess, 'CREATE_NO_WINDOW', 0)
        inside = [installer.subprocess.Popen([str(ping), '-n', '120', '127.0.0.1'], stdout=installer.subprocess.DEVNULL, creationflags=flags) for _ in range(3)]
        other = installer.subprocess.Popen([str(outside / 'ping.exe'), '-n', '120', '127.0.0.1'], stdout=installer.subprocess.DEVNULL, creationflags=flags)
        try:
            installer.stop_running_jarvis(self.home)
            self.assertTrue(all(p.poll() is not None for p in inside))  # gone, not just asked to go
            self.assertIsNone(other.poll())  # a look-alike outside this home's releases keeps running
            ping.unlink()  # the program file is free at once
        finally:
            for p in inside + [other]:
                if p.poll() is None:
                    p.kill()
                p.wait(10)

    @unittest.skipUnless(os.name == 'nt', 'Windows process handling')
    def test_stop_ends_a_program_started_through_a_short_folder_name(self):
        # Windows reports a program's path as it was started; an 8.3 short spelling of this home's releases
        # folder must still be recognised (independent review of the 1.0.13 installer change).
        import ctypes
        folder = self.home / 'releases' / '1.0.0-abc' / 'electron-runtime'
        folder.mkdir(parents=True)
        ping = folder / 'ping.exe'
        shutil.copyfile(Path(os.environ['SYSTEMROOT']) / 'System32' / 'PING.EXE', ping)
        buffer = ctypes.create_unicode_buffer(1024)
        short = buffer.value if ctypes.windll.kernel32.GetShortPathNameW(str(ping), buffer, 1024) else str(ping)
        if os.path.normcase(short) == os.path.normcase(str(ping)):
            self.skipTest('this volume has no 8.3 short names')
        flags = getattr(installer.subprocess, 'CREATE_NO_WINDOW', 0)
        program = installer.subprocess.Popen([short, '-n', '120', '127.0.0.1'], stdout=installer.subprocess.DEVNULL, creationflags=flags)
        try:
            installer.stop_running_jarvis(self.home)
            self.assertIsNotNone(program.poll())
        finally:
            if program.poll() is None:
                program.kill()
            program.wait(10)

    def test_uninstall_waits_briefly_for_a_file_still_in_use_and_otherwise_leaves_jarvis_not_installed(self):
        self.install(self.v1)
        real_unlink, refusals = Path.unlink, []

        def locked(times):
            def unlink(path, missing_ok=False):
                if path.name == 'electron.exe' and len(refusals) < times:
                    refusals.append(path)
                    raise PermissionError(13, 'in use', str(path))
                return real_unlink(path, missing_ok=missing_ok)
            return unlink

        with patch.object(Path, 'unlink', locked(3)):  # released after a moment: the uninstall completes
            self.assertEqual(installer.uninstall(self.home, shortcuts=False, stop=self.stop)['status'], 'uninstalled')
        self.assertEqual(len(refusals), 3)
        self.install(self.v1)
        refusals.clear()
        with patch.object(Path, 'unlink', locked(10 ** 6)), patch.object(installer.time, 'sleep'), \
                patch.object(installer.time, 'monotonic', side_effect=iter(range(0, 10 ** 6, 5))), \
                self.assertRaises(installer.InstallError) as caught:
            installer.uninstall(self.home, shortcuts=False, stop=self.stop)
        self.assertIn('still in use', str(caught.exception))
        self.assertFalse((self.home / 'current.json').exists())  # nothing points at a half-removed release
        self.assertEqual(installer.uninstall(self.home, shortcuts=False, stop=self.stop)['status'], 'uninstalled')  # a rerun finishes
        self.assertEqual([p for p in (self.home / 'releases').rglob('*') if p.is_file()] if (self.home / 'releases').exists() else [], [])

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

    def test_the_command_line_never_touches_real_shortcuts_for_a_home_that_is_not_this_pcs_own(self):
        # 2026-10-07: a sandbox Setup rehearsal whose /NOSHORTCUTS never reached this script wrote and then removed the
        # owner's real shortcuts. Now the command line writes or removes them only for this PC's own install home.
        answers = []

        def run(*argv):
            with patch('sys.stdout', new=io.StringIO()) as out:
                self.assertEqual(installer.main(list(argv)), 0)
            answers.append(json.loads(out.getvalue()).get('shortcuts'))
        home = str(self.home)
        run('install', '--package', str(self.v1), '--home', home)
        run('install', '--package', str(self.v2), '--home', home, '--replace-legacy-shortcuts')
        run('rollback', '--home', home)
        run('uninstall', '--home', home)
        self.assertEqual(self.shortcut_writes, [])  # a home that is not this PC's own: nothing written, nothing removed
        self.assertEqual(set(answers), {"withheld (the home is not this PC's own install home)"})
        with patch.object(installer, 'default_home', return_value=self.home):
            run('install', '--package', str(self.v1), '--home', home)
            run('install', '--package', str(self.v2), '--home', home, '--replace-legacy-shortcuts')
            run('rollback', '--home', home)
            run('uninstall', '--home', home)
        self.assertEqual([(w[0], w[1].split('-')[0]) if w[0] != 'remove' else w for w in self.shortcut_writes],
                         [(home, '1.0.0'), (home, '1.1.0'), ('remove', installer.LEGACY_SHORTCUT), (home, '1.0.0'), ('remove', installer.SHORTCUT)])
        self.assertEqual(answers[4:], ['written', 'written', 'written', 'removed'])
        with patch.object(installer, 'default_home', return_value=self.home):
            run('install', '--package', str(self.v1), '--home', home, '--no-shortcuts')
        self.assertEqual((len(self.shortcut_writes), answers[-1]), (5, 'skipped (--no-shortcuts)'))  # --no-shortcuts still holds for the PC's own home
        self.assertFalse(installer.own_home(self.home))
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(installer.own_home(self.home))  # no %LOCALAPPDATA%: never "own", never a traceback


if __name__ == '__main__':
    unittest.main()


class OwnAppTests(unittest.TestCase):
    """Release 1.0.17 (docs/OWN-APP-PLAN.md 3.2 and 3.3): shortcuts straight at JARVIS.exe, also on rollback;
    JARVIS.ps1 only for a release that has no program file of its own."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.home = self.base / 'home'
        self.old = make_package(self.base, '1.0.16', APP)
        self.new = make_package(self.base, '1.0.17', APP_EXE)
        self.scripts = []
        def fake_run(command, **kw):
            # Records every PowerShell script instead of running it; answers the process check with nothing running.
            self.scripts.append(command[-1])
            return subprocess.CompletedProcess(command, 0, 'remaining=0\n', '')
        patcher = patch.object(installer.subprocess, 'run', side_effect=fake_run)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.stop = lambda home: None

    def test_a_release_with_its_own_program_gets_no_launcher_script_and_shortcuts_at_the_program(self):
        result = installer.install(self.new, self.home, shortcuts=True, stop=self.stop)
        self.assertEqual(result['release'], '1.0.17-abc')
        self.assertFalse((self.home / 'JARVIS.ps1').exists())
        program = self.home / 'releases' / '1.0.17-abc' / 'electron' / 'JARVIS.exe'
        self.assertEqual(installer.program_file(self.home, '1.0.17-abc'), program)
        self.assertEqual(len(self.scripts), 1)
        script = self.scripts[0]
        self.assertIn(installer.ps_quote(program), script)
        self.assertIn("'--login-launch'", script)
        self.assertIn(installer.ps_quote(str(program) + ',0'), script)   # the shortcut carries the program's icon
        self.assertNotIn('powershell.exe', script)
        self.assertNotIn('JARVIS.ps1', script)

    def test_an_older_release_keeps_the_launcher_script_and_powershell_shortcuts(self):
        installer.install(self.old, self.home, shortcuts=True, stop=self.stop)
        self.assertEqual((self.home / 'JARVIS.ps1').read_text(encoding='utf-8'), installer.LAUNCHER)
        self.assertIsNone(installer.program_file(self.home, '1.0.16-abc'))
        self.assertIn('powershell.exe', self.scripts[0])
        self.assertIn('JARVIS.ps1', self.scripts[0])

    def test_an_update_to_the_own_program_removes_the_old_launcher_file_and_a_rollback_writes_it_again(self):
        installer.install(self.old, self.home, shortcuts=True, stop=self.stop)
        installer.install(self.new, self.home, shortcuts=True, stop=self.stop)
        self.assertFalse((self.home / 'JARVIS.ps1').exists())          # decision D6: its text would start an electron.exe 1.0.17 has not
        self.assertIn('JARVIS.exe', self.scripts[-1])
        result = installer.rollback(self.home, stop=self.stop, shortcuts=True)  # on: the shortcuts follow the program
        self.assertEqual(result['release'], '1.0.16-abc')
        self.assertIn('shortcuts', result['seconds'])
        self.assertEqual((self.home / 'JARVIS.ps1').read_text(encoding='utf-8'), installer.LAUNCHER)
        self.assertIn('JARVIS.ps1', self.scripts[-1])                    # the shortcuts followed the program
        self.assertNotIn('JARVIS.exe', self.scripts[-1])
        installer.install(self.new, self.home, shortcuts=True, stop=self.stop)   # update again: back at the program
        self.assertIn('JARVIS.exe', self.scripts[-1])

    def test_a_rollback_without_shortcuts_writes_none(self):
        installer.install(self.old, self.home, shortcuts=False, stop=self.stop)
        installer.install(self.new, self.home, shortcuts=False, stop=self.stop)
        self.assertEqual(self.scripts, [])
        result = installer.rollback(self.home, stop=self.stop, shortcuts=False)
        self.assertEqual(result['release'], '1.0.16-abc')
        self.assertEqual(self.scripts, [])
        self.assertNotIn('shortcuts', result['seconds'])

    def test_the_command_line_passes_no_shortcuts_to_rollback(self):
        installer.install(self.old, self.home, shortcuts=False, stop=self.stop)
        installer.install(self.new, self.home, shortcuts=False, stop=self.stop)
        with patch.object(installer, 'stop_running_jarvis', self.stop), patch('sys.stdout', new=io.StringIO()) as out:
            self.assertEqual(installer.main(['rollback', '--home', str(self.home), '--no-shortcuts']), 0)
        self.assertEqual(json.loads(out.getvalue())['release'], '1.0.16-abc')
        self.assertEqual([s for s in self.scripts if 'CreateShortcut' in s], [])   # the stop check ran; no shortcut script

    def test_uninstall_removes_the_launcher_script_whichever_release_was_current(self):
        installer.install(self.new, self.home, shortcuts=False, stop=self.stop)
        (self.home / 'JARVIS.ps1').write_text('left over', encoding='utf-8')
        installer.uninstall(self.home, shortcuts=False, stop=self.stop)
        self.assertFalse((self.home / 'JARVIS.ps1').exists())
        self.assertFalse((self.home / 'current.json').exists())
