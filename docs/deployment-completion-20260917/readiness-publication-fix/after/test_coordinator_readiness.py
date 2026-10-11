"""Focused TEST harness regressions; synthetic data, no production or providers."""
import copy
import json
import os
from pathlib import Path
import sys
import time
import traceback
import unittest
from unittest.mock import Mock,patch
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parent))
from fixtures import RestartCampaign,BASE

observations=[]

class CoordinatorReadinessTests(unittest.TestCase):
    def setUp(self):
        self.c=RestartCampaign();self.root=self.c.r.exclusion.BASE/('TEST-STAGE4-HARNESS-'+uuid.uuid4().hex)
        self.root.mkdir();(self.root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
        self.c.path=self.root/'fixture-records.json';self.real_items=[]
        self.proc=Mock(pid=self.c.peer['pid'],returncode=None)
        self.proc.poll.side_effect=lambda:self.proc.returncode
        def wait(timeout):self.proc.returncode=0;return 0
        self.proc.wait.side_effect=wait
        cfg={'name':uuid.uuid4().hex,'endpoint':'TEAGUE-TEST-'+uuid.uuid4().hex,'core':{'data_id':'TEST-'+uuid.uuid4().hex},
             'server_key':'a'*64,'owner_key':'b'*64,'owner':'controller'}
        epoch=uuid.uuid4().hex
        self.ready={'endpoint':cfg['endpoint'],'peer':dict(self.c.peer),'identity':{**self.c.peer,
            'mode':'TEST','namespace':self.root.name,'data_id':cfg['core']['data_id'],
            'installation_id':'STAGE4_TEST_COORDINATOR','runtime_build':'STAGE4_TEST_COORDINATOR',
            'core_instance_id':epoch,'startup_epoch':epoch,'protocol':[2,3]}}
        self.item={'process':self.proc,'configuration':cfg,'root':self.root,'token':None,'ready':None,
                   'spawn_peer':dict(self.c.peer),'attach_started':False,'started':time.monotonic(),
                   'readiness_path':self.root/('coordinator-'+cfg['name']+'.json'),'read_attempts':0,'wait_polls':0}
        self.item['readiness_path'].write_text(json.dumps(self.ready),encoding='utf8')
        # These model tests begin after a completed publication. Real-process
        # cases below exercise the inherited-pipe publication protocol.
        self.item['publication_state']='COMPLETE'
    def tearDown(self):
        try:
            for item in self.real_items:
                if item['process'].poll() is None:self.c.close(item)
        finally:
            observations.append({'test':self.id(),'root':str(self.root),'fixture_records':self.c.records,
                'real_coordinators':[{'pid':i['process'].pid,'peer':i.get('spawn_peer'),'ready':i.get('ready'),
                    'exit':i['process'].poll(),'startup_failure':i.get('startup_failure')} for i in self.real_items]})
    def diagnostic(self,operation):
        try:operation()
        except Exception as exc:return exc,self.c.coordinator_diagnostic(self.item,exc,'targeted-test')
        self.fail('Expected explicit failure')
    def fake_auth(self,*args,**kwargs):
        request=args[6]
        if request['op']=='attach':return {'result':'ATTACHED','identity':self.ready['identity'],'token':'c'*64}
        if request['op']=='close':return {'result':'CLOSED'}
        raise AssertionError('Unexpected operation')
    def test_01_file_error_preserves_exact_exception(self):
        error=PermissionError(13,'INJECTED TEST read failure');error.winerror=5
        with patch.object(Path,'read_text',side_effect=error):exc,d=self.diagnostic(lambda:self.c.coordinator_readiness(self.item))
        self.assertIs(exc,error);self.assertEqual((d['exception'],d['errno'],d['winerror']),('PermissionError',13,5))
        self.assertEqual(d['path'],str(self.item['readiness_path']));self.assertEqual(d['read_attempts'],1)
        self.assertIn('PermissionError',d['traceback']);self.assertEqual(d['operation'],'read coordinator readiness UTF-8 file')
    def test_02_malformed_json(self):
        self.item['readiness_path'].write_text('{')
        exc,d=self.diagnostic(lambda:self.c.coordinator_readiness(self.item))
        self.assertIsInstance(exc,json.JSONDecodeError);self.assertEqual(d['operation'],'parse coordinator readiness JSON')
    def test_03_null_record_no_peer_dereference(self):
        self.item['readiness_path'].write_text('null')
        exc,d=self.diagnostic(lambda:self.c.coordinator_readiness(self.item))
        self.assertIs(type(exc),ValueError);self.assertIn('requires peer',str(exc));self.assertNotIn('NoneType',d['traceback'])
    def test_04_missing_peer(self):
        del self.ready['peer'];self.item['readiness_path'].write_text(json.dumps(self.ready))
        exc,_=self.diagnostic(lambda:self.c.coordinator_readiness(self.item));self.assertIs(type(exc),ValueError)
    def test_05_missing_identity_fields(self):
        del self.ready['identity']['created'];self.item['readiness_path'].write_text(json.dumps(self.ready))
        exc,_=self.diagnostic(lambda:self.c.coordinator_readiness(self.item));self.assertIs(type(exc),ValueError)
    def test_06_non_object_record(self):
        for value in ([],False,42,'text',{}):
            with self.subTest(value=value):
                self.item['readiness_path'].write_text(json.dumps(value))
                exc,_=self.diagnostic(lambda:self.c.coordinator_readiness(self.item));self.assertIs(type(exc),ValueError)
    def test_07_utf8_decode_failure(self):
        self.item['readiness_path'].write_bytes(b'\xff')
        exc,d=self.diagnostic(lambda:self.c.coordinator_readiness(self.item));self.assertIsInstance(exc,UnicodeDecodeError)
        self.assertIn('UnicodeDecodeError',d['traceback'])
    def test_08_publication_timeout_preserved(self):
        self.item['readiness_path']=self.root/'never-published.json';self.item['started']=time.monotonic()-9
        import queue
        self.item['publication_state']='NOT_BEGUN';self.item['publication_queue']=queue.Queue()
        exc,d=self.diagnostic(lambda:self.c.coordinator_readiness(self.item,wait=True))
        self.assertIsInstance(exc,TimeoutError);self.assertEqual(d['read_attempts'],0);self.assertEqual(d['wait_polls'],1)
    def test_09_exit_before_publication(self):
        self.item['readiness_path']=self.root/'never-published.json';self.proc.returncode=93
        import queue
        self.item['publication_state']='NOT_BEGUN';self.item['publication_queue']=queue.Queue();self.item['publication_queue'].put('')
        exc,_=self.diagnostic(lambda:self.c.coordinator_readiness(self.item,wait=True))
        self.assertIs(type(exc),RuntimeError);self.assertIn('exited before readiness',str(exc))
    def test_10_valid_ready_and_authenticated_close(self):
        self.item['ready']=self.c.coordinator_readiness(self.item,wait=True)
        with patch.object(self.c.r.authentication,'client',side_effect=self.fake_auth) as client:
            self.c.coordinator_attach(self.item);self.c.close(self.item)
        self.assertEqual([x.args[6]['op'] for x in client.call_args_list],['attach','close'])
        self.assertEqual(self.c.records[-1]['cleanup_result'],'AUTHENTICATED_CLOSE_SUCCEEDED')
    def test_11_incomplete_startup_single_cleanup_load(self):
        self.item['startup_failure']={'exception':'PermissionError','message':'original retained'};original=copy.deepcopy(self.item['startup_failure'])
        with patch.object(self.c.r.authentication,'client',side_effect=self.fake_auth) as client:self.c.close(self.item)
        self.assertEqual(self.item['read_attempts'],1);self.assertEqual(self.item['startup_failure'],original)
        self.assertEqual([x.args[6]['op'] for x in client.call_args_list],['attach','close'])
    def test_12_missing_readiness_cleanup_no_auth(self):
        self.item['readiness_path']=self.root/'never-published.json'
        with patch.object(self.c.r.authentication,'client') as client:
            with self.assertRaises(FileNotFoundError):self.c.close(self.item)
        client.assert_not_called();self.assertEqual(self.c.records[-1]['cleanup_result'],'NOT_ATTEMPTED_IDENTITY_UNESTABLISHED')
        self.assertEqual(self.c.records[-1]['exception'],'FileNotFoundError');self.proc.wait.assert_not_called()
    def test_13_already_exited_without_readiness(self):
        self.proc.returncode=0
        with patch.object(self.c.r.authentication,'client') as client:self.c.close(self.item)
        client.assert_not_called();self.assertEqual(self.c.records[-1]['cleanup_result'],'PROCESS_ALREADY_EXITED')
        self.assertIsNone(self.c.records[-1]['identity'])
    def test_14_abnormal_exit_report_not_none_error(self):
        self.proc.returncode=1
        with self.assertRaisesRegex(AssertionError,'coordinator exit recorded'):self.c.close(self.item)
        self.assertEqual(self.c.records[-1]['exception'],'AssertionError')
    def test_15_no_independent_pin_no_cleanup_auth(self):
        self.item['spawn_peer']=None
        with patch.object(self.c.r.authentication,'client') as client:
            with self.assertRaises(self.c.r.Denied):self.c.close(self.item)
        client.assert_not_called()
    def test_16_pid_creation_mismatch_rejected(self):
        for key,value in [('pid',-1),('created',0),('exe_digest','0'*64)]:
            with self.subTest(field=key):
                ready=copy.deepcopy(self.ready);ready['peer'][key]=value
                with self.assertRaises(self.c.r.Denied):self.c.coordinator_ready_identity(self.item,ready)
    def test_17_live_process_pin_mismatch_rejected(self):
        with patch.object(self.c.r.transport,'identity',return_value={**self.c.peer,'created':0}):
            with self.assertRaises(self.c.r.Denied):self.c.coordinator_ready_identity(self.item,self.ready)
    def test_18_wrong_namespace_data_endpoint_rejected(self):
        for field in ('namespace','data_id','endpoint'):
            with self.subTest(field=field):
                ready=copy.deepcopy(self.ready)
                if field=='endpoint':ready[field]='TEAGUE-TEST-wrong'
                else:ready['identity'][field]='TEST-wrong'
                with self.assertRaises(self.c.r.Denied):self.c.coordinator_ready_identity(self.item,ready)
    def test_19_unknown_attachment_no_second_attach(self):
        self.item['ready']=self.ready;self.item['attach_started']=True
        with patch.object(self.c.r.authentication,'client') as client:
            with self.assertRaisesRegex(RuntimeError,'outcome unknown'):self.c.close(self.item)
        client.assert_not_called();self.assertEqual(self.c.records[-1]['cleanup_result'],'NOT_ATTEMPTED_SESSION_UNESTABLISHED')
    def test_20_authentication_denied_not_close_success(self):
        self.item['ready']=self.ready;self.item['token']='c'*64;self.item['attach_started']=True
        with patch.object(self.c.r.authentication,'client',return_value={'result':'DENIED'}):
            with self.assertRaisesRegex(AssertionError,'explicit coordinator close'):self.c.close(self.item)
        self.proc.wait.assert_not_called();self.assertEqual(self.c.records[-1]['cleanup_result'],'AUTHENTICATED_CLOSE_FAILED')
    def test_21_close_ack_not_proof_of_exit(self):
        import subprocess
        self.item['ready']=self.ready;self.item['token']='c'*64;self.item['attach_started']=True
        self.proc.wait.side_effect=subprocess.TimeoutExpired('TEST process',5)
        with patch.object(self.c.r.authentication,'client',side_effect=self.fake_auth):
            with self.assertRaises(subprocess.TimeoutExpired):self.c.close(self.item)
        self.assertEqual(self.c.records[-1]['cleanup_result'],'AUTHENTICATED_CLOSE_ACKNOWLEDGED_EXIT_UNCONFIRMED')
    def test_22_inherited_installed_pin_compatible(self):
        item={'process':self.proc,'configuration':self.item['configuration'],'root':self.root,'token':None,
              'initial_peer':self.c.peer,'ready':self.ready}
        with patch.object(self.c.r.authentication,'client',side_effect=self.fake_auth):
            result=self.c.cc(item,'attach');item['token']=result['token'];self.c.close(item)
        self.assertEqual(item['spawn_peer'],self.c.peer);self.assertTrue(item['attach_started'])
    def test_23_primary_startup_exception_not_masked(self):
        error=PermissionError(13,'INJECTED TEST startup read failure');error.winerror=5
        with patch('fixtures.subprocess.Popen',return_value=self.proc),patch.object(self.c,'coordinator_readiness',side_effect=error),patch.object(self.c.r.authentication,'client') as client:
            with self.assertRaises(PermissionError) as caught:self.c.coordinator(self.root,self.c.core_config('TEST-synthetic'))
        self.assertIs(caught.exception,error);client.assert_not_called()
        item=self.c.coordinators[-1];self.assertIsNone(item['ready']);self.assertFalse(item['attach_started'])
        d=item['startup_failure'];self.assertEqual(d['winerror'],5);self.assertEqual(d['errno'],13)
        self.assertIn('PermissionError',d['traceback']);self.assertNotIn('NoneType',d['traceback'])
    def test_24_real_authenticated_owner_and_close(self):
        root,data=self.c.namespace();item=self.c.coordinator(root,self.c.core_config(data));self.real_items.append(item)
        self.assertEqual(item['ready']['peer'],self.c.r.transport.identity(item['process'].pid))
        self.assertEqual(self.c.cc(item,'status')['result'],'IDLE')
        self.assertTrue(self.c.denied(lambda:self.c.cc(item,'close',token='f'*64)))
        wrong={**item,'configuration':{**item['configuration'],'owner_key':'0'*64}}
        self.assertTrue(self.c.denied(lambda:self.c.cc(wrong,'close')))
        cfg=item['configuration'];ready=item['ready']
        self.assertTrue(self.c.denied(lambda:self.c.r.authentication.client(cfg['endpoint'],ready['peer'],ready['identity'],
            bytes.fromhex(cfg['server_key']),'foreign-owner',bytes.fromhex(cfg['owner_key']),{'op':'close','token':item['token'],'args':{}})))
        self.assertEqual(self.c.cc(item,'status')['result'],'IDLE');self.assertIsNone(item['process'].poll())
        self.c.close(item);self.assertEqual(item['process'].returncode,0)
        self.assertFalse(list(root.glob('*-start_spawned.json')))
    def test_25_real_partial_startup_cleanup_existing_auth(self):
        root,data=self.c.namespace();original_read=self.c.coordinator_readiness
        error=PermissionError(13,'INJECTED TEST post-publication read failure');error.winerror=5
        def failed_read(item,wait=False):
            original_read(item,wait=wait)
            raise error
        with patch.object(self.c,'coordinator_readiness',side_effect=failed_read):
            with self.assertRaises(PermissionError) as caught:self.c.coordinator(root,self.c.core_config(data))
        item=self.c.coordinators[-1];self.real_items.append(item)
        self.assertIs(caught.exception,error);self.assertIsNone(item['ready']);self.assertFalse(item['attach_started'])
        primary=copy.deepcopy(item['startup_failure']);self.c.close(item)
        self.assertEqual(item['startup_failure'],primary);self.assertEqual(item['process'].returncode,0)
        self.assertEqual(self.c.records[-1]['cleanup_result'],'AUTHENTICATED_CLOSE_SUCCEEDED')
        self.assertFalse(list(root.glob('*-start_spawned.json')))

if __name__=='__main__':
    output=Path(sys.argv[1]) if len(sys.argv)>1 else BASE/('coordinator-readiness-targeted-'+uuid.uuid4().hex+'.json')
    result=unittest.TextTestRunner(verbosity=2,failfast=True).run(unittest.defaultTestLoader.loadTestsFromTestCase(CoordinatorReadinessTests))
    output.write_text(json.dumps({'tests':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),
        'skipped':len(result.skipped),'failure_details':result.failures and [(str(t),e) for t,e in result.failures],
        'error_details':[(str(t),e) for t,e in result.errors],'observations':observations,'production_changed':False,
        'paid_calls':0,'faults_are_explicit_test_injections':True},indent=2),encoding='utf8')
    print('EVIDENCE',output);sys.exit(0 if result.wasSuccessful() else 1)
