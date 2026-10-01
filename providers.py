"""Provider adapters. Credentials remain in this server process."""
import base64
import hashlib
import json
import re
import time
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import math
import socket
import ssl


class ProviderError(Exception):
    pass


_cooldowns = {}
_cooldown_lock = threading.Lock()


def rate_limit(model, headers):
    try:
        seconds = max(1, min(86400, math.ceil(float(headers.get('retry-after', '60')))))
    except (ValueError, TypeError, OverflowError):
        seconds = 60
    with _cooldown_lock:
        _cooldowns[model] = time.time() + seconds
    error = ProviderError(f'Groq is temporarily rate-limited. Try again in about {seconds} seconds. Local notes and timers still work. If this keeps happening, check your Groq account limits; Fish Audio credit is separate.')
    error.retry_after = seconds
    return error


def request(url, data=None, headers=None, method=None, raw=False, timeout=35):
    host = urllib.parse.urlparse(url).hostname
    service = {'api.openai.com': 'OpenAI', 'api.fish.audio': 'Fish Audio', 'api.groq.com': 'Groq', 'serpapi.com': 'SerpApi', 'api.search.brave.com': 'Brave Search'}.get(host, 'External service')
    if host == 'generativelanguage.googleapis.com':
        service = 'Gemini'
    elif (host or '').endswith('.aliyuncs.com'):
        service = 'Qwen'
    path = urllib.parse.urlparse(url).path
    operation = 'transcription' if 'transcriptions' in path else 'voice synthesis' if 'tts' in path or 'text-to-speech' in path else 'chat' if 'completions' in path else 'request'
    prefix = f'{service} {operation}: '
    payload = json.dumps(data).encode() if isinstance(data, dict) else data
    h = {'User-Agent': 'JarvisLocal/1.0', **(headers or {})}
    if isinstance(data, dict):
        h['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=payload, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read(16 * 1024 * 1024)
            return body if raw else json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        # Never return raw upstream response bodies: they can contain sensitive data.
        label = {400: 'Request rejected. Check model and integration settings.', 401: 'Authentication failed. Check your local credentials.', 402: 'Insufficient API credit. Fish Audio API credit is separate from website credit; add API credit in the Fish developer dashboard.', 403: 'Access denied. Check account permissions and subscription.', 404: 'Resource or model not found.', 429: 'Rate limit reached. Wait before retrying; no keys were rotated.'}.get(exc.code, 'The provider could not complete the request.')
        raise ProviderError(f'{prefix}{label} (HTTP {exc.code})') from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, 'reason', exc)
        if isinstance(reason, ssl.SSLError):
            detail = 'Secure connection failed. Check system time and certificate/network settings.'
        elif isinstance(reason, socket.gaierror):
            detail = 'DNS lookup failed. Check your internet connection.'
        elif isinstance(reason, PermissionError) or getattr(reason, 'winerror', None) == 10013:
            detail = 'Network access blocked. Check app network permissions or firewall.'
        elif isinstance(reason, TimeoutError):
            detail = 'Connection timed out. Try again shortly.'
        else:
            detail = 'Connection failed. Check internet access and provider availability.'
        raise ProviderError(prefix + detail) from None
    except ValueError:
        raise ProviderError(prefix + 'Invalid response received from provider.') from None


def capabilities():
    if os.getenv('JARVIS_PROVIDER', '').lower() == 'gemini':
        # Reuse independent voice/search capabilities without selecting another brain.
        result = _base_capabilities()
        configured = bool(os.getenv('GEMINI_API_KEY'))
        result.update(brain='Gemini configured' if configured else 'Gemini not configured',
                      model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
                      vision_provider='Gemini', vision=configured)
        return result
    if os.getenv('JARVIS_PROVIDER', '').lower() == 'qwen':
        result = _base_capabilities()
        configured = bool(os.getenv('DASHSCOPE_API_KEY'))
        result.update(brain='Qwen configured' if configured else 'Qwen not configured',
                      model=os.getenv('QWEN_MODEL', QWEN_DEFAULT_MODEL),
                      vision_provider='Qwen', vision=configured and bool(os.getenv('QWEN_VISION_MODEL')))
        return result
    return _base_capabilities()


def _base_capabilities():
    use_openai = bool(os.getenv('OPENAI_API_KEY') and os.getenv('JARVIS_PROVIDER', 'groq').lower() == 'openai')
    return {
        'brain': 'OpenAI configured' if (os.getenv('OPENAI_API_KEY') and os.getenv('JARVIS_PROVIDER', 'groq').lower() == 'openai') else 'Groq configured' if os.getenv('GROQ_API_KEY') else 'local commands',
        'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini') if (os.getenv('OPENAI_API_KEY') and os.getenv('JARVIS_PROVIDER', 'groq').lower() == 'openai') else os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b'),
        'vision_provider': 'OpenAI' if (os.getenv('OPENAI_API_KEY') and os.getenv('JARVIS_PROVIDER', 'groq').lower() == 'openai') else 'Groq',
        'vision': bool(os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini')) if use_openai else bool(os.getenv('GROQ_API_KEY') and os.getenv('GROQ_VISION_MODEL')),
        'transcription': bool(os.getenv('OPENAI_API_KEY') or os.getenv('GROQ_API_KEY')),
        'elevenlabs': bool(os.getenv('ELEVENLABS_API_KEY') and os.getenv('ELEVENLABS_VOICE_ID')),
        'fish': bool(os.getenv('FISH_API_KEY') and os.getenv('FISH_VOICE_ID')),
        'voice_provider': 'fish' if os.getenv('FISH_API_KEY') and os.getenv('FISH_VOICE_ID') else 'elevenlabs' if os.getenv('ELEVENLABS_API_KEY') and os.getenv('ELEVENLABS_VOICE_ID') else 'browser',
        'search': 'SerpApi configured' if os.getenv('SERPAPI_API_KEY') else 'Brave configured' if os.getenv('BRAVE_API_KEY') else 'DuckDuckGo best effort',
        'youtube': bool(os.getenv('YOUTUBE_API_KEY')),
        'spotify': bool(os.getenv('SPOTIFY_CLIENT_ID')),
    }

def live_health():
    checks = {}
    targets = []
    caps = capabilities()
    use_openai = bool(os.getenv('OPENAI_API_KEY') and os.getenv('JARVIS_PROVIDER', 'groq').lower() == 'openai')
    use_gemini = os.getenv('JARVIS_PROVIDER', '').lower() == 'gemini'
    use_qwen = os.getenv('JARVIS_PROVIDER', '').lower() == 'qwen'
    key = os.getenv('GEMINI_API_KEY') if use_gemini else os.getenv('DASHSCOPE_API_KEY') if use_qwen else os.getenv('OPENAI_API_KEY') if use_openai else os.getenv('GROQ_API_KEY')
    if key and use_qwen:
        # Model Studio has no per-model lookup in compatible mode: a minimal real
        # completion proves key, region and model authorisation together.
        started = time.perf_counter()
        try:
            data = request(qwen_base() + '/chat/completions',
                           {'model': caps['model'], 'messages': [{'role': 'user', 'content': 'Reply with OK.'}],
                            'max_completion_tokens': 8, 'enable_thinking': False},
                           {'Authorization': 'Bearer ' + key}, timeout=15)
            valid = bool(data.get('choices'))
            checks['Chat model access'] = {'status': 'reachable' if valid else 'unexpected_response',
                                           'latency_ms': round((time.perf_counter()-started)*1000),
                                           'detail': 'Qwen answered a minimal test request.' if valid else 'Qwen returned an unexpected response.'}
        except ProviderError as exc:
            checks['Chat model access'] = {'status': 'unavailable', 'latency_ms': round((time.perf_counter()-started)*1000), 'detail': str(exc)}
    elif key:
        base = 'https://api.openai.com/v1/models/' if use_openai else 'https://api.groq.com/openai/v1/models/'
        if use_gemini:
            base = 'https://generativelanguage.googleapis.com/v1beta/openai/models/'
        targets.append(('Chat model access', base + urllib.parse.quote(caps['model'], safe=''), {'Authorization': 'Bearer ' + key}))
    else:
        checks['Chat model access'] = {'status':'not_configured','detail':'Add a chat provider key locally.'}
    if os.getenv('BRAVE_API_KEY'):
        targets.append(('Brave search', 'https://api.search.brave.com/res/v1/web/search?q=Sydney+Opera+House&count=1', {'X-Subscription-Token':os.environ['BRAVE_API_KEY']}))
    else:
        checks['Brave search'] = {'status':'not_configured','detail':'Add BRAVE_API_KEY locally.'}
    for name, url, headers in targets:
        started = time.perf_counter()
        try:
            data = request(url, headers=headers, timeout=15)
            valid = bool(data.get('id')) if name == 'Chat model access' else bool(data.get('web', {}).get('results'))
            checks[name] = {'status':'reachable' if valid else 'unexpected_response','latency_ms':round((time.perf_counter()-started)*1000), 'detail':'Model access confirmed; generation not tested.' if name == 'Chat model access' and valid else 'Live search returned results.' if valid else 'No expected results returned.'}
        except ProviderError as exc:
            checks[name] = {'status':'unavailable','latency_ms':round((time.perf_counter()-started)*1000), 'detail':str(exc)}
    checks['Voice']={'status':'configured' if caps['voice_provider'] != 'browser' else 'manual_check','detail':'Use Settings connection tests for synthesis. Speaker playback requires a device test.'}
    checks['Maps']={'status':'configured' if os.getenv('GOOGLE_MAPS_ROUTES_KEY') and os.getenv('GOOGLE_MAPS_EMBED_KEY') else 'not_configured','detail':'Configuration only. Use Settings to test Routes; open Maps to test display.'}
    return checks


def chat(messages, tools, emit, cancel, vision=False):
    if cancel.is_set():
        return None
    if os.getenv('JARVIS_PROVIDER', '').lower() == 'gemini':
        return gemini_chat(messages, tools, emit, cancel, vision)
    if os.getenv('JARVIS_PROVIDER', '').lower() == 'qwen':
        return qwen_chat(messages, tools, emit, cancel, vision)
    use_openai = bool(os.getenv('OPENAI_API_KEY') and os.getenv('JARVIS_PROVIDER', 'groq').lower() == 'openai')
    key = os.getenv('OPENAI_API_KEY') if use_openai else os.getenv('GROQ_API_KEY')
    if not key:
        raise ProviderError('Add OPENAI_API_KEY or GROQ_API_KEY to your local .env and restart to enable AI conversation.')
    model = (os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini') if vision else os.getenv('OPENAI_MODEL', 'gpt-4o-mini')) if use_openai else (os.getenv('GROQ_VISION_MODEL') if vision else os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b'))
    if not model:
        raise ProviderError('Set a supported vision model before asking about images.')
    if use_openai and model.startswith('gpt-6'):
        inputs=[]
        for m in messages:
            if m.get('_response_output'):
                inputs.extend(m['_response_output'])
            elif m.get('role') == 'tool':
                inputs.append({'type':'function_call_output','call_id':m['tool_call_id'],'output':m['content']})
            else:
                content=m.get('content')
                if isinstance(content,list):
                    content=[{'type':'input_text','text':p['text']} if p['type']=='text' else {'type':'input_image','image_url':p['image_url']['url']} for p in content]
                if content:
                    inputs.append({'role':m['role'],'content':content})
                for call in m.get('tool_calls',[]):
                    inputs.append({'type':'function_call','call_id':call['id'],'name':call['function']['name'],'arguments':call['function']['arguments']})
        payload={'model':model,'input':inputs,'reasoning':{'effort':'medium'},'max_output_tokens':8192,'store':False,'include':['reasoning.encrypted_content']}
        if tools and not vision:
            payload['tools']=[{'type':'function',**t['function'],'strict':False} for t in tools]
            payload['parallel_tool_calls']=False
        if cancel.is_set():
            return None
        result=request('https://api.openai.com/v1/responses',payload,{'Authorization':f'Bearer {key}'},timeout=120)
        if cancel.is_set():
            return None
        if result.get('status') in ('incomplete','failed'):
            raise ProviderError('OpenAI response did not complete. Please narrow the request and retry.')
        output=result.get('output',[])
        content=''.join(p.get('text','') for item in output if item.get('type')=='message' for p in item.get('content',[]) if p.get('type')=='output_text')
        calls=[{'id':item['call_id'],'type':'function','function':{'name':item['name'],'arguments':item['arguments']}} for item in output if item.get('type')=='function_call']
        if content: emit('assistant.delta',{'text':content})
        response={'role':'assistant','content':content or None,'_response_output':output}
        if calls: response['tool_calls']=calls
        return response
    with _cooldown_lock:
        remaining = math.ceil(_cooldowns.get(model, 0) - time.time())
    if remaining > 0:
        error = ProviderError(f'Groq is cooling down. Try again in {remaining} seconds.')
        error.retry_after = remaining
        raise error
    body = {'model': model, 'messages': messages, 'stream': True, 'max_completion_tokens': 1024}
    if use_openai and model.startswith('gpt-6'):
        body.update(reasoning_effort='medium', max_completion_tokens=8192)
    if any(m.get('role') == 'tool' and '"path": "' in str(m.get('content', '')) and ('static/pro.css' in str(m.get('content', '')) or 'personality.txt' in str(m.get('content', ''))) for m in messages):
        body['max_completion_tokens'] = 8192

    if tools and not vision:
        body.update(tools=tools, tool_choice='auto', parallel_tool_calls=False)
    endpoint = 'https://api.openai.com/v1/chat/completions' if use_openai else 'https://api.groq.com/openai/v1/chat/completions'
    # OpenAI's non-streaming response is more resilient on restricted local networks;
    # keep streaming for Groq, while still emitting the completed answer to the UI.
    if use_openai:
        body['stream'] = False
        deadline = time.monotonic() + 120
        def attempt():
            if cancel.is_set():
                return None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProviderError('OpenAI request time limit exceeded.')
            return request(endpoint, body, {'Authorization': f'Bearer {key}'}, timeout=remaining)
        try:
            try:
                result = attempt()
            except ProviderError as first:
                if cancel.is_set():
                    return None
                if 'connection failed' not in str(first).lower() and 'timed out' not in str(first).lower():
                    raise
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProviderError('OpenAI request time limit exceeded.')
                if cancel.wait(min(3, remaining)):
                    return None
                result = attempt()
        except ProviderError as exc:
            if 'HTTP 429' in str(exc):
                exc.retry_after = 30
            raise
        if cancel.is_set():
            return None
        choice = (result.get('choices') or [{}])[0]
        if choice.get('finish_reason') == 'length':
            raise ProviderError('The response reached its token limit. Please narrow the request or split it into smaller steps.')
        message = choice.get('message') or {}
        content = message.get('content') or ''
        if content:
            emit('assistant.delta', {'text': content})
        response = {'role': 'assistant', 'content': content or None}
        if message.get('tool_calls'):
            response['tool_calls'] = message['tool_calls']
        return response
    req = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json', 'User-Agent': 'JarvisLocal/1.0'})
    content, calls = '', {}
    done = False
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            for raw in response:
                if cancel.is_set():
                    return None
                if not raw.startswith(b'data: '):
                    continue
                value = raw[6:].strip()
                if value == b'[DONE]':
                    done = True
                    break
                packet = json.loads(value)
                for choice in packet.get('choices', []):
                    delta = choice.get('delta', {})
                    text = delta.get('content') or ''
                    if text:
                        content += text
                        emit('assistant.delta', {'text': text})
                    for call in delta.get('tool_calls', []):
                        item = calls.setdefault(call['index'], {'id': '', 'type': 'function', 'function': {'name': '', 'arguments': ''}})
                        if call.get('id'):
                            item['id'] = call['id']
                        for field in ('name', 'arguments'):
                            item['function'][field] += call.get('function', {}).get(field, '')
    except urllib.error.HTTPError as exc:
        if exc.code == 429 and not use_openai:
            raise rate_limit(model, exc.headers) from None
        provider = 'OpenAI' if use_openai else 'Groq'
        raise ProviderError(f'{provider} returned HTTP {exc.code}. Check your key, model access, and quota in Settings. No fallback answer was fabricated.') from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise ProviderError('The AI stream failed. Any partial text is incomplete; please retry.') from None
    if not done:
        raise ProviderError('The AI connection ended before completion. Please retry.')
    result = {'role': 'assistant', 'content': content or None}
    if calls:
        result['tool_calls'] = [calls[i] for i in sorted(calls)]
    return result


def gemini_chat(messages, tools, emit, cancel, vision=False):
    """Optional Gemini adapter; results still pass through server evidence/action guards."""
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        raise ProviderError('Gemini is selected. Add GEMINI_API_KEY locally and restart JARVIS.')
    return _compatible_chat('Gemini', 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
                            key, os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'), messages, tools, emit, cancel, vision)


# Alibaba Cloud Model Studio (DashScope), OpenAI-compatible mode. The address depends on
# the account's region; the default is the international (Singapore) endpoint.
QWEN_DEFAULT_BASE = 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1'
QWEN_DEFAULT_MODEL = 'qwen3.8-max'


def qwen_base():
    """Validated DashScope base URL: the key is only ever sent to an Alibaba Cloud host."""
    base = os.getenv('DASHSCOPE_BASE_URL', QWEN_DEFAULT_BASE).strip().rstrip('/')
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme != 'https' or not (parsed.hostname or '').endswith('.aliyuncs.com'):
        raise ProviderError('DASHSCOPE_BASE_URL must be an https://….aliyuncs.com Model Studio address.')
    return base


def qwen_chat(messages, tools, emit, cancel, vision=False):
    """Qwen through Model Studio; results still pass through server evidence/action guards."""
    key = os.getenv('DASHSCOPE_API_KEY')
    if not key:
        raise ProviderError('Qwen is selected. Add DASHSCOPE_API_KEY locally and restart JARVIS.')
    model = os.getenv('QWEN_VISION_MODEL') if vision else os.getenv('QWEN_MODEL', QWEN_DEFAULT_MODEL)
    if not model:
        raise ProviderError('Image understanding needs a Qwen vision model. Authorise one for your key and set QWEN_VISION_MODEL.')
    return _compatible_chat('Qwen', qwen_base() + '/chat/completions', key, model, messages, tools, emit, cancel, vision)


def _compatible_chat(service, endpoint, key, model, messages, tools, emit, cancel, vision):
    """Shared non-streaming OpenAI-compatible adapter (Gemini, Qwen)."""
    if cancel.is_set():
        return None
    # OpenAI Responses metadata is provider-specific; retain ordinary conversation
    # content and tool results when changing provider within an existing session.
    clean = [{k: v for k, v in m.items() if not k.startswith('_')} for m in messages]
    body = {'model': model, 'messages': clean, 'stream': False, 'max_completion_tokens': 8192}
    if tools and not vision:
        body.update(tools=tools, tool_choice='auto')
    result = request(endpoint, body, {'Authorization': f'Bearer {key}'}, timeout=120)
    if cancel.is_set():
        return None
    choice = (result.get('choices') or [{}])[0]
    if choice.get('finish_reason') not in ('stop', 'tool_calls'):
        raise ProviderError(f'{service} did not return a complete response. No partial answer was accepted.')
    message = choice.get('message') or {}
    content = message.get('content') or ''
    calls = message.get('tool_calls') or []
    if not content and not calls:
        raise ProviderError(f'{service} returned no answer or tool request.')
    response = {'role': 'assistant', 'content': content or None}
    if calls:
        response['tool_calls'] = calls
    if content:
        emit('assistant.delta', {'text': content})
    return response


def speech_text(text):
    # Preserve sentence boundaries while removing visual-only formatting.
    text = re.sub(r'```[\s\S]*?```', ' Code is shown on screen. ', text)
    text = re.sub(r'!?\[([^\]]*)\]\([^\n]*?\)', r'\1', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'[`*_#>]+', '', text)
    text = re.sub(r'^\s*(?:[-•]|\d+[.)])\s+', '', text, flags=re.MULTILINE)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = ' '.join(line if re.search(r'[.!?:;]$', line) else line+'.' for line in lines)
    text = re.sub(r'\bMr\.\s*', 'Mister ', text)
    text = re.sub(r'\bMrs\.\s*', 'Missus ', text)
    text = re.sub(r'\b(API|GPS|USB|CPU|AI)\b', lambda m: ' '.join(m[0]), text)
    text = re.sub(r'\bUSD\b', 'US dollars', text)
    text = re.sub(r'\bAUD\b', 'Australian dollars', text)
    text = re.sub(r'(\d)\s*%', r'\1 percent', text)
    text = re.sub(r'(?<=\d)\s*km\b', ' kilometres', text)
    text = re.sub(r'(?<=\d)\s*ms\b', ' milliseconds', text)
    text = re.sub(r'\s+[—–]\s+', ', ', text)
    return re.sub(r'\s+', ' ', text).strip().replace(' :', ':').replace(' ,', ',')


def speech(text, profile='auto'):
    if profile not in ('auto','fish','openai','eleven_flash','eleven_quality'):
        raise ValueError('Unknown voice profile.')
    text = speech_text(text)
    if not text:
        raise ValueError('No spoken text remains after formatting cleanup.')
    if profile == 'openai':
        if not os.getenv('OPENAI_API_KEY'): raise ProviderError('OpenAI speech is not configured.')
        return request('https://api.openai.com/v1/audio/speech', {'model':'gpt-4o-mini-tts','voice':'cedar','input':text[:4000],'response_format':'mp3','instructions':'Speak with a composed British accent, warm understated wit, flowing sentences and natural pauses. Avoid a robotic or theatrical delivery.'}, {'Authorization':'Bearer '+os.environ['OPENAI_API_KEY']},raw=True)
    if profile == 'fish' and not (os.getenv('FISH_API_KEY') and os.getenv('FISH_VOICE_ID')):
        raise ProviderError('Fish Audio key and voice ID are required.')
    if profile in ('auto','fish') and os.getenv('FISH_API_KEY') and os.getenv('FISH_VOICE_ID'):
        return request('https://api.fish.audio/v1/tts', {'text': text[:5000], 'reference_id': os.environ['FISH_VOICE_ID'], 'format': 'mp3', 'mp3_bitrate': 192, 'sample_rate': 44100, 'latency': 'normal', 'normalize': True, 'prosody': {'speed': 1.0, 'volume': 0, 'normalize_loudness': True}, 'chunk_length': 300, 'condition_on_previous_chunks': True}, {'Authorization': 'Bearer ' + os.environ['FISH_API_KEY'], 'model': os.getenv('FISH_MODEL', 's2-pro')}, raw=True)
    key, voice = os.getenv('ELEVENLABS_API_KEY'), os.getenv('ELEVENLABS_VOICE_ID')
    if not key or not voice:
        raise ProviderError('ElevenLabs is not configured. Use the browser voice or add your key and voice ID.')
    model = {'eleven_flash':'eleven_flash_v2_5','eleven_quality':'eleven_multilingual_v2'}.get(profile,os.getenv('ELEVENLABS_MODEL','eleven_flash_v2_5'))
    return request('https://api.elevenlabs.io/v1/text-to-speech/' + urllib.parse.quote(voice, safe=''), {'text': text[:5000], 'model_id': model}, {'xi-api-key': key}, raw=True)


def transcribe(audio, mime):
    use_openai = bool(os.getenv('OPENAI_API_KEY') and os.getenv('JARVIS_PROVIDER', 'groq').lower() == 'openai')
    key = os.getenv('OPENAI_API_KEY') if use_openai else os.getenv('GROQ_API_KEY')
    if not key:
        raise ProviderError('Speech transcription requires a configured AI provider. Browser recognition may be available without it.')
    suffix = {'audio/webm': 'webm', 'audio/ogg': 'ogg', 'audio/mp4': 'mp4', 'audio/wav': 'wav', 'audio/mpeg': 'mp3'}.get(mime.split(';')[0])
    if not suffix:
        raise ValueError('Unsupported recording format.')
    boundary = secrets.token_hex(20)
    model = 'gpt-4o-mini-transcribe' if use_openai else 'whisper-large-v3-turbo'
    data = (f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\n{model}\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="recording.{suffix}"\r\nContent-Type: {mime}\r\n\r\n').encode() + audio + f'\r\n--{boundary}--\r\n'.encode()
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'multipart/form-data; boundary=' + boundary}
    endpoint = 'https://api.openai.com/v1/audio/transcriptions' if use_openai else 'https://api.groq.com/openai/v1/audio/transcriptions'
    try:
        return request(endpoint, data, headers, timeout=60)
    except ProviderError as first:
        if 'timed out' not in str(first).lower() and 'connection failed' not in str(first).lower():
            raise
        time.sleep(2)
        return request(endpoint, data, headers, timeout=60)


class Spotify:
    """PKCE: no client secret. Tokens stay in RAM; reconnect after restart."""
    def __init__(self):
        self.lock = threading.RLock()
        self.pending = None
        self.access = self.refresh = None
        self.expires = 0

    def start(self):
        client = os.getenv('SPOTIFY_CLIENT_ID')
        if not client:
            raise ProviderError('Add SPOTIFY_CLIENT_ID locally first, then restart.')
        verifier, state = secrets.token_urlsafe(64), secrets.token_urlsafe(32)
        with self.lock:
            self.pending = (verifier, state, time.time() + 300)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        return 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode({'client_id': client, 'response_type': 'code', 'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8765/api/spotify/callback'), 'scope': 'user-read-playback-state user-modify-playback-state user-read-currently-playing', 'state': state, 'code_challenge_method': 'S256', 'code_challenge': challenge})

    def token(self, fields):
        return request('https://accounts.spotify.com/api/token', urllib.parse.urlencode(fields).encode(), {'Content-Type': 'application/x-www-form-urlencoded'})

    def callback(self, code, state):
        with self.lock:
            pending, self.pending = self.pending, None
            if not pending or not secrets.compare_digest(state, pending[1]) or time.time() > pending[2]:
                raise ProviderError('Spotify sign-in expired or state did not match. Reconnect from Settings.')
            result = self.token({'grant_type': 'authorization_code', 'code': code, 'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8765/api/spotify/callback'), 'client_id': os.getenv('SPOTIFY_CLIENT_ID'), 'code_verifier': pending[0]})
            self.access, self.refresh = result['access_token'], result.get('refresh_token')
            self.expires = time.time() + result.get('expires_in', 3600)

    def api(self, path, method='GET', data=None):
        with self.lock:
            if not self.access:
                raise ProviderError('Connect Spotify from Settings first. Playback control requires an eligible Spotify account and an active device.')
            if time.time() > self.expires - 30:
                try:
                    tokens = self.token({'grant_type': 'refresh_token', 'refresh_token': self.refresh, 'client_id': os.getenv('SPOTIFY_CLIENT_ID')})
                    self.access = tokens['access_token']
                    self.refresh = tokens.get('refresh_token', self.refresh)
                    self.expires = time.time() + tokens.get('expires_in', 3600)
                except ProviderError:
                    self.access = self.refresh = None
                    raise ProviderError('Spotify session expired. Reconnect from Settings.') from None
            return request('https://api.spotify.com/v1/' + path, data, {'Authorization': 'Bearer ' + self.access}, method)

    def control(self, action, query='', volume=50):
        if action == 'status':
            result = self.api('me/player')
            return {'playing': result.get('is_playing', False), 'track': (result.get('item') or {}).get('name'), 'device': (result.get('device') or {}).get('name')}
        if action == 'play' and query:
            items = self.api('search?' + urllib.parse.urlencode({'q': query, 'type': 'track', 'limit': 10})).get('tracks', {}).get('items', [])
            if not items:
                raise ProviderError('No matching track found.')
            words = set(query.lower().split())
            def score(item):
                name = item['name'].lower()
                artist = ' '.join(a['name'].lower() for a in item['artists'])
                penalty = sum(4 for w in ('karaoke', 'tribute', 'cover', 'remix', 'live') if w in name and w not in words)
                return len(words.intersection((name + ' ' + artist).split())) - penalty
            track = max(items, key=score)
            self.api('me/player/play', 'PUT', {'uris': [track['uri']]})
            return {'track': track['name'], 'status': 'play requested'}
        paths = {'play': ('me/player/play', 'PUT'), 'pause': ('me/player/pause', 'PUT'), 'next': ('me/player/next', 'POST'), 'previous': ('me/player/previous', 'POST'), 'volume': ('me/player/volume?volume_percent=' + str(max(0, min(100, int(volume)))), 'PUT')}
        if action not in paths:
            raise ValueError('Unknown Spotify command.')
        path, method = paths[action]
        self.api(path, method)
        return {'status': action + ' requested'}
