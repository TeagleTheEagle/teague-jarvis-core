"""docs/ASI_ROADMAP.md, Phase 1 item 2: every tool failure goes back to the AI model as a plain error it can act on.
A tool failing in a way it did not foresee no longer ends the whole answer with "The request failed internally": the
model reads the error's kind in plain words (never the exception's own text, which would go to the AI provider), worded
by whether the tool only reads (try another way) or changes something (it may have taken effect: do not repeat it); the
answer goes on; the failure is still marked in the run and in the activity log with its kind, so no success is claimed.
A tool's own refusals keep their sentences. A stop during the failure still ends the question; the Stage 4 test harness
keeps its own failures; a mission's model reads the same words."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import actions
import providers
import server
import stage4_sessions
import system_diagnostics
from store import Store
from test_permissions import DONE, AppCase, calls
from test_workshop import FakeRun, text, tool_call
from workshop import Desk

INTERNAL = 'C:\\Users\\someone\\private-folder\\jarvis.sqlite3 is locked'   # what must never reach the model
READ_ERROR = server.UNEXPECTED_READ_ERROR.format(name='system_diagnostics', kind='KeyError')


def says(content):
    return {'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]}


class ToolErrorTests(AppCase):
    def told(self, body):
        """What the model read back for its tool call."""
        return json.loads(body['messages'][-1]['content'])

    def test_an_unexpected_failure_is_told_to_the_model_and_the_answer_goes_on(self):
        with patch.object(system_diagnostics, 'reading', side_effect=KeyError(INTERNAL)):
            run, events = self.ask('how is my PC doing?', [calls('system_diagnostics'), DONE])
        self.assertEqual(self.told(self.bodies[1]), {'error': READ_ERROR})
        self.assertNotIn('private-folder', json.dumps(self.bodies))          # the exception's text never leaves the PC
        self.assertIn('run.completed', events)
        self.assertNotIn('run.failed', events)
        self.assertEqual(events['assistant.completed']['text'], 'Done.')
        # Still marked as failed where the owner looks: the run's events, and the activity log with the error's kind.
        self.assertEqual(events['tool.failed']['error_code'], 'KeyError')
        self.assertIn('failed: KeyError', [row['status'] for row in self.rows('system_diagnostics')])

    def test_a_tools_own_failure_keeps_its_sentence_and_its_plain_log_status(self):
        with patch.object(system_diagnostics, 'reading', side_effect=ValueError(system_diagnostics.UNAVAILABLE)):
            run, events = self.ask('how is my PC doing?', [calls('system_diagnostics'), DONE])
        self.assertEqual(self.told(self.bodies[1]), {'error': system_diagnostics.UNAVAILABLE})
        self.assertIn('run.completed', events)
        self.assertIn('failed', [row['status'] for row in self.rows('system_diagnostics')])

    def test_the_model_can_try_another_way_after_a_read_fails(self):
        replies = [calls('system_diagnostics'), calls('computer_system_info'), DONE]
        with patch.object(system_diagnostics, 'reading', side_effect=OSError(INTERNAL)), \
                patch('computer_tools.system_info', return_value={'cpu': [{'Name': 'Test CPU'}]}):
            run, events = self.ask('how is my PC doing?', replies)
        self.assertEqual(self.told(self.bodies[1])['error'], server.UNEXPECTED_READ_ERROR.format(name='system_diagnostics', kind='OSError'))
        self.assertEqual(self.told(self.bodies[2]), {'cpu': [{'Name': 'Test CPU'}]})
        self.assertNotIn('private-folder', json.dumps(self.bodies))
        self.assertEqual(events['tool.completed']['name'], 'computer_system_info')
        self.assertIn('run.completed', events)

    def test_a_changing_tool_that_fails_is_not_to_be_repeated_and_no_success_is_claimed(self):
        replies = [calls('create_file', title='Notes', content='Exact text', format='txt'), says("I've created the file.")]
        with patch('actions.create_document', side_effect=OSError(INTERNAL)):
            run, events = self.ask('make a file called Notes', replies)
        told = self.told(self.bodies[1])['error']
        self.assertEqual(told, server.UNEXPECTED_CHANGE_ERROR.format(name='create_file', kind='OSError'))
        self.assertIn('do not repeat it', told)
        # The model's claim gets the receipt under it: the file is not reported as made.
        self.assertIn('create file: failed', events['assistant.completed']['text'])

    def test_a_failure_before_the_tool_started_is_still_marked(self):
        # The permission check itself failing (here, reading this tool's switch) happens before App.tool's own record.
        with patch.object(self.app, 'tool_mode', side_effect=RuntimeError(INTERNAL)):
            run, events = self.ask('how is my PC doing?', [calls('system_diagnostics'), DONE])
        self.assertEqual(self.told(self.bodies[1]), {'error': READ_ERROR.replace('KeyError', 'RuntimeError')})
        self.assertEqual((events['tool.failed']['error_code'], events['tool.failed']['stage']), ('RuntimeError', 'before start'))
        self.assertIn('failed: RuntimeError', [row['status'] for row in self.rows('system_diagnostics')])
        self.assertIn('run.completed', events)

    def test_a_stop_during_the_failure_still_ends_the_question(self):
        def crash_while_stopping(*args, **kwargs):
            for run in self.app.runs.values():
                run.cancel.set()
            raise KeyError(INTERNAL)
        with patch.object(system_diagnostics, 'reading', side_effect=crash_while_stopping):
            run, events = self.ask('how is my PC doing?', [calls('system_diagnostics'), DONE])
        self.assertEqual(len(self.bodies), 1)          # the model was not asked again
        self.assertIn('run.cancelled', events)
        self.assertNotIn('run.completed', events)

    def test_the_stage4_harness_keeps_its_own_failures(self):
        class Harness:
            failed = 0

            def fail_response(self, run):
                Harness.failed += 1
        (self.app.store.root / 'personality.txt').write_text('Stage 4 fixture.', encoding='utf-8')
        self.app.stage4 = Harness()
        with patch.object(self.app, 'tool', side_effect=stage4_sessions.Denied('ADMISSION_CLOSED')):
            run, events = self.ask('check one thing for me please', [calls('time_now'), DONE])
        self.assertEqual((Harness.failed, len(self.bodies)), (1, 1))
        self.assertNotIn('run.completed', events)

    def test_the_words_for_each_kind_of_failure(self):
        self.assertEqual(server.tool_error_text('save_item', ValueError('Say "remember" to save.')), 'Say "remember" to save.')
        self.assertEqual(server.tool_error_text('web_search', providers.ProviderError('Search is down.')), 'Search is down.')
        self.assertEqual(server.tool_error_text('time_now', KeyError(INTERNAL)), server.UNEXPECTED_READ_ERROR.format(name='time_now', kind='KeyError'))
        self.assertEqual(server.tool_error_text('save_item', KeyError(INTERNAL)), server.UNEXPECTED_CHANGE_ERROR.format(name='save_item', kind='KeyError'))
        self.assertEqual(server.tool_error_text('no_such_tool', KeyError(INTERNAL)), server.UNEXPECTED_CHANGE_ERROR.format(name='no_such_tool', kind='KeyError'))
        self.assertEqual((server.failure_status(ValueError('x')), server.failure_status(TypeError('x'))), ('failed', 'failed: TypeError'))
        self.assertIs(self.app.workshop.tool_error, server.tool_error_text)   # the Core wires the same words into missions


class MissionToolErrorTests(unittest.TestCase):
    def mission(self, wire):
        """A mission whose one tool call fails unexpectedly; returns what its model read back."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        desk = Desk(Store(folder.name), Path(folder.name) / 'workshop', settings=lambda: {'workshop_minutes': 5})
        replies = [text('{"steps": ["Read the PC", "Report"]}'), tool_call('computer_system_info'),
                   tool_call('workshop_mission', action='finish', outcome='failed', text='The reading failed.')]
        seen = []

        def ask_model(messages, tools, cancel, words):
            seen.append([dict(m) for m in messages])
            return replies.pop(0) if replies else None

        def crash(name, args, run):
            raise KeyError(INTERNAL)
        extra = {'tool_error': server.tool_error_text} if wire else {}
        desk.connect(ask_model=ask_model, call_tool=crash, instructions=lambda: 'S', make_run=FakeRun, notify=lambda *a: None,
                     audit=lambda *a, **k: None, offered=lambda: list(actions.TOOLS), **extra)
        desk.start_mission('Read this PC and report.')
        self.assertTrue(desk.current.finished.wait(30), 'the mission did not end')
        return json.loads(seen[2][-1]['content'])

    def test_a_missions_model_reads_the_same_plain_words(self):
        self.assertEqual(self.mission(wire=True), {'error': server.UNEXPECTED_READ_ERROR.format(name='computer_system_info', kind='KeyError')})

    def test_an_unwired_desk_keeps_its_old_words(self):
        self.assertEqual(self.mission(wire=False), {'error': repr(INTERNAL)})   # str(KeyError(x)) is repr(x)


if __name__ == '__main__':
    unittest.main()
