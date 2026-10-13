"""OpenRouter as JARVIS's AI connection (docs/VERONICA-MERGE-PLAN.md, phase 1): one key for every AI job except the voice.
Everything here runs against stand-ins; nothing is sent to OpenRouter."""
import base64
import io
import json
import os
import tempfile
import threading
import unittest
import urllib.error
from unittest.mock import patch

import actions
import connection_checks
import providers
from server import App, Run

KEY = 'or-test-key'
ENV = {'JARVIS_PROVIDER': 'openrouter', 'OPENROUTER_API_KEY': KEY}
MAIN, FAST = 'qwen/qwen3.8-max-0902', 'qwen/qwen3.8-flash'
CODING, FALLBACK = MAIN, FAST  # Qwen only (owner, 2026-10-13): coding on the main model, the fast model as backup
ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'


def answer(content='Hi', model=MAIN, finish='stop', calls=None):
    message = {'content': content}
    if calls:
        message['tool_calls'] = calls
    return {'model': model, 'choices': [{'finish_reason': finish, 'message': message}]}


def ask(env=None, reply=None, **kwargs):
    """One providers.chat() call through a stand-in request(); returns (result, url, body, headers). fallback defaults to
    True here because this stands in for the Core's everyday call, which offers OpenRouter's backup model while Settings >
    AI > Backup is on (the shipped default); a test for Backup off passes fallback=False. providers.chat itself defaults
    to False, so a caller that forgets the option never reaches the backup model's company (App.fallback_option)."""
    kwargs.setdefault('fallback', True)
    messages = kwargs.pop('messages', [{'role': 'user', 'content': 'Hello'}])
    tools = kwargs.pop('tools', [])
    with patch.dict(os.environ, env or ENV, clear=True), patch.object(providers, 'request', return_value=reply or answer()) as request:
        result = providers.chat(messages, tools, lambda *args: None, threading.Event(), **kwargs)
    url, body, headers = request.call_args.args[:3]
    return result, url, body, headers


class FakeStream:
    """A streamed answer as OpenRouter sends it: server-sent events, with its "processing" comment lines."""
    def __init__(self, lines):
        self.lines = [line if isinstance(line, bytes) else line.encode() for line in lines]

    def readline(self, limit=-1):
        return self.lines.pop(0) if self.lines else b''

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def event(data):
    return 'data: ' + json.dumps(data) + '\n'


class OpenRouterChatTests(unittest.TestCase):
    def test_the_request_goes_to_openrouter_with_the_main_model_tools_and_room_to_think(self):
        call = {'id': 'c1', 'type': 'function', 'function': {'name': 'lookup', 'arguments': '{}'}}
        tools = [{'type': 'function', 'function': {'name': 'lookup', 'parameters': {'type': 'object'}}}]
        messages = [{'role': 'system', 'content': 'Mr Teague'}, {'role': 'assistant', 'content': 'Earlier', '_response_output': [], '_fallback': {}}]
        result, url, body, headers = ask(reply=answer(None, finish='tool_calls', calls=[call]), messages=messages, tools=tools)
        self.assertEqual(result['tool_calls'], [call])
        self.assertEqual(url, ENDPOINT)
        self.assertEqual(headers['Authorization'], 'Bearer ' + KEY)
        self.assertEqual(body['model'], MAIN)
        self.assertEqual(body['models'], [MAIN, FALLBACK])          # plan D8
        self.assertEqual(body['reasoning'], {'effort': 'medium', 'exclude': True})  # Deep, the default answer speed
        self.assertEqual(body['max_tokens'], providers.OPENROUTER_REPLY_TOKENS)
        self.assertEqual((body['tools'], body['tool_choice']), (tools, 'auto'))
        self.assertEqual(body['messages'][1], {'role': 'assistant', 'content': 'Earlier'})  # the Core's own fields stay home
        for alibaba_only in ('enable_thinking', 'max_completion_tokens'):
            self.assertNotIn(alibaba_only, body)

    def test_the_answer_speed_sets_the_model_and_how_hard_it_thinks(self):
        cases = [({'mode': 'auto', 'text': 'x'}, MAIN, 'minimal'),
                 ({'mode': 'economy', 'text': 'x'}, FAST, 'none'),         # only the fast model may stop thinking
                 ({'mode': 'deep', 'text': 'x'}, MAIN, 'medium'),
                 ({'mode': 'nonsense', 'text': 'x'}, MAIN, 'medium'),      # unknown: the default
                 ({'mode': 'economy', 'text': 'Think hard about this plan.'}, MAIN, 'high'),
                 ({'mode': 'auto', 'text': "Don't think hard about it, just answer."}, MAIN, 'minimal')]
        for options, model, effort in cases:
            body = ask(**options)[2]
            self.assertEqual((body['model'], body['reasoning']['effort']), (model, effort), options)

    def test_pictures_use_the_main_model_without_tools_even_in_economy(self):
        tools = [{'type': 'function', 'function': {'name': 'lookup', 'parameters': {'type': 'object'}}}]
        body = ask(vision=True, mode='economy', text='x', tools=tools)[2]
        self.assertEqual((body['model'], body['reasoning']['effort']), (MAIN, 'minimal'))
        self.assertNotIn('tools', body)
        body = ask(env={**ENV, 'OPENROUTER_VISION_MODEL': 'qwen/qwen3.8-vl'}, vision=True)[2]
        self.assertEqual(body['model'], 'qwen/qwen3.8-vl')  # a key-file vision model, within the owner's Qwen-only rule

    def test_a_mission_is_a_coding_job_for_the_coding_model_with_its_larger_budget(self):
        body = ask(job='coding', max_tokens=40000)[2]
        self.assertEqual(body['model'], CODING)
        self.assertNotIn('reasoning', body)  # the coding model keeps its own default thinking
        self.assertEqual(body['max_tokens'], 40000)
        self.assertEqual(body['models'], [CODING, FALLBACK])
        self.assertEqual(ask(job='coding', max_tokens=8192)[2]['max_tokens'], providers.OPENROUTER_REPLY_TOKENS)

    def test_models_come_from_the_key_file_and_the_fallback_can_be_turned_off(self):
        env = {**ENV, 'OPENROUTER_MODEL': 'qwen/qwen3.7-plus', 'OPENROUTER_FAST_MODEL': 'qwen/qwen3.7-flash',
               'OPENROUTER_CODING_MODEL': 'qwen/qwen3.7-coder', 'OPENROUTER_FALLBACK_MODEL': ''}
        body = ask(env=env)[2]
        self.assertEqual(body['model'], 'qwen/qwen3.7-plus')
        self.assertNotIn('models', body)
        self.assertEqual(ask(env=env, mode='economy', text='x')[2]['model'], 'qwen/qwen3.7-flash')
        self.assertEqual(ask(env=env, job='coding')[2]['model'], 'qwen/qwen3.7-coder')
        self.assertNotIn('models', ask(env={**ENV, 'OPENROUTER_FALLBACK_MODEL': MAIN})[2])  # never the same model twice

    def test_only_qwen_models_may_answer_the_owners_rule_of_2026_10_13(self):
        # Every model line of the key file is refused the moment it names another maker's model, before any request.
        cases = (('OPENROUTER_MODEL', 'anthropic/claude-sonnet-5.5', {}),
                 ('OPENROUTER_VISION_MODEL', 'openai/gpt-4o', {'vision': True}),
                 ('OPENROUTER_FAST_MODEL', 'google/gemini-2.5-flash', {'mode': 'economy', 'text': 'x'}),
                 ('OPENROUTER_CODING_MODEL', 'anthropic/claude-opus-5.5', {'job': 'coding'}),
                 ('OPENROUTER_FALLBACK_MODEL', 'anthropic/claude-sonnet-5.5', {'fallback': True}))
        for line, other, kwargs in cases:
            with self.subTest(line=line):
                with patch.dict(os.environ, {**ENV, line: other}, clear=True), patch.object(providers, 'request') as request, \
                        self.assertRaises(providers.ProviderError) as raised:
                    providers.chat([{'role': 'user', 'content': 'Hello'}], [], lambda *args: None, threading.Event(), **kwargs)
                self.assertIn('Qwen', str(raised.exception))
                self.assertIn(other, str(raised.exception))
                request.assert_not_called()

    def test_settings_still_report_a_model_of_another_maker_instead_of_failing(self):
        # capabilities() is the Settings page's own read: it shows what the key file says (so the owner can see the
        # wrong line) and never raises; only the request paths refuse.
        with patch.dict(os.environ, {**ENV, 'OPENROUTER_MODEL': 'anthropic/claude-sonnet-5.5',
                                     'OPENROUTER_FALLBACK_MODEL': 'openai/gpt-4o'}, clear=True):
            caps = providers.capabilities()
        self.assertEqual(caps['model'], 'anthropic/claude-sonnet-5.5')
        self.assertIn('openai/gpt-4o', caps['backup'] or '')

    def test_no_key_is_said_plainly_and_nothing_is_sent(self):
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'openrouter'}, clear=True), patch.object(providers, 'request') as request, \
                self.assertRaises(providers.ProviderError) as raised:
            providers.chat([], [], lambda *args: None, threading.Event())
        self.assertIn('OPENROUTER_API_KEY', str(raised.exception))
        request.assert_not_called()
        self.assertFalse(providers.backup_worthy(raised.exception))  # a missing key is the owner's to see

    def test_an_answer_from_the_backup_model_is_marked_and_the_note_is_the_cores_own(self):
        result = ask(reply=answer('Paris.', model=FALLBACK))[0]
        self.assertEqual(result['_fallback'], {'asked': MAIN, 'used': FALLBACK})
        note = providers.fallback_note(result)
        self.assertEqual(note, f'[OpenRouter answered this question with its backup model ({FALLBACK}) because {MAIN} could not answer it.]')
        self.assertTrue(providers.BACKUP_OPENING.search(note))
        self.assertEqual(providers.BACKUP_NOTE.sub('', 'Paris.\n\n' + note), 'Paris.')
        self.assertEqual(providers.fallback_note({'_fallback': {'asked': MAIN, 'used': 'evil]\n[name'}}),
                         f'[OpenRouter answered this question with its backup model (another model) because {MAIN} could not answer it.]')

    def test_the_main_model_under_a_dated_name_or_no_name_is_not_a_fallback(self):
        for model in (MAIN, MAIN + '-20261001', None, '', 'someone/else', 'qwen/qwen3.8-max-canonical'):
            result = ask(reply=answer('Hi', model=model))[0]
            self.assertNotIn('_fallback', result, model)
            self.assertIsNone(providers.fallback_note(result))
        self.assertNotIn('_fallback', ask(env={**ENV, 'OPENROUTER_FALLBACK_MODEL': ''}, reply=answer('Hi', model=FALLBACK))[0])

    def test_the_backup_model_is_recognised_under_another_name_of_its_maker(self):
        # OpenRouter may answer with a canonical slug (review of 2026-10-12, M2): the maker decides, when the backup is
        # from another maker than the main model. The owner's Qwen-only rule (2026-10-13) means the key file can no
        # longer name such a backup, so that case is tested on is_fallback directly; it stays defensive about names.
        # The default backup (Qwen's own fast model) under a dated name, end to end.
        self.assertEqual(ask(reply=answer('Hi', model=FALLBACK + '-20260101'))[0]['_fallback'], {'asked': MAIN, 'used': FALLBACK + '-20260101'})
        # A cross-maker answer under a canonical slug, on the function itself.
        for model in ('anthropic/claude-sonnet-5.5-20260101', 'anthropic/claude-5.5-sonnet-20260101'):
            self.assertTrue(providers.is_fallback(model, MAIN, 'anthropic/claude-sonnet-5.5'), model)
        # One name starting with the other: the longer match wins.
        self.assertTrue(providers.is_fallback('x/m-fast', 'x/m', 'x/m-fast'))
        self.assertTrue(providers.is_fallback('x/m-fast-2026', 'x/m', 'x/m-fast'))
        self.assertFalse(providers.is_fallback('x/m-2026', 'x/m', 'x/m-fast'))
        self.assertTrue(providers.is_fallback('x/m', 'x/m-fast', 'x/m'))   # the backup model's own name exactly: it answered
        self.assertFalse(providers.is_fallback('qwen/qwen-x', MAIN, FALLBACK))  # same maker: not decidable, not marked
        self.assertFalse(providers.is_fallback(None, MAIN, FALLBACK))
        self.assertFalse(providers.is_fallback(FALLBACK, MAIN, None))

    def test_with_the_backup_switched_off_no_fallback_is_asked_for(self):
        body = ask(fallback=False)[2]
        self.assertNotIn('models', body)
        self.assertEqual(body['model'], MAIN)

    def test_think_hard_reaches_openrouter_in_the_default_deep_mode(self):
        with patch.dict(os.environ, ENV, clear=True):
            options = providers.chat_options('deep', 'Think hard about this plan.')
            self.assertEqual(options, {'mode': 'deep', 'text': 'Think hard about this plan.'})
            self.assertEqual(providers.chat_options('deep', 'Hello'), {})
            self.assertEqual(providers.chat_options(None, 'Hello'), {})
        self.assertEqual(ask(**options)[2]['reasoning']['effort'], 'high')

    def test_a_short_rate_limit_pauses_voice_commands_and_no_credit_does_not(self):
        for limit, wait in (('rate', 30), ('billing', 0)):
            error = providers.ProviderError('OpenRouter chat: limit')
            error.status, error.limit = 429, limit
            with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=error), \
                    self.assertRaises(providers.ProviderError) as raised:
                providers.chat([], [], lambda *args: None, threading.Event())
            self.assertEqual(raised.exception.retry_after, wait, limit)

    def test_a_provider_line_of_another_name_is_refused_and_points_to_openrouter(self):
        # OpenRouter is the only provider (owner, 2026-10-13): an old JARVIS_PROVIDER line is refused plainly,
        # and a missing line means OpenRouter.
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'qwen', 'OPENROUTER_API_KEY': 'k'}, clear=True), \
                self.assertRaises(providers.ProviderError) as raised:
            providers.chat([], [], lambda *args: None, threading.Event())
        self.assertIn('set JARVIS_PROVIDER=openrouter', str(raised.exception))
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'k'}, clear=True):
            self.assertEqual(providers.provider(), 'openrouter')
            self.assertEqual(providers.capabilities()['brain'], 'OpenRouter configured')

    def test_an_error_inside_an_answer_or_a_cut_off_answer_is_refused(self):
        with self.assertRaises(providers.ProviderError):
            ask(reply={'error': {'code': 502, 'message': 'upstream failed'}, 'choices': []})
        with self.assertRaises(providers.ProviderError) as raised:
            ask(reply=answer('TEAG', finish='length'))
        self.assertIn('No partial answer was accepted', str(raised.exception))

    def test_a_streamed_answer_arrives_in_pieces_past_the_processing_lines(self):
        lines = [': OPENROUTER PROCESSING\n', '\n',
                 event({'model': FALLBACK, 'choices': [{'delta': {'reasoning': 'secret thoughts'}}]}),
                 event({'model': FALLBACK, 'choices': [{'delta': {'content': 'Par'}}]}),
                 event({'model': FALLBACK, 'choices': [{'delta': {'content': 'is.'}, 'finish_reason': 'stop'}]}),
                 'data: [DONE]\n']
        pieces, sent = [], []

        def urlopen(req, timeout=None):
            sent.append(req)
            return FakeStream(lines)

        with patch.dict(os.environ, ENV, clear=True), patch('urllib.request.urlopen', side_effect=urlopen):
            result = providers.chat([{'role': 'user', 'content': 'Capital?'}], [],
                                    lambda name, data: pieces.append(data['text']) if name == 'assistant.piece' else None,
                                    threading.Event(), stream=True, fallback=True)  # the Core offers the backup while Backup is on
        self.assertEqual(pieces, ['Par', 'is.'])  # the thinking is never shown
        self.assertEqual(result['content'], 'Paris.')
        self.assertEqual(result['_fallback'], {'asked': MAIN, 'used': FALLBACK})
        self.assertEqual(sent[0].full_url, ENDPOINT)
        body = json.loads(sent[0].data)
        self.assertTrue(body['stream'])
        self.assertEqual(body['models'], [MAIN, FALLBACK])

    def test_no_credit_is_said_in_our_words_as_a_billing_limit(self):
        upstream = urllib.error.HTTPError(ENDPOINT, 402, 'Payment Required', {}, io.BytesIO(b'{"error":{"code":402,"message":"UPSTREAM-DETAIL"}}'))
        with patch('urllib.request.urlopen', side_effect=upstream), self.assertRaises(providers.ProviderError) as raised:
            providers.request(ENDPOINT, {'model': MAIN})
        error = raised.exception
        self.assertTrue(str(error).startswith('OpenRouter chat: OpenRouter has no credit'))
        self.assertIn('US$0.50', str(error))
        self.assertNotIn('UPSTREAM', str(error))
        self.assertEqual((error.status, error.limit, error.service), (402, 'billing', 'OpenRouter'))

    def test_the_key_only_ever_goes_to_openrouter(self):
        # The address is fixed in the code: no key-file line can send the key elsewhere.
        for name in ('OPENROUTER_BASE_URL', 'DASHSCOPE_BASE_URL', 'OPENAI_BASE_URL'):
            url = ask(env={**ENV, name: 'https://evil.example/v1'})[1]
            self.assertEqual(url, ENDPOINT)


class OpenRouterSearchTests(unittest.TestCase):
    def setUp(self):
        actions._SEARCH_CACHE.clear()
        self.addCleanup(actions._SEARCH_CACHE.clear)

    def test_a_search_model_of_another_maker_is_refused(self):
        # The owner's Qwen-only rule (2026-10-13) covers the web search's small request too.
        with patch.dict(os.environ, {**ENV, 'OPENROUTER_FAST_MODEL': 'openai/gpt-4o'}, clear=True), \
                patch.object(providers, 'request') as request, self.assertRaises(providers.ProviderError) as raised:
            providers.openrouter_search('the news')
        self.assertIn('Qwen', str(raised.exception))
        request.assert_not_called()

    def test_results_are_the_pages_it_cited(self):
        cite = lambda url, title='T', content='x': {'type': 'url_citation', 'url_citation': {'url': url, 'title': title, 'content': content}}
        reply = {'choices': [{'message': {'content': 'One line.', 'annotations': [
            cite('https://a.example/1', 'First   page', 'Some\n  text'),
            cite('https://a.example/1', 'Again'),                 # the same page twice
            cite('javascript:alert(1)'), {'type': 'file', 'file': {}},
            cite('https://b.example/2', '', ''),                  # no title: the address stands in
            cite('http://c.example/3', 'Third', 'y' * 900)]}}]}
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', return_value=reply) as request:
            items = providers.openrouter_search('opera house')
        self.assertEqual([i['url'] for i in items], ['https://a.example/1', 'https://b.example/2', 'http://c.example/3'])
        self.assertEqual(items[0], {'title': 'First page', 'url': 'https://a.example/1', 'description': 'Some text'})
        self.assertEqual(items[1]['title'], 'https://b.example/2')
        self.assertEqual(len(items[2]['description']), 500)
        url, body, headers = request.call_args.args[:3]
        self.assertEqual((url, headers['Authorization']), (ENDPOINT, 'Bearer ' + KEY))
        self.assertEqual(body['plugins'], [{'id': 'web', 'max_results': 5}])
        self.assertEqual((body['model'], body['reasoning']), (FAST, {'effort': 'none'}))
        self.assertIn('opera house', body['messages'][0]['content'])
        self.assertEqual(request.call_args.kwargs['operation'], 'web search')

    def test_a_search_with_no_citations_and_no_key(self):
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', return_value={'choices': [{'message': {'content': 'x'}}]}):
            self.assertEqual(providers.openrouter_search('q'), [])
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'openrouter'}, clear=True), self.assertRaises(providers.ProviderError):
            providers.openrouter_search('q')

    def test_jarvis_searches_through_openrouter_when_it_is_chosen_even_with_a_brave_key(self):
        items = [{'title': 'T', 'url': 'https://a.example/', 'description': 'd'}]
        with patch.dict(os.environ, {**ENV, 'BRAVE_API_KEY': 'b', 'SERPAPI_API_KEY': 's'}, clear=True), \
                patch.object(providers, 'openrouter_search', return_value=items) as search, patch.object(actions, 'request') as other:
            result = actions.search('weather in Sydney')
        self.assertEqual(result['results'], items)
        search.assert_called_once_with('weather in Sydney')
        other.assert_not_called()

    def test_no_results_from_openrouter_does_not_send_the_owner_to_brave(self):
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'openrouter_search', return_value=[]), \
                self.assertRaises(providers.ProviderError) as raised:
            actions.search('zzzz')
        self.assertEqual(str(raised.exception), 'Search returned no usable results. Try a different query.')

    def test_the_search_connection_test_runs_one_openrouter_search(self):
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'openrouter_search', return_value=[{'url': 'u'}]) as search:
            result = connection_checks.check('search')
        self.assertEqual(result['status'], 'passed')
        self.assertIn('OpenRouter web search', result['detail'])
        search.assert_called_once_with('Sydney Opera House', 1)
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'openrouter_search', return_value=[]):
            self.assertEqual(connection_checks.check('search')['status'], 'failed')


STT = {**ENV, 'OPENROUTER_STT_MODEL': 'qwen/qwen3-asr-flash'}  # the cloud option for hearing, named in the key file; a stand-in
# Qwen name (OpenRouter listed no Qwen speech model on 2026-10-13) so the documented request shape stays covered;
# another maker's line is refused, as the refusal test below checks.


class OpenRouterSpeechTests(unittest.TestCase):
    def test_without_a_speech_model_the_cloud_option_is_off_and_this_pc_hears(self):
        # Qwen only (owner, 2026-10-13): OpenRouter's speech-to-text models are not Qwen, so none is named by default.
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request') as request:
            self.assertIsNone(providers.cloud_speech())
            caps = providers.capabilities()
            self.assertEqual((caps['transcription'], caps['transcription_provider']), (False, None))
            with self.assertRaises(providers.ProviderError) as raised:
                providers.transcribe(b'RIFFdata', 'audio/wav')
        self.assertIn('OPENROUTER_STT_MODEL', str(raised.exception))
        request.assert_not_called()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        app = App(folder.name)
        app.store.save_settings({'speech_recognition': 'cloud'})
        pcm = base64.b64encode(bytes(32000)).decode('ascii')
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request') as request, \
                patch.object(app.local_stt, 'transcribe', return_value={'text': 'hello'}) as local:
            self.assertEqual(app.transcribe_speech({'data': pcm})['engine'], 'this PC')
        local.assert_called_once()
        request.assert_not_called()

    def test_cloud_speech_recognition_sends_the_recording_as_openrouter_documents(self):
        with patch.dict(os.environ, STT, clear=True), patch.object(providers, 'request', return_value={'text': '  set a timer  '}) as request:
            self.assertEqual(providers.cloud_speech(), 'openrouter')
            self.assertEqual(providers.capabilities()['transcription_provider'], 'OpenRouter')
            self.assertEqual(providers.transcribe(b'RIFFdata', 'audio/wav', timeout=7), {'text': 'set a timer'})
        url, body, headers = request.call_args.args[:3]
        self.assertEqual(url, 'https://openrouter.ai/api/v1/audio/transcriptions')
        self.assertEqual(body, {'model': 'qwen/qwen3-asr-flash', 'language': 'en',
                                'input_audio': {'data': base64.b64encode(b'RIFFdata').decode(), 'format': 'wav'}})
        self.assertEqual(request.call_args.kwargs['timeout'], 7)

    def test_a_speech_model_of_another_maker_leaves_the_cloud_option_off_and_is_refused(self):
        # The owner's Qwen-only rule (2026-10-13) covers hearing too: a whisper line turns the cloud option off (this
        # PC keeps hearing) and a direct cloud call is refused before any request.
        env = {**ENV, 'OPENROUTER_STT_MODEL': 'openai/whisper-1'}
        with patch.dict(os.environ, env, clear=True), patch.object(providers, 'request') as request:
            self.assertIsNone(providers.cloud_speech())
            caps = providers.capabilities()
            self.assertEqual((caps['transcription'], caps['transcription_provider']), (False, None))
            with self.assertRaises(providers.ProviderError) as raised:
                providers.transcribe(b'RIFFdata', 'audio/wav')
        self.assertIn('Qwen', str(raised.exception))
        self.assertIn('openai/whisper-1', str(raised.exception))
        request.assert_not_called()

    def test_formats_language_size_and_a_bad_answer(self):
        with patch.dict(os.environ, {**STT, 'OPENROUTER_STT_LANGUAGE': ''}, clear=True), \
                patch.object(providers, 'request', return_value={'text': 'hi'}) as request:
            providers.transcribe(b'x', 'audio/webm;codecs=opus')
            body = request.call_args.args[1]
        self.assertEqual(body['input_audio']['format'], 'webm')
        self.assertNotIn('language', body)
        with patch.dict(os.environ, STT, clear=True):
            with self.assertRaises(ValueError):
                providers.transcribe(b'x', 'audio/flac')
            with self.assertRaises(ValueError):
                providers.transcribe(b'x' * (providers.OPENROUTER_AUDIO_LIMIT + 1), 'audio/wav')
            with patch.object(providers, 'request', return_value={'nothing': True}), self.assertRaises(providers.ProviderError):
                providers.transcribe(b'x', 'audio/wav')


class OpenRouterStatusTests(unittest.TestCase):
    def test_settings_show_openrouter_its_model_pictures_and_search(self):
        with patch.dict(os.environ, ENV, clear=True):
            caps = providers.capabilities()
            self.assertEqual(providers.capabilities('economy')['model'], FAST)
        self.assertEqual((caps['brain'], caps['model'], caps['vision_provider'], caps['vision']), ('OpenRouter configured', MAIN, 'OpenRouter', True))
        self.assertEqual(caps['search'], 'OpenRouter web search')
        self.assertEqual(caps['backup'], f"OpenRouter's backup model ({FALLBACK})")  # the fallback is OpenRouter's own (plan D8)
        with patch.dict(os.environ, {**ENV, 'OPENROUTER_FALLBACK_MODEL': ''}, clear=True):
            self.assertIsNone(providers.capabilities()['backup'])   # turned off in the key file: none
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'openrouter', 'BRAVE_API_KEY': 'b'}, clear=True):
            caps = providers.capabilities()
        # The Brave key no longer counts: its search branch is removed (owner, 2026-10-13).
        self.assertEqual((caps['brain'], caps['vision'], caps['search']), ('OpenRouter not configured', False, 'DuckDuckGo best effort'))

    def test_the_health_check_proves_the_key_without_paying_for_an_answer_or_a_search(self):
        asked = []

        def request(url, data=None, headers=None, **kwargs):
            asked.append(url)
            return {'data': {'label': 'x', 'usage': 0}}

        with patch.dict(os.environ, {**ENV, 'BRAVE_API_KEY': 'b'}, clear=True), patch.object(providers, 'request', side_effect=request):
            checks = providers.live_health()
        self.assertEqual(asked, ['https://openrouter.ai/api/v1/key'])
        self.assertEqual(checks['Chat model access']['status'], 'reachable')
        self.assertEqual(checks['Web search']['status'], 'configured')
        self.assertNotIn('Brave search', checks)

    def test_which_key_counts(self):
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'k'}, clear=True):
            self.assertTrue(providers.any_ai_key())
            self.assertEqual(providers.chosen_key(), 'k')  # no JARVIS_PROVIDER line: OpenRouter, the only one, is chosen
        with patch.dict(os.environ, ENV, clear=True):
            self.assertEqual(providers.chosen_key(), KEY)
        with patch.dict(os.environ, {'JARVIS_PROVIDER': 'groq', 'OPENROUTER_API_KEY': 'k'}, clear=True):
            self.assertIsNone(providers.chosen_key())
            self.assertIn('openrouter', str(providers.unsupported_error()))
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(providers.any_ai_key())


class OpenRouterRunTests(unittest.TestCase):
    """A whole question through the Core with OpenRouter chosen."""
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.app = App(folder.name)

    def run_question(self, replies, text='Compare Paris and Lyon for a weekend away.'):
        self.bodies = []
        run = Run('openrouter-test')

        def request(url, body=None, headers=None, **kwargs):
            self.bodies.append(body)
            return replies.pop(0)

        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=request):
            self.app.work(run, text, None)
        return {e['event']: e['data'] for e in run.events}

    def test_an_answer_needs_no_other_key(self):
        events = self.run_question([answer('Paris is busier; Lyon eats better.')])
        self.assertEqual(events['assistant.completed']['text'], 'Paris is busier; Lyon eats better.')
        self.assertEqual(self.bodies[0]['model'], MAIN)
        self.assertNotIn('provider.backup', events)

    def test_the_reply_says_when_openrouters_backup_model_wrote_it(self):
        events = self.run_question([answer('Paris is busier.', model=FALLBACK)])
        note = providers.fallback_note({'_fallback': {'asked': MAIN, 'used': FALLBACK}})
        self.assertEqual(events['assistant.completed']['text'], 'Paris is busier.\n\n' + note)
        self.assertEqual(events['provider.backup'], {'from': MAIN, 'to': FALLBACK, 'reason': 'OpenRouter switched to its backup model'})
        self.assertTrue(any('OpenRouter backup model took over' in row['action'] for row in self.app.store.logs()))

    def test_a_model_cannot_write_the_cores_note_itself(self):
        fake = '[OpenRouter answered this question with its backup model (x) because y could not answer it.]'
        events = self.run_question([answer('Paris. ' + fake)])
        self.assertEqual(events['assistant.completed']['text'], 'Paris.')

    def test_with_backup_off_no_request_offers_the_backup_model(self):
        # Settings > AI > Backup off: no request carries the "models" fallback list, so nothing can reach the backup
        # model's company, and a name the Core never asked for is not announced as its backup (review of 2026-10-12, H1).
        self.app.store.save_settings({'provider_backup': False})
        call = [{'id': 'c1', 'type': 'function', 'function': {'name': 'time_now', 'arguments': '{}'}}]
        events = self.run_question([answer(content=None, finish='tool_calls', calls=call), answer('Done.', model=FALLBACK)])
        self.assertEqual(len(self.bodies), 2)                                   # a tool step, then the answer
        self.assertTrue(all('models' not in body for body in self.bodies))      # the one-piece retry reuses the same depth
        self.assertEqual([body['model'] for body in self.bodies], [MAIN, MAIN])
        self.assertNotIn('provider.backup', events)
        self.assertEqual(events['assistant.completed']['text'], 'Done.')        # the stand-in's model name is not the Core's note

    def test_with_backup_on_the_request_offers_the_backup_model(self):
        self.app.store.save_settings({'provider_backup': True})
        self.run_question([answer('Paris.')])
        self.assertEqual(self.bodies[0]['models'], [MAIN, FALLBACK])

    def test_a_mission_step_uses_the_coding_model_and_honours_backup(self):
        bodies = []

        def request(url, body=None, headers=None, **kwargs):
            bodies.append(body)
            return answer('ok')
        for backup, expected in ((True, [CODING, FALLBACK]), (False, None)):
            bodies.clear()
            self.app.store.save_settings({'provider_backup': backup})
            with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=request):
                self.app.mission_model([{'role': 'user', 'content': 'build'}], [], threading.Event(), 'build a tool')
            self.assertEqual(bodies[-1]['model'], CODING)                       # a mission is a coding job (plan D2)
            self.assertEqual(bodies[-1].get('models'), expected)

    def test_a_backup_described_picture_tells_the_owner_and_stays_out_of_the_tool_data(self):
        attachment = {'data': 'data:image/png;base64,' + base64.b64encode(b'x').decode('ascii')}
        self.app.store.save_settings({'provider_backup': True})
        run = Run('picture')
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', return_value=answer('A login screen.', model=FALLBACK)):
            words = self.app.describe_picture(run, attachment, 'What is on the screen?')
        self.assertEqual(words, 'A login screen.')                              # the note is kept off the tool result
        self.assertTrue(getattr(run, 'nested_fallback_note', None))             # work() adds it to the final reply
        self.assertIn('provider.backup', {e['event'] for e in run.events})
        self.assertTrue(any('backup model described a picture' in row['action'] for row in self.app.store.logs()))
        # Backup off: no request offers the backup model.
        bodies = []
        self.app.store.save_settings({'provider_backup': False})

        def request(url, body=None, headers=None, **kwargs):
            bodies.append(body)
            return answer('A screen.')
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=request):
            self.app.describe_picture(Run('picture-2'), attachment, 'What is on the screen?')
        self.assertTrue(bodies and all('models' not in body for body in bodies))


if __name__ == '__main__':
    unittest.main()
