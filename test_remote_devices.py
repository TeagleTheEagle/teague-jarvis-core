"""The private-network door (release 1.0.16, remote_devices.py; docs/PHONE-CORE-1.0.16.md): the switch in
Settings > Devices, off by default; when on, a second door at the PC's private-network address that serves the
device routes and nothing else. The tests bind the door to 127.0.0.2, a second loopback address standing in for
the PC's Tailscale address: nothing listens on any other address, and no network is touched.
"""
import http.client
import json
import socket
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

import remote_devices
import server
from test_device_gateway import DeviceCase

ADDRESS = '127.0.0.2'
NAME = 'thegrizzlybear.tail-test.ts.net'


def free_port():
    with socket.socket() as sock:
        sock.bind((ADDRESS, 0))
        return sock.getsockname()[1]


class DoorCase(DeviceCase):
    def setUp(self):
        super().setUp()
        self.found = {'installed': True, 'address': ADDRESS, 'name': NAME}
        self.app.remote_devices.find = lambda: dict(self.found)
        self.addCleanup(self.app.remote_devices.shutdown)

    def raw(self, verb, path, port=None, body=b'{}'):
        """One request with any method, as the server answers it: (status, Server header, body bytes)."""
        connection = http.client.HTTPConnection(ADDRESS, port or self.app.remote_devices.bound['port'], timeout=10)
        try:
            connection.request(verb, path, body=body, headers={'Content-Type': 'application/json'})
            response = connection.getresponse()
            return response.status, response.getheader('Server'), response.read()
        finally:
            connection.close()

    def door(self, path, data, headers, host=None, port=None):
        port = port or self.app.remote_devices.bound['port']
        request = urllib.request.Request(f'http://{ADDRESS}:{port}{path}', data=json.dumps(data).encode() if data is not None else None,
                                         headers={'Content-Type': 'application/json', **headers, **({'Host': host} if host else {})})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def turn_on(self, port=None):
        port = port or free_port()
        status, state = self.owner('/api/remote-devices', {'enabled': True, 'port': port})
        self.assertEqual(status, 200, state)
        return port, state


class SwitchTests(DoorCase):
    def test_off_by_default_and_nothing_listens(self):
        status, listing = self.owner('/api/devices')
        remote = listing['remote']
        self.assertEqual((remote['enabled'], remote['open'], remote['port'], remote['address']), (False, False, remote_devices.DEFAULT_PORT, None))
        self.assertTrue(remote['message'].startswith('Off'))
        self.assertIsNone(self.app.remote_devices.door)
        status, state = self.owner('/api/remote-devices')
        self.assertEqual((status, state['enabled']), (200, False))
        # The switch is not a setting: not on the settings page, not in the export, and no device key reaches it.
        self.assertEqual(self.owner('/api/settings', {'remote_devices': True})[0], 400)
        self.assertNotIn('remote_devices', json.dumps(self.owner('/api/export')[1]))
        self.assertEqual(self.send('/api/remote-devices', {'enabled': True}, {})[0], 401)
        self.assertEqual(self.send('/api/remote-devices', None, {})[0], 401)

    def test_turning_it_on_opens_the_door_at_the_private_address_only(self):
        port, state = self.turn_on()
        self.assertEqual((state['enabled'], state['open'], state['port'], state['address'], state['name']), (True, True, port, ADDRESS, NAME))
        self.assertIn(f'Open at {ADDRESS}:{port} ({NAME})', state['message'])
        self.assertEqual(self.app.store.remote_devices_state()['enabled'], True)  # saved in the control table
        with self.app.store.connect() as db:
            self.assertIsNone(db.execute("SELECT 1 FROM settings WHERE key='remote_devices'").fetchone())
        # Bound to the private address: the same port on 127.0.0.1 has nobody listening.
        with self.assertRaises(OSError):
            urllib.request.urlopen(f'http://127.0.0.1:{port}/api/device/hello', timeout=2)
        # The device routes work through the door, which may be named by its address or by its Tailscale name.
        started = self.owner('/api/devices', {'action': 'pair', 'name': 'My phone', 'kind': 'phone'})[1]
        status, paired = self.door('/api/device/pair', {'code': started['code'], 'capabilities': ['microphone', 'speakers']}, {})
        self.assertEqual(status, 200, paired)
        status, hello = self.door('/api/device/hello', {}, {'X-Jarvis-Device': paired['credential']}, host=f'{NAME}:{port}')
        self.assertEqual((status, hello['name'], hello['allowed']), (200, 'My phone', ['microphone', 'speakers']))
        short = NAME.split('.')[0]
        self.assertEqual(self.door('/api/device/status', {}, {'X-Jarvis-Device': paired['credential']}, host=f'{short.upper()}:{port}')[0], 200)
        # Other methods and malformed requests get the same plain JSON line, and no answer names Python.
        for verb in ('HEAD', 'PUT', 'DELETE', 'OPTIONS', 'PATCH', 'GET'):
            status, served_by, body = self.raw(verb, '/api/device/hello')
            self.assertEqual((status, served_by), (404, 'JARVIS'), verb)
            if verb != 'HEAD':
                self.assertEqual(json.loads(body), remote_devices.DoorHandler.REFUSED, verb)
        status, served_by, body = self.raw('POST', '/api/device/status')
        self.assertEqual((status, served_by), (401, 'JARVIS'))  # no key: refused by the gateway, with its own words
        self.assertNotIn(b'Python', self.raw('BREW', '/')[2])
        self.assertTrue(self.rows()[paired['device_id']]['connected'])
        status, stopped = self.door('/api/device/stop', {}, {'X-Jarvis-Device': paired['credential']})
        self.assertEqual((status, stopped, self.app.control()['device_name']), (200, {'stopped': True}, 'My phone'))
        self.app.resume('pc')
        # The PC-only door still refuses a request that names the private address.
        self.assertEqual(self.send('/api/device/hello', {}, {'X-Jarvis-Device': paired['credential'], 'Host': f'{ADDRESS}:{port}'})[0], 403)
        # Nothing else is served through the door: no owner route, no page, no test-client route.
        signed_in = {'Cookie': 'jarvis_session=' + self.app.session}
        for path, data in (('/api/devices', None), ('/api/state', None), ('/', None), ('/api/resume', {}), ('/api/emergency-stop', {}),
                           ('/api/remote-devices', {'enabled': False}), ('/api/settings', {'voice': True}), ('/api/chat', {'text': 'hi', 'conversation': 'c'})):
            self.assertEqual(self.door(path, data, signed_in)[0], 404, path)
        self.assertEqual(self.door('/api/wearable/status', {}, {'X-Jarvis-Wearable': self.server.wearable_service.token})[0], 404)
        self.assertTrue(self.app.remote_devices.status()['enabled'])  # the refused "off" through the door changed nothing
        # A browser origin is never accepted at the door, and a wrong Host is refused.
        self.assertEqual(self.door('/api/device/hello', {}, {'X-Jarvis-Device': paired['credential'], 'Origin': f'http://{ADDRESS}:{port}'})[0], 403)
        self.assertEqual(self.door('/api/device/hello', {}, {'X-Jarvis-Device': paired['credential']}, host='other.example:80')[0], 403)
        # Off again: closed at once; the device stays paired and still comes in through the PC door.
        status, state = self.owner('/api/remote-devices', {'enabled': False})
        self.assertEqual((status, state['enabled'], state['open']), (200, False, False))
        self.assertIsNone(self.app.remote_devices.door)
        with self.assertRaises(OSError):
            urllib.request.urlopen(urllib.request.Request(f'http://{ADDRESS}:{port}/api/device/hello', data=b'{}', headers={'Content-Type': 'application/json'}), timeout=2)
        self.assertEqual(self.device('hello', credential=paired['credential'])[0], 200)
        actions = [r['action'] for r in self.app.store.logs()]
        self.assertIn('private network door switch', actions)
        self.assertIn('private network door', actions)

    def test_without_an_address_or_with_a_taken_port_nothing_opens_and_the_panel_says_why(self):
        self.found = {'installed': False, 'address': None, 'name': None}
        port, state = self.turn_on()
        self.assertEqual((state['enabled'], state['open'], state['address']), (True, False, None))
        self.assertIn('Tailscale is not installed', state['message'])
        self.assertIsNone(self.app.remote_devices.door)
        self.found = {'installed': True, 'address': None, 'name': None}
        self.app.remote_devices.looked = 0.0
        state = self.owner('/api/remote-devices')[1]
        self.assertEqual(state['open'], False)
        self.assertIn('no Tailscale address', state['message'])
        # Tailscale comes up later: the next look opens the door.
        self.found = {'installed': True, 'address': ADDRESS, 'name': None}
        self.app.remote_devices.looked = 0.0
        state = self.owner('/api/remote-devices')[1]
        self.assertEqual((state['open'], state['address'], state['name']), (True, ADDRESS, None))
        self.assertIn(f'Open at {ADDRESS}:{port}.', state['message'])
        # The port is held by something else: said plainly, and nothing is taken over.
        self.owner('/api/remote-devices', {'enabled': False})
        blocker = socket.socket()
        blocker.bind((ADDRESS, port))
        blocker.listen(1)
        self.addCleanup(blocker.close)
        state = self.owner('/api/remote-devices', {'enabled': True, 'port': port})[1]
        self.assertEqual((state['enabled'], state['open']), (True, False))
        self.assertIn(f'port {port} at {ADDRESS} could not be opened', state['message'])
        # What the owner may send.
        self.assertEqual(self.owner('/api/remote-devices', {'enabled': 'yes'})[0], 400)
        self.assertEqual(self.owner('/api/remote-devices', {'enabled': True, 'port': 80})[0], 400)
        self.assertEqual(self.owner('/api/remote-devices', {'enabled': True, 'port': '8790'})[0], 400)
        self.assertEqual(self.owner('/api/remote-devices', {'enabled': True, 'extra': 1})[0], 400)
        self.assertEqual(self.owner('/api/remote-devices', {'port': 9000})[0], 400)

    def test_the_door_follows_the_saved_switch_after_a_restart_of_the_core(self):
        port, _ = self.turn_on()
        self.app.remote_devices.close()
        again = server.App(self.temp.name)
        again.remote_devices.find = lambda: dict(self.found)
        self.addCleanup(again.remote_devices.shutdown)
        self.assertIsNone(again.remote_devices.door)  # an App opens nothing by itself
        again.remote_devices.ensure()                 # as main() does on the owner's saved choice
        self.assertEqual((again.remote_devices.status()['open'], again.remote_devices.bound['port']), (True, port))

    def test_the_watcher_opens_and_closes_the_door_without_anyone_asking(self):
        self.found = {'installed': True, 'address': None, 'name': None}
        port, state = self.turn_on()
        self.assertFalse(state['open'])
        remote = self.app.remote_devices
        with patch.object(remote_devices, 'LOOK_EVERY_SECONDS', 0.2):
            remote.watch()  # as main() does
            self.found = {'installed': True, 'address': ADDRESS, 'name': None}  # Tailscale comes up
            for _ in range(50):
                if remote.door is not None:
                    break
                time.sleep(0.1)
            self.assertIsNotNone(remote.door)  # opened by the watcher: no status call was made
            self.assertEqual(remote.bound['port'], port)
            self.found = {'installed': True, 'address': None, 'name': None}  # and goes away again
            for _ in range(50):
                if remote.door is None:
                    break
                time.sleep(0.1)
            self.assertIsNone(remote.door)
            remote.shutdown()
            self.assertIsNone(remote.watcher)
            remote.watch()
            remote.watch()  # a second call starts no second watcher
            self.assertTrue(remote.watcher.is_alive())
            remote.shutdown()


class AddressTests(unittest.TestCase):
    def test_finding_this_pcs_tailscale_address_and_name(self):
        with patch.object(remote_devices, '_tailscale', return_value='100.101.102.103\n'):
            self.assertEqual(remote_devices.tailscale_address(), '100.101.102.103')
        with patch.object(remote_devices, '_tailscale', return_value='192.168.1.5\nnot an address\n'):
            self.assertIsNone(remote_devices.tailscale_address())  # only an address Tailscale gave, in its range
        with patch.object(remote_devices, '_tailscale', return_value=None):
            self.assertIsNone(remote_devices.tailscale_address())  # Tailscale logged out or not answering: no other source
        with patch.object(remote_devices, 'tailscale_command', return_value=None):
            self.assertEqual(remote_devices.find_address(), {'installed': False, 'address': None, 'name': None})
        with patch.object(remote_devices, 'tailscale_command', return_value='tailscale'), patch.object(remote_devices, '_tailscale', return_value=None):
            self.assertEqual(remote_devices.find_address(), {'installed': True, 'address': None, 'name': None})
        remote_devices._name_cache.update(at=0.0, name=None)
        with patch.object(remote_devices, '_tailscale', return_value=json.dumps({'Self': {'DNSName': 'PC.tail-test.ts.net.'}})):
            self.assertEqual(remote_devices.tailscale_name(), 'pc.tail-test.ts.net')
        remote_devices._name_cache.update(at=0.0, name=None)
        with patch.object(remote_devices, '_tailscale', return_value='not json'):
            self.assertIsNone(remote_devices.tailscale_name())
        remote_devices._name_cache.update(at=0.0, name=None)
        self.assertEqual(remote_devices.RemoteDevices.hosts('100.64.0.7', 8790, 'PC.Tail.ts.net.'),
                         frozenset({'100.64.0.7:8790', 'pc.tail.ts.net:8790', 'pc:8790'}))
        self.assertEqual(remote_devices.RemoteDevices.hosts('100.64.0.7', 8790, None), frozenset({'100.64.0.7:8790'}))


if __name__ == '__main__':
    unittest.main()
