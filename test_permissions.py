"""Permissions in one place (release 1.0.15, scope item 3; master document sections 6 and 18).

The table of every tool, the one decision made from it, the emergency stop that holds, "ask first",
and activity rows that name the question and the device.
"""
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

import actions
import answer_evidence
import permissions
import providers
import server
from server import App, Handler, Run, Server
from store import Store

ENV = {'JARVIS_PROVIDER': 'qwen', 'DASHSCOPE_API_KEY': 'qwen-test-key'}
DONE = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'Done.'}}]}


def calls(name, **arguments):
    """What a model answers when it wants one tool."""
    return {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
        {'id': 'c1', 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(arguments)}}]}}]}


class TableTests(unittest.TestCase):
    def test_every_tool_has_exactly_one_row(self):
        tools = [t['function']['name'] for t in actions.TOOLS]
        self.assertEqual(len(tools), len(set(tools)))
        self.assertEqual(sorted(tools), sorted(permissions.TABLE))

    def test_the_lists_other_modules_used_to_keep_are_unchanged(self):
        # Until 1.0.15 these four lists were written out in server.py, answer_evidence.py, store.py and actions.py.
        self.assertEqual(permissions.WEARABLE_TOOLS, {'device_registry', 'time_now', 'list_items', 'conversation_search',
            'conversation_read', 'project_catalog', 'project_read', 'web_search', 'news_search',
            'mail_search', 'mail_read', 'calendar_events', 'network_devices',  # 1.0.17 items G and H: the mail, calendar and network reads
            'about_you'})  # 1.0.19: the You page (about_you.py)
        self.assertEqual(permissions.ACTION_TOOLS, {'save_item', 'set_timer', 'manage_timer', 'manage_saved_memory', 'preview_action',
            'development_edit', 'development_propose', 'development_rollback', 'assistant_control', 'navigate_panel',
            'inspect_interface', 'create_file', 'project_save_document', 'project_link_chat', 'open_app', 'spotify', 'play_music', 'mail_send',
            'workshop_files', 'workshop_run', 'workshop_mission',  # the Workshop (docs/WORKSHOP.md): its changes are receipts too
            'remember_about_you'})  # 1.0.19: an offer kept on the You page
        self.assertEqual(permissions.EVIDENCE_TOOLS, {'calculate', 'create_file', 'save_item', 'set_timer', 'suit_diagram',
            'project_link_chat', 'project_save_document'})
        self.assertEqual(permissions.PREVIEW_TOOLS, ('save_item', 'set_timer', 'create_file'))
        self.assertIs(server.WEARABLE_READ_TOOLS, permissions.WEARABLE_TOOLS)
        self.assertIs(answer_evidence.ACTION_TOOLS, permissions.ACTION_TOOLS)
        preview = next(t['function'] for t in actions.TOOLS if t['function']['name'] == 'preview_action')
        self.assertEqual(preview['parameters']['properties']['action']['enum'], list(permissions.PREVIEW_TOOLS))

    def test_every_row_says_what_the_owner_needs_to_know(self):
        for name, rule in permissions.TABLE.items():
            with self.subTest(tool=name):
                self.assertIn(rule.effect, (permissions.READS, permissions.CHANGES))
                self.assertTrue(rule.label and rule.undo)
                self.assertIn(rule.asks, (permissions.NEVER, permissions.WORDS, permissions.ALWAYS))
                if rule.wearable:  # a wearable only reads
                    self.assertEqual(rule.effect, permissions.READS)
                if rule.effect == permissions.READS:
                    self.assertEqual((rule.asks, rule.read_actions), (permissions.NEVER, ()))
        # JARVIS changing itself always asks, and so does a draft.
        for name in ('development_propose', 'development_edit', 'development_rollback', 'preview_action', 'mail_send'):
            self.assertEqual(permissions.TABLE[name].asks, permissions.ALWAYS)

    def test_some_actions_of_a_changing_tool_only_read(self):
        self.assertEqual(permissions.effect('manage_timer', {'action': 'list'}), permissions.READS)
        self.assertEqual(permissions.effect('manage_timer', {'action': 'cancel'}), permissions.CHANGES)
        self.assertEqual(permissions.effect('spotify', {'action': 'status'}), permissions.READS)
        self.assertEqual(permissions.effect('spotify', {'action': 'play'}), permissions.CHANGES)
        self.assertEqual(permissions.effect('set_timer', {'title': 'x', 'seconds': 5}), permissions.CHANGES)

    def test_the_owners_switch_can_only_make_a_tool_stricter(self):
        self.assertEqual(permissions.MODES, ('default', 'ask', 'off'))
        self.assertEqual(permissions.modes_for('web_search'), ('default', 'off'))            # a read: nothing to ask about
        self.assertEqual(permissions.modes_for('set_timer'), ('default', 'ask', 'off'))
        self.assertEqual(permissions.modes_for('open_app'), ('default', 'ask', 'off'))
        self.assertEqual(permissions.modes_for('development_edit'), ('default', 'off'))      # already always asks
        self.assertEqual(permissions.modes_for('manage_saved_memory'), ('default', 'off'))   # already needs the owner's words
        self.assertEqual(permissions.modes_for('navigate_panel'), ('default', 'off'))        # inside the window that asked

    def test_the_decision(self):
        decide = permissions.decide
        self.assertEqual(decide('no_such_tool')[0], 'refuse')
        self.assertEqual(decide('set_timer', {})[0], 'run')
        # the owner's switch
        self.assertEqual(decide('set_timer', {}, mode='ask')[0], 'ask')
        self.assertEqual(decide('set_timer', {}, mode='ask', approved=True)[0], 'run')
        self.assertEqual(decide('set_timer', {}, mode='ask', by_jarvis=False)[0], 'run')     # the owner's own click
        self.assertEqual(decide('web_search', {}, mode='ask')[0], 'run')                      # not a position for a read
        self.assertEqual(decide('spotify', {'action': 'status'}, mode='ask')[0], 'run')       # only reads
        self.assertEqual(decide('spotify', {'action': 'play'}, mode='ask')[0], 'ask')
        verdict, why = decide('set_timer', {}, mode='off')
        self.assertEqual(verdict, 'refuse')
        self.assertIn('switched off in Settings > Permissions', why)
        self.assertEqual(decide('set_timer', {}, mode='off', approved=True)[0], 'refuse')    # off means off
        self.assertEqual(decide('set_timer', {}, mode='off', by_jarvis=False)[0], 'run')
        # the device
        self.assertEqual(decide('web_search', {}, wearable=True)[0], 'run')
        self.assertEqual(decide('set_timer', {}, wearable=True)[0], 'refuse')
        # the emergency stop: nothing for JARVIS; for the owner's own interface only reads of JARVIS's own records
        for name in permissions.TABLE:
            self.assertEqual(decide(name, {}, stopped=True), ('refuse', permissions.STOPPED_MESSAGE), name)
            self.assertEqual(decide(name, {}, stopped=True, approved=True)[0], 'refuse', name)
        self.assertEqual(decide('development_history', {}, stopped=True, by_jarvis=False)[0], 'run')
        self.assertEqual(decide('manage_timer', {'action': 'list'}, stopped=True, by_jarvis=False)[0], 'run')
        for name, args in (('manage_timer', {'action': 'cancel'}), ('set_timer', {}), ('web_search', {}), ('open_app', {}),
                           ('computer_run_tests', {}), ('spotify', {'action': 'status'}), ('development_edit', {})):
            self.assertEqual(decide(name, args, stopped=True, by_jarvis=False)[0], 'refuse', name)

    def test_the_stop_words(self):
        for text in ('Emergency stop', 'emergency stop!', 'JARVIS, emergency stop', 'Hey Jarvis emergency stop now',
                     'stop everything', 'Stop everything, Jarvis.', 'stop all', 'kill switch', '  Emergency stop.  '):
            self.assertTrue(permissions.stop_phrase(text), text)
        for text in ('stop', 'Stop speaking', 'stop the timer', 'what is an emergency stop?', 'do not stop everything',
                     'emergency stop the music and tell me a joke', 'resume', '', None, 'x' * 200):
            self.assertFalse(permissions.stop_phrase(text), text)

    def test_the_window_and_the_core_agree_on_the_stop_words(self):
        # static/permissions.js sends the stop straight to the Core when it hears these words, also while JARVIS
        # is busy; the Core accepts the same words in a chat message from any device.
        import subprocess
        from pathlib import Path
        cases = ['Emergency stop', 'emergency stop!', 'JARVIS, emergency stop', 'Hey Jarvis emergency stop now', 'ok jarvis. stop everything',
                 'Stop everything, Jarvis.', 'stop all', 'kill switch please', 'stop', 'Stop speaking', 'stop the timer', 'stop all timers',
                 'what is an emergency stop?', 'emergency stop the music', 'resume', 'emergency  stop', '', 'x' * 200]
        code = "const p=require('./static/permissions.js');console.log(JSON.stringify(" + json.dumps(cases) + ".map(t=>p.stopPhrase(t))))"
        out = subprocess.check_output(['node', '-e', code], text=True, cwd=Path(__file__).resolve().parent)
        self.assertEqual(json.loads(out), [permissions.stop_phrase(text) for text in cases])

    def test_the_listing_the_interface_shows(self):
        rows = {row['name']: row for row in permissions.listing({'set_timer': 'ask', 'web_search': 'off', 'time_now': 'ask', 'gone_tool': 'off'})}
        self.assertEqual(sorted(rows), sorted(permissions.TABLE))
        self.assertEqual((rows['set_timer']['mode'], rows['set_timer']['asks'], rows['set_timer']['modes']), ('ask', permissions.NEVER, ['default', 'ask', 'off']))
        self.assertEqual(rows['web_search']['mode'], 'off')
        self.assertEqual((rows['time_now']['mode'], rows['time_now']['modes']), ('default', ['default', 'off']))  # "ask" is not a position for a read
        # The workshop's commands ship as "ask first" (docs/WORKSHOP.md, the owner's decision of 2026-10-07): no saved
        # row means "ask"; a saved "default" row means the owner set Allowed; every other tool ships as "default".
        self.assertEqual((rows['workshop_run']['mode'], rows['workshop_run']['shipped'], rows['set_timer']['shipped']), ('ask', 'ask', 'default'))
        self.assertEqual(permissions.effective({})['workshop_run'], 'ask')
        self.assertEqual(permissions.effective({'workshop_run': 'default'})['workshop_run'], 'default')
        self.assertEqual({n for n, r in permissions.TABLE.items() if r.shipped != permissions.DEFAULT}, {'workshop_run'})
        self.assertEqual(rows['development_edit']['asks'], permissions.ALWAYS)
        self.assertEqual(rows['manage_timer']['reads_for'], ['list'])
        json.dumps(list(rows.values()))


class StoreTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name

    def test_an_older_database_gains_the_columns_and_keeps_its_rows(self):
        # The activity table as every release up to 1.0.14 created it.
        db = sqlite3.connect(os.path.join(self.folder, 'jarvis.sqlite3'))
        db.execute('CREATE TABLE audit (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, status TEXT NOT NULL, created REAL NOT NULL)')
        db.execute("INSERT INTO audit(action,status,created) VALUES ('old row','completed',1.0)")
        db.commit(); db.close()
        store = Store(self.folder)
        store.audit('set_timer', 'completed', 'a' * 32, 'pc')
        Store(self.folder)  # opening twice must not fail on columns that already exist
        new, old = store.logs()
        self.assertEqual((new['action'], new['run_id'], new['device']), ('set_timer', 'a' * 32, 'pc'))
        self.assertEqual((old['action'], old['run_id'], old['device']), ('old row', None, None))
        # An older JARVIS (after a rollback) writes rows without the new columns: that still works.
        db = sqlite3.connect(os.path.join(self.folder, 'jarvis.sqlite3'))
        db.execute("INSERT INTO audit(action,status,created) VALUES ('written by 1.0.14','completed',2.0)")
        db.commit(); db.close()
        self.assertEqual(store.logs()[0]['action'], 'written by 1.0.14')

    def test_the_stop_and_the_switches_are_out_of_reach_of_settings_export_and_import(self):
        store = Store(self.folder)
        self.assertIsNone(store.stop_state())
        store.set_stop({'since': 5.0, 'device': 'pc', 'reason': 'test'})
        self.assertEqual(Store(self.folder).stop_state()['device'], 'pc')
        store.set_tool_mode('set_timer', 'ask')
        self.assertEqual(Store(self.folder).tool_modes(), {'set_timer': 'ask'})
        self.assertNotIn('emergency_stop', store.settings())
        with self.assertRaises(ValueError): store.save_settings({'emergency_stop': False})
        store.import_data({'settings': [{'key': 'emergency_stop', 'value': 'null'}, {'key': 'tool_modes', 'value': '{}'}], 'items': []})
        self.assertEqual(store.stop_state()['device'], 'pc')
        self.assertEqual(store.tool_modes(), {'set_timer': 'ask'})
        store.set_stop(None)
        self.assertIsNone(store.stop_state())
        store.set_tool_mode('set_timer', 'default')
        self.assertEqual(store.tool_modes(), {})

    def test_a_switch_position_that_does_not_exist_is_refused(self):
        store = Store(self.folder)
        for tool, mode in (('no_such_tool', 'off'), ('web_search', 'ask'), ('development_edit', 'ask'), ('set_timer', 'allow'), ('set_timer', None), (None, 'off')):
            with self.assertRaises(ValueError): store.set_tool_mode(tool, mode)
        self.assertEqual(store.tool_modes(), {})

    def test_an_unreadable_stop_record_means_stopped(self):
        store = Store(self.folder)
        with store.connect() as db:
            db.execute("INSERT INTO control VALUES ('emergency_stop','not json')")
        self.assertEqual(store.stop_state(), {})
        self.assertTrue(App(self.folder).control()['stopped'])


class AppCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name
        self.app = App(folder.name)

    def ask(self, text, replies=(), wearable=False):
        """One question through the real request path; `replies` are the model's answers in order."""
        replies, self.bodies = list(replies), []
        run = Run('permissions-test')
        run.wearable, run.device = wearable, 'local-wearable-client' if wearable else 'pc'
        self.app.runs[run.id] = run

        def request(url, body=None, headers=None, **kwargs):
            self.bodies.append(body)
            return replies.pop(0)

        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=request):
            self.app.work(run, text, None)
        return run, {e['event']: e['data'] for e in run.events}

    def rows(self, action):
        return [row for row in self.app.store.logs() if row['action'] == action]


class StopTests(AppCase):
    def test_the_stop_holds_until_the_owner_resumes(self):
        self.assertEqual(self.app.control(), {'stopped': False, 'since': None, 'device': None, 'reason': None, 'device_name': None, 'saved': True})
        waiting = self.app.tool('preview_action', {'action': 'save_item', 'arguments_json': json.dumps({'kind': 'note', 'body': 'x'})})
        busy = Run('busy'); self.app.runs[busy.id] = busy
        before = time.time()
        control = self.app.emergency_stop('pc', 'test')
        self.assertTrue(control['stopped'] and control['saved'])
        self.assertGreaterEqual(control['since'], before)
        self.assertEqual((control['device'], control['reason']), ('pc', 'test'))
        self.assertTrue(busy.cancel.is_set())            # what was running is stopped
        self.assertEqual(self.app.approvals, {})         # what was waiting cannot go ahead later
        with self.assertRaises(ValueError): self.app.approve(waiting['approval']['id'], True)
        busy.done = True
        for attempt in (lambda: self.app.start_run({'text': 'hello', 'conversation': 'c'}),
                        lambda: self.app.start_run({'text': 'resume', 'conversation': 'c'}),
                        lambda: self.app.start_run({'text': 'what time is it', 'conversation': 'c'}, wearable=True),
                        lambda: self.app.tool('set_timer', {'title': 't', 'seconds': 5}),
                        lambda: self.app.tool('web_search', {'query': 'x'}),
                        lambda: self.app.tool('time_now', {}, Run('c')),
                        lambda: self.app.require_running()):
            with self.assertRaises(ValueError) as refused: attempt()
            self.assertEqual(str(refused.exception), permissions.STOPPED_MESSAGE)
        self.assertEqual(self.app.store.reminders(), [])
        # The owner can still look at what happened.
        self.assertIn('changes', self.app.tool('development_history', {}))
        listed = self.app.tool('manage_timer', {'action': 'list'})
        self.assertEqual((listed['timers'], sorted(listed)), ([], ['now', 'timers']))   # 1.0.18: a listing also says the time now
        self.assertTrue(self.app.state()['control']['stopped'])
        # A second stop changes nothing and writes no second row.
        self.assertEqual(self.app.emergency_stop('pc', 'again')['reason'], 'test')
        self.assertEqual([r['status'] for r in self.rows('emergency stop')], ['stopped; 1 waiting approval(s) dropped'])
        # It survives a restart of the Core.
        self.assertTrue(App(self.folder).control()['stopped'])
        self.assertFalse(self.app.resume('pc')['stopped'])
        self.assertFalse(App(self.folder).control()['stopped'])
        self.assertEqual([r['status'] for r in self.rows('emergency stop')], ['resumed', 'stopped; 1 waiting approval(s) dropped'])
        self.assertEqual(self.app.tool('set_timer', {'title': 't', 'seconds': 5})['status'], 'scheduled')
        self.assertFalse(self.app.resume('pc')['stopped'])  # resuming twice is harmless
        self.assertEqual(len(self.rows('emergency stop')), 2)

    def test_the_stop_words_work_from_any_device_also_while_jarvis_is_busy(self):
        busy = Run('busy'); self.app.runs[busy.id] = busy
        with self.assertRaises(ValueError):  # busy: an ordinary question is turned away
            self.app.start_run({'text': 'hello', 'conversation': 'c'})
        with patch.object(providers, 'request', side_effect=AssertionError('no AI model is asked')), \
                patch.object(threading, 'Thread', side_effect=AssertionError('no worker is started')):
            started = self.app.start_run({'text': 'Jarvis, emergency stop', 'conversation': 'wearable-test'}, wearable=True)
        run = self.app.runs[started['run_id']]
        self.assertTrue(run.done and busy.cancel.is_set())
        events = {e['event']: e['data'] for e in run.events}
        self.assertIn('RESUME on the PC', events['assistant.completed']['text'])
        self.assertIn('run.completed', events)
        control = self.app.control()
        self.assertEqual((control['stopped'], control['device']), (True, 'local-wearable-client'))
        self.assertIn('emergency stop', control['reason'])
        self.assertEqual([m['role'] for m in self.app.store.history('wearable-test')], ['user', 'assistant'])
        self.assertEqual(self.rows('emergency stop')[0]['device'], 'local-wearable-client')

    def test_a_failing_disk_does_not_keep_jarvis_running(self):
        busy = Run('busy'); self.app.runs[busy.id] = busy
        with patch.object(self.app.store, 'set_stop', side_effect=sqlite3.OperationalError('disk')), \
                patch.object(self.app.store, 'audit', side_effect=sqlite3.OperationalError('disk')):
            control = self.app.emergency_stop('pc', 'test')
        self.assertEqual((control['stopped'], control['saved']), (True, False))
        self.assertTrue(busy.cancel.is_set())
        with self.assertRaises(ValueError): self.app.require_running()
        # A resume that cannot be written down leaves JARVIS stopped.
        with patch.object(self.app.store, 'set_stop', side_effect=sqlite3.OperationalError('disk')):
            with self.assertRaises(sqlite3.OperationalError): self.app.resume('pc')
        self.assertTrue(self.app.control()['stopped'])

    def test_inspections_and_approvals_wait_too(self):
        cancelled = []
        with patch.object(server.inspection_jobs, 'cancel_all', side_effect=lambda: cancelled.append(True)):
            self.app.emergency_stop('pc', 'test')
        self.assertEqual(cancelled, [True])
        job = server.inspection_jobs
        event = threading.Event()
        with job.lock:
            job.jobs['t' * 32] = {'cancel': event, 'status': 'running', 'expires': time.monotonic() + 60}
        try:
            job.cancel_all()
            self.assertTrue(event.is_set())
        finally:
            with job.lock: job.jobs.pop('t' * 32, None)


class AskFirstTests(AppCase):
    def test_by_default_a_tool_runs_as_before_and_its_rows_name_the_question_and_the_device(self):
        run, events = self.ask('Wake me in five minutes please', [calls('set_timer', title='Wake', seconds=300), DONE])
        self.assertEqual(events['tool.completed']['result']['status'], 'scheduled')
        self.assertEqual(len(self.app.store.reminders()), 1)
        rows = self.rows('set_timer')
        self.assertEqual([r['status'] for r in rows], ['scheduled', 'started'])
        self.assertEqual({(r['run_id'], r['device']) for r in rows}, {(run.id, 'pc')})

    def test_ask_first_waits_for_the_owner_and_then_does_exactly_what_was_shown(self):
        self.app.set_permission('set_timer', 'ask')
        self.assertEqual(self.rows('permission: set_timer')[0]['status'], 'ask')
        run, events = self.ask('Wake me in five minutes please', [calls('set_timer', title='Wake', seconds=300), DONE])
        result = events['tool.completed']['result']
        self.assertEqual(result['status'], 'awaiting approval')
        self.assertIn('Nothing has happened yet', result['summary'])
        self.assertEqual(self.app.store.reminders(), [])
        approval = result['approval']
        self.assertEqual((approval['tool'], approval['args'], approval['device']), ('set_timer', {'title': 'Wake', 'seconds': 300}, 'pc'))
        self.assertEqual(json.loads(self.bodies[1]['messages'][-1]['content'])['status'], 'awaiting approval')  # the model is told
        done = self.app.approve(approval['id'], True)
        self.assertEqual((done['status'], done['result']['status']), ('applied', 'scheduled'))
        self.assertEqual([r['title'] for r in self.app.store.reminders()], ['Wake'])
        with self.assertRaises(ValueError): self.app.approve(approval['id'], True)  # once only
        self.assertEqual(len(self.app.store.reminders()), 1)
        self.assertEqual({(r['run_id'], r['device']) for r in self.rows('set_timer')}, {(run.id, 'pc')})
        # 1.0.18 (docs/CORE-FIXES-20261010.md): an approved timer's receipt says when it goes off.
        self.assertRegex(self.app.store.history('permissions-test')[-1]['content'],
                         r'Approved on screen: Set a timer\. Result: scheduled; goes off at \d\d:\d\d(?: on \w+ \d+ \w+(?: \d{4})?)?\.')

    def test_denied_or_expired_nothing_happens(self):
        self.app.set_permission('set_timer', 'ask')
        _, events = self.ask('Wake me in five minutes please', [calls('set_timer', title='Wake', seconds=300), DONE])
        self.assertEqual(self.app.approve(events['tool.completed']['result']['approval']['id'], False), {'status': 'denied'})
        _, events = self.ask('Wake me in five minutes please', [calls('set_timer', title='Wake', seconds=300), DONE])
        approval = events['tool.completed']['result']['approval']
        self.app.approvals[approval['id']]['expires'] = time.time() - 1
        with self.assertRaises(ValueError): self.app.approve(approval['id'], True)
        self.assertEqual(self.app.store.reminders(), [])

    def test_a_typed_command_waits_too_and_says_so(self):
        self.app.set_permission('set_timer', 'ask')
        _, events = self.ask('set a timer for 5 minutes')
        self.assertEqual(events['assistant.completed']['text'], 'Waiting for approval on screen: Set a timer. Nothing has happened yet.')
        self.assertEqual(self.app.store.reminders(), [])
        self.app.approve(events['tool.completed']['result']['approval']['id'], True)
        self.assertEqual(len(self.app.store.reminders()), 1)

    def test_the_owners_own_buttons_are_their_own_approval(self):
        self.app.set_permission('set_timer', 'ask')
        self.assertEqual(self.app.tool('set_timer', {'title': 't', 'seconds': 5})['status'], 'scheduled')
        self.app.set_permission('set_timer', 'off')
        self.assertEqual(self.app.tool('set_timer', {'title': 't', 'seconds': 5})['status'], 'scheduled')

    def test_switched_off_the_model_is_not_offered_it_and_a_command_is_refused(self):
        self.app.set_permission('set_timer', 'off')
        self.app.set_permission('web_search', 'off')
        run, events = self.ask('Wake me in five minutes please', [calls('set_timer', title='Wake', seconds=300), DONE])
        offered = {t['function']['name'] for t in self.bodies[0]['tools']}
        self.assertEqual(offered, set(permissions.TABLE) - {'set_timer', 'web_search'})
        # A model that asks for it anyway is refused, and told why.
        self.assertEqual(events['tool.failed']['error_code'], 'PermissionRefused')
        self.assertIn('switched off in Settings > Permissions', json.loads(self.bodies[1]['messages'][-1]['content'])['error'])
        _, events = self.ask('set a timer for 5 minutes')
        self.assertIn('"Set a timer" is switched off in Settings > Permissions', events['run.failed']['message'])
        self.assertEqual(self.app.store.reminders(), [])
        self.assertEqual([r['status'] for r in self.rows('set_timer')], ['refused', 'refused'])
        # A draft of it is refused at once instead of failing at the approval.
        with self.assertRaises(ValueError):
            self.app.tool('preview_action', {'action': 'set_timer', 'arguments_json': json.dumps({'title': 't', 'seconds': 5})}, run)
        # Switched on again, everything is as before.
        self.app.set_permission('set_timer', 'default')
        self.ask('set a timer for 5 minutes')
        self.assertEqual(len(self.app.store.reminders()), 1)

    def test_an_approved_draft_is_not_asked_about_twice(self):
        self.app.set_permission('set_timer', 'ask')
        run = Run('c'); self.app.runs[run.id] = run
        draft = self.app.tool('preview_action', {'action': 'set_timer', 'arguments_json': json.dumps({'title': 't', 'seconds': 5})}, run)
        self.assertEqual(self.app.approve(draft['approval']['id'], True)['result']['status'], 'scheduled')
        self.assertEqual(self.app.approvals, {})

    def test_a_fact_is_still_saved_only_on_the_owners_own_words(self):
        self.app.set_permission('save_item', 'ask')
        _, events = self.ask('What is the capital of France?', [calls('save_item', kind='memory', body='Likes Paris'), DONE])
        self.assertIn('tool.failed', events)            # refused before the owner is asked anything
        self.assertEqual(self.app.approvals, {})
        _, events = self.ask('Please remember that I like Paris', [calls('save_item', kind='memory', body='Likes Paris'), DONE])
        self.assertEqual(events['tool.completed']['result']['status'], 'awaiting approval')

    def test_the_exact_memory_commands_obey_the_same_switches(self):
        # "remember that I prefer ..." and "forget memory: ..." are answered by memory.py without a tool call.
        _, events = self.ask('remember that I prefer tea')
        self.assertIn('Saved that preference', events['assistant.completed']['text'])
        self.assertEqual([(r['status'], r['device']) for r in self.rows('memory command: Save a note, a task or a fact')], [('completed', 'pc')])
        self.app.set_permission('save_item', 'ask')
        _, events = self.ask('remember that I prefer coffee')
        self.assertIn('Waiting for approval on screen', events['assistant.completed']['text'])
        self.assertEqual([m['body'] for m in self.app.store.items('memory')], ['Preference: I prefer tea'])
        approval = events['tool.completed']['result']['approval']
        self.assertEqual(approval['args'], {'command': 'remember that I prefer coffee'})
        done = self.app.approve(approval['id'], True)
        self.assertIn('Saved that preference', done['result']['summary'])
        self.assertEqual(len(self.app.store.items('memory')), 2)
        self.app.set_permission('save_item', 'off')
        _, events = self.ask('remember that I prefer water')
        self.assertIn('switched off in Settings > Permissions', events['run.failed']['message'])
        self.app.set_permission('manage_saved_memory', 'off')
        _, events = self.ask('forget memory: Preference: I prefer tea')
        self.assertIn('switched off in Settings > Permissions', events['run.failed']['message'])
        self.assertEqual(len(self.app.store.items('memory')), 2)
        _, events = self.ask('find memory tea')  # a command that only reads is not governed
        self.assertIn('I prefer tea', events['assistant.completed']['text'])
        self.app.set_permission('manage_saved_memory', 'default')
        _, events = self.ask('forget memory: Preference: I prefer tea')
        self.assertIn('Deleted that saved memory', events['assistant.completed']['text'])

    def test_a_wearable_still_only_reads(self):
        run, events = self.ask('Wake me in five minutes please', [calls('set_timer', title='Wake', seconds=300), DONE], wearable=True)
        self.assertEqual({t['function']['name'] for t in self.bodies[0]['tools']}, set(permissions.WEARABLE_TOOLS))
        self.assertIn('unavailable from the wearable client', json.loads(self.bodies[1]['messages'][-1]['content'])['error'])
        self.assertEqual(self.app.store.reminders(), [])

    def test_the_model_is_told_that_every_change_to_itself_waits(self):
        self.ask('Hello there my friend', [DONE])
        system = self.bodies[0]['messages'][0]['content']
        self.assertIn('Every change waits for the owner\'s approval', system)
        self.assertIn('owner-style.css', system)
        self.assertNotIn('apply supported styling or personality changes directly', system)
        described = {t['function']['name']: t['function']['description'] for t in actions.TOOLS}
        for name in ('development_propose', 'development_edit', 'development_rollback'):
            self.assertIn('approval', described[name])
            self.assertNotIn('apply directly', described[name])
            self.assertNotIn('restore immediately', described[name])


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = Server(('127.0.0.1', 0), Handler)
        self.server.app = App(self.temp.name)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def req(self, path, data=None, cookie=True):
        headers = {'Content-Type': 'application/json'}
        if cookie:
            headers['Cookie'] = 'jarvis_session=' + self.server.app.session
        request = urllib.request.Request(self.url + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.read() if path.endswith('.css') or path.endswith('.js') else json.load(response)

    def refused(self, path, data=None, cookie=True):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.req(path, data, cookie)
        return error.exception.code, json.load(error.exception).get('error', '')

    def test_the_stop_the_resume_and_the_table_need_the_owners_session(self):
        for path, data in (('/api/permissions', None), ('/api/permissions', {'tool': 'set_timer', 'mode': 'off'}),
                           ('/api/emergency-stop', {}), ('/api/resume', {})):
            self.assertEqual(self.refused(path, data, cookie=False)[0], 401, path)
        self.assertFalse(self.server.app.control()['stopped'])

    def test_stop_then_resume_through_the_routes(self):
        self.assertFalse(self.req('/api/state')['control']['stopped'])
        stopped = self.req('/api/emergency-stop', {})
        self.assertEqual((stopped['stopped'], stopped['device'], stopped['reason']), (True, 'pc', 'Stop pressed on the PC'))
        self.assertTrue(self.req('/api/state')['control']['stopped'])
        self.assertEqual(self.refused('/api/chat', {'text': 'hello', 'conversation': 'c'}), (400, permissions.STOPPED_MESSAGE))
        self.assertEqual(self.refused('/api/tool', {'name': 'set_timer', 'args': {'title': 't', 'seconds': 5}}), (400, permissions.STOPPED_MESSAGE))
        # 1.0.18 (review 2026-10-10): the window's own timer waits for RESUME too; before, it was set while the stop held.
        self.assertEqual(self.refused('/api/reminder', {'title': 't', 'seconds': 5}), (400, permissions.STOPPED_MESSAGE))
        self.assertEqual(self.server.app.store.reminders(), [])
        self.assertEqual(self.refused('/api/interface-inspection', {'operation': 'start', 'request': {'panel': 'command', 'focus': 'test'}})[1], permissions.STOPPED_MESSAGE)
        self.assertEqual(self.refused('/api/repair-experiment', {})[1], permissions.STOPPED_MESSAGE)
        self.assertIn('changes', self.req('/api/tool', {'name': 'development_history', 'args': {}}))
        self.assertEqual(self.req('/api/cancel-all', {}), {'status': 'cancel requested'})  # the momentary stop still exists
        self.assertFalse(self.req('/api/resume', {})['stopped'])
        self.assertIn('run_id', self.req('/api/chat', {'text': 'emergency stop', 'conversation': 'c'}))
        self.assertTrue(self.req('/api/state')['control']['stopped'])

    def test_the_table_and_the_switches_through_the_routes(self):
        listing = self.req('/api/permissions')
        self.assertEqual(sorted(row['name'] for row in listing['tools']), sorted(permissions.TABLE))
        self.assertFalse(listing['control']['stopped'])
        changed = self.req('/api/permissions', {'tool': 'open_app', 'mode': 'ask'})
        self.assertEqual(next(row for row in changed['tools'] if row['name'] == 'open_app')['mode'], 'ask')
        self.assertEqual(self.refused('/api/permissions', {'tool': 'web_search', 'mode': 'ask'})[0], 400)
        self.assertEqual(self.refused('/api/permissions', {'tool': 'open_app'})[0], 400)
        self.assertEqual(self.req('/api/state')['logs'][0]['action'], 'permission: open_app')

    def test_the_owners_style_sheet_is_empty_until_a_change_is_approved(self):
        config = tempfile.TemporaryDirectory()
        self.addCleanup(config.cleanup)
        with patch('runtime_paths.config_dir_for', return_value=__import__('pathlib').Path(config.name)):
            self.assertEqual(self.req('/owner-style.css'), b'')
            (__import__('pathlib').Path(config.name) / 'owner-style.css').write_text('body{font-size:18px}', encoding='utf-8')
            self.assertEqual(self.req('/owner-style.css'), b'body{font-size:18px}')


if __name__ == '__main__':
    unittest.main()
