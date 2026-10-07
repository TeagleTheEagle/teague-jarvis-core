"""Release 1.0.17, JARVIS as his own app (docs/OWN-APP-PLAN.md): the build's stamping and bootstrap helpers. The
stamping is proved on a small copy of rcedit's own program (never on the 170 MB Electron binary) with the pinned
rcedit from desktop/node_modules; skipped when that package is not installed."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
try:
    import build_release  # noqa: E402
except ModuleNotFoundError:   # a copy without the development tools (the release regression adds the script; anything else skips)
    raise unittest.SkipTest('tools/build_release.py is not beside these tests') from None

RCEDIT = ROOT / 'desktop' / 'node_modules' / build_release.RCEDIT['package'] / build_release.RCEDIT['exe']


class VersionAndBootstrapTests(unittest.TestCase):
    def test_the_windows_version_has_four_numbers(self):
        self.assertEqual(build_release.version_quad('1.0.17'), '1.0.17.0')
        self.assertEqual(build_release.version_quad('2.1'), '2.1.0.0')
        self.assertEqual(build_release.version_quad('1.0.17.3'), '1.0.17.3')
        for bad in ('1.0.17-rc1', '1.0.17.0.0', 'latest', ''):
            with self.assertRaises(SystemExit, msg=bad):
                build_release.version_quad(bad)

    def test_the_bootstrap_loads_this_releases_desktop_app(self):
        with tempfile.TemporaryDirectory() as folder:
            release = Path(folder) / 'release'
            (release / 'app' / 'desktop').mkdir(parents=True)
            (release / 'app' / 'desktop' / 'main.cjs').write_text('// the app', encoding='utf-8')
            build_release.write_bootstrap(release / 'electron', '1.0.17')
            app = release / 'electron' / 'resources' / 'app'
            package = json.loads((app / 'package.json').read_text(encoding='utf-8'))
            self.assertEqual((package['name'], package['productName'], package['version'], package['main']), ('JARVIS', 'JARVIS', '1.0.17', 'main.cjs'))
            main = (app / 'main.cjs').read_text(encoding='utf-8')
            self.assertIn("require(path.join(__dirname, '..', '..', '..', 'app', 'desktop', 'main.cjs'))", main)
            # The relative path from resources\app really lands on this release's desktop app.
            self.assertEqual((app / '..' / '..' / '..' / 'app' / 'desktop' / 'main.cjs').resolve(), release / 'app' / 'desktop' / 'main.cjs')

    def test_what_ships(self):
        self.assertTrue(build_release.shipped('desktop/install-paths.cjs'))
        self.assertTrue(build_release.shipped('desktop/jarvis.ico'))
        self.assertFalse(build_release.shipped('desktop/test/install-paths.test.cjs'))
        self.assertFalse(build_release.shipped('tools/setup/build_setup.py'))


@unittest.skipUnless(RCEDIT.is_file(), 'rcedit not installed in desktop/node_modules')
class StampingTests(unittest.TestCase):
    def test_the_pinned_rcedit_is_the_one_in_node_modules(self):
        self.assertEqual(build_release.file_sha256(RCEDIT), build_release.RCEDIT['sha256'])

    def test_icon_name_company_and_version_are_stamped(self):
        with tempfile.TemporaryDirectory() as folder:
            victim = Path(folder) / 'JARVIS.exe'
            shutil.copyfile(RCEDIT.parent / 'rcedit.exe', victim)   # a small program with a resource table, as Electron's has
            build_release.stamp_program(victim, '1.0.17', ROOT / 'desktop' / 'jarvis.ico', RCEDIT)
            def read(name):
                return subprocess.run([str(RCEDIT), str(victim), '--get-version-string', name], check=True, capture_output=True, text=True).stdout.strip()
            self.assertEqual(read('ProductName'), 'JARVIS')
            self.assertEqual(read('CompanyName'), 'Teague Industries')
            self.assertEqual(read('FileDescription'), 'JARVIS')
            self.assertEqual(read('OriginalFilename'), 'JARVIS.exe')
            self.assertEqual(read('ProductVersion'), '1.0.17.0')
            self.assertEqual(read('FileVersion'), '1.0.17.0')
            self.assertGreater(victim.stat().st_size, (RCEDIT.parent / 'rcedit.exe').stat().st_size)   # the icon went in


class SetupScriptTests(unittest.TestCase):
    """tools/setup/build_setup.py without Inno Setup: the template's placeholders, its two application ids and the
    four-number version it stamps (review of 2026-10-07, findings L4 and L6)."""

    def setUp(self):
        sys.path.insert(0, str(ROOT / 'tools' / 'setup'))
        import build_setup
        self.build_setup = build_setup
        self.template = build_setup.TEMPLATE.read_text(encoding='utf-8')

    def test_every_placeholder_is_filled_and_a_missing_one_is_refused(self):
        values = {'VERSION': '1.0.17', 'RELEASE_ID': '1.0.17-0123456789ab', 'PACKAGE': r'D:\pkg', 'ICON': r'D:\i.ico',
                  'OUTPUT_DIR': r'D:\out', 'OUTPUT_NAME': 'JARVIS-Setup-1.0.17-0123456789ab', 'VERSION_QUAD': build_release.version_quad('1.0.17')}
        text = self.build_setup.render(self.template, values)
        self.assertNotIn('@VERSION@', text)
        self.assertIn('AppVersion=1.0.17', text)
        self.assertIn('VersionInfoVersion=1.0.17.0', text)
        self.assertIn(r"'\releases\1.0.17-0123456789ab\electron'", text)
        with self.assertRaises(SystemExit) as refused:
            self.build_setup.render(self.template, {k: v for k, v in values.items() if k != 'RELEASE_ID'})
        self.assertIn('@RELEASE_ID@', str(refused.exception))

    def test_the_two_application_ids_come_from_the_template(self):
        real, sandbox = self.build_setup.app_ids(self.template)
        self.assertEqual(real, '{DC2C8033-1BBF-5E1C-99A0-BE0E70DC9937}')
        self.assertRegex(sandbox, r'^\{[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\}$')
        self.assertNotEqual(real, sandbox)
        self.assertIn('AppId={code:AppIdForThisRun}', self.template)   # the id is chosen at run time: a sandbox run never touches the real entry
        self.assertIn("Result := 'JARVIS (sandbox)'", self.template)
        with self.assertRaises(SystemExit):
            self.build_setup.app_ids(self.template.replace('#define SandboxAppGuid', '#define Other'))

    def test_a_version_that_is_not_numbers_is_refused_before_inno_setup(self):
        with self.assertRaises(SystemExit):
            build_release.version_quad('1.0.17-rc1')


if __name__ == '__main__':
    unittest.main()
