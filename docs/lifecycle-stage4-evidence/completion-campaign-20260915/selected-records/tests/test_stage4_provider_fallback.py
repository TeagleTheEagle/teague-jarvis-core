"""Offline acceptance fixtures; no App, Core, Store, credential or network."""
import importlib.util
import json
from pathlib import Path
import sys
import threading
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from stage4_provider_fallback import Router, Failure, HTTPFailure, classify


class TestFallback(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        self.code='rate_limit_exceeded'
        self.cancel=threading.Event()
        self.messages=[{'role':'user','content':'Explain a triangle.'}]
        self.options=dict(tool_attempted=False,partial_output=False)
        def primary(*args):
            self.calls.append('primary')
            raise HTTPFailure(429,self.code,'7')
        def health(*args):self.calls.append('health');return 'ONLINE'
        def local(*args):self.calls.append('local');return {'model':'qwen3:4b','content':'Offline triangle fixture','complete':True}
        self.router=Router(mode='STAGE4_TEST',primary=primary,health=health,local=local,configured_model='configured-fixture',enabled=True)
    def generate(self):return self.router.generate('request',self.messages,self.cancel,**self.options)
    def test_a_openai_success_i_provenance(self):
        self.router.primary=lambda *args:{'model':'returned-openai-fixture','content':'answer','complete':True}
        self.assertEqual(self.generate()['content'],'answer')
        self.assertEqual(self.router.status('request')['actual_final_model'],'returned-openai-fixture')
        self.assertFalse(self.calls)
    def test_b_temporary_retry_guidance(self):
        self.generate();self.assertEqual(self.router.status('request')['primary_failure']['retry_after_seconds'],7)
    def test_c_quota(self):
        self.code='insufficient_quota';self.generate()
        self.assertEqual(self.router.status('request')['fallback_reason'],'quota_exhausted')
        self.assertIsNone(self.router.status('request')['primary_failure']['retry_after_seconds'])
    def test_d_other_429(self):
        self.code='unknown';self.generate();self.assertEqual(self.router.status('request')['fallback_reason'],'other_429')
    def test_e_g_j_k_healthy_local_provenance(self):
        self.generate();r=self.router.status('request')
        self.assertEqual(self.calls,['primary','health','local'])
        self.assertEqual((r['actual_final_provider'],r['actual_final_model']),('Ollama','qwen3:4b'))
        self.assertTrue(r['fallback'])
    def test_f_unavailable(self):
        self.router.health=lambda *args:'OFFLINE'
        with self.assertRaisesRegex(Failure,'FALLBACK_OFFLINE'):self.generate()
        self.assertEqual(self.calls,['primary'])
    def test_h_generation_failure(self):
        def fail(*args):raise RuntimeError('do not expose upstream body')
        self.router.local=fail
        with self.assertRaisesRegex(Failure,'PROVIDER_GENERATION_FAILED'):self.generate()
        self.assertIsNone(self.router.status('request')['actual_final_provider'])
    def test_l_consequential_attempt(self):
        self.options['tool_attempted']=True
        with self.assertRaisesRegex(Failure,'UNSAFE_PRIOR_WORK'):self.generate()
        self.assertEqual(self.calls,['primary'])
    def test_partial_output(self):
        self.options['partial_output']=True
        with self.assertRaisesRegex(Failure,'UNSAFE_PRIOR_WORK'):self.generate()
    def test_tools_required(self):
        self.options['requires_tools']=True
        with self.assertRaisesRegex(Failure,'UNSUPPORTED_REQUEST'):self.generate()
    def test_vision(self):
        self.options['vision']=True
        with self.assertRaisesRegex(Failure,'UNSUPPORTED_REQUEST'):self.generate()
    def test_disabled(self):
        self.router.enabled=False
        with self.assertRaisesRegex(Failure,'DISABLED'):self.generate()
    def test_m_n_p_no_retry_or_duplicate(self):
        self.generate()
        with self.assertRaisesRegex(Failure,'DUPLICATE'):self.generate()
        self.assertEqual(self.calls,['primary','health','local'])
    def test_o_production_refused(self):
        with self.assertRaisesRegex(Failure,'TEST_ONLY'):
            Router(mode='production',primary=None,health=None,local=None,configured_model='x')
    def test_cancel(self):
        self.cancel.set()
        with self.assertRaisesRegex(Failure,'CANCELLED'):self.generate()
        self.assertFalse(self.calls)
    def test_deadline_after_primary(self):
        def primary(*args):self.router.clock=lambda:100;raise HTTPFailure(429,'rate_limit_exceeded')
        self.router.clock=lambda:0;self.router.primary=primary
        with self.assertRaisesRegex(Failure,'DEADLINE'):self.generate()
        self.assertFalse(self.calls)
    def test_missing_actual_model(self):
        self.router.primary=lambda *args:{'content':'answer','complete':True}
        with self.assertRaisesRegex(Failure,'ACTUAL_MODEL'):self.generate()
    def test_local_wrong_model(self):
        self.router.local=lambda *args:{'model':'wrong','content':'answer','complete':True}
        with self.assertRaisesRegex(Failure,'LOCAL_MODEL'):self.generate()
    def test_local_tool_output(self):
        self.router.local=lambda *args:{'model':'qwen3:4b','content':'answer','complete':True,'tool_calls':[{}]}
        with self.assertRaisesRegex(Failure,'UNSUPPORTED'):self.generate()
    def test_auth_failure_no_fallback(self):
        def primary(*args):raise HTTPFailure(401)
        self.router.primary=primary
        with self.assertRaisesRegex(Failure,'NOT_ELIGIBLE'):self.generate()
        self.assertFalse(self.calls)
    def test_status_copy(self):
        self.generate();r=self.router.status('request');r['actual_final_provider']='forged'
        self.assertEqual(self.router.status('request')['actual_final_provider'],'Ollama')
    def test_retry_date_and_invalid(self):
        self.assertEqual(classify(HTTPFailure(429,'rate_limit_exceeded','Thu, 01 Jan 1970 00:00:10 GMT'),0)['retry_after_seconds'],10)
        self.assertIsNone(classify(HTTPFailure(429,'rate_limit_exceeded','nan'))['retry_after_seconds'])


if __name__=='__main__':
    unittest.main(verbosity=2)
