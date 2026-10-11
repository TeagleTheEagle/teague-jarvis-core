import unittest
from unittest.mock import patch
import check_windows_setup as setup


class SetupTests(unittest.TestCase):
    def test_supported_runtime(self):
        self.assertEqual(setup.runtime_errors('Windows', (3, 12, 10), 64), [])

    def test_unsupported_runtime(self):
        for version, bits in [((3, 11, 9), 64), ((3, 13, 0), 64), ((3, 12, 10), 32)]:
            with self.subTest(version=version, bits=bits):
                self.assertTrue(setup.runtime_errors('Windows', version, bits))

    def test_other_platform(self):
        self.assertTrue(setup.runtime_errors('Linux', (3, 12, 10), 64))

    @patch.object(setup.shutil, 'which', return_value=None)
    def test_missing_node(self, _):
        self.assertTrue(any('Node.js' in e for e in setup.check(tests=True)['errors']))

    @patch.object(setup.ctypes, 'WinDLL', create=True, side_effect=OSError('missing'))
    @patch.object(setup.platform, 'system', return_value='Windows')
    def test_missing_vc(self, _, loader):
        errors = setup.check(local_voice=True)['errors']
        self.assertEqual(sum('Redistributable' in e for e in errors), 3)
        self.assertTrue(all(call.kwargs['winmode'] == 0x800 for call in loader.call_args_list))

    @patch.object(setup.subprocess, 'run')
    def test_optional_checks_do_not_launch(self, run):
        setup.check()
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
