"""Core release 1.0.16, the phone release (docs/PHONE-CORE-1.0.16.md; docs/PHONE-PLAN.md section 5): what the
iPhone app needs from the Core, tried through the Core's own routes with a real local server: pairing limits
counted per caller, the owner's tick "may save memories and tasks", a device's own conversations, the PC's
health and an overview for the Status screen, an answer route that waits, and the stop for a recording.
"""
import json
import os
import threading
import time
import unittest
from unittest.mock import patch

import device_gateway
import permissions
import providers
from test_device_gateway import DONE, ENV, DeviceCase, calls


class PairingLimitTests(DeviceCase):
    def test_wrong_codes_lock_the_caller_out_and_leave_the_pairing_waiting(self):
        status, started = self.owner('/api/devices', {'action': 'pair', 'name': 'My phone', 'kind': 'phone'})
        self.assertEqual(status, 200, started)
        wrong = '0000 0000' if started['code'] != '0000 0000' else '1111 1111'
        for _ in range(device_gateway.WRONG_CODES_BEFORE_LOCKOUT - 1):
            self.assertEqual(self.device('pair', {'code': wrong, 'capabilities': []})[0], 403)
        self.assertEqual(self.device('pair', {'code': wrong, 'capabilities': []}), (429, {'error': device_gateway.LOCKED_MESSAGE}))
        self.assertEqual(self.owner('/api/devices')[1]['pairing']['name'], 'My phone')  # the pairing still waits
        # Locked out of pairing: this caller's right code is refused too, and nothing is used up. Its other requests
        # are counted separately (a wrong key is a wrong key, not a locked pairing).
        self.assertEqual(self.device('pair', {'code': started['code'], 'capabilities': []})[0], 429)
        self.assertEqual(self.device('hello', credential='0' * 16 + '.' + 'A' * 43)[0], 401)
        self.assertEqual(self.owner('/api/devices')[1]['pairing']['name'], 'My phone')
        rows = [r for r in self.app.store.logs() if r['action'] == 'device door: a caller is locked out']
        self.assertEqual([r['status'] for r in rows], ['wrong pairing codes from 127.0.0.1'])
        # The lockout passes: the right code pairs.
        gateway = self.app.device_gateway
        with gateway.lock:
            for record in gateway.callers.values():
                record['locked'] = 0.0
        self.assertEqual(self.device('pair', {'code': started['code'], 'capabilities': ['speakers']})[0], 200)

    def test_pairing_calls_are_limited_per_caller_without_ending_anything(self):
        for _ in range(device_gateway.PAIR_CALLS_A_MINUTE):
            self.assertEqual(self.device('pair', {'code': '1234 5678', 'capabilities': []})[0], 403)  # no pairing waits: not a wrong code
        self.assertEqual(self.device('pair', {'code': '1234 5678', 'capabilities': []}), (400, {'error': 'Too many pairing attempts. Wait one minute.'}))
        self.assertEqual(self.device('hello', credential='0' * 16 + '.' + 'A' * 43)[0], 401)  # not locked out: only pairing is paused

    def test_wrong_keys_lock_the_caller_out_of_that_device_but_never_a_valid_key(self):
        paired, other = self.pair(), self.pair('Glasses', 'glasses')
        bad = paired['device_id'] + '.' + 'A' * 43
        for _ in range(device_gateway.BAD_KEYS_A_MINUTE - 1):
            self.assertEqual(self.device('hello', credential=bad)[0], 401)
        self.assertEqual(self.device('hello', credential=bad)[0], 429)  # the twentieth wrong key locks this caller out of that device id
        self.assertEqual(self.device('hello', credential=bad)[0], 429)
        # A valid key is never a guess: the device itself, its stop above all, and the other device all go through.
        self.assertEqual(self.device('hello', credential=paired['credential'])[0], 200)
        self.assertEqual(self.device('stop', credential=paired['credential']), (200, {'stopped': True}))
        self.app.resume('pc')
        self.assertEqual(self.device('hello', credential=other['credential'])[0], 200)
        # A wrong key for another device id is counted on its own (a same-PC program in a retry loop locks nobody else).
        self.assertEqual(self.device('hello', credential=other['device_id'] + '.' + 'B' * 43)[0], 401)
        rows = [r['status'] for r in self.app.store.logs() if r['action'] == 'device door: a caller is locked out']
        self.assertEqual(rows, ['wrong keys for device ' + paired['device_id'] + ' from 127.0.0.1'])


class WritesTests(DeviceCase):
    def test_without_the_tick_a_device_only_reads(self):
        paired = self.pair()
        key = paired['credential']
        self.assertFalse(paired['writes'])
        self.assertEqual((self.device('hello', credential=key)[1]['writes'], self.rows()[paired['device_id']]['writes']), (False, False))
        replies = [calls('set_timer', title='Wake', seconds=300), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'Wake me in five minutes'}, key)
            self.assertEqual(status, 200, started)
            events = self.finished(key, started['run_id'])
        self.assertIn('tool.failed', events)
        self.assertEqual(self.app.store.reminders(), [])
        # The exact memory command is not a command for a device without the tick: nothing is saved.
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', return_value=DONE):
            status, started = self.device('start', {'text': 'remember that I prefer short answers'}, key)
            self.finished(key, started['run_id'])
        self.assertEqual(self.app.store.items('memory'), [])

    def test_with_the_tick_memories_and_timers_are_saved_from_the_device(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.assertEqual(self.owner('/api/devices', {'action': 'writes', 'id': ident, 'allowed': 'yes'})[0], 400)
        status, listing = self.owner('/api/devices', {'action': 'writes', 'id': ident, 'allowed': True})
        self.assertEqual(status, 200, listing)
        self.assertTrue(self.rows()[ident]['writes'])
        hello = self.device('hello', credential=key)[1]
        self.assertEqual((hello['writes'], hello['protocol']), (True, 2))
        self.assertIn('saving memories', hello['scope'])
        # The exact memory command is answered by the Core itself, as on the PC: no model is asked.
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=AssertionError('no model is needed')):
            status, started = self.device('start', {'text': 'remember that I prefer short answers'}, key)
            self.assertEqual(status, 200, started)
            events = self.finished(key, started['run_id'])
        self.assertIn('assistant.completed', events)
        self.assertTrue(any('short answers' in r['body'] for r in self.app.store.items('memory')))
        # A saving tool runs, and its activity row names the device.
        replies = [calls('set_timer', title='Wake', seconds=300), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'Wake me in five minutes'}, key)
            events = self.finished(key, started['run_id'])
        self.assertIn('tool.completed', events)
        self.assertEqual([r['title'] for r in self.app.store.reminders()], ['Wake'])
        rows = [r for r in self.app.store.logs() if r['action'] == 'set_timer']
        self.assertTrue(rows and all(r['device'] == ident and r['status'] != 'refused' for r in rows))
        # Still refused with the tick: everything that is not saving a memory, note, task or timer.
        replies = [calls('open_app', app='calculator'), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'open the calculator'}, key)
            events = self.finished(key, started['run_id'])
        self.assertIn('tool.failed', events)
        # The owner takes the tick back: the next question only reads again.
        self.owner('/api/devices', {'action': 'writes', 'id': ident, 'allowed': False})
        self.assertFalse(self.device('hello', credential=key)[1]['writes'])
        replies = [calls('set_timer', title='Again', seconds=300), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'Wake me again in five minutes'}, key)
            events = self.finished(key, started['run_id'])
        self.assertIn('tool.failed', events)
        self.assertEqual([r['title'] for r in self.app.store.reminders()], ['Wake'])

    def test_with_the_tick_a_tool_set_to_ask_first_asks_on_the_pc(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.owner('/api/devices', {'action': 'writes', 'id': ident, 'allowed': True})
        self.assertEqual(self.owner('/api/permissions', {'tool': 'set_timer', 'mode': 'ask'})[0], 200)
        replies = [calls('set_timer', title='Wake', seconds=300), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'Wake me in five minutes'}, key)
            events = self.finished(key, started['run_id'])
        self.assertEqual(events['tool.completed']['result']['status'], 'awaiting approval')
        self.assertEqual(self.app.store.reminders(), [])
        self.assertEqual([a['device'] for a in self.app.approvals.values()], [ident])

    def test_taking_the_tick_back_during_a_question_stops_the_saving(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.owner('/api/devices', {'action': 'writes', 'id': ident, 'allowed': True})
        self.device('hello', credential=key)
        with patch.object(threading, 'Thread'):  # the question stays "running"
            started = self.app.start_run({'text': 'wake me later', 'conversation': 'device-' + ident + '-x'}, wearable=True, device=ident, writes=True)
        run = self.app.runs[started['run_id']]
        self.assertTrue(run.writes)
        self.owner('/api/devices', {'action': 'writes', 'id': ident, 'allowed': False})
        with self.assertRaises(ValueError) as refused:
            self.app.tool('set_timer', {'title': 'Wake', 'seconds': 300}, run=run)
        self.assertIn('may not save memories or tasks', str(refused.exception))
        self.assertEqual(self.app.store.reminders(), [])
        run.cancel.set()

    def test_revoking_takes_the_tick_away(self):
        paired = self.pair()
        ident = paired['device_id']
        self.owner('/api/devices', {'action': 'writes', 'id': ident, 'allowed': True})
        self.owner('/api/devices', {'action': 'revoke', 'id': ident})
        self.assertFalse(self.rows()[ident]['writes'])
        self.assertEqual(self.owner('/api/devices', {'action': 'writes', 'id': ident, 'allowed': True})[0], 400)
        self.assertIn('device may save memories and tasks: My phone', [r['action'] for r in self.app.store.logs()])


class ReadTests(DeviceCase):
    def test_a_device_lists_and_reads_only_its_own_conversations(self):
        first, second = self.pair('Phone'), self.pair('Glasses', 'glasses')
        mine, other = 'device-' + first['device_id'], 'device-' + second['device_id']
        with patch.dict(os.environ, {}, clear=True):  # no AI key: the Core's own local answer, nothing is sent anywhere
            for paired, text, conversation in ((first, 'hello', mine + '-local'), (first, 'hello again', mine + '-chat'), (second, 'hi', other + '-local')):
                status, started = self.device('start', {'text': text, 'conversation': conversation}, paired['credential'])
                self.assertEqual(status, 200, started)
                self.finished(paired['credential'], started['run_id'])
        status, listing = self.device('conversations', {}, first['credential'])
        self.assertEqual(status, 200, listing)
        self.assertEqual(sorted(c['id'] for c in listing['conversations']), sorted([mine + '-local', mine + '-chat']))
        chat = next(c for c in listing['conversations'] if c['id'] == mine + '-chat')
        self.assertEqual((chat['title'], chat['messages']), ('hello again', 2))
        self.assertTrue(chat['last'] and chat['updated'] >= chat['created'])
        status, history = self.device('history', {'conversation': mine + '-chat'}, first['credential'])
        self.assertEqual(status, 200, history)
        self.assertEqual([m['role'] for m in history['messages']], ['user', 'assistant'])
        self.assertEqual(set(history['messages'][0]), {'id', 'role', 'content', 'created'})
        self.assertEqual(len(self.device('history', {'conversation': mine + '-chat', 'limit': 1}, first['credential'])[1]['messages']), 1)
        # Never another device's conversation, never the PC's, and nothing else in the request.
        self.assertEqual(self.device('history', {'conversation': other + '-local'}, first['credential'])[0], 400)
        self.app.store.message('pc-chat', 'user', 'something said on the PC')
        self.assertEqual(self.device('history', {'conversation': 'pc-chat'}, first['credential'])[0], 400)
        self.assertNotIn('pc-chat', json.dumps(self.device('conversations', {}, first['credential'])[1]))
        self.assertEqual(self.device('conversations', {'x': 1}, first['credential'])[0], 400)
        self.assertEqual(self.device('history', {'conversation': mine + '-chat', 'limit': 0}, first['credential'])[0], 400)
        # The same-PC test client keeps its old surface.
        with self.assertRaises(ValueError):
            self.server.wearable_service.dispatch('conversations', {})

    def test_the_pcs_health_and_an_overview_for_the_status_screen(self):
        paired = self.pair()
        key = paired['credential']
        with patch.dict(os.environ, ENV, clear=True):
            status, metrics = self.device('metrics', {}, key)
        self.assertEqual(status, 200, metrics)
        for field in ('cpu_percent', 'memory', 'disk', 'core_uptime_seconds', 'core_version', 'ai_ready', 'stopped', 'sampled_at', 'scope'):
            self.assertIn(field, metrics)
        self.assertEqual((metrics['ai_ready'], metrics['stopped']), (True, False))
        self.assertTrue(metrics['core_version'].startswith('development '))  # the installed release's id in an installation
        self.assertFalse(any(k.startswith('gpu') or 'temperature' in k for k in metrics))
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(self.device('metrics', {}, key)[1]['ai_ready'])
        self.app.emergency_stop('pc', 'test')
        self.assertTrue(self.device('metrics', {}, key)[1]['stopped'])  # a read, so it still answers while stopped
        self.app.resume('pc')
        # The overview: open tasks, the reminders of the next day, projects with their open tasks, its own conversations.
        store = self.app.store
        task = store.task_put('Buy milk')
        done = store.task_put('Old task')
        store.complete_task(done['id'])
        store.reminder('Call the dentist', 3600)
        store.reminder('Far away', 7 * 86400)
        import workspaces
        project = workspaces.change(store, {'action': 'create', 'name': 'Mini PC'})['id']
        workspaces.change(store, {'action': 'link', 'project': project, 'kind': 'task', 'ref': task['id']})
        workspaces.change(store, {'action': 'link', 'project': project, 'kind': 'task', 'ref': done['id']})
        status, overview = self.device('overview', {}, key)
        self.assertEqual(status, 200, overview)
        self.assertEqual(overview['tasks_open'], 1)
        self.assertEqual([r['title'] for r in overview['reminders']], ['Call the dentist'])
        self.assertEqual([(p['name'], p['open_tasks']) for p in overview['projects']], [('Mini PC', 1)])
        self.assertEqual(overview['conversations'], 0)
        self.assertEqual(self.device('overview', {'x': 1}, key)[0], 400)

    def test_the_answer_route_waits_for_news_without_holding_anything_up(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.device('hello', credential=key)  # present, as a device that asks always is
        with patch.object(threading, 'Thread'):  # the question stays "running" with no events of its own
            started = self.app.start_run({'text': 'hello there', 'conversation': 'device-' + ident + '-x'}, wearable=True, device=ident)
        self.app.device_gateway.session(self.app.device_book.get(ident)).runs.add(started['run_id'])
        run = self.app.runs[started['run_id']]
        # A reply arrives while the device waits: the wait ends at once with the new events.
        threading.Timer(0.3, lambda: run.emit('assistant.delta', {'text': 'Hi'})).start()
        began = time.monotonic()
        status, report = self.device('events', {'run_id': started['run_id'], 'after': -1}, key)
        self.assertEqual(status, 200, report)
        self.assertEqual([e['event'] for e in report['events']], ['assistant.delta'])
        self.assertLess(time.monotonic() - began, 5)
        # Nothing new after the cursor: an empty answer after the wait; the old form still answers everything at once.
        with patch.object(run.condition, 'wait', return_value=False) as waited:
            status, report = self.device('events', {'run_id': started['run_id'], 'after': 0}, key)
            self.assertEqual((status, report['events'], report['done']), (200, [], False))
            self.assertEqual(waited.call_count, 1)
        self.assertEqual(len(self.device('events', {'run_id': started['run_id']}, key)[1]['events']), 1)
        self.assertEqual(self.device('events', {'run_id': started['run_id'], 'after': 'x'}, key), (400, {'error': 'Supply only run_id and after.'}))
        self.assertEqual(self.device('events', {'run_id': 'other', 'after': 0}, key), (400, {'error': 'Unknown wearable run.'}))
        # While one request waits, a cancel from the same device gets through: the wait holds no lock of the service.
        with patch.object(run.condition, 'wait', side_effect=lambda timeout: time.sleep(0.6)):
            waiter = threading.Thread(target=self.device, args=('events', {'run_id': started['run_id'], 'after': 0}, key))
            waiter.start()
            time.sleep(0.15)
            self.assertEqual(self.device('cancel', {'run_id': started['run_id']}, key), (200, {'cancelled': True}))
            waiter.join()
        self.assertTrue(run.cancel.is_set())

    def test_a_recording_is_not_turned_into_text_while_stopped(self):
        paired = self.pair(capabilities=('microphone',))
        key = paired['credential']
        self.app.emergency_stop('pc', 'test')
        with patch.object(self.app.local_stt, 'transcribe', side_effect=AssertionError('nothing is transcribed while stopped')):
            self.assertEqual(self.device('transcribe', {'data': 'AAAA'}, key), (400, {'error': permissions.STOPPED_MESSAGE}))
        self.app.resume('pc')


class PermissionTableTests(unittest.TestCase):
    def test_the_tick_opens_only_the_saving_tools(self):
        self.assertEqual(permissions.DEVICE_WRITE_TOOLS, frozenset({'save_item', 'set_timer', 'manage_timer', 'manage_saved_memory',
                                                                    'remember_about_you'}))   # 1.0.19: an offer for the You page, still approved by the owner
        for name in permissions.DEVICE_WRITE_TOOLS:
            self.assertEqual(permissions.TABLE[name].reach, permissions.LOCAL)
            self.assertEqual(permissions.decide(name, {}, wearable=True, writes=True)[0], 'run')
        verdict, why = permissions.decide('set_timer', {}, wearable=True)
        self.assertEqual(verdict, 'refuse')
        self.assertIn('unavailable from the wearable client', why)
        self.assertIn('Settings > Devices', why)
        self.assertEqual(permissions.decide('open_app', {}, wearable=True, writes=True), ('refuse', 'This operation is unavailable from the wearable client.'))
        self.assertEqual(permissions.decide('development_propose', {}, wearable=True, writes=True)[0], 'refuse')
        self.assertEqual(permissions.decide('web_search', {}, wearable=True, writes=True)[0], 'run')
        self.assertEqual(permissions.decide('set_timer', {}, wearable=True, writes=True, stopped=True)[0], 'refuse')
        self.assertEqual(permissions.decide('set_timer', {}, wearable=True, writes=True, mode=permissions.ASK)[0], 'ask')
        self.assertEqual(permissions.decide('set_timer', {}, wearable=True, writes=True, mode=permissions.OFF)[0], 'refuse')
        self.assertTrue(all('device_writes' in row for row in permissions.listing()))


if __name__ == '__main__':
    unittest.main()
