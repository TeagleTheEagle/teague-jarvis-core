"""Interface inspection renders with a browser every Windows 11 PC has (no hidden Chrome dependency)."""
import unittest

import inspection_runtime


class FakeChromium:
    def __init__(self, available, flaky_first_start=()):
        self.available, self.flaky, self.tried = available, set(flaky_first_start), []

    def launch(self, channel, headless):
        self.tried.append(channel)
        if channel in self.flaky:
            self.flaky.discard(channel)
            raise RuntimeError(f'{channel} exited during its first start')
        if channel not in self.available:
            raise RuntimeError(f'{channel} is not installed')
        return f'browser:{channel}'


class FakePlaywright:
    def __init__(self, *available, flaky_first_start=()):
        self.chromium = FakeChromium(available, flaky_first_start)


class InspectionBrowserTests(unittest.TestCase):
    def test_edge_is_used_first(self):
        p = FakePlaywright('msedge', 'chrome')
        self.assertEqual(inspection_runtime.launch_browser(p), 'browser:msedge')
        self.assertEqual(p.chromium.tried, ['msedge'])

    def test_chrome_is_the_fallback_when_edge_is_missing(self):
        p = FakePlaywright('chrome')
        self.assertEqual(inspection_runtime.launch_browser(p), 'browser:chrome')
        self.assertEqual(p.chromium.tried, ['msedge', 'msedge', 'chrome'])

    def test_a_failed_first_start_of_edge_is_retried_before_chrome(self):
        p = FakePlaywright('msedge', 'chrome', flaky_first_start=['msedge'])
        self.assertEqual(inspection_runtime.launch_browser(p), 'browser:msedge')
        self.assertEqual(p.chromium.tried, ['msedge', 'msedge'])

    def test_no_browser_is_a_failure_not_a_download(self):
        p = FakePlaywright()
        with self.assertRaises(RuntimeError):
            inspection_runtime.launch_browser(p)
        self.assertEqual(p.chromium.tried, ['msedge', 'msedge', 'chrome', 'chrome'])


class InspectionAssets(unittest.TestCase):
    def test_every_file_the_page_loads_is_available_to_the_inspection_renderer(self):
        # The renderer serves only inspection_runtime.STATIC; a script or stylesheet index.html loads but the
        # list lacks would be refused, and the inspected picture would differ from the real interface.
        import pathlib, re
        static = pathlib.Path(inspection_runtime.__file__).resolve().parent / 'static'
        page = (static / 'index.html').read_text(encoding='utf-8')
        loaded = set(re.findall(r'<(?:script|img)[^>]*\ssrc="/([^"]+)"', page)) | set(re.findall(r'<link[^>]*\shref="/([^"]+)"', page))
        self.assertIn('command-dashboard.js', loaded)
        self.assertEqual(sorted(loaded - set(inspection_runtime.STATIC)), [])
        for name in inspection_runtime.STATIC:
            self.assertTrue((static / name).is_file(), name)
        for key in ('cpu_percent', 'memory', 'disk', 'core_uptime_seconds', 'last_response_ms'):
            self.assertIsNone(inspection_runtime.METRICS_OMITTED[key])


if __name__ == '__main__':
    unittest.main()
