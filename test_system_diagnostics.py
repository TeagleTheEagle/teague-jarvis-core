"""The tool system_diagnostics (the owner's request of 2026-10-12): this PC's live condition, read only. Windows is faked
here (no PowerShell; the ctypes readings replaced): every part, what draws attention and what does not, a part Windows does
not give, nothing at all, the battery in words, the script pinned to reading only, the dashboard's own processor reading
left alone; then the tool through the Core for the PC's own question, and a paired device without the owner's tick
refused."""
import ctypes
import json
import os
import re
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import providers
import system_diagnostics as diag
import system_metrics
from server import Run
from test_device_gateway import DONE, ENV, DeviceCase, calls

GB = 1024 ** 3
WINDOWS = {'programs': [{'name': 'chrome', 'count': 12, 'memory': 1358 * 1024 ** 2},
                        {'name': 'odd\x07 name\n\tthere', 'count': 1, 'memory': 10 * 1024 ** 2}],
           # A single object instead of a list (the script's @() gives a list; the reader takes either).
           'adapters': {'Name': 'Wi-Fi', 'InterfaceDescription': 'TP-Link Wi-Fi 6 PCIe Adapter', 'Status': 'Up', 'LinkSpeed': '573.5 Mbps'}}
DRIVES = {'C:\\': ('fixed', {'free_bytes': 5 * GB, 'total_bytes': 100 * GB}),
          'D:\\': ('fixed', {'free_bytes': 650 * GB, 'total_bytes': 1000 * GB}),
          'E:\\': ('removable', None),        # an empty card reader
          'Z:\\': (None, None)}               # a network drive: not read at all
BUSY = ((0, 0, 0), (5, 100, 100))             # 97.5% busy over the reading
QUIET = ((100, 200, 300), (150, 400, 500))    # 87.5%
AT_LIMIT = ((0, 0, 0), (10, 50, 50))          # exactly 90.0%


def fake_run(script):
    """Windows PowerShell, faked; the boundary pinned on the real script."""
    assert script.startswith(diag.PREFIX)
    assert not any(word in script for word in diag.FORBIDDEN), script
    return json.dumps(WINDOWS)


def power(ac_line=1, flag=1, percent=80, saver=0, life=0xFFFFFFFF):
    return diag._PowerStatus(ac_line, flag, percent, saver, life, 0xFFFFFFFF)


class ReadingTests(unittest.TestCase):
    def windows(self, times=BUSY, memory=(93, 2.2, 31.9), drives=DRIVES, uptime=6.2, battery=None, run=fake_run):
        """Every part of Windows the tool reads, faked; returns the tool's reading."""
        disk = {root: usage for root, (_, usage) in drives.items()}
        patches = [patch.object(system_metrics, 'system_times', side_effect=list(times)),
                   patch.object(system_metrics, 'memory', return_value=memory and {
                       'used_percent': memory[0], 'available_bytes': int(memory[1] * GB), 'total_bytes': int(memory[2] * GB)}),
                   patch.object(diag.os, 'listdrives', create=True, return_value=list(drives)),
                   patch.object(diag, '_drive_kind', side_effect=lambda root: drives[root][0]),
                   patch.object(system_metrics, 'disk', side_effect=lambda root: disk[root]),
                   patch.object(diag, 'uptime_hours', return_value=uptime),
                   patch.object(diag, 'battery', return_value=battery),
                   patch.object(diag.sys, 'platform', 'win32')]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        return diag.reading(run=run, sleep=lambda seconds: None)

    def test_every_part_and_what_draws_attention(self):
        r = self.windows(battery={'present': True, 'percent': 15, 'on_mains': False, 'charging': False, 'saver_on': True, 'minutes_left': 40})
        self.assertEqual((r['status'], r['processor_percent'], r['windows_uptime_hours'], r['unreadable']), ('completed', 97.5, 6.2, []))
        self.assertEqual(r['memory'], {'used_percent': 93, 'available_gb': 2.2, 'total_gb': 31.9})
        self.assertEqual(r['drives'], [{'drive': 'C:', 'kind': 'fixed', 'free_gb': 5.0, 'total_gb': 100.0, 'free_percent': 5.0},
                                       {'drive': 'D:', 'kind': 'fixed', 'free_gb': 650.0, 'total_gb': 1000.0, 'free_percent': 65.0}])
        self.assertEqual(r['programs'], [{'name': 'chrome', 'processes': 12, 'memory_mb': 1358},
                                         {'name': 'odd name there', 'processes': 1, 'memory_mb': 10}])   # a name is text only
        self.assertEqual(r['network_adapters'], [{'name': 'Wi-Fi', 'description': 'TP-Link Wi-Fi 6 PCIe Adapter', 'status': 'Up', 'link_speed': '573.5 Mbps'}])
        self.assertEqual(r['attention'], ['The processor is 97.5% busy.', 'Memory is 93% in use: 2.2 GB free of 31.9 GB.',
                                          'Drive C: is nearly full: 5.0 GB free of 100.0 GB.', 'The battery is at 15% and not on mains power.'])
        self.assertRegex(r['read_at'], r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$')
        self.assertIn('nothing was changed, ended or started', r['scope'])
        self.assertIn('not instructions', r['scope'])

    def test_below_the_thresholds_nothing_is_flagged(self):
        drives = {'C:\\': ('fixed', {'free_bytes': 10 * GB, 'total_bytes': 100 * GB})}   # exactly 10% free is not "under 10%"
        on_mains = {'present': True, 'percent': 5, 'on_mains': True, 'charging': True, 'saver_on': False, 'minutes_left': None}
        r = self.windows(times=QUIET, memory=(89, 3.5, 31.9), drives=drives, battery=on_mains)
        self.assertEqual((r['processor_percent'], r['attention']), (87.5, []))
        # Power state unknown: a low battery is not called "not on mains".
        unknown = dict(on_mains, percent=20, on_mains=None)
        self.assertEqual(diag.attention({'processor_percent': None, 'memory': None, 'drives': [], 'battery': unknown}), [])

    def test_every_threshold_at_its_exact_limit(self):
        battery = {'present': True, 'percent': 20, 'on_mains': False, 'charging': False, 'saver_on': False, 'minutes_left': None}
        drives = {'C:\\': ('fixed', {'free_bytes': int(9.9 * GB), 'total_bytes': 100 * GB})}
        r = self.windows(times=AT_LIMIT, memory=(90, 3.2, 31.9), drives=drives, battery=battery)
        self.assertEqual(r['attention'], ['The processor is 90.0% busy.', 'Memory is 90% in use: 3.2 GB free of 31.9 GB.',
                                          'Drive C: is nearly full: 9.9 GB free of 100.0 GB.', 'The battery is at 20% and not on mains power.'])

    def test_names_and_rows_are_capped(self):
        many = {'programs': [{'name': 'p' * 200, 'count': 1, 'memory': 1}] * 20,
                'adapters': [{'Name': 'a', 'InterfaceDescription': 'd', 'Status': 'Up', 'LinkSpeed': ''}] * 30}
        programs, adapters = diag.programs_and_adapters(run=lambda script: json.dumps(many))
        self.assertEqual((len(programs), len(adapters)), (diag.MAX_PROGRAMS, diag.MAX_ADAPTERS))
        self.assertEqual(len(programs[0]['name']), diag.NAME_CHARACTERS)
        self.assertIsNone(adapters[0]['link_speed'])   # an empty speed is not a speed
        # A part Windows refused inside the script comes back null: that part only is unreadable.
        self.assertEqual(diag.programs_and_adapters(run=lambda script: json.dumps({'programs': None, 'adapters': []})), (None, []))
        # A value of the wrong kind is the plain failure, not a crash of the question.
        with self.assertRaisesRegex(ValueError, re.escape(diag.UNAVAILABLE)):
            diag.programs_and_adapters(run=lambda script: json.dumps({'programs': [{'name': 'x', 'count': 'many'}], 'adapters': []}))

    def test_an_unexpected_error_loses_one_part_not_the_answer(self):
        with patch.object(diag, 'drives', side_effect=OSError('the drive list failed')):
            r = self.windows(battery={'present': False, 'on_mains': True})
        self.assertEqual((r['status'], r['drives'], r['unreadable']), ('completed', None, ['drives']))

    def test_a_part_windows_does_not_give_is_none_and_named(self):
        def failing(script):
            raise ValueError(diag.UNAVAILABLE)
        r = self.windows(memory=None, battery={'present': False, 'on_mains': True}, run=failing)
        self.assertEqual((r['memory'], r['programs'], r['network_adapters']), (None, None, None))
        self.assertEqual(r['unreadable'], ['memory', 'programs', 'network_adapters'])
        self.assertEqual(r['drives'][0]['drive'], 'C:')   # the rest is still read
        # Text that is not JSON, or JSON that is not the answer, is the same plain failure.
        for answer in ('Get-Process : access denied', '[]'):
            with self.subTest(answer=answer), self.assertRaisesRegex(ValueError, re.escape(diag.UNAVAILABLE)):
                diag.programs_and_adapters(run=lambda script: answer)

    def test_nothing_readable_is_one_plain_sentence(self):
        with patch.object(diag.sys, 'platform', 'linux'), patch.object(system_metrics, 'system_times', return_value=None), \
                patch.object(system_metrics, 'memory', return_value=None), patch.object(diag, 'uptime_hours', return_value=None), \
                patch.object(diag, 'battery', return_value=None):
            with self.assertRaisesRegex(ValueError, re.escape(diag.UNAVAILABLE)):
                diag.reading(run=lambda script: 'null', sleep=lambda seconds: None)

    def test_the_battery_in_words(self):
        self.assertEqual(ctypes.sizeof(diag._PowerStatus), 12)   # SYSTEM_POWER_STATUS: 4 bytes, then two DWORDs
        self.assertIsNone(diag.battery_from(power(flag=255)))                                          # Windows cannot say
        self.assertEqual(diag.battery_from(power(flag=128)), {'present': False, 'on_mains': True})     # a desktop
        self.assertEqual(diag.battery_from(power(ac_line=0, flag=2, percent=18, saver=1, life=2400)),
                         {'present': True, 'percent': 18, 'on_mains': False, 'charging': False, 'saver_on': True, 'minutes_left': 40})
        self.assertEqual(diag.battery_from(power(ac_line=255, flag=8, percent=255)),
                         {'present': True, 'percent': None, 'on_mains': None, 'charging': True, 'saver_on': False, 'minutes_left': None})

    def test_the_script_only_reads(self):
        verbs = set(re.findall(r'\b([A-Z][A-Za-z]+)-[A-Z][A-Za-z]+\b', diag.SCRIPT))
        self.assertEqual(verbs, {'Get', 'Group', 'ForEach', 'Measure', 'Sort', 'Select', 'ConvertTo'})
        self.assertFalse([word for word in diag.FORBIDDEN if word in diag.SCRIPT])
        # The real call: Windows PowerShell from System32, no profile, never interactive, a time limit; a failure is the plain sentence.
        with patch.object(diag.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout='')) as run:
            with self.assertRaisesRegex(ValueError, re.escape(diag.UNAVAILABLE)):
                diag.programs_and_adapters()
        command = run.call_args.args[0]
        self.assertTrue(command[0].replace('\\', '/').lower().endswith('system32/windowspowershell/v1.0/powershell.exe'), command[0])
        self.assertEqual(command[1:4], ['-NoProfile', '-NonInteractive', '-Command'])
        self.assertEqual(run.call_args.kwargs['timeout'], diag.SCRIPT_SECONDS)

    def test_the_dashboards_own_reading_is_left_alone(self):
        kept = (1, 2, 3)
        with patch.object(system_metrics, '_previous', kept):
            self.windows(times=QUIET)
            self.assertIs(system_metrics._previous, kept)
        self.assertIsNone(system_metrics.busy_percent(None, (1, 2, 3)))
        self.assertIsNone(system_metrics.busy_percent((1, 2, 3), (1, 2, 3)))
        self.assertEqual(system_metrics.busy_percent(*QUIET), 87.5)


@unittest.skipUnless(sys.platform == 'win32', 'the Windows readers')
class RealWindowsTests(unittest.TestCase):
    def test_the_ctypes_readers_on_this_pc(self):
        """The fast readers for real (read only; no PowerShell): a wrong restype or structure would show here."""
        self.assertGreater(diag.uptime_hours(), 0)
        self.assertTrue(diag.drives())
        self.assertTrue(all(d['total_gb'] > 0 and 0 <= d['free_percent'] <= 100 for d in diag.drives()))
        self.assertGreater(diag.memory()['total_gb'], 0)
        battery = diag.battery()
        self.assertTrue(battery is None or battery['present'] in (True, False))


class CoreTests(DeviceCase):
    def setUp(self):
        super().setUp()
        drive = {'drive': 'C:', 'kind': 'fixed', 'free_gb': 39.0, 'total_gb': 222.0, 'free_percent': 17.6}
        for p in (patch.object(diag, 'programs_and_adapters', lambda run=None: ([{'name': 'chrome', 'processes': 12, 'memory_mb': 1358}], [])),
                  patch.object(diag, 'CPU_SECONDS', 0), patch.object(diag, 'drives', return_value=[drive]),
                  patch.object(diag, 'memory', return_value={'used_percent': 36, 'available_gb': 20.2, 'total_gb': 31.9}),
                  patch.object(diag, 'uptime_hours', return_value=6.2), patch.object(diag, 'battery', return_value={'present': False, 'on_mains': True})):
            p.start()
            self.addCleanup(p.stop)

    def test_the_tool_for_the_pcs_own_question_and_not_for_a_device_without_the_tick(self):
        run = Run('diag-test')
        self.app.runs[run.id] = run
        replies = [calls('system_diagnostics'), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            self.app.work(run, 'how is my PC doing?', None)
        done = {e['event']: e['data'] for e in run.events}
        result = done['tool.completed']['result']
        self.assertEqual((result['status'], result['programs'][0]['name'], result['network_adapters']), ('completed', 'chrome', []))
        self.assertEqual((result['drives'][0]['drive'], result['memory']['total_gb'], result['windows_uptime_hours']), ('C:', 31.9, 6.2))
        self.assertEqual(result['attention'], [])
        self.assertIn('completed', [r['status'] for r in self.app.store.logs() if r['action'] == 'system_diagnostics'])
        # A paired phone the owner has not ticked "may use this PC's tools" for: refused, and the row names the device.
        paired = self.pair()
        replies = [calls('system_diagnostics'), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'how is my PC doing?'}, paired['credential'])
            self.assertEqual(status, 200, started)
            events = self.finished(paired['credential'], started['run_id'])
        self.assertIn('tool.failed', events)
        from_device = [r['status'] for r in self.app.store.logs() if r['action'] == 'system_diagnostics' and r['device'] == paired['device_id']]
        self.assertEqual(from_device, ['refused'])


if __name__ == '__main__':
    unittest.main()
