import tempfile
import unittest
from conversation_context import select_history
from store import Store


class ContextTests(unittest.TestCase):
    def test_long_message_preserves_followup(self):
        rows = [{'role': 'assistant', 'content': 'A' * 25000}, {'role': 'user', 'content': 'Save that'}]
        selected = select_history(rows, 1000)
        self.assertEqual(selected[-1]['content'], 'Save that')
        self.assertIn('[Earlier content truncated]', selected[0]['content'])
        self.assertLessEqual(sum(len(r['content']) for r in selected), 1000)

    def test_evidence_is_scoped_bounded_and_cleared(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            for i in range(12):
                store.record_evidence('one', 'calculate', {'value': i})
            self.assertEqual(len(store.recent_evidence('one')), 8)
            self.assertEqual(store.recent_evidence('two'), [])
            self.assertEqual(Store(root).recent_evidence('one')[-1]['result']['value'], 11)
            store.clear_conversation('one')
            self.assertEqual(store.recent_evidence('one'), [])

    def test_source_contents_and_credentials_not_retained(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            store.record_evidence('one', 'development_read', {'content': 'private source'})
            store.record_evidence('one', 'save_item', {'body': 'api_key=example'})
            self.assertEqual(store.recent_evidence('one'), [])


if __name__ == '__main__':
    unittest.main()
