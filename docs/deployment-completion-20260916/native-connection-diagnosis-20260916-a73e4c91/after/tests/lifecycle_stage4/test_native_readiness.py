"""TEST native-probe readiness sequencing; no production or providers."""
from pathlib import Path
import io,json,subprocess,sys,time,unittest,uuid
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lifecycle_stage2'))
import pipe_transport as pt
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fixtures as f

class NativeReadinessTests(unittest.TestCase):
    def setUp(self):
        self.out=f.BASE/('native-readiness-unit-'+uuid.uuid4().hex);self.out.mkdir()
        self.base=patch.object(f,'BASE',self.out);self.base.start()
        self.peer={'pid':123,'created':456,'exe_digest':'a'*64}
    def tearDown(self):self.base.stop()
    def fake(self,line='STAGE4_NATIVE_READY\n',result='{"passed":true}',exit=0):
        process=Mock(pid=123,returncode=exit,stdout=io.StringIO(line))
        process.communicate.return_value=(result,'');process.poll.return_value=exit
        return process
    def test_ready_starts_server(self):
        start=Mock();f._native_ready_handoff('STAGE4_NATIVE_READY\n',time.monotonic()+10,start);start.assert_called_once()
    def test_wrong_readiness_never_starts_server(self):
        start=Mock()
        with self.assertRaisesRegex(ValueError,'NATIVE_CLIENT_READINESS'):f._native_ready_handoff('READY\n',time.monotonic()+10,start)
        start.assert_not_called()
    def test_empty_readiness_never_starts_server(self):
        start=Mock()
        with self.assertRaises(ValueError):f._native_ready_handoff('',time.monotonic()+10,start)
        start.assert_not_called()
    def test_deadline_never_starts_server(self):
        start=Mock()
        with patch.object(f.time,'monotonic',return_value=12):
            with self.assertRaisesRegex(TimeoutError,'STARTUP_DEADLINE'):f._native_ready_handoff('STAGE4_NATIVE_READY\n',12,start)
        start.assert_not_called()
    def test_server_starts_before_config_and_result_is_preserved(self):
        p=self.fake();sequence=[];p.communicate.side_effect=lambda *a,**k:(sequence.append('config') or ('{"passed":true}',''))
        with patch.object(f.subprocess,'Popen',return_value=p) as popen,patch.object(pt,'identity',return_value=self.peer):
            r=f._run_native_case(['electron','driver'],{'peer':'unchanged'}, {},lambda:sequence.append('server'))
        self.assertEqual(sequence,['server','config']);self.assertEqual(r.stdout,'{"passed":true}');self.assertEqual(r.native_evidence['identity'],self.peer)
        self.assertEqual(popen.call_args.args[0],['electron','driver','--native-ready']);p.terminate.assert_not_called()
        self.assertEqual(json.loads(p.communicate.call_args.args[0]),{'peer':'unchanged'})
    def test_failed_peer_result_is_not_converted_to_pass(self):
        p=self.fake(result='{"passed":false,"error":"PEER_IDENTITY_MISMATCH"}')
        with patch.object(f.subprocess,'Popen',return_value=p),patch.object(pt,'identity',return_value=self.peer):r=f._run_native_case(['electron'],{}, {},lambda:None)
        self.assertFalse(json.loads(r.stdout)['passed']);self.assertEqual(json.loads(r.stdout)['error'],'PEER_IDENTITY_MISMATCH')
    def test_nonzero_child_exit_preserved(self):
        p=self.fake(exit=1)
        with patch.object(f.subprocess,'Popen',return_value=p),patch.object(pt,'identity',return_value=self.peer):r=f._run_native_case(['electron'],{}, {},lambda:None)
        self.assertEqual(r.returncode,1)
    def test_invalid_readiness_cleans_only_reverified_child(self):
        p=self.fake('WRONG\n');p.poll.return_value=None;start=Mock()
        with patch.object(f.subprocess,'Popen',return_value=p),patch.object(pt,'identity',return_value=self.peer):
            with self.assertRaises(ValueError):f._run_native_case(['electron'],{}, {},start)
        start.assert_not_called();p.terminate.assert_called_once();self.assertEqual(len(list(self.out.glob('native-startup-failure-*.json'))),1)
    def test_uncertain_identity_never_terminated(self):
        p=self.fake('WRONG\n');p.poll.return_value=None
        with patch.object(f.subprocess,'Popen',return_value=p),patch.object(pt,'identity',side_effect=[self.peer,{**self.peer,'created':457}]):
            with self.assertRaises(ValueError):f._run_native_case(['electron'],{}, {},lambda:None)
        p.terminate.assert_not_called();e=json.loads(next(self.out.glob('native-startup-failure-*.json')).read_text())
        self.assertEqual(e['cleanup_error']['reason'],'NATIVE_CLEANUP_IDENTITY_UNCERTAIN')

if __name__=='__main__':unittest.main(verbosity=2)
