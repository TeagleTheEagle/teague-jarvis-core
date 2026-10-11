import concurrent.futures
import http.client
import json
import tempfile
import threading
import unittest
from phone_bridge import Bridge, Server, Handler


class PhoneBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bridge = Bridge(self.temp.name)
        self.ident, self.token = self.bridge.pair('Test phone')

    def test_saved_task_visible_to_desktop_store(self):
        r = self.bridge.create(self.token, {'title': 'Test task', 'request_id': 'a'*16})
        self.assertEqual(self.bridge.store.tasks()[0]['id'], r['task']['id'])

    def test_concurrent_retry_exactly_one_task(self):
        body = {'title': 'One task', 'request_id': 'b'*16}
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda _: self.bridge.create(self.token, body), range(10)))
        self.assertEqual(len({r['task']['id'] for r in results}), 1)
        self.assertEqual(len(self.bridge.store.tasks()), 1)

    def test_id_conflict_rejected(self):
        self.bridge.create(self.token, {'title':'One', 'request_id':'c'*16})
        with self.assertRaises(ValueError):
            self.bridge.create(self.token, {'title':'Two', 'request_id':'c'*16})

    def test_revoked_key_cannot_read_or_write(self):
        self.bridge.revoke(self.ident)
        with self.assertRaises(PermissionError): self.bridge.tasks(self.token)
        with self.assertRaises(PermissionError): self.bridge.create(self.token, {'title':'No', 'request_id':'d'*16})

    def test_malformed_input_does_not_write(self):
        for body in ([], {}, {'title':'', 'request_id':'e'*16}, {'title':'a'*501, 'request_id':'e'*16}, {'title':'ok','request_id':'short'}, {'title':'ok','request_id':'e'*16,'command':'shell'}):
            with self.assertRaises(ValueError): self.bridge.create(self.token, body)
        self.assertEqual(self.bridge.store.tasks(), [])

    def test_stored_device_has_only_hash(self):
        with self.bridge.store.connect() as db:
            row = dict(db.execute('SELECT * FROM phone_devices').fetchone())
        self.assertNotIn(self.token, str(row))

    def test_http_boundaries(self):
        server = Server(('127.0.0.1',0), Handler)
        server.tls = None
        server.bridge = self.bridge
        server.authority = 'jarvis.test'
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        def call(path='/v1/tasks', headers=None, method='GET', body=None):
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            try:
                conn.request(method,path,body,{'Host':'jarvis.test', **(headers or {})})
                r=conn.getresponse()
                return r.status, r.read()
            finally: conn.close()
        try:
            self.assertEqual(call()[0],401)
            auth={'Authorization':'Bearer '+self.token}
            self.assertEqual(call(headers=auth)[0],200)
            self.assertEqual(call(headers={**auth,'Origin':'https://evil.test'})[0],403)
            self.assertEqual(call(headers={**auth,'Host':'evil.test'})[0],403)
            self.assertEqual(call('/api/settings',auth)[0],404)
            self.assertEqual(call('/.env',auth)[0],404)
            self.assertEqual(call(headers={'Authorization':self.token})[0],401)
            code,_=call(headers={**auth,'Content-Type':'application/json'},method='POST',body=json.dumps({'title':'HTTP test','request_id':'f'*16}))
            self.assertEqual(code,200)
            self.bridge.revoke(self.ident)
            self.assertEqual(call(headers=auth)[0],401)
        finally:
            server.shutdown(); server.server_close(); worker.join()


if __name__ == '__main__': unittest.main()
