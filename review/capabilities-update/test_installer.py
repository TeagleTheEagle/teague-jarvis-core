import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from install_update import install

class InstallTests(unittest.TestCase):
    def test_review_gate_apply_rollback_and_source_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            live=Path(tmp);stage=live/'review/capabilities-update'
            (stage/'candidate').mkdir(parents=True);(stage/'before').mkdir()
            (live/'actions.py').write_bytes(b'old');(stage/'before/actions.py').write_bytes(b'old');(stage/'candidate/actions.py').write_bytes(b'new')
            row={'path':'actions.py','before_sha256':hashlib.sha256(b'old').hexdigest(),'candidate_sha256':hashlib.sha256(b'new').hexdigest()}
            (stage/'manifest.json').write_text(json.dumps({'files':[row]}))
            self.assertEqual(install(stage)['status'],'validated_only');self.assertEqual((live/'actions.py').read_bytes(),b'old')
            install(stage,apply=True);self.assertEqual((live/'actions.py').read_bytes(),b'new')
            install(stage,rollback=True,apply=True);self.assertEqual((live/'actions.py').read_bytes(),b'old')
            (live/'actions.py').write_bytes(b'user change')
            with self.assertRaisesRegex(ValueError,'Source changed'):install(stage,apply=True)
            self.assertEqual((live/'actions.py').read_bytes(),b'user change')

if __name__=='__main__':unittest.main(verbosity=2)
