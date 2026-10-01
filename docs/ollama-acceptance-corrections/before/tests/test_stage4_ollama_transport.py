"""Offline transport boundary/error tests; never contacts a provider."""
import sys, json, socket, threading, time, unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import stage4_ollama_transport as m

class Tests(unittest.TestCase):
 def setUp(self):self.t=m.Transport(mode='STAGE4_TEST');self.cancel=threading.Event()
 def request(self):return self.t.request('/api/chat',{},self.cancel,time.monotonic()+1)
 def test_only_fixed_destination(self):
  self.assertTrue(m.permitted(('127.0.0.1',11434)))
  for address in [('localhost',11434),('127.0.0.1',80),('::1',11434),('192.168.1.1',11434),('api.openai.com',443),('127.0.0.1',True),['127.0.0.1',11434]]:self.assertFalse(m.permitted(address))
  self.assertFalse(m.permitted(m.ADDRESS,socket.AF_INET6));self.assertFalse(m.permitted(m.ADDRESS,kind=socket.SOCK_DGRAM))
 def test_no_dns(self):
  with patch.object(m.socket,'socket') as sock,patch.object(m.socket,'getaddrinfo',side_effect=AssertionError('DNS')):
   m.LocalConnection(*m.ADDRESS).connect();sock.return_value.connect.assert_called_once_with(m.ADDRESS)
 def test_wrong_host_rejected_before_socket(self):
  with patch.object(m.socket,'socket') as sock:
   with self.assertRaisesRegex(m.Failure,'DESTINATION_DENIED'):m.LocalConnection('localhost',11434).connect()
   sock.assert_not_called()
 def test_production_denied(self):
  with self.assertRaisesRegex(m.Failure,'TEST_ONLY'):m.Transport(mode='production')
 def test_endpoint_denied(self):
  with self.assertRaisesRegex(m.Failure,'ENDPOINT_DENIED'):self.t.request('/api/pull',{},self.cancel,time.monotonic()+1)
 def test_unavailable(self):
  with patch.object(m.LocalConnection,'request',side_effect=ConnectionRefusedError):
   with self.assertRaisesRegex(m.Failure,'OLLAMA_UNAVAILABLE'):self.request()
 def test_timeout(self):
  with patch.object(m.LocalConnection,'request',side_effect=TimeoutError):
   with self.assertRaisesRegex(m.Failure,'OLLAMA_TIMEOUT'):self.request()
 def test_malformed_error_redirect_large(self):
  for raw,status,code in [(b'bad',200,'MALFORMED'),(b'{"a":1,"a":2}',200,'MALFORMED'),(b'{"error":"failed"}',200,'GENERATION_ERROR'),(b'{}',302,'HTTP_ERROR'),(b'x'*131073,200,'TOO_LARGE')]:
   with self.subTest(code=code),patch.object(m,'LocalConnection') as factory:
    response=factory.return_value.getresponse.return_value;response.status=status;response.read.return_value=raw
    with self.assertRaisesRegex(m.Failure,code):self.request()
 def test_cancel_during_closed_connection_response(self):
  with patch.object(m,'LocalConnection') as factory:
   conn=factory.return_value;conn.sock=None;released=threading.Event();conn.transport_socket.shutdown.side_effect=lambda _:released.set()
   response=conn.getresponse.return_value;response.status=200
   def read(_):self.cancel.set();self.assertTrue(released.wait(.5));return b'{}'
   response.read.side_effect=read
   with self.assertRaisesRegex(m.Failure,'CANCELLED'):self.request()
   conn.transport_socket.shutdown.assert_called_once()
 def test_deadline_interrupt(self):
  with patch.object(m,'LocalConnection') as factory:
   conn=factory.return_value;released=threading.Event();conn.transport_socket.shutdown.side_effect=lambda _:released.set()
   response=conn.getresponse.return_value;response.status=200
   def read(_):self.assertTrue(released.wait(1));return b'{}'
   response.read.side_effect=read
   with self.assertRaisesRegex(m.Failure,'OLLAMA_TIMEOUT'):self.t.request('/api/chat',{},self.cancel,time.monotonic()+.05)
 def test_no_tools_exact_model(self):
  with patch.object(self.t,'request') as req:
   with self.assertRaisesRegex(m.Failure,'TEXT_ONLY'):self.t.generate([{'role':'user','content':'x','tools':[]}],m.MODEL,self.cancel,time.monotonic()+1)
   with self.assertRaisesRegex(m.Failure,'MODEL_DENIED'):self.t.generate([], 'other',self.cancel,time.monotonic()+1)
   req.assert_not_called()
 def test_payload_and_real_metrics(self):
  envelope={'model':m.MODEL,'done':True,'done_reason':'stop','message':{'content':'hello'},'eval_count':2,'eval_duration':1000000000}
  with patch.object(self.t,'request',return_value=envelope) as req:
   result=self.t.generate([{'role':'user','content':'hello'}],m.MODEL,self.cancel,time.monotonic()+1)
   payload=req.call_args.args[1];self.assertNotIn('tools',payload);self.assertFalse(payload['stream']);self.assertEqual(result['metrics']['tokens_per_second'],2)
 def test_wrong_incomplete_tool_response(self):
  for envelope in [{'model':'other'}, {'model':m.MODEL,'done':True,'done_reason':'length','message':{'content':'x'}},{'model':m.MODEL,'done':True,'done_reason':'stop','message':{'tool_calls':[{}]}}]:
   with patch.object(self.t,'request',return_value=envelope):
    with self.assertRaisesRegex(m.Failure,'INVALID_OR_INCOMPLETE'):self.t.generate([{'role':'user','content':'x'}],m.MODEL,self.cancel,time.monotonic()+1)

if __name__=='__main__':unittest.main()
