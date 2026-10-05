"""Replies that appear while they are written (release 1.0.15, scope item 8; docs/REPLY-STREAM.md): the answer
asked for in pieces (Qwen), and the Core showing as a draft only what its claim checks have passed.
No provider is contacted: the connection is a stand-in that plays back what a provider would send.
"""
import http.client
import io
import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
from unittest.mock import patch

import providers
from server import App, Run

QWEN = {'JARVIS_PROVIDER': 'qwen', 'DASHSCOPE_API_KEY': 'qwen-test-key'}
ANSWER = 'A transistor is a semiconductor switch. It amplifies or switches signals. Billions sit in one chip.'


def event(delta=None, finish=None, **more):
    """One server-sent event as an OpenAI-compatible provider sends it."""
    return ('data: ' + json.dumps({'choices': [{'index': 0, 'delta': delta or {}, 'finish_reason': finish}], **more}) + '\n\n').encode()


def written(text, size=9, finish='stop'):
    """An answer sent in pieces of `size` characters, then the finish mark and [DONE]."""
    lines = [event({'role': 'assistant', 'content': ''})]
    lines += [event({'content': text[at:at + size]}) for at in range(0, len(text), size)]
    return lines + [event({}, finish), b'data: [DONE]\n\n']


class Connection:
    """Stands in for the provider's open connection: plays back lines (streamed) or one whole body."""

    def __init__(self, lines=None, body=None):
        self.lines = [part for line in (lines or []) for part in (line.splitlines(keepends=True) if isinstance(line, bytes) else [line])]
        self.body = body

    def readline(self, *_):
        if not self.lines:
            return b''
        item = self.lines.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def read(self, *_):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class Silent(Connection):
    """A provider that sends some lines and then nothing more. Shutting its socket down ends the wait, as with a real one."""

    def __init__(self, lines):
        super().__init__(lines)
        self.woken = threading.Event()
        sock = type('Socket', (), {'shutdown': lambda _, how: self.woken.set()})()
        self.fp = type('File', (), {'raw': type('Raw', (), {'_sock': sock})()})()

    def readline(self, *_):
        if self.lines:
            return Connection.readline(self)
        self.woken.wait(20)
        return b''


class Provider:
    """What urllib.request.urlopen is replaced with: hands out the prepared connections in order and keeps the requests."""

    def __init__(self, *answers):
        self.answers, self.requests = list(answers), []

    def __call__(self, request, timeout=None):
        self.requests.append(json.loads(request.data))
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer if isinstance(answer, Connection) else Connection(answer)


def whole(content=None, tool=None):
    """A complete answer the old way (one piece)."""
    message = {'content': content}
    if tool:
        message['tool_calls'] = [{'id': 'c1', 'type': 'function', 'function': {'name': tool, 'arguments': '{}'}}]
    return Connection(body=json.dumps({'choices': [{'finish_reason': 'tool_calls' if tool else 'stop', 'message': message}]}).encode())


class ProviderTests(unittest.TestCase):
    def ask(self, *answers, stream=True, tools=(), cancel=None):
        provider, emitted = Provider(*answers), []
        with patch.dict(os.environ, QWEN, clear=True), patch('urllib.request.urlopen', provider):
            reply = providers.chat([{'role': 'user', 'content': 'hello'}], list(tools), lambda name, data: emitted.append((name, data)), cancel or threading.Event(), stream=stream)
        return reply, emitted, provider.requests

    def test_the_answer_arrives_in_pieces_and_is_the_same_answer(self):
        reply, emitted, requests = self.ask(written(ANSWER))
        self.assertEqual(reply, {'role': 'assistant', 'content': ANSWER})
        pieces = [data['text'] for name, data in emitted if name == 'assistant.piece']
        self.assertEqual(''.join(pieces), ANSWER)
        self.assertGreater(len(pieces), 5)
        self.assertEqual(emitted[-1], ('assistant.delta', {'text': ANSWER}))  # the finished answer, as before
        # The request is the usual one with "stream": true and nothing else changed.
        _, _, usual = self.ask(whole(ANSWER), stream=False)
        self.assertEqual({**usual[0], 'stream': True}, requests[0])
        self.assertIs(usual[0]['stream'], False)

    def test_a_models_thinking_is_not_part_of_the_answer(self):
        lines = [event({'reasoning_content': 'Let me think about transistors.'}), event({'reasoning_content': ' Two sentences.'})] + written('It is a switch.')
        reply, emitted, _ = self.ask(lines)
        self.assertEqual(reply['content'], 'It is a switch.')
        self.assertNotIn('think', json.dumps(emitted))

    def test_a_tool_request_that_arrives_in_parts_is_put_together(self):
        lines = [event({'content': 'One moment. '}),
                 event({'tool_calls': [{'index': 0, 'id': 'call_1', 'type': 'function', 'function': {'name': 'set_timer', 'arguments': ''}}]}),
                 event({'tool_calls': [{'index': 0, 'function': {'arguments': '{"title": "Tea",'}}]}),
                 event({'tool_calls': [{'index': 0, 'function': {'arguments': ' "seconds": 300}'}}, {'index': 1, 'id': 'call_2', 'function': {'name': 'time_now', 'arguments': '{}'}}]}),
                 event({}, 'tool_calls'), b'data: [DONE]\n\n']
        reply, _, _ = self.ask(lines)
        self.assertEqual(reply['content'], 'One moment. ')
        self.assertEqual(reply['tool_calls'], [{'id': 'call_1', 'type': 'function', 'function': {'name': 'set_timer', 'arguments': '{"title": "Tea", "seconds": 300}'}},
                                               {'id': 'call_2', 'type': 'function', 'function': {'name': 'time_now', 'arguments': '{}'}}])

    def test_a_stream_that_breaks_is_an_error_and_no_partial_answer_is_accepted(self):
        half = written(ANSWER)[:4]
        for name, lines in (('the connection drops', half + [ConnectionResetError('reset')]), ('it goes quiet', half + [TimeoutError('timed out')]),
                            ('it is cut off', half + [http.client.IncompleteRead(b'da')]), ('a piece is not readable', half + [b'data: {not json\n\n']),
                            ('the provider reports an error', half + [b'data: {"error": {"message": "overloaded"}}\n\n']),
                            ('a piece is not a piece', half + [b'data: [1, 2]\n\n']),
                            ('it ends without saying it is finished', half)):
            with self.assertRaises(providers.ProviderError, msg=name) as failed:
                self.ask(lines)
            self.assertIn('stream failed', str(failed.exception).lower(), name)  # the Core then asks again in one piece
        with patch.object(providers, 'STREAM_MOST_BYTES', 300), self.assertRaisesRegex(providers.ProviderError, 'Stream failed'):
            self.ask(written(ANSWER * 5))  # it grows past what a complete answer may be
        # The provider itself says the answer was cut short: the usual "not complete" error, and no second try.
        with self.assertRaisesRegex(providers.ProviderError, 'did not return a complete response'):
            self.ask(written(ANSWER, finish='length'))

    def test_stop_takes_effect_between_pieces(self):
        cancel = threading.Event()
        lines = written(ANSWER)

        class Stopping(Connection):
            def readline(inner, *_):
                line = Connection.readline(inner)
                if len(inner.lines) == 6:
                    cancel.set()  # the owner presses Stop while the answer is arriving
                return line

        reply, emitted, _ = self.ask(Stopping(lines), cancel=cancel)
        self.assertIsNone(reply)
        self.assertNotIn('assistant.delta', [name for name, _ in emitted])

    def test_stop_ends_the_wait_for_a_provider_that_has_gone_silent(self):
        """Review finding 4: Stop was only looked at between lines, so a silent stream held it for up to a minute."""
        cancel = threading.Event()
        threading.Timer(0.3, cancel.set).start()
        started = time.monotonic()
        reply, emitted, _ = self.ask(Silent(written(ANSWER)[:5]), cancel=cancel)
        self.assertIsNone(reply)
        self.assertLess(time.monotonic() - started, 3)
        self.assertNotIn('assistant.delta', [name for name, _ in emitted])

    def test_an_answer_still_arriving_when_the_time_is_up_ends_as_timed_out_not_as_a_broken_stream(self):
        """Review finding 3: asking again in one piece after the full time could not succeed either."""
        class Writing(Connection):
            def readline(inner, *_):
                time.sleep(0.01)
                return Connection.readline(inner)

        for connection in (Silent(written(ANSWER)[:5]),                                 # it went silent
                           Writing([event({'content': 'word '}) for _ in range(400)])):  # it kept writing
            started = time.monotonic()
            with patch.object(providers, 'STREAM_TOTAL_SECONDS', 0.3), self.assertRaises(providers.ProviderError) as failed:
                self.ask(connection)
            self.assertLess(time.monotonic() - started, 5)
            self.assertIn('Connection timed out', str(failed.exception))
            self.assertNotIn('stream failed', str(failed.exception).lower())
            self.assertTrue(failed.exception.unreachable)

    def test_tool_request_parts_that_cannot_be_put_in_order_are_a_broken_stream(self):
        """Review finding 5: mixed kinds of index raised a TypeError outside the reader's own handling."""
        for first, second in ((None, 1), ('0', 1), (True, 0), (1.5, 0)):
            lines = [event({'tool_calls': [{'index': first, 'id': 'a', 'function': {'name': 'time_now', 'arguments': '{}'}}]}),
                     event({'tool_calls': [{'index': second, 'id': 'b', 'function': {'name': 'time_now', 'arguments': '{}'}}]}), event({}, 'tool_calls'), b'data: [DONE]\n\n']
            with self.assertRaisesRegex(providers.ProviderError, 'Stream failed', msg=str((first, second))):
                self.ask(lines)
        deep = b'data: ' + b'[' * 100000 + b'\n\n'                      # nested far too deep to read
        with self.assertRaisesRegex(providers.ProviderError, 'Stream failed'):
            self.ask(written(ANSWER)[:3] + [deep])

    def test_a_refusal_or_no_connection_reads_as_it_always_did(self):
        refusal = urllib.error.HTTPError('https://dashscope-intl.aliyuncs.com/x', 401, 'Unauthorized', {}, io.BytesIO(b'{"error": {"code": "InvalidApiKey", "message": "no"}}'))
        with self.assertRaises(providers.ProviderError) as failed:
            self.ask(refusal)
        self.assertIn('Authentication failed', str(failed.exception))
        self.assertNotIn('stream failed', str(failed.exception).lower())
        with self.assertRaises(providers.ProviderError) as failed:
            self.ask(urllib.error.URLError(ConnectionRefusedError('refused')))
        self.assertTrue(failed.exception.unreachable)
        self.assertIn('Connection failed', str(failed.exception))

    def test_openai_answers_in_one_piece_as_before(self):
        provider = Provider(Connection(body=json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'content': 'Hello.'}}]}).encode()))
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'openai', 'OPENAI_API_KEY': 'k', 'OPENAI_MODEL': 'gpt-4o-mini'}, clear=True), patch('urllib.request.urlopen', provider):
            reply = providers.chat([{'role': 'user', 'content': 'hello'}], [], lambda *_: None, threading.Event(), stream=True)
        self.assertEqual(reply['content'], 'Hello.')
        self.assertIs(provider.requests[0]['stream'], False)


class CoreTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.app = App(folder.name)
        self.app.store.save_settings({'reply_stream': True})
        self.app.DRAFT_SECONDS = 0  # every complete sentence is shown, whatever the clock says

    def ask(self, text, *answers, wearable=False, env=QWEN):
        self.provider = Provider(*answers)
        run = Run('stream-test')
        run.wearable, run.device = wearable, 'local-wearable-client' if wearable else 'pc'
        self.app.runs[run.id] = run
        with patch.dict(os.environ, env, clear=True), patch('urllib.request.urlopen', self.provider):
            self.app.work(run, text, None)
        return run, [(e['event'], e['data']) for e in run.events]

    @staticmethod
    def of(events, name):
        return [data for kind, data in events if kind == name]

    def test_the_reply_appears_as_it_is_written_and_ends_as_the_checked_answer(self):
        _, events = self.ask('What is a transistor?', written(ANSWER))
        drafts = [d['text'] for d in self.of(events, 'assistant.draft')]
        self.assertEqual(drafts, ['A transistor is a semiconductor switch.', 'A transistor is a semiconductor switch. It amplifies or switches signals.'])
        self.assertEqual(self.of(events, 'assistant.delta'), [{'text': ANSWER}])
        self.assertEqual(self.of(events, 'assistant.completed')[0]['text'], ANSWER)
        kinds = [kind for kind, _ in events]
        self.assertLess(kinds.index('assistant.draft'), kinds.index('assistant.delta'))  # the drafts come first
        self.assertEqual(self.app.store.history('stream-test')[-1]['content'], ANSWER)   # only the finished answer is kept
        self.assertIs(self.provider.requests[0]['stream'], True)

    def test_a_claim_the_checks_would_change_is_never_on_screen(self):
        claimed = 'Certainly, sir. I have saved the note for you. Anything else?'
        _, events = self.ask('Please write that down somewhere.', written(claimed))
        self.assertEqual([d['text'] for d in self.of(events, 'assistant.draft')], ['Certainly, sir.'])
        final = self.of(events, 'assistant.completed')[0]['text']
        self.assertEqual(final, 'No matching action result was recorded for this request. Completion is not confirmed.')
        self.assertNotIn('saved the note', json.dumps(events))

    def test_every_draft_is_a_beginning_of_the_answer_that_the_checks_leave_unchanged(self):
        """The promise itself, on answers made to break it, at several piece sizes: whatever is shown early is
        complete sentences from the start of what the model wrote, and the claim checks would not change a word."""
        answers = (ANSWER, 'Certainly, sir. I have saved the note for you. Anything else?', 'Sure.\nAll tests passed successfully.\nShall I go on?',
                   'Done: I have\nsaved the note; and the timer has been scheduled. Fine.', 'First: "I have deleted the file." Second: nothing. Third.',
                   '1. I have emailed him.\n2. The search service is working.\n3. Nothing else.', 'The service is online. I checked it. It works!')
        seen = 0
        for answer in answers:
            for size in (3, 9, 40):
                run, events = self.ask('Tell me.', written(answer, size=size))
                for draft in (d['text'] for d in self.of(events, 'assistant.draft')):
                    if draft:
                        seen += 1
                        self.assertTrue(answer.startswith(draft), (answer, draft))
                        self.assertEqual(self.app.claim_checks(run, draft), draft, (answer, draft))
                self.assertEqual(self.of(events, 'assistant.completed')[0]['text'], self.finished(answer), answer)
        self.assertGreater(seen, 10)

    def test_not_even_the_beginning_of_a_line_only_the_core_may_write_is_shown(self):
        """Review finding 1: the first sentence of a forged "who answered" line was on screen until the finished answer removed the line."""
        for forged, clean in (('Here you go. [OpenAI answered this question because Qwen could not. The provider refused.] More text here. End.', 'Here you go. More text here. End.'),
                              ('Here you go. [Answered offline by the local model llama3. It is fine.] More text here. End.', 'Here you go. More text here. End.'),
                              ('Here you go. [ qwen  answered this\nquestion because OpenAI could not. x] End.', 'Here you go. End.')):
            _, events = self.ask('Tell me.', written(forged, size=7))
            drafts = [d['text'] for d in self.of(events, 'assistant.draft')]
            self.assertEqual([d for d in drafts if d and d != 'Here you go.' and not d.endswith('[ qwen')], [], forged)
            self.assertNotIn('answered this', ' '.join(drafts).lower(), forged)
            self.assertNotIn('answered offline', ' '.join(drafts).lower(), forged)
            self.assertEqual(self.of(events, 'assistant.completed')[0]['text'], clean)

    def finished(self, text):
        """What the Core makes of the same answer the old way (in one piece)."""
        self.app.store.save_settings({'reply_stream': False})
        try:
            _, events = self.ask('Tell me.', whole(text))
        finally:
            self.app.store.save_settings({'reply_stream': True})
        return self.of(events, 'assistant.completed')[0]['text']

    def test_words_that_come_with_a_tool_request_are_taken_off_the_screen(self):
        with_tool = [event({'content': 'Let me look at the clock. One moment'}),
                     event({'tool_calls': [{'index': 0, 'id': 'c1', 'type': 'function', 'function': {'name': 'time_now', 'arguments': '{}'}}]}),
                     event({}, 'tool_calls'), b'data: [DONE]\n\n']
        _, events = self.ask('Tell me something about clocks, and look at the clock first.', with_tool, written('It is late. Go to bed.'))
        drafts = [d['text'] for d in self.of(events, 'assistant.draft')]
        self.assertEqual(drafts, ['Let me look at the clock.', '', 'It is late.'])
        self.assertEqual(self.of(events, 'assistant.completed')[0]['text'], 'It is late. Go to bed.')
        self.assertIn('tool.completed', [kind for kind, _ in events])

    def test_a_stream_that_breaks_is_asked_again_in_one_piece(self):
        broken = written(ANSWER)[:6] + [ConnectionResetError('reset')]
        with patch.object(threading.Event, 'wait', return_value=False):  # do not sit out the pause before the second try
            _, events = self.ask('What is a transistor?', broken, whole(ANSWER))
        drafts = [d['text'] for d in self.of(events, 'assistant.draft')]
        self.assertEqual(drafts[-1], '')  # what was shown of the broken attempt is taken away
        self.assertEqual(self.of(events, 'assistant.completed')[0]['text'], ANSWER)
        self.assertEqual([request['stream'] for request in self.provider.requests], [True, False])

    def test_a_provider_that_turns_the_request_down_is_asked_the_usual_way(self):
        refused = urllib.error.HTTPError('https://dashscope-intl.aliyuncs.com/x', 400, 'Bad Request', {}, io.BytesIO(b'{"error": {"code": "InvalidParameter", "message": "stream"}}'))
        with patch.object(threading.Event, 'wait', return_value=False):
            _, events = self.ask('What is a transistor?', refused, whole(ANSWER))
        self.assertEqual(self.of(events, 'assistant.completed')[0]['text'], ANSWER)
        self.assertEqual([request['stream'] for request in self.provider.requests], [True, False])
        # A refusal that has nothing to do with pieces (a wrong key) is not asked twice.
        wrong_key = urllib.error.HTTPError('https://dashscope-intl.aliyuncs.com/x', 401, 'Unauthorized', {}, io.BytesIO(b'{}'))
        _, events = self.ask('What is a transistor?', wrong_key)
        self.assertEqual(len(self.provider.requests), 1)
        self.assertIn('Authentication failed', self.of(events, 'run.failed')[0]['message'])

    def test_an_unpaid_bill_is_not_asked_twice(self):
        """Review finding 2: every HTTP 400 was asked again, also Alibaba's "account overdue" (which is a 400)."""
        overdue = urllib.error.HTTPError('https://dashscope-intl.aliyuncs.com/x', 400, 'Bad Request', {}, io.BytesIO(b'{"error":{"code":"Arrearage","message":"UPSTREAM-DETAIL-NOT-SHOWN"}}'))
        _, events = self.ask('What is a transistor?', overdue)
        self.assertEqual([request['stream'] for request in self.provider.requests], [True])
        self.assertIn('overdue', self.of(events, 'run.failed')[0]['message'])

    def test_time_that_is_up_is_not_followed_by_a_second_attempt(self):
        """Review finding 3, in the Core: after the full time the question fails as it does without the setting."""
        self.app.store.save_settings({'offline_answers': False})
        with patch.object(providers, 'STREAM_TOTAL_SECONDS', 0.3):
            _, events = self.ask('What is a transistor?', Silent(written(ANSWER)[:8]))
        self.assertEqual([request['stream'] for request in self.provider.requests], [True])
        self.assertIn('Connection timed out', self.of(events, 'run.failed')[0]['message'])
        self.assertEqual([d['text'] for d in self.of(events, 'assistant.draft')][-1], '')  # what was shown is taken away

    def test_a_tool_runs_once_when_the_stream_breaks_after_it(self):
        with_tool = [event({'tool_calls': [{'index': 0, 'id': 'c1', 'type': 'function', 'function': {'name': 'time_now', 'arguments': '{}'}}]}), event({}, 'tool_calls'), b'data: [DONE]\n\n']
        broken = written('It is late. Go to bed.')[:3] + [ConnectionResetError('reset')]
        with patch.object(threading.Event, 'wait', return_value=False):
            _, events = self.ask('Tell me something about clocks, and look at the clock first.', with_tool, broken, whole('It is late. Go to bed.'))
        self.assertEqual([kind for kind, _ in events].count('tool.completed'), 1)
        self.assertEqual(self.of(events, 'assistant.completed')[0]['text'], 'It is late. Go to bed.')
        self.assertEqual([request['stream'] for request in self.provider.requests], [True, True, False])

    def test_a_broken_stream_then_no_connection_then_the_backup_provider(self):
        self.app.store.save_settings({'provider_backup': True})
        broken = written(ANSWER)[:6] + [ConnectionResetError('reset')]
        gone = urllib.error.URLError(ConnectionRefusedError('refused'))
        with patch.object(threading.Event, 'wait', return_value=False):
            _, events = self.ask('What is a transistor?', broken, gone, whole('From the backup.'), env={**QWEN, 'OPENAI_API_KEY': 'openai-test-key', 'OPENAI_MODEL': 'gpt-4o-mini'})
        final = self.of(events, 'assistant.completed')[0]['text']
        self.assertTrue(final.startswith('From the backup.\n\n[OpenAI answered this question because Qwen could not.'), final)
        self.assertEqual([d['text'] for d in self.of(events, 'assistant.draft')][-1], '')
        self.assertEqual([request['stream'] for request in self.provider.requests], [True, False, False])

    def test_stop_takes_the_unfinished_reply_off_the_screen(self):
        run = Run('stream-test')
        run.wearable, run.device = False, 'pc'

        class Stopping(Connection):
            def readline(inner, *_):
                if len(inner.lines) == 2:
                    run.cancel.set()  # the owner presses Stop while the answer is arriving
                return Connection.readline(inner)

        self.app.runs[run.id] = run
        with patch.dict(os.environ, QWEN, clear=True), patch('urllib.request.urlopen', Provider(Stopping(written(ANSWER)))):
            self.app.work(run, 'What is a transistor?', None)
        events = [(e['event'], e['data']) for e in run.events]
        drafts = [d['text'] for d in self.of(events, 'assistant.draft')]
        self.assertTrue(drafts[0].startswith('A transistor'))
        self.assertEqual(drafts[-1], '')
        self.assertEqual(self.of(events, 'assistant.completed'), [])
        self.assertIn('run.cancelled', [kind for kind, _ in events])
        self.assertNotEqual(self.app.store.history('stream-test')[-1]['role'], 'assistant')  # nothing of it is kept

    def test_off_by_default_and_then_the_request_is_exactly_the_old_one(self):
        with tempfile.TemporaryDirectory() as fresh:
            self.assertIs(App(fresh).store.settings()['reply_stream'], False)
        self.app.store.save_settings({'reply_stream': False})
        _, events = self.ask('What is a transistor?', whole(ANSWER))
        self.assertEqual(self.of(events, 'assistant.draft'), [])
        self.assertIs(self.provider.requests[0]['stream'], False)
        self.assertEqual(self.of(events, 'assistant.completed')[0]['text'], ANSWER)

    def test_another_devices_question_is_answered_in_one_piece(self):
        _, events = self.ask('What is a transistor?', whole(ANSWER), wearable=True)
        self.assertEqual(self.of(events, 'assistant.draft'), [])
        self.assertIs(self.provider.requests[0]['stream'], False)


if __name__ == '__main__':
    unittest.main()
