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
import socket
import ssl


class ProviderError(Exception):
    retry_after = 0  # seconds to pause new voice commands (a temporary rate limit only)
    status = None    # the provider's HTTP status, when it answered
    limit = None     # 'rate' (temporary: waiting helps) or 'billing' (credits, quota or bill: it does not)
    service = None   # which provider answered
    unreachable = False  # the provider could not be reached at all (network, DNS, timeout)


AI_PROVIDERS = ('openai', 'qwen', 'openrouter')  # Groq, Gemini and ElevenLabs were removed in 1.0.15 (owner decision 2026-10-05);
# OpenRouter added for the VERONICA merge (owner decision 2026-10-12, docs/VERONICA-MERGE-PLAN.md): one key for every AI job
# except the voice, which stays on Fish Audio. OpenAI and Qwen stay until OpenRouter has passed its live test.
AI_KEYS = {'openai': 'OPENAI_API_KEY', 'qwen': 'DASHSCOPE_API_KEY', 'openrouter': 'OPENROUTER_API_KEY'}
VOICE_PROFILES = ('auto', 'fish', 'openai', 'qwen')
ANSWER_MODES = ('auto', 'deep', 'economy')  # Settings > Answer speed; see qwen_plan()
# What 1.0.14 did (Qwen thinks before every answer), until the owner chooses another default.
DEFAULT_ANSWER_MODE = 'deep'


def provider():
    """The chat provider named by JARVIS_PROVIDER; OpenAI when the line is missing."""
    return os.getenv('JARVIS_PROVIDER', '').strip().lower() or 'openai'


def unsupported_error():
    return ProviderError(f'JARVIS_PROVIDER={provider()} is not supported. Set JARVIS_PROVIDER=openrouter, openai or qwen in your local .env and restart JARVIS.')


def any_ai_key():
    """True when the key of any supported AI provider is in place; without one the Core answers in local command mode."""
    return any(os.getenv(name) for name in AI_KEYS.values())


def chosen_key():
    """The chosen provider's key, or None."""
    name = AI_KEYS.get(provider())
    return (os.getenv(name) or None) if name else None


_ERROR_CODE = re.compile(r'[A-Za-z0-9_.-]{1,64}')


def _error_fields(exc):
    """The provider's machine-readable error code and type, if present: a bounded read, and only
    values that look like codes. Best effort: a broken or cut-off body only loses the code."""
    try:
        body = json.loads(exc.read(4096) or b'{}')
        if isinstance(body, list):
            body = body[0] if body and isinstance(body[0], dict) else {}
        error = body.get('error') if isinstance(body, dict) and isinstance(body.get('error'), dict) else body
        if not isinstance(error, dict):
            return None, None
        return tuple(value if isinstance(value, str) and _ERROR_CODE.fullmatch(value) else None
                     for value in (error.get('code'), error.get('type')))
    except Exception:
        return None, None


# HTTP 429 codes the providers document as quota, credit or billing problems (checked 2026-10-04).
# The same word differs per provider: OpenAI's insufficient_quota means no credits; Qwen's is a
# per-minute throttle.
_BILLING_429 = {
    'OpenAI': {'insufficient_quota': 'The OpenAI account has no API credits left',
               'credit_balance_exhausted': 'The OpenAI account has no API credits left',
               'organization_spend_limit_exceeded': 'The OpenAI organisation reached its spend limit',
               'project_spend_limit_exceeded': 'The OpenAI project reached its spend limit',
               'organization_usage_limit_exceeded': 'The OpenAI organisation reached its usage limit'},
    'Qwen': {'PrepaidBillOverdue': 'The Alibaba Cloud account has an overdue prepaid bill',
             'PostpaidBillOverdue': 'The Alibaba Cloud account has an overdue bill',
             'BudgetLimitExceeded': 'The Alibaba Cloud budget limit is used up',
             'CommodityNotPurchased': 'The Alibaba Cloud workspace has not purchased this model'},
}
_BILLING_ACTION = {'OpenAI': 'add credits or raise the limit under Billing in the OpenAI dashboard, or choose another provider',
                   'Qwen': 'resolve it in the Alibaba Cloud console, then retry'}
_RATE_429 = {'OpenAI': {'rate_limit_exceeded', 'slow_down'},
             'Qwen': {'Throttling', 'Throttling.RateQuota', 'LimitRequests', 'limit_requests', 'Throttling.BurstRate',
                      'limit_burst_rate', 'Throttling.AllocationQuota', 'insufficient_quota',
                      'Throttling.ServiceOverloaded', 'Throttling.ResourceExhausted'}}
_PLAN_SERVICES = ('OpenAI', 'Qwen', 'OpenRouter', 'SerpApi', 'Brave Search', 'Fish Audio')
_STATUS_LABELS = {400: 'Request rejected. Check model and integration settings.', 401: 'Authentication failed. Check your local credentials.', 403: 'Access denied. Check account permissions and subscription.', 404: 'Resource or model not found.'}
FISH_402 = 'Insufficient API credit. Fish Audio API credit is separate from website credit; add API credit in the Fish developer dashboard.'
# OpenRouter answers 402 when the credit is used up, and for spoken requests below US$0.50 of credit (function test, 2026-10-12).
OPENROUTER_402 = ('OpenRouter has no credit for this request: the credit left is less than this request could cost at most. '
                  'Add credit at openrouter.ai (Settings > Credits); spoken requests need at least US$0.50 left.')


def _http_error(prefix, service, exc):
    """The provider's refusal in our own words. Never the raw upstream body (it can contain
    sensitive data): only documented, allow-listed codes are used or shown."""
    status = exc.code
    code, kind = _error_fields(exc) if service == 'Qwen' or (service == 'OpenAI' and status == 429) else (None, None)
    label, limit, tail = _STATUS_LABELS.get(status, 'The provider could not complete the request.'), None, f'HTTP {status}'
    if service == 'Qwen' and code == 'Arrearage':
        label, limit = 'Alibaba Cloud refused access: the account balance is overdue or empty. Top up in Alibaba Cloud Billing, then retry.', 'billing'
    elif service == 'Qwen' and code == 'AccessDenied.Unpurchased':
        # Seen on the owner's account on 2026-10-05; the cause there was an unpaid bill, not a missing purchase.
        label, limit = ('Alibaba Cloud refused access to this model. Either the model is not activated for the account in Model Studio, '
                        'or an unpaid bill blocks it. Waiting will not help: check Model Studio and Billing in the Alibaba Cloud console, then retry.'), 'billing'
        tail = f'HTTP {status}, {code}'
    elif status == 413:
        # Seen on 2026-10-05 from a free plan whose limit per minute was smaller than one JARVIS question.
        label = ('The request is larger than this provider or plan accepts at once. Waiting will not help: '
                 'use a plan or model with a higher limit, or ask with a shorter question or a smaller attachment.')
    elif status == 429:
        billing = _BILLING_429.get(service, {})
        if code in billing or (service == 'OpenAI' and kind == 'insufficient_quota'):
            reason = billing.get(code, 'OpenAI reports a billing or quota limit on this account')
            label = f'{reason}. This is a billing limit, not a short rate limit, so waiting will not help: {_BILLING_ACTION[service]}. No keys were rotated.'
            limit, tail = 'billing', f'HTTP 429, {code}' if code in billing else 'HTTP 429, type insufficient_quota'
        else:
            limit = 'rate'
            if code in _RATE_429.get(service, ()) or kind == 'rate_limit_error':
                label = 'Rate limit reached (temporary). Wait a little, then retry. No keys were rotated.'
            elif service in _PLAN_SERVICES:
                label = f'Rate limit or usage quota reached. Wait a little, then retry; if it keeps happening, check the {service} plan, usage limits and billing. No keys were rotated.'
            else:
                label = 'Rate limit reached. Wait before retrying; no keys were rotated.'
    elif status == 402:
        limit = 'billing'
        label = (FISH_402 if service == 'Fish Audio' else OPENROUTER_402 if service == 'OpenRouter' else
                 'Payment required: the account has no credit for this request. Check its billing.')
    error = ProviderError(f'{prefix}{label} ({tail})')
    error.status, error.limit, error.service = status, limit, service
    return error


class _KeysStayPut(urllib.request.HTTPRedirectHandler):
    """A request that carries a key is never sent on to another address: a redirect answer ends it instead.
    (urllib would repeat the request, key included, at whatever address the answer names.) Requests without a
    key, such as fetching a finished sound or a picture, follow redirects as before."""
    KEY_HEADERS = frozenset(('authorization', 'x-subscription-token', 'x-goog-api-key', 'api-key', 'x-api-key'))

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if any(name.lower() in self.KEY_HEADERS for name in list(req.headers) + list(req.unredirected_hdrs)):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


urllib.request.install_opener(urllib.request.build_opener(_KeysStayPut))


def request(url, data=None, headers=None, method=None, raw=False, timeout=35, operation=None):
    host = urllib.parse.urlparse(url).hostname
    service = {'api.openai.com': 'OpenAI', 'api.fish.audio': 'Fish Audio', 'serpapi.com': 'SerpApi', 'api.search.brave.com': 'Brave Search',
               'openrouter.ai': 'OpenRouter'}.get(host, 'External service')
    if (host or '').endswith('.aliyuncs.com'):
        service = 'Qwen'
    path = urllib.parse.urlparse(url).path
    operation = operation or ('transcription' if 'transcriptions' in path else 'voice synthesis' if 'tts' in path else 'chat' if 'completions' in path or path.endswith('/responses') else 'request')
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
        raise _http_error(prefix, service, exc) from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise _unreachable(prefix, service, exc) from None
    except ValueError:
        raise ProviderError(prefix + 'Invalid response received from provider.') from None


def _unreachable(prefix, service, exc):
    """The provider could not be reached at all: one error in our own words, marked as such (the backup provider
    and the offline answer are for exactly this case)."""
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
    error = ProviderError(prefix + detail)
    error.unreachable, error.service = True, service
    return error


def capabilities(mode=None):
    """What is configured. mode is the saved answer mode (Settings > Answer speed): with Qwen the
    model named here is the one that answers in that mode, so labels and checks match the answers."""
    result = _base_capabilities()
    if provider() == 'qwen':
        configured = bool(os.getenv('DASHSCOPE_API_KEY'))
        result.update(brain='Qwen configured' if configured else 'Qwen not configured',
                      model=qwen_plan(mode)[0],
                      vision_provider='Qwen', vision=configured and bool(os.getenv('QWEN_VISION_MODEL')))
    elif provider() == 'openrouter':
        configured = bool(os.getenv('OPENROUTER_API_KEY'))
        # The main model takes pictures too (qwen/qwen3.8-max-0902: text, image and video in; model list of 2026-10-12).
        result.update(brain='OpenRouter configured' if configured else 'OpenRouter not configured',
                      model=openrouter_plan(mode)[0], vision_provider='OpenRouter', vision=configured)
    elif provider() == 'openai':
        configured = bool(os.getenv('OPENAI_API_KEY'))
        # No AI key at all: the server answers in local command mode (server.py).
        result.update(brain='OpenAI configured' if configured else 'OpenAI not configured' if any_ai_key() else 'local commands',
                      model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'), vision_provider='OpenAI',
                      vision=configured and bool(os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini')))
    else:
        result.update(brain=f'Unsupported provider {provider()}: use openrouter, openai or qwen', model=None, vision_provider=None, vision=False)
    result['backup'] = PROVIDER_NAMES.get(backup_provider())  # which provider could stand in, or None
    if provider() == 'openrouter' and os.getenv('OPENROUTER_API_KEY'):
        # With OpenRouter the stand-in is its own backup model (plan D8), used only while Settings > AI > Backup is on.
        fallback = openrouter_fallback(result['model'] or '')
        result['backup'] = f"OpenRouter's backup model ({fallback})" if fallback else None
    return result


def _base_capabilities():
    return {
        # Speech recognition in the cloud is done by the chosen AI provider (cloud_speech below); the app's own
        # default is local recognition, which needs neither.
        'transcription': cloud_speech() is not None,
        'transcription_provider': PROVIDER_NAMES.get(cloud_speech()),
        'fish': bool(os.getenv('FISH_API_KEY') and os.getenv('FISH_VOICE_ID')),
        'qwen_voice': qwen_voice_configured(),
        # OpenAI speech needs only the OpenAI key, whichever provider does the thinking (speech() below).
        'openai_voice': bool(os.getenv('OPENAI_API_KEY')),
        'voice_provider': 'qwen' if qwen_voice_configured() else 'fish' if os.getenv('FISH_API_KEY') and os.getenv('FISH_VOICE_ID') else 'browser',
        'search': ('OpenRouter web search' if provider() == 'openrouter' and os.getenv('OPENROUTER_API_KEY') else  # plan D6
                   'SerpApi configured' if os.getenv('SERPAPI_API_KEY') else 'Brave configured' if os.getenv('BRAVE_API_KEY') else 'DuckDuckGo best effort'),
        'youtube': bool(os.getenv('YOUTUBE_API_KEY')),
        'spotify': bool(os.getenv('SPOTIFY_CLIENT_ID')),
    }

def live_health(mode=None):
    checks = {}
    targets = []
    caps = capabilities(mode)
    use_qwen = provider() == 'qwen'
    use_openrouter = provider() == 'openrouter'
    key = chosen_key()
    if provider() not in AI_PROVIDERS:
        checks['Chat model access'] = {'status': 'not_configured', 'detail': str(unsupported_error())}
    elif key and use_openrouter:
        # OpenRouter's key route proves the key without paying for an answer.
        started = time.perf_counter()
        try:
            data = request(OPENROUTER_BASE + '/key', headers={'Authorization': 'Bearer ' + key}, timeout=15)
            valid = isinstance(data.get('data'), dict)
            checks['Chat model access'] = {'status': 'reachable' if valid else 'unexpected_response',
                                           'latency_ms': round((time.perf_counter()-started)*1000),
                                           'detail': 'OpenRouter accepted the key; generation not tested.' if valid else 'OpenRouter returned an unexpected response.'}
        except ProviderError as exc:
            checks['Chat model access'] = {'status': 'unavailable', 'latency_ms': round((time.perf_counter()-started)*1000), 'detail': str(exc)}
    elif key and use_qwen:
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
        targets.append(('Chat model access', 'https://api.openai.com/v1/models/' + urllib.parse.quote(caps['model'], safe=''), {'Authorization': 'Bearer ' + key}))
    else:
        checks['Chat model access'] = {'status':'not_configured','detail':'Add a chat provider key locally.'}
    if use_openrouter and key:
        # Each search is paid for, so the health check does not run one (Settings > Connections > Search does).
        checks['Web search'] = {'status': 'configured', 'detail': 'OpenRouter web search (about US$0.007 a search); not run by this check. Use the search connection test.'}
    elif os.getenv('BRAVE_API_KEY'):
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


PROVIDER_NAMES = {'openai': 'OpenAI', 'qwen': 'Qwen', 'openrouter': 'OpenRouter'}
# The line the Core adds to a reply written by the backup provider, or by OpenRouter's backup model (fallback_note).
# The same pattern removes it from what goes back to a model and from anything a model writes, so that only the Core
# can say it.
BACKUP_OPENING = re.compile(r'\[\s*(?:OpenAI|Qwen|OpenRouter)\s+answered\b', re.I)
# Any bracketed line that starts like one of the Core's notes goes, however a model words the rest (review of 2026-10-12, L4).
BACKUP_NOTE = re.compile(r'\s*\[\s*(?:OpenAI|Qwen|OpenRouter)\s+(?:answered|had\s+taken\s+over)\b[^\]]{0,400}\]', re.I)


def backup_provider(vision=False):
    """The other AI provider, when its key is in place and it can take this kind of request, else
    None. The Core uses it only when the owner has switched the backup on (Settings) and the
    chosen provider has failed on a question in which no tool has run yet."""
    chosen = provider()
    if chosen == 'qwen' and os.getenv('OPENAI_API_KEY') and (not vision or os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini')):
        return 'openai'
    if chosen == 'openai' and os.getenv('DASHSCOPE_API_KEY') and (not vision or os.getenv('QWEN_VISION_MODEL')):
        return 'qwen'
    return None


def backup_worthy(error):
    """True when the chosen provider itself refused the request (it answered with an HTTP error)
    or could not be reached. A missing key or picture model, or an answer that came back cut short,
    is not: the owner should see those, not pay a second provider because of them."""
    return getattr(error, 'status', None) is not None or bool(getattr(error, 'unreachable', False))


def first_sentence(error):
    """The first sentence of one of our own error texts, without square brackets, for a short note."""
    return re.split(r'(?<=[.!?])\s', str(error).strip(), maxsplit=1)[0].replace('[', '(').replace(']', ')')[:200]


def backup_note(backup, error):
    """Who answered instead of the chosen provider, and the first sentence of why."""
    chosen = PROVIDER_NAMES.get(provider(), provider())
    return f'[{PROVIDER_NAMES[backup]} answered this question because {chosen} could not. {first_sentence(error)}]'


def chat(messages, tools, emit, cancel, vision=False, mode=None, text='', use=None, stream=False, max_tokens=None, job='chat', fallback=False):
    """One model request. mode (Settings > Answer speed; None means the default) and text (the
    user's own words) steer Qwen and OpenRouter: see qwen_plan() and openrouter_plan(). use names the provider for
    this one request when it is not the chosen one (the backup, see backup_provider()). stream: ask for the
    answer in pieces (Qwen and OpenRouter; each piece is handed to emit as 'assistant.piece'). max_tokens: a larger
    reply budget for the OpenAI and OpenRouter paths (a workshop mission writes whole files in one reply; docs/WORKSHOP.md).
    job: 'coding' for a workshop mission, which OpenRouter gives to the coding model (plan D2); the others ignore it.
    fallback: True only when Settings > AI > Backup is on and OpenRouter is chosen, so that OpenRouter may try its backup
    model (plan D8). It is off by default, so a caller that does not opt in never sends anything to the backup model's
    company (App.fallback_option carries the owner's switch; others ignore the flag)."""
    if cancel.is_set():
        return None
    chosen = use or provider()
    if chosen == 'openrouter':
        return openrouter_chat(messages, tools, emit, cancel, vision, mode, text, stream, max_tokens, job, fallback)
    if chosen == 'qwen':
        return qwen_chat(messages, tools, emit, cancel, vision, mode, text, stream)
    if chosen != 'openai':
        raise unsupported_error()
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        hint = ' Your key file has an OpenRouter key: set JARVIS_PROVIDER=openrouter to use it.' if os.getenv('OPENROUTER_API_KEY') else ''
        raise ProviderError('OpenAI is selected. Add OPENAI_API_KEY locally and restart JARVIS.' + hint)
    model = os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini') if vision else os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    if not model:
        raise ProviderError('Set a supported vision model before asking about images.')
    if model.startswith('gpt-6'):
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
    body = {'model': model, 'messages': messages, 'stream': False, 'max_completion_tokens': 1024}
    if any(m.get('role') == 'tool' and '"path": "' in str(m.get('content', '')) and ('static/pro.css' in str(m.get('content', '')) or 'personality.txt' in str(m.get('content', ''))) for m in messages):
        body['max_completion_tokens'] = 8192

    if tools and not vision:
        body.update(tools=tools, tool_choice='auto', parallel_tool_calls=False)
    endpoint = 'https://api.openai.com/v1/chat/completions'
    # OpenAI's non-streaming response is more resilient on restricted local networks;
    # the completed answer is still emitted to the UI.
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
                # The time ran out on a provider that could not be reached: that is still "could not be reached"
                # (the backup provider and the offline answer are for exactly this).
                late = ProviderError('OpenAI request time limit exceeded.')
                late.unreachable, late.service = bool(getattr(first, 'unreachable', False)), 'OpenAI'
                raise late
            if cancel.wait(min(3, remaining)):
                return None
            result = attempt()
    except ProviderError as exc:
        if 'HTTP 429' in str(exc) and exc.limit != 'billing':  # no credits: waiting will not help
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


# Qwen 3.8 models think before every answer unless told not to (Alibaba's default). Measured on
# the owner's account on 2026-10-05 with a full JARVIS request: a 150-word answer took 11.9 s with
# thinking and 5.8 s without (docs/CAPABILITY-PLAN.md section 3). These words in the user's own
# message ask for a considered answer; in every mode they get the main model with thinking on.
QWEN_FAST_MODEL = 'qwen3.8-flash'
# "enable_thinking": false together with an image was accepted on the owner's account on 2026-10-05
# (Test-AiSpeed picture run, qwen3.8-max: 5.6 s against 7.1 s with thinking). False restores the
# request 1.0.14 sent for pictures, should another vision model refuse the field; so does Deep.
QWEN_PICTURES_WITHOUT_THINKING = True
_DEPTH_REQUEST = re.compile(
    r'\b(?:think(?:ing)?\s+(?:(?:very|really|real|extra|more|long\s+and)\s+)?'
    r'(?:hard(?!\s+(?:drive|disk|work)s?\b)|harder|carefully|deeply|(?:it|this|that)\s+through|step[\s-]by[\s-]step)'
    r'|think\s+about\s+(?:it|this|that)\s+(?:(?:very|really|more)\s+)?(?:carefully|hard|deeply)'
    r'|take\s+your\s+time(?!\s+off\b)|deep[\s-](?:dive|analysis)\s+(?:into|on|of)'
    r'|reason\s+(?:carefully|step[\s-]by[\s-]step))\b', re.I)
# "don't think hard about it, just answer": the words just before a match can turn it around.
_DEPTH_DECLINED = re.compile(r"(?:\b(?:don'?t|do\s+not|no\s+need\s+to|needn'?t|without|never|not)\s+(?:\w+\s+){0,2})$", re.I)


def wants_depth(text):
    """True when the user's own words ask JARVIS to think first ("think hard about ..."). A miss
    costs a quicker answer and a false hit a slower one; neither changes what JARVIS may do."""
    text = text or ''
    return any(not _DEPTH_DECLINED.search(text[max(0, match.start() - 40):match.start()])
               for match in _DEPTH_REQUEST.finditer(text))


def qwen_plan(mode=None, text='', vision=False):
    """Which Qwen model answers and whether it thinks first: (model, thinking).
    deep (the default, also for None or an unknown mode): the main model, thinking before every
        answer, which is what 1.0.14 and older always did.
    auto: the main model without thinking.
    economy: the cheaper fast model without thinking, for everything except pictures.
    A request for depth in the user's own words gets the main model with thinking in every mode."""
    main = os.getenv('QWEN_VISION_MODEL') if vision else os.getenv('QWEN_MODEL', QWEN_DEFAULT_MODEL)
    if mode not in ANSWER_MODES:
        mode = DEFAULT_ANSWER_MODE
    if mode == 'deep' or wants_depth(text) or (vision and not QWEN_PICTURES_WITHOUT_THINKING):
        return main, True
    if mode == 'economy' and not vision:
        return os.getenv('QWEN_FAST_MODEL') or QWEN_FAST_MODEL, False
    return main, False


def chat_options(mode, text):
    """Keyword arguments for chat() that carry the saved answer mode and the user's own words.
    Empty when they would change nothing, so that the Core's everyday call to chat() keeps its
    five arguments (test doubles and the Stage 4 harness replace chat() with that shape)."""
    mode = mode if mode in ANSWER_MODES else DEFAULT_ANSWER_MODE
    depth = wants_depth(text)
    # With Qwen, Deep already thinks before every answer; with OpenRouter, "think hard" asks for more than Deep does
    # (openrouter_plan), so the words must reach it (review of 2026-10-12, M1).
    if mode == DEFAULT_ANSWER_MODE and (not depth or (mode == 'deep' and provider() != 'openrouter')):
        return {}
    return {'mode': mode, 'text': text}


def qwen_chat(messages, tools, emit, cancel, vision=False, mode=None, text='', stream=False):
    """Qwen through Model Studio; results still pass through server evidence/action guards."""
    key = os.getenv('DASHSCOPE_API_KEY')
    if not key:
        raise ProviderError('Qwen is selected. Add DASHSCOPE_API_KEY locally and restart JARVIS.')
    model, thinking = qwen_plan(mode, text, vision)
    if not model:
        raise ProviderError('Image understanding needs a Qwen vision model. Authorise one for your key and set QWEN_VISION_MODEL.')
    return _compatible_chat('Qwen', qwen_base() + '/chat/completions', key, model, messages, tools, emit, cancel, vision, thinking, stream)


# OpenRouter (owner decision 2026-10-12, docs/VERONICA-MERGE-PLAN.md): OpenAI-compatible, one key for every AI job except
# the voice. The address is fixed, so the key is only ever sent to openrouter.ai. Model names as OpenRouter's model list
# gave them on 2026-10-12; each can be changed in the key file. Qwen only (owner, 2026-10-13: "can we make it only use
# qwen models for all the functions?"), to match a Qwen-only guardrail on the key.
OPENROUTER_BASE = 'https://openrouter.ai/api/v1'
OPENROUTER_DEFAULT_MODEL = 'qwen/qwen3.8-max-0902'             # everyday chat, tools, pictures (plan D2)
OPENROUTER_DEFAULT_FAST_MODEL = 'qwen/qwen3.8-flash'           # Economy, and the small request behind a web search
OPENROUTER_DEFAULT_CODING_MODEL = 'qwen/qwen3.8-max-0902'      # coding and research jobs (plan D2, Qwen since 2026-10-13)
OPENROUTER_DEFAULT_FALLBACK_MODEL = 'qwen/qwen3.8-flash'       # OpenRouter tries it when the first model fails (plan D8)
# The cloud option for hearing (plan D7): none by default, as OpenRouter's speech-to-text models are not Qwen; this PC's
# own recognition does the hearing. An OPENROUTER_STT_MODEL line (e.g. openai/whisper-1) turns the cloud option on.
OPENROUTER_DEFAULT_STT_MODEL = ''
# Thinking counts against the reply limit on OpenRouter: with a small limit the owner's function test of 2026-10-12 got a
# cut-off answer ("TEAG") and an empty one. The limit is a ceiling, not a charge, but OpenRouter refuses (402) when the credit
# left could not pay for a reply that long: about US$0.10 with Qwen 3.8 Max, US$0.33 with Claude Opus (review of 2026-10-12, L1).
OPENROUTER_REPLY_TOKENS = 16384
# How hard the model thinks (OpenRouter's reasoning "effort"). Qwen 3.8 Max always thinks on OpenRouter ("mandatory",
# default effort "xhigh", model list of 2026-10-12), so Auto asks for the least; "none" is sent only to the fast model,
# whose thinking can be switched off.
OPENROUTER_EFFORT = {'depth': 'high', 'deep': 'medium', 'auto': 'minimal', 'economy': 'none'}
OPENROUTER_SEARCH_RESULTS = 5
OPENROUTER_AUDIO_FORMATS = {'audio/wav': 'wav', 'audio/mpeg': 'mp3', 'audio/webm': 'webm', 'audio/ogg': 'ogg', 'audio/mp4': 'm4a'}
OPENROUTER_AUDIO_LIMIT = 20 * 1024 * 1024
_MODEL_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,95}')


def openrouter_plan(mode=None, text='', vision=False, job='chat'):
    """Which model answers through OpenRouter and how hard it thinks: (model, effort or None).
    coding: the coding model with its own default thinking.
    Otherwise as qwen_plan(): a request for depth in the user's own words gets the main model thinking hard;
    deep (the default): the main model, medium thinking; auto: the main model, minimal thinking;
    economy: the fast model without thinking, for everything except pictures."""
    if job == 'coding':
        return os.getenv('OPENROUTER_CODING_MODEL') or OPENROUTER_DEFAULT_CODING_MODEL, None
    main = os.getenv('OPENROUTER_MODEL') or OPENROUTER_DEFAULT_MODEL
    if vision:
        main = os.getenv('OPENROUTER_VISION_MODEL') or main
    if mode not in ANSWER_MODES:
        mode = DEFAULT_ANSWER_MODE
    if wants_depth(text):
        return main, OPENROUTER_EFFORT['depth']
    if mode == 'economy' and not vision:
        return os.getenv('OPENROUTER_FAST_MODEL') or OPENROUTER_DEFAULT_FAST_MODEL, OPENROUTER_EFFORT['economy']
    return main, OPENROUTER_EFFORT['deep' if mode == 'deep' else 'auto']


def openrouter_fallback(model):
    """The model OpenRouter tries when the first one fails (plan D8), or None: OPENROUTER_FALLBACK_MODEL, empty to turn
    it off. Never the same as the first."""
    fallback = os.getenv('OPENROUTER_FALLBACK_MODEL', OPENROUTER_DEFAULT_FALLBACK_MODEL).strip()
    return fallback if fallback and fallback != model else None


def openrouter_chat(messages, tools, emit, cancel, vision=False, mode=None, text='', stream=False, max_tokens=None, job='chat', fallback=False):
    """One request through OpenRouter; results still pass through the server's evidence and action guards. fallback is
    off unless the caller opts in, so nothing goes to the backup model's company unless Settings > AI > Backup is on."""
    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        raise ProviderError('OpenRouter is selected. Add OPENROUTER_API_KEY locally and restart JARVIS.')
    model, effort = openrouter_plan(mode, text, vision, job)
    extra = {'max_tokens': max(int(max_tokens or 0), OPENROUTER_REPLY_TOKENS)}
    if effort:
        extra['reasoning'] = {'effort': effort, 'exclude': True}  # the thinking itself is not sent back
    second = openrouter_fallback(model) if fallback else None
    if second:
        extra['models'] = [model, second]
    try:
        return _compatible_chat('OpenRouter', OPENROUTER_BASE + '/chat/completions', key, model, messages, tools, emit, cancel,
                                vision, stream=stream, dialect='openrouter', extra=extra)
    except ProviderError as exc:
        if exc.status == 429 and exc.limit != 'billing':  # a short rate limit: new voice commands pause, as with OpenAI
            exc.retry_after = 30
        raise


def is_fallback(answered_by, asked, fallback):
    """True when OpenRouter's answer names its backup model rather than the model asked for (plan D8). OpenRouter may name
    a model by a longer or canonical slug (a date, a different word order), so: a name that starts with one of the two
    belongs to it, the longer match winning when one name starts with the other; a name that starts with neither belongs
    to the backup model when it comes from the backup model's maker and not the first model's (review of 2026-10-12, M2)."""
    if not (isinstance(answered_by, str) and answered_by and fallback):
        return False
    of_asked, of_fallback = answered_by.startswith(asked), answered_by.startswith(fallback)
    if of_asked and of_fallback:
        return len(fallback) > len(asked)
    if of_asked or of_fallback:
        return of_fallback
    maker = lambda name: name.split('/', 1)[0].lower()
    return maker(answered_by) == maker(fallback) != maker(asked)


def model_label(name):
    """A model name from OpenRouter's answer, as text fit for a note (or 'another model')."""
    return name if isinstance(name, str) and _MODEL_NAME.fullmatch(name) else 'another model'


def fallback_note(response):
    """The line the Core adds when OpenRouter's backup model wrote the answer (plan D8), or None."""
    used = response.get('_fallback') if isinstance(response, dict) else None
    if not isinstance(used, dict):
        return None
    return (f"[OpenRouter answered this question with its backup model ({model_label(used.get('used'))}) "
            f"because {model_label(used.get('asked'))} could not answer it.]")


def openrouter_search(query, count=OPENROUTER_SEARCH_RESULTS):
    """Web search through OpenRouter's web plugin (plan D6, in place of Brave): one small request to the fast model with
    the plugin on, its thinking off. The pages found come back as citations, which become the results (title, address,
    excerpt). About US$0.007 a search (OpenRouter's price for its default engine, read 2026-10-12)."""
    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        raise ProviderError('OpenRouter web search needs OPENROUTER_API_KEY.')
    body = {'model': os.getenv('OPENROUTER_FAST_MODEL') or OPENROUTER_DEFAULT_FAST_MODEL,
            'messages': [{'role': 'user', 'content': 'Search the web for: ' + query + '\nAnswer in one short sentence.'}],
            'plugins': [{'id': 'web', 'max_results': count}], 'max_tokens': 600, 'reasoning': {'effort': 'none'}}
    result = request(OPENROUTER_BASE + '/chat/completions', body, {'Authorization': 'Bearer ' + key}, timeout=60, operation='web search')
    choices = result.get('choices') if isinstance(result, dict) else None
    message = choices[0].get('message') if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
    notes = message.get('annotations') if isinstance(message, dict) else None
    items, seen = [], set()
    for note in notes if isinstance(notes, list) else []:
        cite = note.get('url_citation') if isinstance(note, dict) and note.get('type') == 'url_citation' else None
        url = cite.get('url') if isinstance(cite, dict) else None
        if not _web_address(url) or url in seen:
            continue
        seen.add(url)
        title = cite.get('title') if isinstance(cite.get('title'), str) and cite['title'].strip() else url
        content = cite.get('content') if isinstance(cite.get('content'), str) else ''
        items.append({'title': ' '.join(title.split())[:300], 'url': url, 'description': ' '.join(content.split())[:500]})
        if len(items) >= count:
            break
    return items


def _web_address(url):
    """A web page address fit to show and to open: http(s), a host, at most 2,048 characters, no spaces or control
    characters (search results are other people's text; review of 2026-10-12, L2)."""
    if not isinstance(url, str) or len(url) > 2048 or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.hostname)
    except ValueError:
        return False


def openrouter_stt_model():
    """The model for OpenRouter's speech-to-text, or '' when the cloud option for hearing is off (the default)."""
    return (os.getenv('OPENROUTER_STT_MODEL') or OPENROUTER_DEFAULT_STT_MODEL).strip()


def openrouter_transcribe(audio, mime, timeout=60):
    """Speech to text through OpenRouter (plan D7, the cloud option; the app's own default is local recognition). The
    request is OpenRouter's documented one: base64 audio with its format in JSON, not a file upload."""
    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        raise ProviderError('OpenRouter speech recognition needs OPENROUTER_API_KEY. Local recognition works without it.')
    model = openrouter_stt_model()
    if not model:
        raise ProviderError('OpenRouter speech recognition has no model: add an OPENROUTER_STT_MODEL line to use it. Local recognition works without it.')
    fmt = OPENROUTER_AUDIO_FORMATS.get(mime.split(';')[0])
    if not fmt:
        raise ValueError('Unsupported recording format.')
    if len(audio) > OPENROUTER_AUDIO_LIMIT:
        raise ValueError('The recording is too large for cloud speech recognition (20 MB).')
    body = {'model': model, 'input_audio': {'data': base64.b64encode(audio).decode('ascii'), 'format': fmt}}
    language = os.getenv('OPENROUTER_STT_LANGUAGE', 'en').strip()
    if language:  # an empty OPENROUTER_STT_LANGUAGE line lets the model detect the language
        body['language'] = language
    result = request(OPENROUTER_BASE + '/audio/transcriptions', body, {'Authorization': f'Bearer {key}'}, timeout=timeout, operation='speech recognition')
    if not isinstance(result, dict) or not isinstance(result.get('text'), str):
        raise ProviderError('OpenRouter speech recognition: no text in the answer.')
    return {'text': result['text'].strip()}


STREAM_QUIET_SECONDS = 60   # a streamed answer that sends nothing for this long is given up
STREAM_TOTAL_SECONDS = 120  # and so is one that is still going after this long
STREAM_MOST_BYTES = 16 * 1024 * 1024  # or one that grows past what request() accepts as a complete answer


def cut_connection(sock):
    """Ends a connection that another thread is waiting on, so that the thread wakes at once. shutdown() wakes it on
    most systems; on Windows only closing the socket itself does (seen on this PC over a real local connection), and
    the socket is taken from its Python object first so that nothing closes the same handle twice."""
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    try:
        socket.close(sock.detach())
    except Exception:
        pass


def _end_stream(response, cancel, deadline, done):
    """Ends a streamed answer from outside its reader: at once when the owner presses Stop, and when the total
    time is up. (The reader may be waiting for the provider's next bytes, where it can look at neither.)"""
    while not done.is_set():
        if cancel.is_set() or time.monotonic() > deadline:
            try:
                cut_connection(response.fp.raw._sock)
            except Exception:
                try:
                    response.close()
                except Exception:
                    pass
            return
        time.sleep(0.1)


def _compatible_stream(service, endpoint, key, body, emit, cancel):
    """The same request with "stream": true (OpenAI-compatible server-sent events). Each piece of the answer's
    text is handed to emit('assistant.piece', {'text': piece}) as it arrives; a model's thinking is not.
    Returns (text, tool calls, finish reason, the model that answered as the stream named it), or None when cancelled. A stream that breaks raises a
    ProviderError that says "stream failed": no partial answer is ever accepted, and the Core then asks again
    the old way, in one piece. A stream still going when the total time is up ends as the one-piece request
    does after that time ("timed out", could not be reached): asking again could not succeed either."""
    prefix = f'{service} chat: '
    payload = json.dumps({**body, 'stream': True}).encode()
    req = urllib.request.Request(endpoint, data=payload, headers={'User-Agent': 'JarvisLocal/1.0', 'Authorization': f'Bearer {key}',
                                                                   'Content-Type': 'application/json', 'Accept': 'text/event-stream'})
    try:
        response = urllib.request.urlopen(req, timeout=STREAM_QUIET_SECONDS)
    except urllib.error.HTTPError as exc:
        raise _http_error(prefix, service, exc) from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise _unreachable(prefix, service, exc) from None
    broken = ProviderError(prefix + 'Stream failed before the answer was complete. No partial answer was accepted.')
    text, calls, finish, size, deadline, answered_by = [], {}, None, 0, time.monotonic() + STREAM_TOTAL_SECONDS, None
    done = threading.Event()
    threading.Thread(target=_end_stream, args=(response, cancel, deadline, done), name='reply-stream-watch', daemon=True).start()
    try:
        with response:
            while True:
                if cancel.is_set():
                    return None
                if time.monotonic() > deadline:
                    break  # the total time is up (decided below)
                raw = response.readline(1024 * 1024)
                if not raw:
                    break
                size += len(raw)
                if size > STREAM_MOST_BYTES:
                    raise broken
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'):
                    continue  # a blank line between events, a comment, an event name
                data = line[5:].strip()
                if data == '[DONE]':
                    break
                chunk = json.loads(data)
                if not isinstance(chunk, dict) or chunk.get('error'):
                    raise broken
                if isinstance(chunk.get('model'), str):
                    answered_by = chunk['model']  # OpenRouter names the model that answered (its backup model, if it took over)
                for choice in chunk.get('choices') or []:
                    delta = choice.get('delta') or {}
                    piece = delta.get('content')
                    if isinstance(piece, str) and piece:
                        text.append(piece)
                        emit('assistant.piece', {'text': piece})
                    for call in delta.get('tool_calls') or []:
                        # A tool request arrives in parts: its id and name once, its arguments bit by bit.
                        index = call.get('index', 0)
                        if not isinstance(index, int) or isinstance(index, bool):
                            raise broken
                        slot = calls.setdefault(index, {'id': '', 'type': 'function', 'function': {'name': '', 'arguments': ''}})
                        function = call.get('function') or {}
                        if call.get('id'):
                            slot['id'] = call['id']
                        if isinstance(function.get('name'), str):
                            slot['function']['name'] += function['name']
                        if isinstance(function.get('arguments'), str):
                            slot['function']['arguments'] += function['arguments']
                    if choice.get('finish_reason'):
                        finish = choice['finish_reason']
        answer = ''.join(text), [calls[index] for index in sorted(calls)], finish, answered_by
    except ProviderError:
        if cancel.is_set():
            return None
        raise
    except Exception:
        # The connection dropped, went quiet, was ended from outside (Stop, the total time), or sent something
        # that is not a piece of an answer. What it was is decided below.
        answer = None
    finally:
        done.set()
    if cancel.is_set():
        return None
    if answer is None or finish is None:
        if time.monotonic() > deadline:
            raise _unreachable(prefix, service, TimeoutError()) from None
        raise broken  # also: it ended without saying that it was finished
    return answer


def _compatible_chat(service, endpoint, key, model, messages, tools, emit, cancel, vision, thinking=False, stream=False, dialect='qwen', extra=None):
    """OpenAI-compatible adapter (Qwen, OpenRouter): one complete answer, or (stream) the same answer received in pieces.
    dialect 'qwen' sends Alibaba's fields (max_completion_tokens, enable_thinking); 'openrouter' sends the fields in extra
    (max_tokens, reasoning, the fallback list "models") and marks an answer written by the fallback model (_fallback)."""
    if cancel.is_set():
        return None
    # OpenAI Responses metadata is provider-specific; retain ordinary conversation
    # content and tool results when changing provider within an existing session.
    clean = [{k: v for k, v in m.items() if not k.startswith('_')} for m in messages]
    body = {'model': model, 'messages': clean, 'stream': False}
    if dialect == 'openrouter':
        body.update(extra or {})
    else:
        body['max_completion_tokens'] = 8192
        # "Off" is sent explicitly. "On" is left to Alibaba's default, so that a thinking request is
        # exactly the request 1.0.14 sent (the shape proven on the owner's account).
        if not thinking:
            body['enable_thinking'] = False
    if tools and not vision:
        body.update(tools=tools, tool_choice='auto')
    if stream:
        streamed = _compatible_stream(service, endpoint, key, body, emit, cancel)
        if streamed is None:
            return None
        choice = {'finish_reason': streamed[2], 'message': {'content': streamed[0], 'tool_calls': streamed[1]}}
        answered_by = streamed[3]
    else:
        result = request(endpoint, body, {'Authorization': f'Bearer {key}'}, timeout=120)
        if cancel.is_set():
            return None
        if isinstance(result.get('error'), dict):
            # OpenRouter can report a failure of the model behind it inside an ordinary answer.
            raise ProviderError(f'{service} chat: the model reported an error. No partial answer was accepted.')
        choice = (result.get('choices') or [{}])[0]
        answered_by = result.get('model')
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
    fallback = (extra or {}).get('models', [None])[-1] if dialect == 'openrouter' and (extra or {}).get('models') else None
    if fallback and is_fallback(answered_by, model, fallback):  # OpenRouter names the model that answered
        response['_fallback'] = {'asked': model, 'used': answered_by}
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


QWEN_TTS_DEFAULT_MODEL = 'qwen3-tts-vc-2026-01-22'  # must match the model the voice was enrolled for
QWEN_TTS_CHUNK = 500  # Model Studio accepts about 600 characters per synthesis request


def qwen_voice_configured():
    return bool(os.getenv('DASHSCOPE_API_KEY') and os.getenv('QWEN_TTS_VOICE'))


def speech_chunks(text, limit=QWEN_TTS_CHUNK):
    """Split at sentence ends (then spaces) into pieces of at most `limit` characters."""
    chunks, current = [], ''
    for sentence in re.split(r'(?<=[.!?])\s+', text.strip()):
        while len(sentence) > limit:
            cut = sentence.rfind(' ', 0, limit)
            cut = cut if cut > limit // 2 else limit
            if current:
                chunks.append(current)
                current = ''
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if current and len(current) + 1 + len(sentence) > limit:
            chunks.append(current)
            current = sentence
        else:
            current = (current + ' ' + sentence).strip()
    if current:
        chunks.append(current)
    return [c for c in chunks if c]


def join_audio(clips):
    """Join synthesized clips into one playable file (WAV frames merged; MP3 frames concatenated)."""
    if len(clips) == 1:
        return clips[0]
    if all(c[:4] == b'RIFF' for c in clips):
        import io, wave
        frames, params = [], None
        for clip in clips:
            with wave.open(io.BytesIO(clip), 'rb') as part:
                if params is None:
                    params = part.getparams()
                elif part.getparams()[:3] != params[:3]:
                    raise ProviderError('Qwen voice returned clips in different audio formats.')
                frames.append(part.readframes(part.getnframes()))
        out = io.BytesIO()
        with wave.open(out, 'wb') as whole:
            whole.setnchannels(params.nchannels)
            whole.setsampwidth(params.sampwidth)
            whole.setframerate(params.framerate)
            whole.writeframes(b''.join(frames))
        return out.getvalue()
    if any(c[:4] == b'RIFF' for c in clips):
        raise ProviderError('Qwen voice returned clips in different audio formats.')
    return b''.join(clips)


def audio_mime(audio):
    return 'audio/wav' if audio[:4] == b'RIFF' else 'audio/mpeg'


def qwen_tts_url():
    """Qwen-TTS endpoint: DASHSCOPE_TTS_URL if set (for workspace-style accounts whose
    synthesis address differs), otherwise derived from the chat base URL. Alibaba hosts only."""
    explicit = os.getenv('DASHSCOPE_TTS_URL', '').strip()
    if explicit:
        parsed = urllib.parse.urlparse(explicit)
        if parsed.scheme != 'https' or not (parsed.hostname or '').endswith('.aliyuncs.com'):
            raise ProviderError('DASHSCOPE_TTS_URL must be an https://….aliyuncs.com Model Studio address.')
        return explicit
    base = qwen_base()
    if not base.endswith('/compatible-mode/v1'):
        raise ProviderError('DASHSCOPE_BASE_URL must end with /compatible-mode/v1, or set DASHSCOPE_TTS_URL.')
    return base[:-len('/compatible-mode/v1')] + '/api/v1/services/aigc/multimodal-generation/generation'


def qwen_result_link(url):
    """The link in Alibaba's answer to a finished sound, as JARVIS fetches it: an Alibaba file server
    (*.aliyuncs.com) over https. Alibaba's Beijing result server hands out plain http links (seen on
    2026-10-06); its file servers answer at the same name over https, and the link's signature does not
    depend on the scheme, so the sound is fetched over https either way. Anything else is refused."""
    if not isinstance(url, str):
        return None
    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or '').lower()
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme not in ('http', 'https') or not host.endswith('.aliyuncs.com') or port not in (None, 80, 443):
        return None
    return urllib.parse.urlunparse(('https', host, parsed.path, parsed.params, parsed.query, ''))


def qwen_speech(text):
    """Cloned JARVIS voice through Model Studio non-real-time Qwen-TTS."""
    key, voice = os.getenv('DASHSCOPE_API_KEY'), os.getenv('QWEN_TTS_VOICE')
    if not (key and voice):
        raise ProviderError('Qwen voice needs DASHSCOPE_API_KEY and QWEN_TTS_VOICE (your cloned voice ID).')
    endpoint = qwen_tts_url()
    model = os.getenv('QWEN_TTS_MODEL', QWEN_TTS_DEFAULT_MODEL)
    clips = []
    for chunk in speech_chunks(text):
        result = request(endpoint, {'model': model, 'input': {'text': chunk, 'voice': voice, 'language_type': 'English'}},
                         {'Authorization': f'Bearer {key}'}, timeout=60)
        audio = ((result.get('output') or {}).get('audio') or {})
        if audio.get('data'):
            clips.append(base64.b64decode(audio['data']))
            continue
        link = qwen_result_link(audio.get('url'))
        if not link:
            raise ProviderError('Qwen voice returned no usable audio link.')
        clips.append(request(link, raw=True, timeout=60))  # presigned link: no credentials sent
    if not clips:
        raise ValueError('No spoken text remains after formatting cleanup.')
    return join_audio(clips)


def speech(text, profile='auto'):
    if profile not in VOICE_PROFILES:
        raise ValueError('Unknown voice profile.')
    text = speech_text(text)
    if not text:
        raise ValueError('No spoken text remains after formatting cleanup.')
    if profile == 'qwen' or (profile == 'auto' and qwen_voice_configured()):
        return qwen_speech(text)
    if profile == 'openai':
        if not os.getenv('OPENAI_API_KEY'): raise ProviderError('OpenAI speech is not configured.')
        return request('https://api.openai.com/v1/audio/speech', {'model':'gpt-4o-mini-tts','voice':'cedar','input':text[:4000],'response_format':'mp3','instructions':'Speak with a composed British accent, warm understated wit, flowing sentences and natural pauses. Avoid a robotic or theatrical delivery.'}, {'Authorization':'Bearer '+os.environ['OPENAI_API_KEY']},raw=True)
    if profile == 'fish' and not (os.getenv('FISH_API_KEY') and os.getenv('FISH_VOICE_ID')):
        raise ProviderError('Fish Audio key and voice ID are required.')
    if profile in ('auto','fish') and os.getenv('FISH_API_KEY') and os.getenv('FISH_VOICE_ID'):
        return request('https://api.fish.audio/v1/tts', {'text': text[:5000], 'reference_id': os.environ['FISH_VOICE_ID'], 'format': 'mp3', 'mp3_bitrate': 192, 'sample_rate': 44100, 'latency': 'normal', 'normalize': True, 'prosody': {'speed': 1.0, 'volume': 0, 'normalize_loudness': True}, 'chunk_length': 300, 'condition_on_previous_chunks': True}, {'Authorization': 'Bearer ' + os.environ['FISH_API_KEY'], 'model': os.getenv('FISH_MODEL', 's2-pro')}, raw=True)
    raise ProviderError('No voice provider is configured. Add the Fish Audio or Qwen voice settings locally, or use the browser voice.')


QWEN_ASR_MODEL = 'qwen3-asr-flash'  # Alibaba Model Studio, speech recognition for a finished recording
QWEN_ASR_LIMIT = 10 * 1024 * 1024   # Alibaba's limit for one recording once it is written out as text (base64)


def cloud_speech():
    """The provider that turns speech into text in the cloud: the chosen AI provider, when its key is in place
    (and, for OpenRouter, a speech model is named). None otherwise. (The app's own default is local recognition with
    Whisper, which needs neither.)"""
    name = provider()
    if name == 'openrouter' and os.getenv('OPENROUTER_API_KEY') and openrouter_stt_model():
        return 'openrouter'
    if name == 'qwen' and os.getenv('DASHSCOPE_API_KEY'):
        return 'qwen'
    if name == 'openai' and os.getenv('OPENAI_API_KEY'):
        return 'openai'
    return None


def qwen_transcribe(audio, mime, timeout=60):
    """Speech to text through Alibaba Model Studio (qwen3-asr-flash, the OpenAI-compatible route). The request
    and the answer are as Alibaba's API reference gives them (read 2026-10-06). Anything else than text in the
    answer is an error, never "nothing was said"."""
    key = os.getenv('DASHSCOPE_API_KEY')
    if not key:
        raise ProviderError('Qwen speech recognition needs DASHSCOPE_API_KEY. Local recognition works without it.')
    kind = mime.split(';')[0]
    if kind not in ('audio/wav', 'audio/mpeg'):
        raise ValueError('Qwen speech recognition takes WAV or MP3 recordings.')
    data = 'data:' + kind + ';base64,' + base64.b64encode(audio).decode('ascii')
    if len(data) > QWEN_ASR_LIMIT:
        raise ValueError('The recording is too large for Qwen speech recognition (10 MB).')
    options = {'enable_itn': True}  # numbers as digits ("5 minutes"), as the local recognition writes them
    language = os.getenv('QWEN_ASR_LANGUAGE', 'en').strip()
    if language:  # an empty QWEN_ASR_LANGUAGE line lets Alibaba detect the language
        options['language'] = language
    body = {'model': os.getenv('QWEN_ASR_MODEL', QWEN_ASR_MODEL), 'stream': False, 'asr_options': options,
            'messages': [{'role': 'user', 'content': [{'type': 'input_audio', 'input_audio': {'data': data}}]}]}
    result = request(qwen_base() + '/chat/completions', body, {'Authorization': f'Bearer {key}'}, timeout=timeout, operation='speech recognition')
    try:
        text = result['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        raise ProviderError('Qwen speech recognition: no text in the answer.') from None
    if isinstance(text, list) and all(isinstance(part, dict) and isinstance(part.get('text'), str) for part in text):
        text = ' '.join(part['text'] for part in text)  # Alibaba's other answer shape: [{"text": "..."}]
    if not isinstance(text, str):
        raise ProviderError('Qwen speech recognition: no text in the answer.')
    return {'text': text.strip()}


def transcribe(audio, mime, timeout=None):
    """Speech to text in the cloud, by the chosen AI provider: OpenRouter (the OPENROUTER_STT_MODEL), Qwen (qwen3-asr-flash)
    or OpenAI. The app itself transcribes locally with Whisper unless the owner chose the cloud in Settings > AI.
    timeout: seconds for the one request; given, there is no second try (the microphone path cannot wait)."""
    if provider() == 'openrouter':
        return openrouter_transcribe(audio, mime, timeout or 60)
    if provider() == 'qwen':
        return qwen_transcribe(audio, mime, timeout or 60)
    if provider() != 'openai':
        raise ProviderError('Cloud speech recognition is done by the chosen AI provider: set JARVIS_PROVIDER to openrouter, openai or qwen. Local recognition works without it.')
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        raise ProviderError('Cloud speech transcription needs OPENAI_API_KEY. Local transcription and browser recognition work without it.')
    suffix = {'audio/webm': 'webm', 'audio/ogg': 'ogg', 'audio/mp4': 'mp4', 'audio/wav': 'wav', 'audio/mpeg': 'mp3'}.get(mime.split(';')[0])
    if not suffix:
        raise ValueError('Unsupported recording format.')
    boundary = secrets.token_hex(20)
    model = 'gpt-4o-mini-transcribe'
    data = (f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\n{model}\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="recording.{suffix}"\r\nContent-Type: {mime}\r\n\r\n').encode() + audio + f'\r\n--{boundary}--\r\n'.encode()
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'multipart/form-data; boundary=' + boundary}
    endpoint = 'https://api.openai.com/v1/audio/transcriptions'
    try:
        result = request(endpoint, data, headers, timeout=timeout or 60)
    except ProviderError as first:
        if timeout or ('timed out' not in str(first).lower() and 'connection failed' not in str(first).lower()):
            raise
        time.sleep(2)
        result = request(endpoint, data, headers, timeout=60)
    if not isinstance(result, dict) or not isinstance(result.get('text'), str):
        raise ProviderError('OpenAI transcription: no text in the answer.')
    return result


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
