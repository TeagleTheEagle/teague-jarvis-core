"""User-triggered, bounded diagnostics. Never retain provider payloads or keys."""
import os
import threading
import time
import urllib.parse
import providers
import maps


def check(service):
    if service not in ('chat', 'voice', 'search', 'maps'):
        raise ValueError('Choose chat, voice, search or maps.')
    start = time.perf_counter()
    result = {'service': service, 'checked_at': time.time()}
    try:
        if service == 'chat':
            reply = providers.chat([{'role': 'user', 'content': 'Connection test. Reply with only READY.'}], [], lambda *args: None, threading.Event())
            if not reply.get('content'):
                raise ValueError('The model returned no text.')
            detail = 'The configured chat model generated text. Tool use and vision were not tested.'
        elif service == 'voice':
            if providers.capabilities()['voice_provider'] == 'browser':
                return {**result, 'status': 'manual_check', 'detail': 'Browser voice needs an audible playback test on this device.', 'latency_ms': 0}
            audio = providers.speech('At your service, Mr. Teague.')
            if not isinstance(audio, bytes) or len(audio) < 100:
                raise ValueError('No usable audio was returned.')
            detail = 'The configured voice provider returned audio. Speaker playback and voice quality were not tested.'
        elif service == 'search':
            key = os.getenv('BRAVE_API_KEY')
            if not key:
                return {**result, 'status': 'not_configured', 'detail': 'Add BRAVE_API_KEY locally and restart JARVIS.', 'latency_ms': 0}
            data = providers.request('https://api.search.brave.com/res/v1/web/search?q=Sydney+Opera+House&count=1', headers={'X-Subscription-Token': key}, timeout=15)
            if not data.get('web', {}).get('results'):
                raise ValueError('Search completed but returned no results.')
            detail = 'Brave returned a live result for a public test query.'
        else:
            maps.directions('Sydney Opera House, NSW', 'Sydney Airport, NSW')
            detail = 'Google Routes returned a public test journey with traffic. Test map display and location permission in the Maps section.'
        result.update(status='passed', detail=detail)
    except (providers.ProviderError, ValueError) as exc:
        result.update(status='failed', detail=str(exc))
    except Exception:
        result.update(status='failed', detail='Unexpected provider response. Check integration settings and retry.')
    result['latency_ms'] = round((time.perf_counter() - start) * 1000)
    return result
