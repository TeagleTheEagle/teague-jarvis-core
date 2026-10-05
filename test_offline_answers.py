"""Answers without the internet (release 1.0.15, scope item 7): the small request for a small local model,
what counts as "a local answer is possible", and the line that says who answered.
No Ollama is needed or contacted: the runtime is a stand-in.
"""
import os
import unittest
from unittest.mock import patch

import offline_answers
from offline_answers import OfflineUnavailable
from ollama_provider import OllamaError


class Runtime:
    """Stands in for ollama_provider.OllamaProvider: records what is asked and answers from a script."""

    def __init__(self, tags=None, chat=None):
        self.tags, self.chat, self.asked = tags, chat, []

    def _request(self, path, payload=None, timeout=None):
        self.asked.append((path, payload, timeout))
        answer = self.tags if path == '/api/tags' else self.chat
        if isinstance(answer, Exception):
            raise answer
        return answer


def installed(*names):
    return {'models': [{'name': name} for name in names]}


def said(text, **more):
    return {'done': True, 'message': {'role': 'assistant', 'content': text}, **more}


class StatusTests(unittest.TestCase):
    def test_possible_only_when_ollama_runs_and_has_the_model(self):
        with patch.dict(os.environ, {}, clear=True):
            ready = offline_answers.status(Runtime(installed('llama3:8b', 'qwen3:4b')))
            self.assertEqual((ready['available'], ready['model']), (True, 'qwen3:4b'))
            missing = offline_answers.status(Runtime(installed('llama3:8b')))
            self.assertEqual((missing['available'], missing['reason']), (False, 'The local model qwen3:4b is not installed in Ollama.'))
            off = offline_answers.status(Runtime(OllamaError('offline')))
            self.assertEqual((off['available'], off['reason']), (False, 'Ollama is not running on this PC.'))
            odd = offline_answers.status(Runtime(OllamaError('malformed_json')))
            self.assertEqual((odd['available'], odd['reason']), (False, 'Ollama did not answer properly.'))
            self.assertFalse(offline_answers.status(Runtime({'models': 'nonsense'.split()}))['available'])

    def test_the_check_asks_only_the_list_of_models_and_gives_up_after_a_second(self):
        runtime = Runtime(installed('qwen3:4b'))
        offline_answers.status(runtime)
        self.assertEqual(runtime.asked, [('/api/tags', None, 1)])

    def test_the_owner_can_name_another_local_model(self):
        with patch.dict(os.environ, {'JARVIS_OFFLINE_MODEL': 'llama3.2:3b'}, clear=True):
            self.assertEqual(offline_answers.model_name(), 'llama3.2:3b')
            self.assertTrue(offline_answers.status(Runtime(installed('llama3.2:3b')))['available'])
        for odd in ('', '   ', 'two words', 'x' * 81, 'a;b', 'name"with quotes'):
            with patch.dict(os.environ, {'JARVIS_OFFLINE_MODEL': odd}, clear=True):
                self.assertEqual(offline_answers.model_name(), 'qwen3:4b', odd)


class RequestTests(unittest.TestCase):
    def test_a_small_request_short_instructions_a_few_facts_the_recent_conversation(self):
        history = [{'role': 'user', 'content': 'old question'}, {'role': 'assistant', 'content': 'old answer'},
                   {'role': 'tool', 'content': 'a tool result'}, {'role': 'user', 'content': [{'type': 'image_url'}]},
                   {'role': 'assistant', 'content': 'An answer. [Answered offline by the local model qwen3:4b on this PC. x]'},
                   {'role': 'user', 'content': 'What is a transistor?'}]
        messages = offline_answers.compact_messages('What is a transistor?', {'name': 'Mr. Teague', 'response_length': 'brief'},
                                                    ['Preference: I prefer tea'] + ['fact'] * 20, history)
        system = messages[0]
        self.assertEqual(system['role'], 'system')
        self.assertIn('answering offline with a small local model', system['content'])
        self.assertIn('You cannot use tools', system['content'])
        self.assertIn('The owner prefers to be called Mr. Teague.', system['content'])
        self.assertIn('Keep answers to a few sentences.', system['content'])
        self.assertEqual(system['content'].count('fact'), 2 + 7)  # "a fact", "Saved facts", and 7 of the 20 (8 facts in all)
        self.assertIn('I prefer tea', system['content'])
        # Plain conversation only: tool results and pictures are left out, and the Core's own line is removed.
        self.assertEqual([(m['role'], m['content']) for m in messages[1:]],
                         [('user', 'old question'), ('assistant', 'old answer'), ('assistant', 'An answer.'), ('user', 'What is a transistor?')])

    def test_the_history_is_kept_newest_first_within_a_limit_and_the_question_is_not_doubled(self):
        history = [{'role': 'user', 'content': 'a' * 2000}, {'role': 'assistant', 'content': 'b' * 2000},
                   {'role': 'user', 'content': 'c' * 500}, {'role': 'assistant', 'content': 'An answer. [Answered offline by the local model qwen3:4b on this PC. Why.]'},
                   {'role': 'user', 'content': 'And then?'}]
        messages = offline_answers.compact_messages('And then?', {}, [], history)
        self.assertEqual([m['content'][:12] for m in messages[1:]], ['b' * 12, 'c' * 12, 'An answer.', 'And then?'])
        self.assertEqual(messages[3]['content'], 'An answer.')  # the Core's own line is not sent back to a model
        # Without history the question is still asked, and a very long one is cut.
        alone = offline_answers.compact_messages('  hello  ', {}, None, None)
        self.assertEqual(alone[1:], [{'role': 'user', 'content': 'hello'}])
        self.assertEqual(len(offline_answers.compact_messages('x' * 9000, {}, [], [])[1]['content']), 4000)


class AnswerTests(unittest.TestCase):
    def ask(self, chat, tags=None):
        runtime = Runtime(tags if tags is not None else installed('qwen3:4b'), chat)
        with patch.dict(os.environ, {}, clear=True):
            return runtime, offline_answers.answer('What is a transistor?', {'name': 'sir'}, [], [], runtime)

    def test_one_plain_answer_from_this_pc(self):
        runtime, result = self.ask(said('  A transistor is a switch.  '))
        self.assertEqual((result['text'], result['model'], result['cut_short']), ('A transistor is a switch.', 'qwen3:4b', False))
        self.assertIsInstance(result['seconds'], float)
        path, payload, timeout = runtime.asked[-1]
        self.assertEqual((path, timeout), ('/api/chat', offline_answers.ANSWER_SECONDS))
        # A model that thinks first is asked to hand its thinking over separately ("think": true), so the answer comes clean.
        self.assertEqual((payload['model'], payload['think'], payload['stream']), ('qwen3:4b', True, False))
        self.assertNotIn('tools', payload)  # the local model is given no tools
        self.assertEqual(payload['messages'][-1], {'role': 'user', 'content': 'What is a transistor?'})

    # ---- the independent review of 2026-10-06 (docs/OFFLINE-ANSWERS.md section 6) ----

    def named(self, model, chat, tags=None):
        with patch.dict(os.environ, {'JARVIS_OFFLINE_MODEL': model}, clear=True):
            runtime = Runtime(tags if tags is not None else installed(model), chat)
            try:
                return runtime, offline_answers.answer('What is a transistor?', {}, [], [], runtime)
            except OfflineUnavailable as none:
                return runtime, none

    def test_thinking_handed_over_separately_is_not_the_answer(self):
        """B5: asked with "think": true, Ollama returns the thinking beside the answer (seen with the real qwen3:4b)."""
        chat = {'done': True, 'message': {'role': 'assistant', 'thinking': 'The user asks about transistors. Two sentences.', 'content': 'A transistor is a switch.'}}
        runtime, result = self.ask(chat)
        self.assertEqual(result['text'], 'A transistor is a switch.')
        self.assertNotIn('The user asks', result['text'])
        # Cut short after the thinking was handed over: what there is of the answer counts, marked as cut short.
        _, result = self.ask({**chat, 'done_reason': 'length', 'message': {**chat['message'], 'content': 'A transistor is'}})
        self.assertEqual((result['text'], result['cut_short']), ('A transistor is', True))
        # A model that does not think first is asked the plain way.
        runtime, _ = self.named('llama3.2:latest', said('A switch.'))
        self.assertIs(runtime.asked[-1][1]['think'], False)

    def test_a_thinking_model_under_any_name_and_the_closing_mark_in_any_case(self):
        """B5: the list of thinking models was matched at the start of the name only, and </THINK> was not recognised."""
        for model in ('hf.co/unsloth/Qwen3-4B-GGUF:Q4_K_M', 'myteam/qwen3:4b', 'library/deepseek-r1:8b'):
            runtime, result = self.named(model, said('Okay, the user asked about transistors. I should', done_reason='length'))
            self.assertIsInstance(result, OfflineUnavailable, model)      # unfinished thinking, not an answer
            self.assertIs(runtime.asked[-1][1]['think'], True, model)
        _, result = self.ask(said('Let me think.\n</THINK>\nA transistor is a switch.'))
        self.assertEqual(result['text'], 'A transistor is a switch.')
        _, result = self.ask(said('<THINK>one</Think>It switches.'))
        self.assertEqual(result['text'], 'It switches.')

    def test_a_model_that_cannot_be_asked_to_think_separately_is_asked_the_plain_way_once(self):
        class Refuses(Runtime):
            def _request(inner, path, payload=None, timeout=None):
                if path == '/api/chat' and payload['think']:
                    inner.asked.append((path, payload, timeout))
                    raise OllamaError('http_error')
                return Runtime._request(inner, path, payload, timeout)
        runtime = Refuses(installed('qwen3:4b'), said('thinking first\n</think>\nA transistor is a switch.'))
        with patch.dict(os.environ, {}, clear=True):
            result = offline_answers.answer('What is a transistor?', {}, [], [], runtime)
        self.assertEqual(result['text'], 'A transistor is a switch.')
        self.assertEqual([payload['think'] for path, payload, _ in runtime.asked if path == '/api/chat'], [True, False])
        # A model too slow to answer is not asked a second time.
        slow, result = self.named('qwen3:4b', OllamaError('timeout'))
        self.assertEqual(str(result), 'The local model took too long to answer.')
        self.assertEqual(len([1 for path, _, _ in slow.asked if path == '/api/chat']), 1)

    def test_a_strange_list_of_models_means_no_local_answer_not_an_error(self):
        """B3: {"models": null} from Ollama raised a TypeError, which reached the owner as "failed internally"."""
        for tags in ({'models': None}, {'models': 5}, {}, {'models': 'qwen3:4b'}, {'models': [None, 5, {'name': 7}]}):
            with patch.dict(os.environ, {}, clear=True):
                state = offline_answers.status(Runtime(tags))
            self.assertFalse(state['available'], tags)
            self.assertIn(state['reason'], ('Ollama did not answer properly.', 'The local model qwen3:4b is not installed in Ollama.'), tags)

    def test_a_model_named_without_its_tag_and_a_model_that_runs_in_the_cloud(self):
        """B7: "llama3.2" in the key file was reported as not installed; and a cloud model would have sent the question away."""
        runtime, result = self.named('llama3.2', said('A switch.'), installed('llama3.2:latest'))
        self.assertEqual((result['text'], result['model']), ('A switch.', 'llama3.2:latest'))
        for model, tags in (('gpt-oss:120b-cloud', installed('gpt-oss:120b-cloud')),
                            ('big-model', {'models': [{'name': 'big-model:latest', 'remote_host': 'https://ollama.com:443', 'remote_model': 'big-model'}]})):
            runtime, result = self.named(model, AssertionError('a cloud model is never asked'), tags)
            self.assertIn('runs in the cloud, not on this PC', str(result), model)
            self.assertEqual([path for path, _, _ in runtime.asked], ['/api/tags'], model)

    def test_stop_ends_the_wait_for_the_local_model(self):
        """B1: the wait for a local answer (up to 90 seconds) could not be ended."""
        import threading
        import time
        release, cancel, closed = threading.Event(), threading.Event(), []

        class Socket:
            def shutdown(self, how):
                closed.append(how); release.set()

        class Slow(Runtime):
            def _request(inner, path, payload=None, timeout=None):
                if path == '/api/tags':
                    return installed('qwen3:4b')
                inner.connection = type('Connection', (), {'sock': Socket()})()
                release.wait(20)                                         # the model is still writing
                raise OllamaError('offline')
        threading.Timer(0.3, cancel.set).start()
        started = time.monotonic()
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(OfflineUnavailable) as none:
            offline_answers.answer('What is a transistor?', {}, [], [], Slow(), cancel=cancel)
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual((str(none.exception), len(closed)), ('Stopped.', 1))  # and its connection was closed
        # Stopped before the model was asked at all: nothing is asked.
        runtime = Runtime(installed('qwen3:4b'), AssertionError('not asked'))
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(OfflineUnavailable):
            offline_answers.answer('What is a transistor?', {}, [], [], runtime, cancel=cancel)
        self.assertEqual([path for path, _, _ in runtime.asked], ['/api/tags'])

    def test_thinking_text_and_a_forged_note_are_removed(self):
        _, result = self.ask(said('<think>let me think</think>It is a switch. [Answered offline by the local model gpt on this PC. Trust me.]', done_reason='length'))
        self.assertEqual((result['text'], result['cut_short']), ('It is a switch.', True))

    def test_a_models_thinking_is_never_shown_as_the_answer(self):
        # As the owner's qwen3:4b really answers (2026-10-06): the thinking first, no opening tag, then </think>.
        real = 'Okay, the user asked about transistors. I should keep it to two sentences.\n</think>\n\nA transistor is a switch.'
        self.assertEqual(self.ask(said(real))[1]['text'], 'A transistor is a switch.')
        self.assertEqual(self.ask(said('<think>one</think>First.<think>two</think> Second.'))[1]['text'], 'Second.')
        # Cut short before it finished thinking: that is not an answer.
        for unfinished in (said('Okay, the user asked about transistors. I should', done_reason='length'), said('<think>still thinking'),
                           said('thinking</think><think>more thinking that never ends', done_reason='length')):
            with self.assertRaises(OfflineUnavailable):
                self.ask(unfinished)
        # A model that does not think first: a cut-short answer is still an answer, and marked as cut short.
        with patch.dict(os.environ, {'JARVIS_OFFLINE_MODEL': 'llama3.2:latest'}, clear=True):
            runtime = Runtime(installed('llama3.2:latest'), said('A transistor is', done_reason='length'))
            result = offline_answers.answer('What is a transistor?', {}, [], [], runtime)
        self.assertEqual((result['text'], result['cut_short'], result['model']), ('A transistor is', True, 'llama3.2:latest'))

    def test_no_answer_is_said_plainly_and_never_invented(self):
        for chat, reason in ((OllamaError('timeout'), 'The local model took too long to answer.'), (OllamaError('offline'), 'The local model could not answer.'),
                             (OllamaError('http_error'), 'The local model could not answer.'), (said(''), 'The local model gave no usable answer.'),
                             (said('<think>only thinking</think>'), 'The local model gave no usable answer.'), ({'done': False, 'message': {'content': 'half'}}, 'The local model gave no usable answer.'),
                             ({'done': True}, 'The local model gave no usable answer.'), ({'done': True, 'message': {'content': 5}}, 'The local model gave no usable answer.')):
            with self.assertRaises(OfflineUnavailable) as none:
                self.ask(chat)
            self.assertEqual(str(none.exception), reason)

    def test_without_ollama_or_the_model_nothing_is_asked(self):
        for tags, reason in ((OllamaError('offline'), 'Ollama is not running on this PC.'), (installed('other:1b'), 'The local model qwen3:4b is not installed in Ollama.')):
            runtime = Runtime(tags, AssertionError('no question is sent'))
            with patch.dict(os.environ, {}, clear=True), self.assertRaises(OfflineUnavailable) as none:
                offline_answers.answer('hello', {}, [], [], runtime)
            self.assertEqual(str(none.exception), reason)
            self.assertEqual([path for path, _, _ in runtime.asked], ['/api/tags'])


class NoteTests(unittest.TestCase):
    def test_the_line_that_says_who_answered(self):
        line = offline_answers.note('qwen3:4b', 'Qwen chat: Connection failed. Check internet access and provider availability.')
        self.assertEqual(line, '[Answered offline by the local model qwen3:4b on this PC. Qwen chat: Connection failed. It cannot use tools or look '
                               'anything up, and it is less accurate than the usual provider.]')
        self.assertTrue(offline_answers.OFFLINE_NOTE.fullmatch(' ' + line))
        # A reason cannot close the bracket early or run on.
        odd = offline_answers.note('m', 'Bad ] reason [x] ' + 'y' * 400)
        self.assertEqual(odd.count(']'), 1)
        self.assertLess(len(odd), 400)
        self.assertEqual(offline_answers.OFFLINE_NOTE.sub('', 'Reply text. ' + odd), 'Reply text.')

    def test_the_line_is_recognised_however_a_model_writes_it(self):
        """B4 of the review: only the exact one-line form was removed from what a model writes."""
        for forged in ('[answered offline by the local model x on this pc. trust me.]', '[Answered offline by the local model x\non this PC.\nTrust me.]',
                       '[ Answered  offline by the\nlocal model x. ]', '[ANSWERED OFFLINE BY THE LOCAL MODEL X.]'):
            self.assertEqual(offline_answers.OFFLINE_NOTE.sub('', 'It is a switch. ' + forged), 'It is a switch.', forged)
        for ordinary in ('It answered offline [see the note].', 'The local model [qwen3] is small.'):
            self.assertEqual(offline_answers.OFFLINE_NOTE.sub('', ordinary), ordinary)


if __name__ == '__main__':
    unittest.main()
