"""Release 1.0.18: the list of this Core's devices for a paired device (the app's device panel, R6 of
docs/MAC-REQUESTS-20261007.md; record docs/PHONE-DEVICES-1.0.18.md), tried through the Core's own routes with a real
local server and through the private-network door: the paired devices that are not revoked, with what the owner allows
each; this PC with its JARVIS version; the test client marked as simulated. Read only, counted with the light reads.
"""
import json
import os
import threading
import time
import unittest
from unittest.mock import patch

import server
from test_device_gateway import DeviceCase
from test_remote_devices import DoorCase

FIELDS = {'id', 'name', 'kind', 'online', 'last_seen', 'allowed', 'writes', 'tools', 'approve', 'this_device'}
LIMIT = {'error': 'Wearable request limit reached. Wait one minute.'}


class DeviceListTests(DeviceCase):
    def test_a_paired_device_lists_the_paired_devices_this_pc_and_the_test_client(self):
        phone = self.pair()
        glasses = self.pair('My glasses', 'glasses', ('camera', 'microphone'))
        old = self.pair('Old phone')
        self.owner('/api/devices', {'action': 'revoke', 'id': old['device_id']})
        self.owner('/api/devices', {'action': 'tools', 'id': glasses['device_id'], 'allowed': True})
        self.owner('/api/devices', {'action': 'approve', 'id': phone['device_id'], 'allowed': True})
        status, listing = self.device('devices', {}, phone['credential'])
        self.assertEqual(status, 200, listing)
        self.assertEqual(set(listing), {'devices', 'pc', 'simulated'})
        rows = {d['id']: d for d in listing['devices']}
        self.assertEqual(list(rows), [phone['device_id'], glasses['device_id']])  # in pairing order; the revoked one left out
        for row in rows.values():
            self.assertEqual(set(row), FIELDS)
            self.assertIsInstance(row['last_seen'], float)
        me, other = rows[phone['device_id']], rows[glasses['device_id']]
        self.assertEqual((me['name'], me['kind'], me['online'], me['this_device'], me['allowed']), ('My phone', 'phone', True, True, ['microphone', 'speakers']))
        self.assertEqual((me['writes'], me['tools'], me['approve']), (False, False, True))
        self.assertEqual((other['name'], other['kind'], other['online'], other['this_device'], other['allowed']), ('My glasses', 'glasses', False, False, ['microphone', 'camera']))
        self.assertEqual((other['writes'], other['tools'], other['approve']), (True, True, False))  # the PC's tools include saving, as in hello
        # This PC, with the Core's own version (the installed release, or the development revision here).
        self.assertEqual(listing['pc'], {'name': server.pc_name(), 'core_version': self.app.store.release, 'online': True})
        self.assertTrue(listing['pc']['name'])
        # The same-PC glasses test client, marked as simulated and never counted as a device.
        self.assertEqual(listing['simulated'], [{'name': 'Glasses test client', 'kind': 'glasses', 'online': True}])
        # Nothing secret and nothing about the revoked device crosses.
        text = json.dumps(listing)
        for secret in (phone['key'], glasses['key'], old['key']):
            self.assertNotIn(secret, text)
        for word in (old['device_id'], 'Old phone', 'key_valid', 'declared', 'revoked', 'pairing'):
            self.assertNotIn(word, text)
        # A device that talks to the Core is online from then on, for every device's list.
        self.assertEqual(self.device('hello', {}, glasses['credential'])[0], 200)
        rows = {d['id']: d for d in self.device('devices', {}, phone['credential'])[1]['devices']}
        self.assertTrue(rows[glasses['device_id']]['online'])
        rows = {d['id']: d for d in self.device('devices', {}, glasses['credential'])[1]['devices']}
        self.assertEqual((rows[glasses['device_id']]['this_device'], rows[phone['device_id']]['this_device']), (True, False))

    def test_what_is_declared_but_not_allowed_never_shows_and_the_saving_tick_alone_is_writes(self):
        # Review L5: a capability the device declares later is not allowed by itself and appears nowhere in the list.
        phone = self.pair()
        status, hello = self.device('hello', {'capabilities': ['microphone', 'speakers', 'display']}, phone['credential'])
        self.assertEqual((status, hello['declared'], hello['allowed']), (200, ['microphone', 'speakers', 'display'], ['microphone', 'speakers']))
        listing = self.device('devices', {}, phone['credential'])[1]
        self.assertEqual(listing['devices'][0]['allowed'], ['microphone', 'speakers'])
        self.assertNotIn('display', json.dumps(listing))
        # The tick "may save memories and tasks" alone: writes, not tools.
        self.assertEqual(self.owner('/api/devices', {'action': 'writes', 'id': phone['device_id'], 'allowed': True})[0], 200)
        row = self.device('devices', {}, phone['credential'])[1]['devices'][0]
        self.assertEqual((row['writes'], row['tools'], row['approve']), (True, False, False))

    def test_bye_makes_a_device_offline_at_once_and_a_key_of_another_installation_is_left_out(self):
        phone = self.pair()
        glasses = self.pair('My glasses', 'glasses', ('camera',))
        self.assertEqual(self.device('hello', {}, glasses['credential'])[0], 200)
        rows = {d['id']: d for d in self.device('devices', {}, phone['credential'])[1]['devices']}
        self.assertTrue(rows[glasses['device_id']]['online'])
        self.assertEqual(self.device('bye', {}, glasses['credential'])[0], 200)
        rows = {d['id']: d for d in self.device('devices', {}, phone['credential'])[1]['devices']}
        self.assertFalse(rows[glasses['device_id']]['online'])
        # Review L2: a device whose key was made for another installation (restored data) can never reach this Core:
        # left out of the phone's list (the PC's panel shows it with "pair it again").
        with self.app.store.connect() as db:
            db.execute('UPDATE devices SET secret_id=? WHERE id=?', ('0' * 16, glasses['device_id']))
        self.assertFalse(self.rows()[glasses['device_id']]['key_valid'])
        listing = self.device('devices', {}, phone['credential'])[1]
        self.assertEqual([d['id'] for d in listing['devices']], [phone['device_id']])
        self.assertNotIn(glasses['device_id'], json.dumps(listing))

    def test_it_waits_for_its_turn_instead_of_answering_busy(self):
        # Review L1: another request of the same device holding the session (an overview being read) makes the list
        # wait, not fail; the app may load its panels side by side.
        phone = self.pair()
        self.assertEqual(self.device('status', {}, phone['credential'])[0], 200)
        session = self.app.device_gateway.session(phone['device_id'])
        self.assertTrue(session.lock.acquire(timeout=5))
        threading.Timer(0.3, session.lock.release).start()
        began = time.monotonic()
        status, listing = self.device('devices', {}, phone['credential'])
        self.assertEqual(status, 200, listing)
        self.assertGreaterEqual(time.monotonic() - began, 0.25)  # it waited for the session, then answered
        self.assertEqual(listing['devices'][0]['id'], phone['device_id'])

    def test_an_empty_request_only_counted_with_the_light_reads_and_only_for_a_paired_device(self):
        phone = self.pair()
        self.assertEqual(self.device('devices', {'id': 'x'}, phone['credential']), (400, {'error': 'Unknown fields.'}))
        session = self.app.device_gateway.sessions[phone['device_id']]
        session.reads = [time.monotonic()] * 120
        self.assertEqual(self.device('devices', {}, phone['credential']), (400, LIMIT))
        # No key, or a revoked one: refused before anything is read.
        self.assertEqual(self.device('devices', {})[0], 401)
        self.owner('/api/devices', {'action': 'revoke', 'id': phone['device_id']})
        self.assertEqual(self.device('devices', {}, phone['credential'])[0], 401)
        # The same-PC test client does not get it.
        token = self.server.wearable_service.token
        self.assertEqual(self.send('/api/wearable/devices', {}, {'X-Jarvis-Wearable': token})[0], 400)

    def test_it_reads_on_while_the_emergency_stop_holds_and_changes_nothing(self):
        phone = self.pair()
        before = self.rows()[phone['device_id']]
        self.app.emergency_stop('pc', 'test')
        status, listing = self.device('devices', {}, phone['credential'])
        self.assertEqual(status, 200, listing)  # a read, like the overview: the app still shows the devices while stopped
        after = self.rows()[phone['device_id']]
        self.assertEqual({k: before[k] for k in ('allowed', 'writes', 'tools', 'approve', 'revoked')},
                         {k: after[k] for k in ('allowed', 'writes', 'tools', 'approve', 'revoked')})


class DeviceListDoorTests(DoorCase):
    def test_the_list_through_the_private_network_door(self):
        self.turn_on()
        started = self.owner('/api/devices', {'action': 'pair', 'name': 'My phone', 'kind': 'phone'})[1]
        status, paired = self.door('/api/device/pair', {'code': started['code'], 'capabilities': ['microphone']}, {})
        self.assertEqual(status, 200, paired)
        status, listing = self.door('/api/device/devices', {}, {'X-Jarvis-Device': paired['credential']})
        self.assertEqual(status, 200, listing)
        self.assertEqual([(d['name'], d['online'], d['this_device']) for d in listing['devices']], [('My phone', True, True)])
        self.assertEqual(listing['pc']['core_version'], self.app.store.release)


class PcNameTests(unittest.TestCase):
    def test_the_pcs_own_name_or_this_pc(self):
        with patch('socket.gethostname', return_value='TheGrizzlyBear'):
            self.assertEqual(server.pc_name(), 'TheGrizzlyBear')
        with patch('socket.gethostname', return_value=' '), patch.dict(os.environ, {'COMPUTERNAME': 'BOX'}):
            self.assertEqual(server.pc_name(), 'BOX')
        with patch('socket.gethostname', side_effect=OSError), patch.dict(os.environ, {'COMPUTERNAME': ''}):
            self.assertEqual(server.pc_name(), 'This PC')
        with patch('socket.gethostname', return_value='bad\x00name'):
            self.assertEqual(server.pc_name(), 'This PC')
        with patch('socket.gethostname', return_value='x' * 80):
            self.assertEqual(server.pc_name(), 'x' * 60)


if __name__ == '__main__':
    unittest.main()
