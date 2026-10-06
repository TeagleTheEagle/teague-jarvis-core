"""User-triggered, bounded diagnostics. Never retain provider payloads or keys."""
import json
import os
import threading
import time
import urllib.parse
import providers
import maps


SERVICES = ('chat', 'full', 'voice', 'search', 'maps', 'mail', 'calendar')


def check(service, mode=None, full=None):
    """mode is the saved answer mode (Settings > Answer speed), so the chat check asks the model that answers.
    full, for the 'full' check: a function returning (messages, tools) exactly as a real question sends them."""
    if service not in SERVICES:
        raise ValueError('Choose chat, full, voice, search, maps, mail or calendar.')
    start = time.perf_counter()
    result = {'service': service, 'checked_at': time.time()}
    try:
        if service == 'chat':
            reply = providers.chat([{'role': 'user', 'content': 'Connection test. Reply with only READY.'}], [], lambda *args: None, threading.Event(), **providers.chat_options(mode, ''))
            if not reply.get('content'):
                raise ValueError('The model returned no text.')
            detail = 'The configured chat model generated text. This was a tiny request: use the full question test to check a real-size one. Tool use and vision were not tested.'
        elif service == 'full':
            # A provider can pass the tiny test and still refuse a real question: on 2026-10-05 a free plan accepted
            # "READY" and answered every real question with HTTP 413. This sends what a real question sends.
            if full is None:
                raise ValueError('The full question test is not available here.')
            messages, tools = full()
            reply = providers.chat(messages, tools, lambda *args: None, threading.Event(), **providers.chat_options(mode, ''))
            asked_tool = bool(reply and reply.get('tool_calls'))
            if not reply or not (reply.get('content') or asked_tool):
                raise ValueError('The model returned neither text nor a tool request.')
            size = len(json.dumps(messages, ensure_ascii=False)) + len(json.dumps(tools, ensure_ascii=False))
            detail = (f'The chat model accepted a real-size JARVIS question: the full instructions and all {len(tools)} tools, about {size:,} characters. '
                      + ('It asked for a tool, as a real question does. ' if asked_tool else 'It answered in text without asking for a tool. ')
                      + 'This was one question without earlier conversation; a long conversation is larger. No tool was run.')
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
        elif service == 'mail':
            # 1.0.17 item G: one sign-in and the unread count; the address, the password and the mails stay out of the answer.
            import mail
            if not mail.configured():
                return {**result, 'status': 'not_configured', 'detail': 'Put GMAIL_ADDRESS and GMAIL_APP_PASSWORD in the key file (docs/GOOGLE-STEPS.md) and start JARVIS again.', 'latency_ms': 0}
            found = mail.test_connection()
            detail = f"Gmail signed in with the app password: {found['unread']} unread in the inbox. Nothing was read or changed."
        elif service == 'calendar':
            import calendar_feed
            if not calendar_feed.configured():
                return {**result, 'status': 'not_configured', 'detail': 'Put GOOGLE_CALENDAR_ICS in the key file (docs/GOOGLE-STEPS.md) and start JARVIS again.', 'latency_ms': 0}
            found = calendar_feed.test_connection()
            detail = (f"{found['calendars']} calendar{'s' if found['calendars'] != 1 else ''} fetched: {found['events_next_7_days']} events in the next seven days."
                      + (' ' + '; '.join(found['notes']).capitalize() + '.' if found['notes'] else ''))
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
