import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime_paths

LAYOUT = ('JARVIS_DATA_DIR', 'JARVIS_CONFIG_DIR', 'JARVIS_MODELS_DIR')


class RuntimePathTests(unittest.TestCase):
    def test_development_defaults_are_unchanged(self):
        with patch.dict(os.environ, {k: '' for k in LAYOUT}):
            self.assertFalse(runtime_paths.installed())
            self.assertEqual(runtime_paths.data_dir(), runtime_paths.ROOT / 'data')
            self.assertEqual(runtime_paths.models_dir(), runtime_paths.ROOT / 'data')
            self.assertEqual(runtime_paths.env_file(), runtime_paths.ROOT / '.env')
            self.assertEqual(runtime_paths.wearable_connection_file(), runtime_paths.ROOT / '.env.wearable-connection.json')

    def test_installed_layout_keeps_data_and_config_outside_the_program(self):
        with tempfile.TemporaryDirectory() as home:
            home = Path(home)
            env = {'JARVIS_DATA_DIR': str(home / 'data'), 'JARVIS_CONFIG_DIR': str(home / 'config'),
                   'JARVIS_MODELS_DIR': str(home / 'release' / 'models')}
            with patch.dict(os.environ, env):
                self.assertTrue(runtime_paths.installed())
                self.assertEqual(runtime_paths.data_dir(), home / 'data')
                self.assertEqual(runtime_paths.env_file(), home / 'config' / '.env')
                self.assertEqual(runtime_paths.models_dir(), home / 'release' / 'models')
                self.assertEqual(runtime_paths.wearable_connection_file(), home / 'config' / '.env.wearable-connection.json')

    def test_installed_release_is_found_from_its_own_layout_without_the_launcher(self):
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {k: '' for k in LAYOUT}):
            home = Path(home)
            app = home / 'releases' / '1.0.0-abc' / 'app'
            app.mkdir(parents=True)
            with patch.object(runtime_paths, 'ROOT', app):
                self.assertFalse(runtime_paths.installed())  # no manifest beside the app: development layout
                (app.parent / 'manifest.json').write_text('{"product": "JARVIS", "release_id": "1.0.0-abc"}', encoding='utf-8')
                self.assertTrue(runtime_paths.installed())
                self.assertEqual(runtime_paths.install_home(), home)
                self.assertEqual(runtime_paths.data_dir(), home / 'data')
                self.assertEqual(runtime_paths.config_dir(), home / 'config')
                self.assertEqual(runtime_paths.models_dir(), app.parent / 'models')
                self.assertEqual(runtime_paths.release_id(), '1.0.0-abc')
            with patch.object(runtime_paths, 'ROOT', home / 'elsewhere' / 'app'):
                self.assertIsNone(runtime_paths.release_id())

    def test_personality_prefers_owner_config_then_shipped_default(self):
        with tempfile.TemporaryDirectory() as config:
            with patch.dict(os.environ, {'JARVIS_CONFIG_DIR': config}):
                self.assertEqual(runtime_paths.personality_file(), runtime_paths.ROOT / 'personality.txt')
                (Path(config) / 'personality.txt').write_text('Owner personality.', encoding='utf-8')
                self.assertEqual(runtime_paths.personality_file(), Path(config) / 'personality.txt')

    def test_offline_voice_check_uses_the_release_models_not_a_development_path(self):
        import importlib
        import check_voice_offline
        with tempfile.TemporaryDirectory() as models, patch.dict(os.environ, {'JARVIS_MODELS_DIR': models}):
            self.assertEqual(importlib.reload(check_voice_offline).MODEL, Path(models) / 'speech-models' / 'base.en')
        with patch.dict(os.environ, {k: '' for k in LAYOUT}):
            self.assertEqual(importlib.reload(check_voice_offline).MODEL, runtime_paths.ROOT / 'data' / 'speech-models' / 'base.en')

    def test_core_reads_keys_from_the_config_folder_when_installed(self):
        import server
        with tempfile.TemporaryDirectory() as config:
            (Path(config) / '.env').write_text('JARVIS_LAYOUT_TEST_SETTING=from-config\n', encoding='utf-8')
            with patch.dict(os.environ, {'JARVIS_CONFIG_DIR': config}):
                os.environ.pop('JARVIS_LAYOUT_TEST_SETTING', None)
                server.load_env()
                self.assertEqual(os.environ.get('JARVIS_LAYOUT_TEST_SETTING'), 'from-config')


if __name__ == '__main__':
    unittest.main()
