"""Release 1.0.17, the access items (docs/PHONE-ACCESS-PLAN.md, docs/PHONE-ACCESS-1.0.17.md), item A: approve from
the pocket, and this PC's tools for a paired device, tried through the Core's own routes with a real local server:
the two ticks set only on the PC, a device's question running the PC's tools under the owner's switches, the
waiting list and the answer from the device, and the fixed shapes a device is told.
"""
import os
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import permissions
import providers
import server
from server import Run
from test_device_gateway import DONE, ENV, DeviceCase, calls

NOTE = {'title': 'Plan', 'content': 'Buy milk', 'format': 'txt'}
NOT_ALLOWED = {'error': 'Approving is not allowed for this device.'}


class TicksTests(DeviceCase):
    def test_the_two_ticks_are_off_for_a_new_device_and_set_only_on_the_pc(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.assertEqual((paired['tools'], paired['approve'], paired['writes']), (False, False, False))
        hello = self.device('hello', credential=key)[1]
        self.assertEqual((hello['tools'], hello['approve'], hello['waiting'], hello['notices'], hello['protocol']), (False, False, 0, 0, 2))
        self.assertEqual(self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': 'yes'})[0], 400)
        self.assertEqual(self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': True})[0], 200)
        self.assertEqual(self.owner('/api/devices', {'action': 'approve', 'id': ident, 'allowed': True})[0], 200)
        row = self.rows()[ident]
        self.assertEqual((row['tools'], row['approve'], row['writes']), (True, True, False))
        hello = self.device('hello', credential=key)[1]
        self.assertEqual((hello['tools'], hello['approve'], hello['writes']), (True, True, True))  # the PC's tools include saving
        self.assertIn("this PC's tools", hello['scope'])
        self.assertIn('May approve', hello['scope'])
        self.assertEqual(self.device('hello', {'tools': True}, key)[0], 400)  # a device cannot tick itself
        actions = [r['action'] for r in self.app.store.logs()]
        self.assertIn("device may use this PC's tools: My phone", actions)
        self.assertIn('device may approve for JARVIS: My phone', actions)
        # A revoke takes both ticks away, and nothing can be ticked for a revoked device.
        self.owner('/api/devices', {'action': 'revoke', 'id': ident})
        row = self.rows()[ident]
        self.assertEqual((row['tools'], row['approve'], row['writes']), (False, False, False))
        self.assertEqual(self.owner('/api/devices', {'action': 'approve', 'id': ident, 'allowed': True})[0], 400)
        self.assertEqual(self.owner('/api/devices', {'action': 'nonsense', 'id': ident, 'allowed': True})[0], 400)

    def test_the_columns_are_added_to_an_older_database(self):
        import tempfile
        from devices import DeviceBook
        from store import Store
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        store = Store(Path(folder.name))
        with store.connect() as db:  # a 1.0.16 database: the writes column, nothing newer, one device with the tick
            db.execute('''CREATE TABLE devices (id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, key_hash TEXT NOT NULL, secret_id TEXT NOT NULL,
                declared TEXT NOT NULL, allowed TEXT NOT NULL, created REAL NOT NULL, last_seen REAL, revoked REAL, writes INTEGER NOT NULL DEFAULT 0)''')
            db.execute("INSERT INTO devices VALUES ('0123456789abcdef','Old phone','phone','x','y','[\"microphone\"]','[\"microphone\"]',1.0,NULL,NULL,1)")
        book = DeviceBook(store, folder.name)
        with store.connect() as db:
            columns = {row[1] for row in db.execute('PRAGMA table_info(devices)')}
        self.assertTrue({'writes', 'tools', 'approve'} <= columns)
        row = book.get('0123456789abcdef')
        self.assertEqual((row['writes'], row['tools'], row['approve']), (True, False, False))


class ToolsTests(DeviceCase):
    def generated(self):
        folder = Path(self.app.store.root) / 'generated'
        return sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []

    def ask(self, key, text, replies):
        replies = list(replies)
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': text}, key)
            self.assertEqual(status, 200, started)
            return self.finished(key, started['run_id'])

    def test_without_the_tick_a_changing_tool_is_refused_and_with_it_the_pcs_switches_decide(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        events = self.ask(key, 'Write my plan down as a file', [calls('create_file', **NOTE), DONE])
        self.assertIn('tool.failed', events)
        self.assertEqual(self.generated(), [])
        # The tick: the same tool runs, on the PC, and its activity row names the device.
        self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': True})
        events = self.ask(key, 'Write my plan down as a file', [calls('create_file', **NOTE), DONE])
        self.assertIn('tool.completed', events)
        self.assertEqual(len(self.generated()), 1)
        rows = [r for r in self.app.store.logs() if r['action'] == 'create_file']
        self.assertTrue(rows and all(r['device'] == ident for r in rows))
        self.assertIn('started', [r['status'] for r in rows])
        # Off on the PC: refused from the device too.
        self.assertEqual(self.owner('/api/permissions', {'tool': 'create_file', 'mode': 'off'})[0], 200)
        events = self.ask(key, 'Write my plan down as a file', [calls('create_file', **NOTE), DONE])
        self.assertIn('tool.failed', events)
        self.assertEqual(len(self.generated()), 1)
        # The model is offered the PC's tools only with the tick; the instructions say what that means.
        bodies = []
        replies = [DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda url, body=None, headers=None, **k: (bodies.append(body), replies.pop(0))[1]):
            status, started = self.device('start', {'text': 'Tell me a joke about milk'}, key)
            self.finished(key, started['run_id'])
        names = {t['function']['name'] for t in bodies[0]['tools']}
        self.assertIn('open_app', names)
        self.assertNotIn('create_file', names)  # switched off: not offered at all
        self.assertFalse(names & permissions.WINDOW_TOOLS)  # the window's own tools are not offered to a device
        self.assertIn('not reachable from here', bodies[0]['messages'][0]['content'])
        # Asked for anyway: refused with the sentence, nothing "requested" that no window would see.
        events = self.ask(key, 'open the settings section', [calls('navigate_panel', panel='settings'), DONE])
        self.assertIn('tool.failed', events)
        self.assertNotIn('tool.completed', events)
        # The same-PC test client gets none of the new ops.
        token = self.server.wearable_service.token
        for op in ('approvals', 'approve', 'reject'):
            self.assertEqual(self.send('/api/wearable/' + op, {}, {'X-Jarvis-Wearable': token})[0], 400)
        self.assertIn("use this PC's tools", bodies[0]['messages'][0]['content'])

    def test_taking_the_tick_back_during_a_question_stops_the_tools(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': True})
        self.device('hello', credential=key)
        with patch.object(threading, 'Thread'):  # the question stays "running"
            started = self.app.start_run({'text': 'write it down', 'conversation': 'device-' + ident + '-x'}, wearable=True, device=ident, writes=True, tools=True)
        run = self.app.runs[started['run_id']]
        self.assertTrue(run.tools)
        self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': False})
        with self.assertRaises(ValueError) as refused:
            self.app.tool('create_file', NOTE, run=run)
        self.assertIn('unavailable from the wearable client', str(refused.exception))
        self.assertEqual(self.generated(), [])
        run.cancel.set()


class ApprovalTests(DeviceCase):
    def pc_question(self, text, replies):
        """One question of the PC's own, through the real request path (the model's answers in order)."""
        replies = list(replies)
        run = Run('pc-chat')
        self.app.runs[run.id] = run
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            self.app.work(run, text, None)
        return run, {e['event']: e['data'] for e in run.events}

    def test_without_the_tick_nothing_is_listed_or_answered(self):
        paired = self.pair()
        key = paired['credential']
        self.assertEqual(self.device('approvals', credential=key), (403, NOT_ALLOWED))
        self.assertEqual(self.device('approve', {'id': 'a' * 32}, key), (403, NOT_ALLOWED))
        self.assertEqual(self.device('reject', {'id': 'a' * 32}, key), (403, NOT_ALLOWED))

    def test_an_ask_first_call_of_the_pc_is_answered_from_the_phone(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.owner('/api/devices', {'action': 'approve', 'id': ident, 'allowed': True})
        self.assertEqual(self.owner('/api/permissions', {'tool': 'set_timer', 'mode': 'ask'})[0], 200)
        self.assertEqual(self.device('approvals', credential=key), (200, {'items': []}))
        run, events = self.pc_question('Wake me in five minutes please', [calls('set_timer', title='Wake', seconds=300), DONE])
        self.assertEqual(events['tool.completed']['result']['status'], 'awaiting approval')
        approval = events['tool.completed']['result']['approval']
        self.assertAlmostEqual(approval['expires'] - approval['created'], server.APPROVAL_SECONDS, delta=2)  # fifteen minutes
        self.assertEqual(self.device('status', credential=key)[1]['waiting'], 1)
        status, listing = self.device('approvals', credential=key)
        self.assertEqual(status, 200, listing)
        (item,) = listing['items']
        self.assertEqual({k: item[k] for k in ('id', 'kind', 'tool', 'label', 'device', 'device_name', 'run_id', 'conversation')},
                         {'id': approval['id'], 'kind': 'tool', 'tool': 'set_timer', 'label': 'Set a timer', 'device': 'pc', 'device_name': 'this PC',
                          'run_id': run.id, 'conversation': 'pc-chat'})
        self.assertEqual(item['detail'], 'title: Wake\nseconds: 300')
        self.assertEqual((item['created'], item['expires']), (approval['created'], approval['expires']))
        # Rejected from the phone: nothing happens, and the row says who.
        self.assertEqual(self.device('reject', {'id': item['id']}, key), (200, {'status': 'denied'}))
        self.assertEqual(self.app.store.reminders(), [])
        self.assertEqual(self.device('status', credential=key)[1]['waiting'], 0)
        self.assertIn('denied from My phone', [r['status'] for r in self.app.store.logs() if r['action'] == 'set_timer'])
        # Approved from the phone: exactly what was shown runs, once; the PC's conversation says so.
        _, events = self.pc_question('Wake me in five minutes please', [calls('set_timer', title='Wake', seconds=300), DONE])
        ident_two = events['tool.completed']['result']['approval']['id']
        self.assertEqual(self.device('approve', {'id': ident_two}, key), (200, {'status': 'applied', 'result': 'scheduled'}))
        self.assertEqual([r['title'] for r in self.app.store.reminders()], ['Wake'])
        self.assertEqual(self.device('approve', {'id': ident_two}, key), (200, {'status': 'unknown'}))  # once only
        self.assertEqual(len(self.app.store.reminders()), 1)
        self.assertIn('approved from My phone', [r['status'] for r in self.app.store.logs() if r['action'] == 'set_timer'])
        self.assertEqual(self.app.store.history('pc-chat')[-1]['content'], 'Approved from My phone: Set a timer. Result: scheduled.')
        # The PC's own answer is unchanged in its words.
        _, events = self.pc_question('Wake me in five minutes please', [calls('set_timer', title='Again', seconds=300), DONE])
        self.app.approve(events['tool.completed']['result']['approval']['id'], True)
        self.assertEqual(self.app.store.history('pc-chat')[-1]['content'], 'Approved on screen: Set a timer. Result: scheduled.')

    def test_waiting_counts_only_for_a_device_that_may_approve_and_the_pc_may_answer_a_devices_item(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': True})
        self.owner('/api/permissions', {'tool': 'create_file', 'mode': 'ask'})
        replies = [calls('create_file', **NOTE), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'Write my plan down as a file'}, key)
            events = self.finished(key, started['run_id'])
        waiting = events['tool.completed']['result']['approval']['id']
        self.assertEqual(self.device('status', credential=key)[1]['waiting'], 0)  # something waits, but this device may not approve
        self.assertEqual(self.device('approvals', credential=key), (403, NOT_ALLOWED))
        # The PC answers the device's item: the device's conversation gets the PC's line, and nothing waits any more.
        status, done = self.owner('/api/approval', {'id': waiting, 'approved': True})
        self.assertEqual((status, done['status']), (200, 'applied'), done)
        messages = self.device('history', {'conversation': 'device-' + ident + '-local'}, key)[1]['messages']
        self.assertTrue(messages[-1]['content'].startswith('Approved on screen: Create a document file. Result: '))
        self.owner('/api/devices', {'action': 'approve', 'id': ident, 'allowed': True})
        self.assertEqual(self.device('status', credential=key)[1]['waiting'], 0)
        self.assertEqual(self.device('approvals', credential=key), (200, {'items': []}))

    def test_the_devices_own_ask_first_call_waits_and_is_answered_from_the_device(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        for flag in ('tools', 'approve'):
            self.owner('/api/devices', {'action': flag, 'id': ident, 'allowed': True})
        self.owner('/api/permissions', {'tool': 'create_file', 'mode': 'ask'})
        replies = [calls('create_file', **NOTE), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'Write my plan down as a file'}, key)
            events = self.finished(key, started['run_id'])
        self.assertEqual(events['tool.completed']['result']['status'], 'awaiting approval')
        (item,) = self.device('approvals', credential=key)[1]['items']
        self.assertEqual((item['kind'], item['label'], item['device'], item['device_name'], item['conversation']),
                         ('tool', 'Create a document file', ident, 'My phone', 'device-' + ident + '-local'))
        self.assertIn('title: Plan', item['detail'])
        status, done = self.device('approve', {'id': item['id']}, key)
        self.assertEqual((status, done['status']), (200, 'applied'), done)
        self.assertTrue(done['result'])
        self.assertEqual(len(list((Path(self.app.store.root) / 'generated').iterdir())), 1)
        messages = self.device('history', {'conversation': 'device-' + ident + '-local'}, key)[1]['messages']
        self.assertTrue(messages[-1]['content'].startswith('Approved from My phone: Create a document file. Result: '))
        # The tick taken back between the question and the answer: the approved call is refused like any other.
        replies = [calls('create_file', title='Second', content='x', format='txt'), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'Write the second plan down'}, key)
            events = self.finished(key, started['run_id'])
        waiting = events['tool.completed']['result']['approval']['id']
        self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': False})
        self.assertEqual(self.device('approve', {'id': waiting}, key), (200, {'status': 'failed', 'result': 'Refused or failed on the PC; nothing was changed.'}))
        self.assertEqual(len(list((Path(self.app.store.root) / 'generated').iterdir())), 1)

    def test_a_memory_command_and_a_draft_are_listed_in_their_own_kinds(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        for flag in ('tools', 'approve'):
            self.owner('/api/devices', {'action': flag, 'id': ident, 'allowed': True})
        self.owner('/api/permissions', {'tool': 'save_item', 'mode': 'ask'})
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=AssertionError('no model is needed')):
            status, started = self.device('start', {'text': 'remember that I prefer short answers'}, key)
            self.finished(key, started['run_id'])
        (item,) = self.device('approvals', credential=key)[1]['items']
        self.assertEqual((item['kind'], item['label']), ('memory', 'Save a note, a task or a fact'))
        self.assertTrue(item['detail'].startswith('remember that I prefer short answers'))
        status, done = self.device('approve', {'id': item['id']}, key)
        self.assertEqual((status, done['status']), (200, 'applied'), done)
        self.assertIn('short answers', done['result'])
        self.assertTrue(any('short answers' in r['body'] for r in self.app.store.items('memory')))
        # A draft (preview_action) is a kind of its own; approving it runs the drafted call.
        self.owner('/api/permissions', {'tool': 'save_item', 'mode': 'default'})
        replies = [calls('preview_action', action='save_item', arguments_json='{"kind": "note", "body": "Call the bank"}'), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'Draft a note to call the bank'}, key)
            self.finished(key, started['run_id'])
        (item,) = self.device('approvals', credential=key)[1]['items']
        self.assertEqual((item['kind'], item['label'], item['device']), ('draft', 'Save a note, a task or a fact (draft)', ident))
        self.assertIn('body: Call the bank', item['detail'])
        status, done = self.device('approve', {'id': item['id']}, key)
        self.assertEqual((status, done['status']), (200, 'applied'), done)
        self.assertEqual([n['body'] for n in self.app.store.items('note')], ['Call the bank'])

    def test_a_self_change_is_listed_with_its_difference_and_a_broken_one_fails_plainly(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.owner('/api/devices', {'action': 'approve', 'id': ident, 'allowed': True})
        self.app.keep_approval({'id': 'b' * 32, 'tool': 'development_propose', 'args': {'proposal': 'no-such-proposal'},
                                'preview': {'path': 'personality.txt', 'reason': 'Shorter greetings', 'diff': '-Good evening, Sir.\n+Evening, Sir.'},
                                'created': time.time(), 'expires': time.time() + 1800, 'run_id': None, 'conversation': None, 'device': 'pc'})
        (item,) = self.device('approvals', credential=key)[1]['items']
        self.assertEqual((item['kind'], item['label'], item['device_name']), ('self_change', 'Change to personality.txt', 'this PC'))
        self.assertEqual(item['detail'], 'Shorter greetings\n-Good evening, Sir.\n+Evening, Sir.')
        self.assertEqual(self.device('approve', {'id': item['id']}, key), (200, {'status': 'failed', 'result': 'Refused or failed on the PC; nothing was changed.'}))
        self.assertEqual(self.device('approvals', credential=key)[1]['items'], [])  # single use, whatever happened

    def test_expired_unknown_and_stopped(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.owner('/api/devices', {'action': 'approve', 'id': ident, 'allowed': True})
        self.assertEqual(self.device('approve', {'id': 'c' * 32}, key), (200, {'status': 'unknown'}))
        self.assertEqual(self.device('reject', {'id': 'c' * 32}, key), (200, {'status': 'unknown'}))
        self.assertEqual(self.device('approve', {'id': 'not-an-id'}, key)[0], 400)
        self.app.keep_approval({'id': 'd' * 32, 'tool': 'set_timer', 'args': {'title': 'Old', 'seconds': 60}, 'generic': True, 'label': 'Set a timer',
                                'created': time.time() - 1000, 'expires': time.time() - 1, 'run_id': None, 'conversation': None, 'device': 'pc'})
        self.assertEqual(self.device('approvals', credential=key)[1]['items'], [])
        self.assertEqual(self.device('reject', {'id': 'd' * 32}, key), (200, {'status': 'expired'}))
        self.assertEqual(self.device('approve', {'id': 'd' * 32}, key), (200, {'status': 'unknown'}))  # gone now
        self.assertEqual(self.app.store.reminders(), [])
        # The question that asked was cancelled: its item is not listed and answers expired.
        run = Run('pc-chat')
        self.app.runs[run.id] = run
        run.cancel.set()
        self.app.keep_approval({'id': 'f' * 32, 'tool': 'set_timer', 'args': {'title': 'Gone', 'seconds': 60}, 'generic': True, 'label': 'Set a timer',
                                'created': time.time(), 'expires': time.time() + 900, 'run_id': run.id, 'conversation': 'pc-chat', 'device': 'pc'})
        self.assertEqual(self.device('approvals', credential=key)[1]['items'], [])
        self.assertEqual(self.device('approve', {'id': 'f' * 32}, key), (200, {'status': 'expired'}))
        # Answered on the PC a moment ago: unknown, not expired.
        self.app.keep_approval({'id': 'a' * 32, 'tool': 'set_timer', 'args': {'title': 'Twice', 'seconds': 60}, 'generic': True, 'label': 'Set a timer',
                                'created': time.time(), 'expires': time.time() + 900, 'run_id': None, 'conversation': None, 'device': 'pc'})
        self.assertEqual(self.app.approve('a' * 32, False)['status'], 'denied')
        self.assertEqual(self.device('approve', {'id': 'a' * 32}, key), (200, {'status': 'unknown'}))
        # While the emergency stop holds: the stopped sentence, and the stop has dropped every approval anyway.
        self.app.keep_approval({'id': 'e' * 32, 'tool': 'set_timer', 'args': {'title': 'Later', 'seconds': 60}, 'generic': True, 'label': 'Set a timer',
                                'created': time.time(), 'expires': time.time() + 900, 'run_id': None, 'conversation': None, 'device': 'pc'})
        self.assertEqual(self.device('status', credential=key)[1]['waiting'], 1)
        self.assertEqual(self.device('stop', credential=key), (200, {'stopped': True}))
        self.assertEqual(self.device('approvals', credential=key), (400, {'error': permissions.STOPPED_MESSAGE}))
        self.assertEqual(self.device('approve', {'id': 'e' * 32}, key), (400, {'error': permissions.STOPPED_MESSAGE}))
        self.assertEqual(self.device('status', credential=key)[1]['waiting'], 0)
        self.app.resume('pc')
        self.assertEqual(self.device('approve', {'id': 'e' * 32}, key), (200, {'status': 'unknown'}))


if __name__ == '__main__':
    unittest.main()
