import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

import core_lock

ROOT = Path(__file__).resolve().parent


class CoreLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / 'data'

    def test_second_owner_is_refused_and_named(self):
        first = core_lock.CoreLock(self.data)
        self.addCleanup(first.release)
        first.publish(4321)
        with self.assertRaises(core_lock.CoreAlreadyRunning) as raised:
            core_lock.CoreLock(self.data)
        self.assertEqual(raised.exception.owner['pid'], os.getpid())
        self.assertIn('port 4321', str(raised.exception))

    def test_release_allows_next_owner_and_removes_own_record(self):
        first = core_lock.CoreLock(self.data)
        first.publish(1111)
        first.release()
        self.assertFalse((self.data / core_lock.OWNER_NAME).exists())
        second = core_lock.CoreLock(self.data)
        self.addCleanup(second.release)

    def test_release_keeps_another_owners_record(self):
        first = core_lock.CoreLock(self.data)
        first.publish(1111)
        (self.data / core_lock.OWNER_NAME).write_text(json.dumps({'pid': -1, 'port': 2}), encoding='utf-8')
        first.release()
        self.assertEqual(core_lock.read_owner(self.data)['pid'], -1)

    def test_owner_record_contains_no_secret_fields(self):
        lock = core_lock.CoreLock(self.data)
        self.addCleanup(lock.release)
        lock.publish(5555)
        self.assertEqual(set(core_lock.read_owner(self.data)), {'pid', 'port', 'started'})

    def test_different_data_folders_are_independent(self):
        first = core_lock.CoreLock(self.data)
        self.addCleanup(first.release)
        other = core_lock.CoreLock(Path(self.temp.name) / 'other')
        self.addCleanup(other.release)


class CoreProcessTests(unittest.TestCase):
    """Real server.py processes against one data folder."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = str(Path(self.temp.name) / 'data')
        self.env = {k: v for k, v in os.environ.items() if k != 'JARVIS_DESKTOP_TOKEN'}

    def start(self):
        process = subprocess.Popen([sys.executable, '-u', str(ROOT / 'server.py'), '--port', '0', '--data-dir', self.data],
                                   cwd=ROOT, env=self.env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True)
        self.addCleanup(self.stop, process)
        return process

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.kill()
            process.wait(timeout=20)
        if process.stdout:
            process.stdout.close()

    def wait_ready(self, process):
        lines = []
        def read():
            for line in process.stdout:
                lines.append(line)
                if 'JARVIS ready at' in line:
                    return
        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        reader.join(90)
        ready = [line for line in lines if 'JARVIS ready at' in line]
        self.assertTrue(ready, 'Core did not become ready: ' + ''.join(lines)[-500:])
        return ready[0].split('JARVIS ready at ')[1].strip()

    def test_second_core_on_same_data_is_refused_and_crash_releases_ownership(self):
        first = self.start()
        origin = self.wait_ready(first)
        self.assertEqual(core_lock.read_owner(self.data)['port'], int(origin.rsplit(':', 1)[1]))

        second = self.start()
        output, _ = second.communicate(timeout=60)
        self.assertEqual(second.returncode, core_lock.ALREADY_RUNNING_EXIT_CODE)
        self.assertIn('already running for this data folder', output)
        with urllib.request.urlopen(origin, timeout=5) as response:  # first Core unaffected
            self.assertEqual(response.status, 200)

        first.kill()  # abrupt exit: no cleanup code runs, the OS must release the lock
        first.wait(timeout=20)
        deadline = time.monotonic() + 20
        third = None
        while time.monotonic() < deadline:
            third = self.start()
            try:
                self.wait_ready(third)
                break
            except AssertionError:
                if third.poll() != core_lock.ALREADY_RUNNING_EXIT_CODE:
                    raise
                time.sleep(0.5)
        self.assertIsNone(third.poll(), 'Core could not start after the previous owner crashed')


if __name__ == '__main__':
    unittest.main()
