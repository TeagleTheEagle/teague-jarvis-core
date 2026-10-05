"""The independent review of "permissions in one place" (docs/PERMISSIONS.md section 9), one test per finding
that the Core, the store, the self-change module or the bridges fixed. The window's side is in
test_permissions_view.cjs and test_voice_thinking_wake.cjs.
"""
import email.message
import io
import json
import os
import sqlite3
import subprocess
import tempfile
import threading
import time
import types
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import actions
import development
import permissions
import runtime_paths
import server
import test_permissions as base
import wearables.service
from phone_bridge import Bridge, Stopped
from server import App, Handler, Server
from store import Store


class StopWordTests(unittest.TestCase):
    STOPS = ('Emergency stop?', 'Emergency, stop.', 'Hey, Jarvis, emergency stop.', 'EMERGENCY STOP!!!',
             'Okay Jarvis: kill switch, please.', 'emergency-stop', 'Stop everything now, Jarvis!',
             'Kill switch?', 'ok stop all', 'Emergency stop…', '“Emergency stop”', 'emergency stop')
    # Anything besides the words and punctuation means it is not the stop: a digit, an emoji, another script.
    NOT_STOPS = ('stop', 'Is there an emergency stop?', "don't stop everything", 'stop all timers',
                 'emergency stop the music', 'non-emergency stop', 'please stop', 'jarvis', '?!',
                 'Stop all 3', 'stop all 2!', 'kill switch 2', 'Emergency stop #2', '1. stop all', 'stop all (3)',
                 'stop everything \U0001f602', 'stop all таймеры', 'stop_all',
                 'emergency stop' + '\U0001f602' * 34, 'emergency stop' + ' ' * 70, 'emergency stop')

    def test_capitals_and_punctuation_do_not_matter(self):  # finding 6
        for text in self.STOPS:
            self.assertTrue(permissions.stop_phrase(text), text)
        for text in self.NOT_STOPS:
            self.assertFalse(permissions.stop_phrase(text), text)

    def test_the_window_agrees_on_them(self):
        cases = list(self.STOPS + self.NOT_STOPS)
        code = "const p=require('./static/permissions.js');console.log(JSON.stringify(" + json.dumps(cases) + ".map(t=>p.stopPhrase(t))))"
        out = subprocess.check_output(['node', '-e', code], text=True, cwd=Path(__file__).resolve().parent)
        self.assertEqual(json.loads(out), [permissions.stop_phrase(text) for text in cases])


class CoreTests(base.AppCase):
    def test_the_window_is_told_which_switches_differ_from_allowed(self):  # finding 2
        self.assertEqual(self.app.state()['permissions'], {})
        self.app.set_permission('navigate_panel', 'off')
        self.app.set_permission('inspect_interface', 'ask')
        self.assertEqual(self.app.state()['permissions'], {'navigate_panel': 'off', 'inspect_interface': 'ask'})
        self.app.set_permission('navigate_panel', 'default')
        self.assertEqual(self.app.state()['permissions'], {'inspect_interface': 'ask'})
        # A stored position that no longer exists for a tool is not passed on.
        self.assertEqual(permissions.changed({'web_search': 'ask', 'gone_tool': 'off', 'set_timer': 'default'}), {})

    def test_nothing_is_kept_for_approval_once_the_stop_holds(self):  # finding 4
        self.app.emergency_stop('pc', 'test')
        with self.assertRaises(ValueError) as refused:
            self.app.keep_approval({'id': 'a' * 32, 'tool': 'set_timer', 'args': {}, 'expires': time.time() + 60, 'run_id': None})
        self.assertEqual(str(refused.exception), permissions.STOPPED_MESSAGE)
        self.assertEqual(self.app.approvals, {})

    def test_a_stop_that_lands_while_a_draft_is_prepared_leaves_no_approval(self):  # finding 4
        real = actions.validate

        def validate_then_stop(name, args):
            checked = real(name, args)
            if name == 'save_item':
                self.app.emergency_stop('pc', 'lands in between')
            return checked

        with patch.object(server.actions, 'validate', side_effect=validate_then_stop):
            with self.assertRaises(ValueError) as refused:
                self.app.tool('preview_action', {'action': 'save_item', 'arguments_json': json.dumps({'kind': 'note', 'body': 'x'})})
        self.assertEqual(str(refused.exception), permissions.STOPPED_MESSAGE)
        self.assertEqual(self.app.approvals, {})

    def test_a_running_repair_experiment_is_stopped_too(self):  # finding 5
        experiment = {'operation': 'op-1', 'status': 'RUNNING', 'cancel': threading.Event()}
        self.app.repair_experiment = experiment
        self.app.emergency_stop('pc', 'test')
        self.assertTrue(experiment['cancel'].is_set())
        # And none starts once the stop holds: looked at under the lock the stop takes (second review, L4).
        import budgeted_repair
        experiment['status'] = 'CANCELLED'  # the stopped one has ended
        with self.assertRaises(ValueError) as refused:
            budgeted_repair.dispatch(self.app, None, {'action': 'run', 'operation': 'op-2', 'project': 'p', 'task': 't', 'confirmation': 'c'})
        self.assertEqual(str(refused.exception), permissions.STOPPED_MESSAGE)
        self.assertEqual(self.app.repair_experiment['operation'], 'op-1')

    def test_a_question_cannot_slip_in_at_the_moment_a_stop_arrives(self):  # second review, L4
        # The stop is looked at while holding the lock the stop itself takes: either the question is refused,
        # or it is already registered when the stop runs and is cancelled by it.
        held = []
        real = self.app.require_running

        def looked_at():
            held.append(self.app.lock._is_owned())
            return real()

        with patch.object(self.app, 'require_running', side_effect=looked_at), patch.object(threading, 'Thread') as worker:
            started = self.app.start_run({'text': 'hello there', 'conversation': 'c'})
        self.assertEqual(held, [True])
        self.assertTrue(worker.called)
        self.app.emergency_stop('pc', 'test')
        self.assertTrue(self.app.runs[started['run_id']].cancel.is_set())

    def test_repeating_the_stop_words_piles_nothing_up(self):  # second review, L5
        for _ in range(6):
            self.app.start_run({'text': 'Emergency stop', 'conversation': 'c'})
        self.assertEqual([m['role'] for m in self.app.store.history('c')], ['user', 'assistant'])  # said once
        self.assertEqual(len(self.rows('emergency stop')), 1)
        # A wearable that repeats them once JARVIS is stopped is an ordinary client again: its usual limits apply.
        service = wearables.service.Service(self.app)
        service.calls = [time.monotonic()] * 20
        with self.assertRaises(ValueError) as refused:
            service.dispatch('start', {'text': 'emergency stop', 'conversation': 'wearable-x'})
        self.assertIn('request limit', str(refused.exception))
        # Old answers are not kept for ever.
        for run in self.app.runs.values():
            run.created -= 3600
        self.app.start_run({'text': 'Emergency stop', 'conversation': 'c'})
        self.assertEqual(len(self.app.runs), 1)

    def test_the_stop_words_come_before_everything_else_about_a_question(self):  # finding 6
        started = self.app.start_run({'text': 'Emergency, stop.', 'conversation': 'not a valid id!', 'attachment': 5})
        self.assertTrue(self.app.control()['stopped'])
        self.assertTrue(self.app.runs[started['run_id']].done)
        self.assertEqual(self.app.store.conversations(), [])  # nothing is written under an id that is not one

    def test_a_wearables_stop_words_are_never_turned_away(self):  # finding 6
        service = wearables.service.Service(self.app)
        service.calls = [time.monotonic()] * 20   # at its limit of questions a minute
        service.lock.acquire()                    # and busy
        try:
            result = service.dispatch('start', {'text': 'Hey, Jarvis, emergency stop.', 'conversation': 'someone-elses-chat', 'extra': 1})
        finally:
            service.lock.release()
        control = self.app.control()
        self.assertEqual((control['stopped'], control['device']), (True, 'local-wearable-client'))
        self.assertIn(result['run_id'], service.runs)
        self.assertEqual([m['role'] for m in self.app.store.history('wearable-local')], ['user', 'assistant'])
        self.assertEqual(self.app.store.history('someone-elses-chat'), [])
        # While stopped a device is told so plainly, and nothing is spoken for it.
        service.calls = []
        for op, body in (('start', {'text': 'what time is it', 'conversation': 'wearable-x'}), ('speech', {'text': 'hello'})):
            with self.assertRaises(ValueError) as refused:
                service.dispatch(op, body)
            self.assertEqual(str(refused.exception), permissions.STOPPED_MESSAGE, op)
        body = json.dumps({'text': 'what time is it', 'conversation': 'wearable-x'}).encode()
        headers = email.message.Message()
        for name, value in (('Host', '127.0.0.1:1'), ('X-Jarvis-Wearable', service.token), ('Content-Length', str(len(body))), ('Content-Type', 'application/json')):
            headers[name] = value
        sent = []
        handler = types.SimpleNamespace(server=types.SimpleNamespace(wearable_service=service, server_port=1), headers=headers,
                                        rfile=io.BytesIO(body), path='/api/wearable/start', close_connection=False,
                                        send=lambda status, payload: sent.append((status, payload)))
        wearables.service.handle(handler)
        self.assertEqual(sent, [(400, {'error': permissions.STOPPED_MESSAGE, 'stopped': True})])

    def test_a_wearables_refused_tool_call_has_its_activity_row(self):  # finding 9
        self.ask('Wake me in five minutes please', [base.calls('set_timer', title='Wake', seconds=300), base.DONE], wearable=True)
        self.assertEqual([(r['status'], r['device']) for r in self.rows('set_timer')], [('refused', 'local-wearable-client')])
        self.assertEqual(self.app.store.reminders(), [])

    def test_a_memory_command_row_names_the_command_and_says_when_nothing_changed(self):  # finding 14
        self.ask('remember that I prefer tea')
        self.ask('forget memory: something that was never saved')
        self.assertEqual([r['status'] for r in self.rows('memory command: Save a note, a task or a fact')], ['completed'])
        self.assertEqual([r['status'] for r in self.rows('memory command: Change or delete a saved fact')], ['nothing changed'])
        self.assertEqual(len(self.app.store.items('memory')), 1)

    def test_a_tool_set_to_ask_first_is_offered_to_the_model_saying_so(self):  # finding 14
        self.app.set_permission('open_app', 'ask')
        self.ask('Hello there my friend', [base.DONE])
        described = {t['function']['name']: t['function']['description'] for t in self.bodies[0]['tools']}
        self.assertIn('asked on screen before this happens', described['open_app'])
        self.assertNotIn('immediately', described['open_app'])
        self.assertNotIn('asked on screen', described['set_timer'])
        shared = next(t for t in actions.TOOLS if t['function']['name'] == 'open_app')['function']['description']
        self.assertNotIn('asked on screen', shared)  # the shared list of tools is not changed by one owner's switch
        self.assertEqual(permissions.offered({'function': {'name': 'web_search', 'description': 'x'}}, 'ask')['function']['description'], 'x')


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = Server(('127.0.0.1', 0), Handler)
        self.server.app = App(self.temp.name)
        self.server.wearable_service = None
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def req(self, path, data=None):
        headers = {'Content-Type': 'application/json', 'Cookie': 'jarvis_session=' + self.server.app.session}
        request = urllib.request.Request(self.url + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)

    def refused(self, path, data=None):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.req(path, data)
        return error.exception.code, json.load(error.exception).get('error', '')

    def test_while_stopped_the_owners_own_buttons_do_not_reach_the_internet(self):  # finding 3
        self.req('/api/emergency-stop', {})
        nothing = AssertionError('nothing reaches the internet while stopped')
        with patch.object(server.actions, 'search', side_effect=nothing), patch.object(server.maps, 'directions', side_effect=nothing), \
                patch.object(server.providers, 'transcribe', side_effect=nothing), patch.object(server.connection_checks, 'check', side_effect=nothing), \
                patch.object(self.server.app.voice_engine, 'synthesize', side_effect=nothing):
            for path, data in (('/api/web/search', {'query': 'x'}), ('/api/maps/route', {'origin': 'a', 'destination': 'b'}),
                               ('/api/connections/test', {'service': 'chat'}), ('/api/speech', {'text': 'hello'}), ('/api/transcribe', {'data': ''})):
                self.assertEqual(self.refused(path, data), (400, permissions.STOPPED_MESSAGE), path)
            # Pictures for the owner's own search results wait too (second review).
            self.assertEqual(self.refused('/api/image?url=https://upload.wikimedia.org/x.jpg')[0], 400)
        # The owner's own editing buttons still work.
        self.req('/api/item', {'kind': 'note', 'body': 'still mine'})
        self.assertEqual([n['body'] for n in self.req('/api/state')['notes']], ['still mine'])

    def test_a_page_file_that_is_named_but_missing_is_not_found(self):
        # The old Command background picture is still named in the Core's list of page files and was never shipped.
        self.assertFalse((server.ROOT / 'static' / 'assets' / 'branding' / 'teague' / 'command-background.png').exists())
        self.assertEqual(self.refused('/assets/branding/teague/command-background.png')[0], 404)

    def test_a_repair_experiment_can_be_looked_at_and_cancelled_while_stopped(self):  # finding 5
        experiment = {'operation': 'op-1', 'status': 'RUNNING', 'cancel': threading.Event()}
        self.server.app.repair_experiment = experiment
        self.req('/api/emergency-stop', {})
        status = self.req('/api/repair-experiment', {'action': 'status', 'operation': 'op-1'})
        self.assertEqual((status['status'], status['cancel_requested']), ('RUNNING', True))
        self.assertTrue(self.req('/api/repair-experiment', {'action': 'cancel', 'operation': 'op-1'})['cancel_requested'])
        run = {'action': 'run', 'operation': 'op-2', 'project': 'p', 'task': 't', 'confirmation': 'c'}
        self.assertEqual(self.refused('/api/repair-experiment', run)[1], permissions.STOPPED_MESSAGE)


class StoreTests(unittest.TestCase):
    def test_a_column_that_cannot_be_added_is_an_error_not_silence(self):  # finding 11
        with tempfile.TemporaryDirectory() as folder:
            db = sqlite3.connect(os.path.join(folder, 'jarvis.sqlite3'))
            # An activity "table" that no column can be added to.
            db.execute('CREATE TABLE audit_rows (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, status TEXT NOT NULL, created REAL NOT NULL)')
            db.execute('CREATE VIEW audit AS SELECT * FROM audit_rows')
            db.commit(); db.close()
            with self.assertRaises(sqlite3.OperationalError):
                Store(folder)


class SelfChangeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root, self.data, self.config = (Path(temp.name) / name for name in ('app', 'data', 'config'))
        for folder in (self.root, self.data, self.config):
            folder.mkdir()
        (self.root / 'personality.txt').write_text('Shipped.', encoding='utf-8')

    def test_a_proposed_style_cannot_touch_the_stop_or_the_approval_controls(self):  # finding 10
        where = development.layout(self.root, self.data, self.config, True)
        for css in ('.es-banner{display:none}', '#emergencyStop { opacity: 0 }', '.approval button{display:none}',
                    '[role = "alert"]{display:none}', '.perm-row select{pointer-events:none}',
                    '.action-review{display:none}', '.reliability-panel button{visibility:hidden}',
                    'b' + chr(92) + 'utton{display:none}', '.es' + chr(92) + '2d banner{display:none}'):
            with self.assertRaises(ValueError, msg=css):
                development.prepare(where, 'owner-style.css', css, 'test')
        self.assertTrue(development.prepare(where, 'owner-style.css', 'body{font-size:18px}', 'bigger text')['requires_approval'])

    def test_a_proposed_style_sets_only_how_things_look(self):  # second review, M2
        # Colours, fonts, text size, spacing, borders and shadows, in plain rules. Nothing that hides, moves,
        # covers or relabels by the usual means. It limits a style change; the owner still sees the difference.
        where = development.layout(self.root, self.data, self.config, True)
        refused = (
            '[class^="es"]{transform:scale(0)}', '[id^="emergency"]{position:fixed;left:-200vw}',
            '[role\t=\t"alert"]{display:none}', '[role^=alert]{visibility:hidden}', 'div[role]{opacity:0}',
            '.topbar>button:last-child{font-size:0}', '.topbar>button::after{content:"HELP"}', 'button:after{color:red}',
            '.permissions-panel{display:none}', '.message div>button{display:none}', '[class*="pproval"]{display:none}',
            'body::after{content:"";position:fixed;inset:0;z-index:2147483647;background:#000}',
            'body{width:0}', 'body{height:1px;overflow:hidden}', 'main{clip-path:circle(0)}', 'main{filter:opacity(0)}',
            '.topbar{padding-bottom:300vh}', 'button{margin-left:-900px}', 'button{margin:0 -4px}', 'p{padding:999px}',
            'p{font-size:0.01em}', 'p{font-size:1px}', 'p{font-size:var(--tiny)}', 'p{font-size:calc(1px - 1px)}',
            'p{color:transparent}', 'p{color:#ffffff00}', 'p{color:rgba(0,0,0,0)}', 'p{color:rgb(0 0 0 / 0%)}',
            '@media (min-width:1px){p{color:red}}', '@font-face{font-family:x}', 'p{color:red} /* unfinished',
            # found by the review of this check: numbers written to slip past it, units it did not know,
            # a colour hidden in a variable, the program's own layout variables, names reached by attribute
            'p{font-size:1e-9px}', 'p{font-size:1q}', 'p{font-size:1mm}', '*{font-size:.5em}', 'p{font-size:50%}', 'p{line-height:0}',
            'p{line-height:9999}', 'p{padding:9e9px}', 'p{margin:999pc}', 'p{padding:500dvh}', 'p{margin:300vi}', 'p{margin-left:400%}',
            ':root{--x:transparent}', 'p{color:var(--x)}', 'p{color:rgba(0,0,0,0e0)}', ':root{--cd-side:0px}', ':root{--dock-width:0 !important}',
            '[class^="es"]{color:red}', '[class*="pproval"]{color:red}', '[class^="perm"]{color:red}', '[id^="emergency"]{color:red}',
            '[role\n=alert]{color:red}', '[role/**/=alert]{color:red}', '.devices-panel{color:#000}', 'button.device-revoke{color:#000}',
            'p{letter-spacing:-300px}', 'p{letter-spacing:3em}', 'p{margin:5}', 'p{border-width:-1px}', 'p{color:red;transform:none}',
            'p{color:red !important !important}', 'p{color}', 'p{background:element(#x)}', 'color:red', 'p{color:red}}',
        )
        for css in refused:
            with self.assertRaises(ValueError, msg=css):
                development.prepare(where, 'owner-style.css', css, 'test')
        accepted = ('body{font-size:18px}', 'body { font-size: 1.2rem; line-height: 150% }', '/* bigger text */\n.message p{font-size:17px;color:#e8f4ff!important}',
                    # harmless things the first version of the check refused by mistake
                    'button{border-radius:999px}', 'p{box-shadow:-2px -2px 4px #000;letter-spacing:-0.5px}', 'div{background:linear-gradient(-45deg,#123,#456)}',
                    'p{border-top-color:#fff;border-top-left-radius:4px;border-bottom-width:2px}', '/* the approval of colours */ p{color:#fff}',
                    'p{line-height:1.5;margin:0 auto 1.5em;padding:4px 8px 4px 8px}', ':root{--ti-amber:rgb(255, 179, 71)}', 'h1{font-size:2rem;font-weight:700}',
                    ':root{--ti-amber:#ffb347}', '.nav{letter-spacing:.08em;padding:6px 12px;border-radius:8px}',
                    'button:hover{background:linear-gradient(180deg,#123,#456);box-shadow:0 0 8px rgba(0,0,0,.5)}',
                    'h2{color:hsl(200, 50%, 80%);font-family:"Segoe UI",sans-serif;font-weight:600}',
                    'p{color:rgba(255,255,255,0.9);margin:0 0 12px}', 'a{color:#fff0f0}', 'p{font-size:larger}',
                    'p{color:rgb(255, 200, 0)}', 'p{color:rgb(10 20 0)}', 'p{color:hsl(0, 0%, 0%)}', 'p{color:#aabb00}',
                    'p{color:rgba(0,0,0,0.5)}', 'p{color:rgb(0 0 0 / 50%)}')
        for css in accepted:
            with self.subTest(css=css):
                self.assertTrue(development.prepare(where, 'owner-style.css', css, 'test')['requires_approval'])
        # The program's own style file (changed only when JARVIS runs from the source folder) keeps its older checks.
        source = development.layout(self.root, self.data, self.root, False)
        (self.root / 'static').mkdir()
        (self.root / 'static' / 'pro.css').write_text('p{display:block}', encoding='utf-8')
        self.assertTrue(development.prepare(source, 'static/pro.css', 'p{display:flex;position:relative}', 'test')['requires_approval'])

    def test_undo_always_works_also_back_to_a_sheet_todays_rules_would_refuse(self):  # review of item 4, L6
        where = development.layout(self.root, self.data, self.config, True)
        by_hand = 'p{display:block;font-size:1.1em}'  # the owner's own hand-written sheet: not something JARVIS may propose
        (self.config / 'owner-style.css').write_text(by_hand, encoding='utf-8')
        with self.assertRaises(ValueError):
            development.prepare(where, 'owner-style.css', by_hand + ' a{color:#fff}', 'test')
        change = development.prepare(where, 'owner-style.css', 'p{font-size:18px}', 'bigger text')
        development.apply(where, change['proposal'])
        self.assertTrue(next(row for row in development.history(where)['changes'] if row['proposal'] == change['proposal'])['can_undo'])
        undo = development.rollback(where, change['proposal'])
        self.assertTrue(undo['requires_approval'])
        development.apply(where, undo['proposal'])
        self.assertEqual((self.config / 'owner-style.css').read_text(encoding='utf-8'), by_hand)

    def test_undoing_back_to_an_earlier_releases_wording_says_what_will_apply(self):  # second review, L3
        where = development.layout(self.root, self.data, self.config, True)
        copy = self.config / 'personality.txt'
        hashes = frozenset({runtime_paths.personality_hash('Old.'), runtime_paths.personality_hash('New.')})
        with patch.object(runtime_paths, 'SHIPPED_PERSONALITIES', hashes):
            (self.root / 'personality.txt').write_text('Old.', encoding='utf-8')         # the release that was installed
            mine = development.prepare(where, 'personality.txt', 'Mine.', 'my own wording')
            development.apply(where, mine['proposal'])
            self.assertEqual(copy.read_text(encoding='utf-8'), 'Mine.')
            (self.root / 'personality.txt').write_text('New.', encoding='utf-8')         # an update
            self.assertEqual(development.read(where, 'personality.txt'), 'Mine.')        # the owner's wording stays
            undo = development.rollback(where, mine['proposal'])
            self.assertIn('wording of an earlier release', undo['validation'])
            self.assertIn('personality of the release that is running applies', undo['validation'])
            development.apply(where, undo['proposal'])
            self.assertFalse(copy.exists())                                              # no copy of the old text is kept
            self.assertEqual(development.read(where, 'personality.txt'), 'New.')
            # Back to exactly the running release's text says nothing extra.
            again = development.prepare(where, 'personality.txt', 'Mine again.', 'test')
            development.apply(where, again['proposal'])
            back = development.rollback(where, again['proposal'])
            self.assertNotIn('earlier release', back['validation'])

    def test_installed_with_the_config_folder_in_the_program_folder_nothing_is_written_there(self):  # finding 12
        where = development.layout(self.root, self.data, self.root, True)
        for path, content in (('personality.txt', 'New personality.'), ('owner-style.css', 'body{font-size:18px}')):
            result = development.prepare(where, path, content, 'test')
            self.assertEqual((result['requires_approval'], result['status']), (False, development.PROPOSAL_ONLY), path)
            with self.assertRaises(ValueError):
                development.apply(where, result['proposal'])
        self.assertEqual((self.root / 'personality.txt').read_text(encoding='utf-8'), 'Shipped.')
        self.assertFalse((self.root / 'owner-style.css').exists())
        # The usual installed layout (config beside the program) still applies the owner's files after approval.
        usual = development.layout(self.root, self.data, self.config, True)
        self.assertTrue(development.prepare(usual, 'personality.txt', 'New personality.', 'test')['requires_approval'])

    def test_an_untouched_copy_of_an_earlier_releases_personality_gives_way_to_the_running_release(self):  # finding 14
        where = development.layout(self.root, self.data, self.config, True)
        copy = self.config / 'personality.txt'
        with patch.object(runtime_paths, 'SHIPPED_PERSONALITIES', frozenset({runtime_paths.personality_hash('Old shipped text.')})):
            copy.write_bytes(b'Old shipped text.\r\n')  # what the installer copied at the first install
            self.assertEqual(runtime_paths.personality_file_for(self.root, self.config), self.root / 'personality.txt')
            self.assertEqual(development.read(where, 'personality.txt'), 'Shipped.')
            copy.write_text('Old shipped text. And a sentence of my own.', encoding='utf-8')  # the owner's own wording stays
            self.assertEqual(runtime_paths.personality_file_for(self.root, self.config), copy)
            self.assertEqual(development.read(where, 'personality.txt'), 'Old shipped text. And a sentence of my own.')
            copy.unlink()
            self.assertEqual(runtime_paths.personality_file_for(self.root, self.config), self.root / 'personality.txt')

    def test_every_personality_a_release_shipped_is_on_the_list(self):
        # Add the new hash to runtime_paths.SHIPPED_PERSONALITIES whenever personality.txt changes; never remove one.
        shipped = (runtime_paths.ROOT / 'personality.txt').read_text(encoding='utf-8')
        self.assertIn(runtime_paths.personality_hash(shipped), runtime_paths.SHIPPED_PERSONALITIES)
        self.assertIn('3edf45e42879411a65161564c11d6d7b08ad57f8c772ad311378ce2ab293f5d5', runtime_paths.SHIPPED_PERSONALITIES)  # 1.0.7 to 1.0.14


class PhoneBridgeTests(unittest.TestCase):
    def test_the_phone_bridge_obeys_the_stop_and_names_the_device(self):  # finding 13
        with tempfile.TemporaryDirectory() as folder:
            bridge = Bridge(folder)
            ident, token = bridge.pair('Phone')
            bridge.create(token, {'title': 'Buy milk', 'request_id': 'r' * 16})
            row = Store(folder).logs()[0]
            self.assertEqual((row['action'], row['device']), ('phone.task.create', 'phone-' + ident[:12]))
            Store(folder).set_stop({'since': time.time(), 'device': 'pc', 'reason': 'test'})
            with self.assertRaises(Stopped):
                bridge.create(token, {'title': 'Buy bread', 'request_id': 's' * 16})
            with self.assertRaises(Stopped):
                bridge.tasks(token)
            Store(folder).set_stop(None)
            self.assertEqual([t['body'] for t in bridge.tasks(token)['tasks']], ['Buy milk'])


if __name__ == '__main__':
    unittest.main()
