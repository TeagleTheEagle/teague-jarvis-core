"""Candidate HTTP dispatch/authentication tests without opening a server."""
import io
import json
import os
from email.message import Message
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT)]
import server


class RouteTests(unittest.TestCase):
    def request(self, body=None, cookie=True, origin='http://127.0.0.1:8765'):
        handler=object.__new__(server.Handler)
        handler.server=SimpleNamespace(server_port=8765,app=SimpleNamespace(session='test-session',store=SimpleNamespace(path='test.sqlite')))
        handler.path='/api/interface-inspection'
        handler.headers=Message()
        for key,value in {'Host':'127.0.0.1:8765','Origin':origin,'Content-Type':'application/json'}.items():handler.headers[key]=value
        if cookie:handler.headers['Cookie']='jarvis_session=test-session'
        raw=json.dumps(body or {'request':{'panel':'command'},'transmit':False}).encode()
        handler.headers['Content-Length']=str(len(raw))
        handler.rfile=io.BytesIO(raw)
        replies=[]
        handler.send=lambda status,data,*a,**k:replies.append((status,data))
        with patch.dict(os.environ,{'JARVIS_DESKTOP_TOKEN':''}),patch.object(server.providers,'capabilities',return_value={}),patch.object(server.inspection_runtime,'run',return_value={'status':'test'}) as worker:
            handler.do_POST()
            return replies,worker.call_args

    def test_authenticated_dispatch_no_model_consent_default(self):
        replies,call=self.request()
        self.assertEqual(replies[0][0],200)
        self.assertFalse(call.args[4])
        self.assertIsNone(call.args[5])

    def test_missing_cookie_denied_before_worker(self):
        replies,call=self.request(cookie=False)
        self.assertEqual(replies[0][0],401)
        self.assertIsNone(call)

    def test_foreign_origin_denied_before_worker(self):
        replies,call=self.request(origin='https://example.com')
        self.assertEqual(replies[0][0],403)
        self.assertIsNone(call)

    def test_extra_fields_and_nonboolean_consent_rejected(self):
        for body in ({'request':{'panel':'command'},'url':'https://example.com'}, {'request':{'panel':'command'},'transmit':'true'}, {'request':{'panel':'command','path':'secret'}}):
            replies,call=self.request(body)
            self.assertEqual(replies[0][0],400)
            self.assertIsNone(call)


if __name__=='__main__':unittest.main(verbosity=2)
