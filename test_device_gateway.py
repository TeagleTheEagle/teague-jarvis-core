"""Devices the right way round (release 1.0.15, scope item 4; docs/DEVICES.md): the whole path of a paired
device through the Core's own routes: pair with a code read from the PC, ask, be limited to what the owner
allows, stop everything, be revoked.
"""
import base64
import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

import device_gateway
import devices
import permissions
import providers
import recovery
import server
from pathlib import Path
from server import App, Handler, Server
from wearables.service import Service

ENV = {'JARVIS_PROVIDER': 'openrouter', 'OPENROUTER_API_KEY': 'qwen-test-key'}
DONE = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'Done.'}}]}


def calls(name, **arguments):
    return {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
        {'id': 'c1', 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(arguments)}}]}}]}


class DeviceCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = Server(('127.0.0.1', 0), Handler)
        self.app = self.server.app = App(self.temp.name)
        self.server.wearable_service = Service(self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def send(self, path, data, headers):
        request = urllib.request.Request(self.url + path, data=json.dumps(data).encode() if data is not None else None,
                                         headers={'Content-Type': 'application/json', **headers})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def owner(self, path, data=None, signed_in=True):
        return self.send(path, data, {'Cookie': 'jarvis_session=' + self.app.session} if signed_in else {})

    def device(self, op, body=None, credential=None):
        return self.send('/api/device/' + op, body or {}, {'X-Jarvis-Device': credential} if credential else {})

    def pair(self, name='My phone', kind='phone', capabilities=('microphone', 'speakers')):
        status, started = self.owner('/api/devices', {'action': 'pair', 'name': name, 'kind': kind})
        self.assertEqual(status, 200, started)
        status, paired = self.device('pair', {'code': started['code'], 'capabilities': list(capabilities)})
        self.assertEqual(status, 200, paired)
        return paired

    def rows(self):
        return {d['device_id']: d for d in self.owner('/api/devices')[1]['devices']}

    def finished(self, credential, run_id):
        for _ in range(100):
            status, events = self.device('events', {'run_id': run_id}, credential)
            self.assertEqual(status, 200, events)
            if events['done']:
                return {e['event']: e['data'] for e in events['events']}
            time.sleep(0.05)
        self.fail('The question did not finish.')


class PairingTests(DeviceCase):
    def test_pairing_needs_the_owner_on_the_pc_and_the_code_once(self):
        self.assertEqual(self.owner('/api/devices', signed_in=False)[0], 401)
        self.assertEqual(self.owner('/api/devices', {'action': 'pair', 'name': 'x', 'kind': 'phone'}, signed_in=False)[0], 401)
        status, listing = self.owner('/api/devices')
        self.assertEqual((status, listing['pairing']), (200, None))
        self.assertEqual([(d['device_id'], d.get('builtin', False), d['simulated']) for d in listing['devices']],
                         [('pc', True, False), ('local-wearable-client', False, True)])
        status, started = self.owner('/api/devices', {'action': 'pair', 'name': 'My phone', 'kind': 'phone'})
        self.assertRegex(started['code'], r'^\d{4} \d{4}$')
        self.assertEqual(self.owner('/api/devices')[1]['pairing']['name'], 'My phone')
        self.assertNotIn(started['code'].replace(' ', ''), json.dumps(self.owner('/api/devices')[1]))  # the code is shown once only
        self.assertEqual(self.device('pair', {'code': '0000 0000', 'capabilities': []})[0], 403)
        status, paired = self.device('pair', {'code': started['code'], 'capabilities': ['microphone', 'speakers']})
        self.assertEqual((status, paired['name'], paired['kind'], paired['allowed']), (200, 'My phone', 'phone', ['microphone', 'speakers']))
        self.assertEqual(self.device('pair', {'code': started['code'], 'capabilities': []})[0], 403)  # single use
        row = self.rows()[paired['device_id']]
        self.assertEqual((row['name'], row['kind'], row['simulated'], row['connected']), ('My phone', 'phone', False, False))
        self.assertNotIn(paired['key'], json.dumps(self.owner('/api/devices')[1]))
        self.assertNotIn(paired['key'], json.dumps(self.owner('/api/state')[1]))
        actions = [r['action'] for r in self.app.store.logs()]
        self.assertIn('device pairing started: My phone', actions)
        self.assertIn('device paired: My phone', actions)

    def test_no_device_joins_while_the_emergency_stop_holds(self):
        status, started = self.owner('/api/devices', {'action': 'pair', 'name': 'My phone', 'kind': 'phone'})
        self.app.emergency_stop('pc', 'test')
        self.assertEqual(self.device('pair', {'code': started['code'], 'capabilities': []}), (400, {'error': permissions.STOPPED_MESSAGE}))
        self.assertEqual(self.owner('/api/devices', {'action': 'pair', 'name': 'Other', 'kind': 'phone'})[1]['error'], permissions.STOPPED_MESSAGE)
        self.app.resume('pc')
        self.assertEqual(self.device('pair', {'code': started['code'], 'capabilities': []})[0], 200)

    def test_a_device_survives_a_restart_of_the_core(self):
        paired = self.pair()
        again = App(self.temp.name)
        self.assertEqual(again.device_book.authenticate(paired['credential'])['name'], 'My phone')
        self.assertEqual([d['name'] for d in again.device_rows() if not d.get('builtin') and not d['simulated']], ['My phone'])


class PathTests(DeviceCase):
    def test_only_its_own_key_opens_the_door(self):
        paired = self.pair()
        self.assertEqual(self.device('hello')[0], 401)
        self.assertEqual(self.device('hello', credential=paired['device_id'] + '.' + 'A' * 43)[0], 401)
        self.assertEqual(self.device('hello', credential='0' * 16 + '.' + paired['key'])[0], 401)
        status, hello = self.device('hello', credential=paired['credential'])
        self.assertEqual((status, hello['name'], hello['allowed'], hello['stopped']), (200, 'My phone', ['microphone', 'speakers'], False))
        self.assertTrue(self.rows()[paired['device_id']]['connected'])
        self.assertEqual(self.device('resume', credential=paired['credential'])[0], 400)       # no device can resume
        self.assertEqual(self.device('register', credential=paired['credential'])[0], 400)
        # The owner's routes are not opened by a device's key.
        self.assertEqual(self.send('/api/devices', None, {'X-Jarvis-Device': paired['credential']})[0], 401)
        self.assertEqual(self.send('/api/chat', {'text': 'hello', 'conversation': 'c'}, {'X-Jarvis-Device': paired['credential']})[0], 401)

    def test_a_question_from_a_device_only_reads_and_its_rows_name_the_device(self):
        paired = self.pair()
        key = paired['credential']
        replies = [calls('set_timer', title='Wake', seconds=300), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            self.assertEqual(self.device('start', {'text': 'Wake me in five minutes', 'conversation': 'someone-elses-chat'}, key)[0], 400)
            self.assertEqual(self.device('start', {'text': 'Wake me in five minutes', 'conversation': 'device-0000000000000000-chat'}, key)[0], 400)
            status, started = self.device('start', {'text': 'Wake me in five minutes', 'conversation': 'device-' + paired['device_id'] + '-chat'}, key)
            self.assertEqual(status, 200, started)
            events = self.finished(key, started['run_id'])
        self.assertIn('tool.failed', events)
        self.assertEqual(self.app.store.reminders(), [])
        refused = [r for r in self.app.store.logs() if r['action'] == 'set_timer']
        self.assertEqual([(r['status'], r['device']) for r in refused], [('refused', paired['device_id'])])
        # Another device cannot look at this device's question.
        other = self.pair('Glasses', 'glasses', ())
        self.assertEqual(self.device('events', {'run_id': started['run_id']}, other['credential'])[0], 400)

    def test_what_a_device_may_use_is_the_owners_choice(self):
        paired = self.pair(capabilities=('microphone', 'speakers'))
        key, ident = paired['credential'], paired['device_id']
        with patch.object(self.app.voice_engine, 'synthesize', return_value=b'RIFF0000WAVEfmt ' + b'0' * 200):
            status, spoken = self.device('speech', {'text': 'hello'}, key)
            self.assertEqual(status, 200, spoken)
            self.assertEqual(spoken['mime'], providers.audio_mime(b'RIFF0000WAVEfmt ' + b'0' * 200))
            self.assertEqual(self.owner('/api/devices', {'action': 'allow', 'id': ident, 'capabilities': ['microphone']})[0], 200)
            status, refused = self.device('speech', {'text': 'hello'}, key)
            self.assertEqual(status, 403)
            self.assertIn('speakers of this device is not allowed', refused['error'])
        # A picture needs the camera, which this device does not even declare.
        self.assertEqual(self.device('start', {'text': 'what is this', 'image': 'AAAA'}, key)[0], 403)
        # A capability it starts to declare later is not allowed until the owner allows it.
        status, hello = self.device('hello', {'capabilities': ['microphone', 'speakers', 'camera']}, key)
        self.assertEqual((hello['declared'], hello['allowed']), (['microphone', 'camera', 'speakers'], ['microphone']))
        self.assertEqual(self.owner('/api/devices', {'action': 'allow', 'id': ident, 'capabilities': ['display']})[0], 400)  # not declared

    def test_any_paired_device_can_stop_everything_and_none_can_resume(self):
        paired = self.pair()
        status, stopped = self.device('stop', credential=paired['credential'])
        self.assertEqual((status, stopped), (200, {'stopped': True}))
        control = self.owner('/api/state')[1]['control']
        self.assertEqual((control['stopped'], control['device'], control['device_name']), (True, paired['device_id'], 'My phone'))
        self.assertEqual(self.device('start', {'text': 'hello'}, paired['credential']), (400, {'error': permissions.STOPPED_MESSAGE}))
        self.assertTrue(self.device('status', credential=paired['credential'])[1]['stopped'])
        self.assertEqual(self.device('resume', credential=paired['credential'])[0], 400)
        self.assertTrue(self.app.control()['stopped'])
        self.assertFalse(self.owner('/api/resume', {})[1]['stopped'])

    def test_revoked_means_refused_from_the_next_request_on(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.device('hello', credential=key)
        with patch.object(threading, 'Thread'):  # the question stays "running"
            started = self.app.start_run({'text': 'hello there', 'conversation': 'device-' + ident + '-x'}, wearable=True, device=ident)
        self.app.device_gateway.session(ident).runs.add(started['run_id'])
        self.assertEqual(self.owner('/api/devices', {'action': 'forget', 'id': ident})[0], 400)  # revoke first
        status, listing = self.owner('/api/devices', {'action': 'revoke', 'id': ident})
        self.assertEqual(status, 200, listing)
        self.assertTrue(self.app.runs[started['run_id']].cancel.is_set())
        self.assertEqual(self.device('hello', credential=key)[0], 401)
        row = self.rows()[ident]
        self.assertTrue(row['revoked'])
        self.assertEqual((row['connected'], row['allowed'], row['ready']), (False, [], []))
        self.assertEqual(self.owner('/api/devices', {'action': 'forget', 'id': ident})[0], 200)
        self.assertNotIn(ident, self.rows())
        self.assertIn('device revoked: My phone', [r['action'] for r in self.app.store.logs()])


class ReviewTests(DeviceCase):
    """The independent review of this item (docs/DEVICES.md section 8): one test per finding fixed in the Core."""

    def test_a_devices_stop_is_never_turned_away(self):  # M1
        paired = self.pair(capabilities=('microphone',))  # no camera allowed
        key = paired['credential']
        # The stop words with a picture attached, from a device that may not send pictures: still a stop.
        status, started = self.device('start', {'text': 'Emergency stop!', 'image': 'AAAA', 'conversation': 'not-even-a-valid-chat'}, key)
        self.assertEqual(status, 200, started)
        self.assertEqual((self.app.control()['stopped'], self.app.control()['device']), (True, paired['device_id']))
        self.app.resume('pc')
        # The stop button of a device while the database cannot be written (a backup holds it): still a stop, at once.
        self.app.device_gateway.seen_at.clear()
        with patch.object(self.app.device_book, 'seen', side_effect=AssertionError('nothing is written before a stop')):
            self.assertEqual(self.device('stop', credential=key), (200, {'stopped': True}))
        self.app.resume('pc')
        # "Last seen" is written at most once a minute, and a failure to write it never fails the request.
        self.app.device_gateway.seen_at.clear()
        with patch.object(self.app.device_book, 'seen', side_effect=sqlite3.OperationalError('database is locked')) as seen:
            self.assertEqual(self.device('status', credential=key)[0], 200)
            self.assertEqual(seen.call_count, 1)
        with patch.object(self.app.device_book, 'seen') as seen:
            for _ in range(3):
                self.assertEqual(self.device('status', credential=key)[0], 200)
            self.assertEqual(seen.call_count, 1)

    def test_an_older_copy_of_the_database_does_not_bring_a_revoked_device_back(self):  # M3
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        database = Path(self.temp.name) / 'jarvis.sqlite3'
        with self.app.store.connect() as db:
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        before = database.read_bytes()
        self.owner('/api/devices', {'action': 'revoke', 'id': ident})
        self.owner('/api/devices', {'action': 'forget', 'id': ident})
        self.assertEqual(self.device('hello', credential=key)[0], 401)
        with self.app.store.connect() as db:
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        database.write_bytes(before)  # the older copy, put back into the same installation
        self.assertEqual(self.device('hello', credential=key)[0], 401)
        row = self.rows()[ident]
        self.assertTrue(row['revoked'])
        self.assertEqual((row['allowed'], row['connected'], row['key_valid']), ([], False, False))
        self.assertEqual(self.owner('/api/devices', {'action': 'allow', 'id': ident, 'capabilities': ['microphone']})[0], 400)
        self.assertEqual(self.owner('/api/devices', {'action': 'forget', 'id': ident})[0], 200)  # and it can be removed again

    def test_a_backup_of_an_isolated_instance_leaves_the_key_files_out(self):  # L1
        self.assertEqual(set(recovery.DEVICE_KEY_FILES), {devices.SECRET_FILE, devices.REVOKED_FILE, devices.REVOKED_FILE + '.new'})
        paired = self.pair()
        self.owner('/api/devices', {'action': 'revoke', 'id': paired['device_id']})
        self.assertTrue((Path(self.temp.name) / devices.SECRET_FILE).is_file())  # an isolated instance keeps them with its data
        self.assertTrue((Path(self.temp.name) / devices.REVOKED_FILE).is_file())
        selected, excluded = recovery.inventory(server.ROOT, Path(self.temp.name))
        self.assertFalse(any('.env.device' in name for name in selected))
        self.assertTrue({devices.SECRET_FILE, devices.REVOKED_FILE} <= set(excluded))

    def test_each_device_has_its_own_conversations(self):  # L2
        first, second = self.pair('Phone'), self.pair('Glasses', 'glasses')
        with patch.dict(os.environ, {}, clear=True):  # no AI key: the Core's own local answer, nothing is sent anywhere
            for paired in (first, second):
                status, started = self.device('start', {'text': 'hello'}, paired['credential'])
                self.assertEqual(status, 200, started)
                self.finished(paired['credential'], started['run_id'])
        chats = {c['id'] for c in self.app.store.conversations()}
        self.assertEqual(chats, {'device-' + first['device_id'] + '-local', 'device-' + second['device_id'] + '-local'})
        self.assertEqual(self.device('start', {'text': 'hello', 'conversation': 'device-' + first['device_id'] + '-local'}, second['credential'])[0], 400)

    def test_a_revoke_that_lands_during_a_request_lets_nothing_through(self):  # L3
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        gateway, book = self.app.device_gateway, self.app.device_book
        real_present = gateway.present

        def present_then_revoke(device):  # the owner's click lands after the key was checked
            real_present(device)
            book.revoke(ident)

        with patch.object(gateway, 'present', side_effect=present_then_revoke), patch.object(self.app, 'start_run', side_effect=AssertionError('no question starts')):
            self.assertEqual(self.device('start', {'text': 'hello'}, key)[0], 401)
        self.assertEqual(self.app.store.history('device-' + ident + '-local'), [])
        self.assertNotIn(ident, gateway.sessions)
        self.assertEqual(self.owner('/api/devices', {'action': 'forget', 'id': ident})[0], 200)
        self.assertEqual(sorted(self.rows()), ['local-wearable-client', 'pc'])  # no leftover row named by its id
        # And when it lands while the question is being started, that question is cancelled.
        paired = self.pair('Second')
        key, ident = paired['credential'], paired['device_id']
        real_start = self.app.start_run

        def start_then_revoke(*args, **kwargs):
            started = real_start(*args, **kwargs)
            book.revoke(ident)
            return started

        with patch.dict(os.environ, {}, clear=True), patch.object(providers, 'request', side_effect=AssertionError('nothing is sent')),                 patch.object(self.app, 'start_run', side_effect=start_then_revoke):
            self.assertEqual(self.device('start', {'text': 'hello there'}, key)[0], 401)
        self.assertTrue(all(run.cancel.is_set() for run in self.app.runs.values() if getattr(run, 'device', None) == ident))

    def test_only_a_refused_key_says_pair_again(self):  # L4
        paired = self.pair(capabilities=('speakers',))
        key = paired['credential']
        with patch.object(self.app.voice_engine, 'synthesize', side_effect=PermissionError('a locked file somewhere')):
            self.assertEqual(self.device('speech', {'text': 'hello'}, key), (503, {'error': 'JARVIS service unavailable.'}))
        # Nothing of Python's own wording reaches a device.
        self.assertEqual(self.device('start', {'text': 'look', 'image': '!!not base64!!'}, key)[0], 403)  # no camera: said first
        camera = self.pair('Camera', 'glasses', ('camera',))['credential']
        self.assertEqual(self.device('start', {'text': 'look', 'image': '!!not base64!!'}, camera), (400, {'error': device_gateway.GENERAL}))
        self.assertEqual(self.device('start', {'text': 'look', 'image': base64.b64encode(b'this is not a picture').decode()}, camera), (400, {'error': 'Unsupported image.'}))
        self.assertEqual(self.device('events', {'run_id': 5}, key), (400, {'error': 'Unknown wearable run.'}))

    def test_the_secret_is_made_on_the_owners_click_and_never_written_over(self):  # L4
        secret = Path(self.temp.name) / devices.SECRET_FILE
        self.assertFalse(secret.exists())
        status, started = self.owner('/api/devices', {'action': 'pair', 'name': 'Phone', 'kind': 'phone'})
        self.assertTrue(secret.is_file())  # made when the owner starts pairing, so a problem shows on the PC
        paired = self.device('pair', {'code': started['code'], 'capabilities': []})[1]
        secret.write_text('not a secret any more', encoding='ascii')  # damaged
        status, refused = self.owner('/api/devices', {'action': 'pair', 'name': 'Other', 'kind': 'phone'})
        self.assertEqual(status, 400)
        self.assertIn('cannot be read', refused['error'])
        self.assertEqual(secret.read_text(encoding='ascii'), 'not a secret any more')  # not replaced
        self.assertEqual(self.device('hello', credential=paired['credential'])[0], 401)
        self.assertFalse(self.rows()[paired['device_id']]['key_valid'])
        # The file vanishes between the owner's click and the device's code: the code is not used up.
        secret.unlink()
        status, started = self.owner('/api/devices', {'action': 'pair', 'name': 'Third', 'kind': 'phone'})
        secret.unlink()
        self.assertEqual(self.device('pair', {'code': started['code'], 'capabilities': []})[0], 403)
        self.assertEqual(self.owner('/api/devices')[1]['pairing']['name'], 'Third')


class TestClientTests(DeviceCase):
    def test_a_client_can_no_longer_declare_itself_real(self):
        service = self.server.wearable_service
        service.dispatch('register', {'capabilities': ['camera', 'microphone'], 'ready': ['camera'], 'simulated': False})
        row = self.rows()['local-wearable-client']
        self.assertEqual((row['simulated'], row['connected'], row['kind']), (True, True, 'glasses'))
        state = self.owner('/api/state')[1]
        self.assertEqual([d['device_id'] for d in state['devices'] if d['connected'] and not d['simulated']], ['pc'])


if __name__ == '__main__':
    unittest.main()
