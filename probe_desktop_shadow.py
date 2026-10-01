"""Explicit localhost desktop-Core probe; no new Core and no credentials printed."""
import argparse
import hashlib
import http.cookiejar
import json
from pathlib import Path
import time
import urllib.request
from urllib.parse import urlsplit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label', required=True)
    args = p.parse_args()
    session = json.loads(Path('desktop/.jarvis-session.json').read_text())
    origin = session['origin']
    parsed = urlsplit(origin)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.username or parsed.path:
        raise ValueError('Unexpected desktop origin')
    client = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    client.addheaders = [('X-Jarvis-Desktop', session['token']), ('Origin', origin)]
    client.open(origin+'/', timeout=5).close()
    def get(path):
        return json.load(client.open(origin+path, timeout=5))
    def memory_digest(state):
        return hashlib.sha256(json.dumps(state['memory'],sort_keys=True).encode()).hexdigest()
    before = memory_digest(get('/api/state'))
    started = time.perf_counter()
    request = urllib.request.Request(origin+'/api/chat', data=json.dumps({'text':'what time is it','conversation':'phase1-shadow-validation'}).encode(), headers={'Content-Type':'application/json'})
    run_id = json.load(client.open(request, timeout=5))['run_id']
    completed, shadow = False, None
    deadline = time.monotonic()+28
    core_ms = None
    while time.monotonic()<deadline:
        events = get('/api/runs/'+run_id+'/events?after=-1')['events']
        if any(e['event']=='run.completed' for e in events) and not completed:
            completed=True; core_ms=round((time.perf_counter()-started)*1000,3)
        state=get('/api/state'); candidate=state['capabilities']['ollama_shadow']['last']
        if candidate and candidate['request_id']==run_id:
            shadow=candidate
        if completed and shadow:
            break
        time.sleep(.25)
    print(json.dumps({'label':args.label,'scope':'authenticated production desktop Core API, not UI typing',
        'origin':origin,'request_id':run_id,'core_completed':completed,'core_completion_observed_ms':core_ms,
        'memory_unchanged':before==memory_digest(get('/api/state')),'shadow':shadow},indent=2))


if __name__=='__main__':
    main()
