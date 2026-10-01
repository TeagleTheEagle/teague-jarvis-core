import tempfile
import unittest
from unittest.mock import patch
from store import Store
from conversation_context import search_saved, read_saved

class RecallTests(unittest.TestCase):
    def test_search_read_and_secret_redaction(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(folder)
            store.message('older','user','Project helmet plan test-private-token')
            store.message('unrelated','user','Shopping list')
            with patch.dict('os.environ',{'TEST_SECRET':'test-private-token'}):
                result=search_saved(store,'helmet plan')
                self.assertEqual(len(result['matches']),1)
                self.assertEqual(result['matches'][0]['conversation'],'older')
                self.assertNotIn('test-private-token',str(result))
                self.assertNotIn('test-private-token',str(read_saved(store,'older')))
            self.assertEqual(search_saved(store,'nonexistent')['matches'],[])
            with self.assertRaises(ValueError):read_saved(store,'missing')
            with self.assertRaises(ValueError):search_saved(store,' ')
