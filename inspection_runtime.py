"""On-demand isolated inspection. No user database writes or persistent captures."""
import base64
import datetime
import json
import mimetypes
import re
import sqlite3
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from interface_inspection import validate_request, new_evidence

LOCK = threading.Lock()
IMAGES = {}
IMAGE_LOCK = threading.Lock()
MAX_CAPTURES = 6
STATIC = ('index.html','app.js','voice.js','style.css','pro.css','gallery.css',
          'diagrams.js','workspaces.js','reliability.js','reliability.css',
          'latency.js','voice-core.js','teague.js','teague.css','maps.js','maps.css','recovery.js','voice-preview.js','inspection-client.js','desktop-updates.js','assistant-controls.js',
          'command-dashboard.js','command-dashboard.css','horizon.js','horizon.css','world-map.js','markdown-view.js','dashboard-model.js',
          'permissions.js','devices.js','devices.css','permissions.css','music.js','music.css','connectors.js','connectors.css',
          'assets/branding/teague/teague-mark.svg','assets/branding/teague/jarvis-mark.svg')
# test_inspection_browser.py keeps this list in step with the files index.html loads.
# PC readings are not part of an inspection snapshot: the dashboard shows them as not read.
METRICS_OMITTED = {'omitted': True, 'cpu_percent': None, 'memory': None, 'disk': None, 'core_uptime_seconds': None,
                   'last_response_ms': None, 'responses_measured': 0, 'scope': 'Omitted during read-only inspection.'}


def api_payloads(data):
    """What the inspected page receives for each Core request it makes: the masked snapshot, never the live Core."""
    return {'/api/state':data['state'], '/api/history':{'messages':data['messages']},
            '/api/workspaces':{'projects':data['projects']}, '/api/metrics':METRICS_OMITTED,
            '/api/maps/config':{'available':False,'error':'External maps omitted during inspection'}}


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def clean_images():
    now = time.monotonic()
    with IMAGE_LOCK:
        for key in list(IMAGES):
            if IMAGES[key][0] < now:
                del IMAGES[key]


def image_get(key):
    clean_images()
    with IMAGE_LOCK:
        return IMAGES.get(key, (0, None))[1]


def snapshot(path):
    """Read actual records, withholding ALL user-authored strings before rendering.

    This intentionally trades content analysis for reliable secret exclusion.
    Neither heuristic credential matching nor model discretion is a boundary.
    """
    db = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    omissions = ['User-authored text is withheld; layout and controls only.',
                 'Unsaved drafts, browser preferences and external content are omitted.',
                 'Lists are limited to 100 records; virtualized/offscreen content may be omitted.']
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        def rows(sql, args=()):
            return [dict(r) for r in db.execute(sql, args).fetchall()]
        items = rows('SELECT kind,created,updated FROM items ORDER BY updated DESC LIMIT 100')
        for n, r in enumerate(items):
            r.update(id=str(n), body='[Private text withheld]')
        reminders = rows('SELECT due,fired FROM reminders ORDER BY due LIMIT 100')
        for n, r in enumerate(reminders):
            r.update(id=str(n), title='[Private text withheld]')
        documents = rows('SELECT created,updated FROM documents ORDER BY updated DESC LIMIT 100')
        for n, r in enumerate(documents):
            r.update(id=str(n), name='[Private filename withheld]')
        messages = rows('SELECT role,created FROM messages ORDER BY id DESC LIMIT 100')[::-1]
        for r in messages:
            r['role'] = r['role'] if r['role'] in ('user','assistant') else 'user'
            r['content'] = '[Private message withheld]'
        logs = rows('SELECT created FROM audit ORDER BY id DESC LIMIT 100')
        for r in logs:
            r.update(action='[Private activity withheld]', status='SNAPSHOT')
        projects = []
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='workspaces'").fetchone():
            for n, _ in enumerate(rows('SELECT id FROM workspaces LIMIT 100')):
                projects.append({'id':str(n),'name':'[Private project withheld]','links':[]})
            omissions.append('Project links are omitted to avoid exposing private content.')
        return {'captured_at':stamp(), 'omissions':omissions, 'messages':messages,
                'projects':projects, 'state':{
                'capabilities':{}, 'settings':{'name':'','voice':False,'continuous':False,
                    'proactive':False,'quiet_hours':True,'response_length':'balanced'},
                'uptime':0, 'memory':[r for r in items if r['kind']=='memory'],
                'notes':[r for r in items if r['kind']=='note'],
                'projects':[r for r in items if r['kind']=='project'],
                'tasks':[dict(r, priority='normal', completed=0) for r in items if r['kind']=='task'],
                'documents':documents,'reminders':reminders,'logs':logs,'conversations':[]}}
    finally:
        db.close()


INIT = r"""(() => {
  Object.defineProperty(window,'JARVIS_INSPECTION',{value:true});
  window.__inspectionAttempts=[];
  window.__inspectionPending=0;
  const originalFetch=window.fetch.bind(window);
  window.fetch=async(...args)=>{window.__inspectionPending++;try{return await originalFetch(...args);}finally{window.__inspectionPending--;}};
  const deny=name=>(...args)=>{window.__inspectionAttempts.push(name);throw new Error('Disabled during inspection');};
  window.setInterval=()=>0;
  if(navigator.mediaDevices){for(const key of ['getUserMedia','getDisplayMedia','enumerateDevices'])
    Object.defineProperty(navigator.mediaDevices,key,{value:deny(key)});}
  for(const key of ['AudioContext','webkitAudioContext','Audio','Notification','WebSocket','EventSource'])
    Object.defineProperty(window,key,{value:deny(key),configurable:false});
  if(window.speechSynthesis)window.speechSynthesis.speak=deny('speech');
  window.open=deny('popup');
  Object.defineProperty(window,'jarvisDesktop',{value:undefined});
})();"""


def launch_browser(playwright):
    """Microsoft Edge, present on every Windows 11 PC, else installed Chrome. Playwright's own
    browser downloads are never used, so the release has no hidden browser dependency.
    Each is tried twice: a browser's first start on a new Windows account can exit at once."""
    failure = None
    for channel in ('msedge', 'msedge', 'chrome', 'chrome'):
        try:
            return playwright.chromium.launch(channel=channel, headless=True)
        except Exception as exc:
            failure = exc
    raise failure


def capture(root, origin, request, data):
    """Render supplied real assets. Every browser request is intercepted locally.

    No personal profile, server cookie, network/API response or desktop bridge
    enters this renderer. Authentication remains at the calling server route.
    """
    from playwright.sync_api import sync_playwright
    parsed = urlsplit(origin)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port or parsed.path not in ('','/') or parsed.username or parsed.query or parsed.fragment:
        raise ValueError('Inspection requires the configured loopback origin.')
    assets = {('/' if name=='index.html' else '/'+name):root/'static'/name for name in STATIC}
    denied, errors = [], []
    report = new_evidence(request)
    report['limitations'] = list(data['omissions'])
    report['limitations'].append('Masking changes text wrapping and record lengths; typography findings about private text are limited.')
    report['snapshot_at'] = data['captured_at']
    report['viewport'] = {'width':1440,'height':900}
    images = []
    with sync_playwright() as p:
        browser = launch_browser(p)
        try:
            context = browser.new_context(viewport=report['viewport'], service_workers='block',
                                          accept_downloads=False, reduced_motion='reduce')
            context.add_init_script(INIT)
            def route_handler(route):
                url = urlsplit(route.request.url)
                if url.scheme+'://'+url.netloc != origin.rstrip('/') or route.request.method != 'GET':
                    denied.append('Blocked request'); return route.abort()
                path = url.path
                if path in assets and assets[path].is_file() and not url.query:
                    return route.fulfill(body=assets[path].read_bytes(),content_type=mimetypes.guess_type(str(assets[path]))[0] or 'text/plain')
                payload = api_payloads(data).get(path)
                if payload is not None:
                    return route.fulfill(json=payload)
                denied.append('Unavailable resource')
                route.fulfill(status=403,json={'error':'Unavailable during read-only inspection'})
            context.route('**/*', route_handler)
            page = context.new_page()
            page.set_default_timeout(20000)
            page.on('pageerror',lambda _:errors.append('Frontend script error'))
            report['stages']['navigation_requested']='completed'
            page.goto(origin, wait_until='load')
            page.wait_for_function("typeof view==='function' && typeof state!=='undefined' && state.data && document.getElementById('mapsView') && document.querySelector('#projectsView .workspace-projects')")
            page.evaluate("async panel=>{await refresh();await loadHistory();view(panel);await document.fonts.ready;document.querySelectorAll('iframe').forEach(e=>e.remove());document.querySelectorAll('input,textarea').forEach(e=>{e.value='';if(e.type==='password')e.style.visibility='hidden';});for(const id of ['connection','brainStatus','voiceStatus','footerStatus','inputStatus','voiceSessionStatus']){const e=document.getElementById(id);if(e)e.textContent='INSPECTION SNAPSHOT — live state unavailable';}if(panel==='changes')document.querySelector('#changesView>div').textContent='Change records and diffs are omitted from this private-text-masked inspection.';document.getElementById('toasts').replaceChildren();}", request['panel'])
            page.wait_for_function('window.__inspectionPending===0')
            page.wait_for_function("panel=>document.querySelector('.nav.active')?.dataset.view===panel && !document.getElementById(panel+'View').classList.contains('hidden')",arg=request['panel'])
            if errors:
                raise RuntimeError('Frontend rendering failed; no visual evidence submitted.')
            report['verified_panel']=request['panel']
            if request['panel']=='changes':report['limitations'].append('Change records and diffs are omitted; only the panel shell was inspected.')
            report['stages']['panel_rendered']='completed'
            report['captured_at']=stamp()
            # Bounded real section captures, including nested scroll containers.
            sections = page.evaluate("panel=>{const root=document.getElementById(panel+'View');return [...new Set([document.scrollingElement,root,...root.querySelectorAll('*')])].filter(e=>e.getClientRects().length&&e.scrollHeight>e.clientHeight+4&&e.clientHeight>40).slice(0,5).map((e,i)=>{e.dataset.inspectionScroll=String(i);return {id:i,height:e.scrollHeight,view:e.clientHeight,document:e===document.scrollingElement};});}",request['panel'])
            positions=[None]
            if request['scope']=='full_panel':
                for s in sections:
                    offsets=list(range(0,s['height']-s['view']+1,max(1,s['view']-80)))
                    offsets.append(s['height']-s['view'])
                    for offset in sorted(set(offsets)):
                        if s['document'] and offset==0:continue
                        positions.append({'id':s['id'],'offset':offset})
            report['planned_tiles']=len(positions)
            report['coverage_limited']=len(positions)>MAX_CAPTURES
            if report['coverage_limited']:report['limitations'].append('Capture limited to six overlapping tiles; remaining scrollable content was not captured.')
            for pos in positions[:MAX_CAPTURES]:
                if pos:
                    page.evaluate("p=>{const el=document.querySelector('[data-inspection-scroll=\"'+p.id+'\"]');if(el!==document.scrollingElement)el.scrollIntoView({block:'start'});el.scrollTop=p.offset;}",pos)
                page.wait_for_function('window.__inspectionPending===0')
                page.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                images.append(page.screenshot(type='png',animations='disabled'))
                evidence=page.evaluate(r"""()=>{
                    const visible=e=>{const r=e.getBoundingClientRect();if(!e.getClientRects().length||getComputedStyle(e).visibility==='hidden'||r.bottom<=0||r.top>=innerHeight||r.right<=0||r.left>=innerWidth)return false;
                      for(let p=e.parentElement;p;p=p.parentElement){const s=getComputedStyle(p);if(/hidden|auto|scroll/.test(s.overflowY)){const a=p.getBoundingClientRect();if(r.top>=a.bottom||r.bottom<=a.top)return false;}}return true;};
                    const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n,text='';
                    while((n=walker.nextNode())&&text.length<20000){if(!['SCRIPT','STYLE'].includes(n.parentElement.tagName)&&visible(n.parentElement))text+=n.textContent.trim()+'\n';}
                    return {text:text.slice(0,20000),controls:[...document.querySelectorAll('button,input,select,textarea,[role]')].filter(visible).slice(0,200).map(e=>({role:e.getAttribute('role')||e.tagName.toLowerCase(),name:(e.getAttribute('aria-label')||e.innerText||e.getAttribute('placeholder')||'').slice(0,200),disabled:!!e.disabled}))};
                }""")
                report['screenshots'].append({'section':pos or {'viewport':'initial'},'reference':None,
                                               'visible_text':evidence['text'], 'accessibility':evidence['controls']})
            report['visible_text']='\n'.join(s['visible_text'] for s in report['screenshots'])[:20000]
            report['accessibility']=[c for s in report['screenshots'] for c in s['accessibility']][:200]
            report['coverage']='bounded_sections' if len(images)>1 else 'viewport'
            report['captured_tiles']=len(images)
            report['omissions']=['Offscreen and virtualized content not proven complete.', 'Per-capture text/roles are bounded; aggregate text limited to 20000 characters and 200 controls.']
            report['stages']['screenshot_captured']='completed'
            report['isolation']={'blocked_resources':len(denied),'side_effect_attempts':page.evaluate('window.__inspectionAttempts')}
            if report['isolation']['side_effect_attempts']:
                raise RuntimeError('Inspection attempted a prohibited side effect.')
            return report, images
        finally:
            browser.close()


def run(root, database, origin, arguments, transmit=False, analyzer=None, provider=None):
    request=validate_request(arguments)
    if request['panel']=='all':raise ValueError('Use an inspection job for all panels.')
    if type(transmit) is not bool:
        raise ValueError('Invalid transmission consent.')
    if not LOCK.acquire(blocking=False):
        raise ValueError('Another inspection is running.')
    started=time.perf_counter()
    report=new_evidence(request)
    try:
        clean_images()
        report, images=capture(root, origin, request, snapshot(database))
        with IMAGE_LOCK:
            # Bound retention across requests as well as within one request.
            while len(IMAGES)+len(images)>18:
                del IMAGES[next(iter(IMAGES))]
            for entry, image in zip(report['screenshots'],images):
                key=uuid.uuid4().hex
                IMAGES[key]=(time.monotonic()+300,image)
                entry['reference']='/api/interface-inspection/image/'+key
        cleanup=threading.Timer(301,clean_images)
        cleanup.daemon=True
        cleanup.start()
        report['assessment_mode']='dom_only'
        report['analysis']='DOM-only assessment. Purpose: inspect '+request['panel']+'. Observed elements: '+str(len(report['accessibility']))+' controls/roles. No model has analysed these images. Review the attached captures; private text and external services are omitted.'
        if transmit and analyzer:
            report['provider']=provider
            report['stages']['image_submitted']='attempted'
            try:
                answer=analyzer(images,request['focus'],report['visible_text'])
                if not isinstance(answer,str) or not answer.strip():
                    raise ValueError('Empty analysis')
                report['stages']['image_submitted']='completed'
                report['stages']['analysis_completed']='completed'
                report['assessment_mode']='visual_analysis'
                report['analysis']=answer
            except Exception:
                report['stages']['analysis_completed']='failed'
                report['errors'].append('Vision analysis unavailable. Submission may have reached the provider; receipt not confirmed.')
        elif transmit:
            report['limitations'].append('No vision analyzer available; no external request made.')
    except Exception:
        # Diagnosable from data/logs/core.log; the report itself stays free of internals.
        print('Interface inspection failed: ' + traceback.format_exc(limit=6)[-3000:], file=sys.stderr, flush=True)
        report['errors'].append('Inspection unavailable or rendering failed. No success is claimed; check worker installation and rendering tests.')
    finally:
        report['duration_ms']=round((time.perf_counter()-started)*1000)
        LOCK.release()
    return report
