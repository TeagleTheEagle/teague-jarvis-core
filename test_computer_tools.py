import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import computer_tools as tools

class ComputerToolsTests(unittest.TestCase):
    def test_file_scope_and_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'static').mkdir()
            (root/'.env').write_text('SECRET=private')
            (root/'server.py').write_text('test-secret-value')
            self.assertNotIn('.env',tools.source_files(root))
            for path in ('.env','../server.py',str(root/'server.py')):
                with self.assertRaises(ValueError):tools.read_source(root,path)
            with patch.dict('os.environ',{'TEST_API_KEY':'test-secret-value'}):
                self.assertIn('[REDACTED]',tools.read_source(root,'server.py')['content'])

    def test_browser_only_normal_urls(self):
        for url in ('file:///C:/Windows','javascript:alert(1)','https://user:pass@example.com','https://example.com?api_key=private'):
            with self.assertRaises(ValueError):tools.open_page(url)
        with patch('webbrowser.open',return_value=True) as launch:
            self.assertEqual(tools.open_page('https://example.com')['status'],'requested')
            launch.assert_called_once_with('https://example.com',new=2)

    def test_test_runner_fixed_command_and_real_exit_status(self):
        with patch('subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='',stderr='FAILED')) as run:
            self.assertEqual(tools.run_tests(Path('.'))['status'],'failed')
            self.assertEqual(run.call_args.args[0][1:4],['-m','unittest','discover'])
            self.assertEqual(run.call_args.kwargs['timeout'],90)

    def test_hardware_errors_not_fabricated(self):
        with patch('subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='')):
            with self.assertRaisesRegex(ValueError,'access was denied'):tools.system_info()
