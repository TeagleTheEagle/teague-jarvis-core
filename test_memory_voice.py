import base64
import tempfile
import unittest
from pathlib import Path
import memory
from store import Store
from wake import WakeDetector


class MemoryTests(unittest.TestCase):
    def test_names_corrections_and_restart(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            memory.command(store, 'call me Alex')
            memory.command(store, 'my name is Jordan')
            reopened = Store(root)
            self.assertEqual(len(reopened.items('memory')), 1)
            self.assertEqual(reopened.settings()['name'], 'Jordan')
            item = reopened.items('memory')[0]
            reopened.put('memory', 'Preferred name: Sam', item['id'])
            self.assertEqual(reopened.settings()['name'], 'Sam')
            reopened.save_settings({'name': 'Taylor'})
            self.assertEqual(reopened.items('memory')[0]['body'], 'Preferred name: Taylor')
            reopened.delete('memory', item['id'])
            self.assertEqual(reopened.settings()['name'], '')

    def test_project_update_and_retrieval(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            memory.command(store, 'project Website: design next')
            memory.command(store, 'update project Website: testing next')
            for i in range(25):
                store.put('memory', 'Unrelated fact ' + str(i))
            self.assertEqual(memory.relevant(store.items('memory'), 'Website progress')[0]['body'], 'Project Website: testing next')
            self.assertEqual(memory.command(store, 'show projects'), 'Project Website: testing next')

    def test_explicit_replacement_deletion_and_no_inference(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            self.assertIsNone(memory.command(store, 'What is my name?'))
            store.put('memory', 'I like blue')
            store.put('memory', 'I like blue.')
            self.assertEqual(len(store.items('memory')), 1)
            memory.command(store, 'replace memory: I like blue => I like cyan')
            memory.command(store, 'forget memory: cyan')
            self.assertEqual(len(store.items('memory')), 1)
            memory.command(store, 'forget memory: I like cyan')
            self.assertEqual(store.items('memory'), [])
            with self.assertRaises(ValueError):
                store.put('memory', 'sk-fish-test-placeholder')


class WakeTests(unittest.TestCase):
    def test_invalid_audio_rejected_before_loading(self):
        detector = WakeDetector(Path('missing'))
        with self.assertRaises(ValueError):
            detector.predict({'client':'test', 'data':base64.b64encode(b'bad').decode()})
        self.assertIsNone(detector.model)


if __name__ == '__main__':
    unittest.main()
