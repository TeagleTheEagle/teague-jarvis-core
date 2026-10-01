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


if __name__ == '__main__':
    unittest.main()
