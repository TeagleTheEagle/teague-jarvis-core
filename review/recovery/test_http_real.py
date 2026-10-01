import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from test_jarvis import HTTPTests
from unittest.mock import patch
import unittest,recovery

class RealRecoveryHTTP(HTTPTests):
    def test_real_archive(self):
        service=recovery.Recovery(ROOT,ROOT/'data')
        original=service.rehearse
        def run(ident):
            try:return original(ident)
            except Exception:
                import traceback
                traceback.print_exc();raise
        with patch('server.recovery.Recovery',return_value=service),patch.object(service,'rehearse',side_effect=run):
            with self.req('/api/recovery',{'action':'rehearse','id':'03f021f6a4ba4a96995b1318ba18f32c'}) as response:
                self.assertEqual(json.load(response)['status'],'restore_rehearsal_passed')

if __name__=='__main__':unittest.main(defaultTest='RealRecoveryHTTP.test_real_archive')
