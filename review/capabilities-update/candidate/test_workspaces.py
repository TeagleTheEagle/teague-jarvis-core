import tempfile
import unittest
from store import Store
import workspaces as w

class WorkspaceTests(unittest.TestCase):
    def test_persistence_context_and_unlink(self):
        with tempfile.TemporaryDirectory() as root:
            s=Store(root);w.setup(s)
            p=w.change(s,{'action':'create','name':'Research'})['id']
            w.change(s,{'action':'link','project':p,'kind':'conversation','ref':'chat1','title':'Chat'})
            note=s.put('note','Check battery life')
            ref=note['id']
            w.change(s,{'action':'link','project':p,'kind':'note','ref':ref})
            self.assertIn('Check battery life',w.context(s,'chat1'))
            self.assertEqual('',w.context(s,'unrelated'))
            s=Store(root);w.setup(s)
            self.assertEqual(2,len(w.listing(s)[0]['links']))
            w.change(s,{'action':'unlink','project':p,'kind':'note','ref':ref})
            self.assertEqual(1,len(s.items('note')))
            self.assertNotIn('Check battery life',w.context(s,'chat1'))
            with self.assertRaises(ValueError):w.change(s,{'action':'link','project':'missing','kind':'note','ref':ref})
