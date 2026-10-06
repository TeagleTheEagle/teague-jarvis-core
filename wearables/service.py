"""Narrow same-PC bridge into the already-running App. Never starts another brain.

One Service is one device's session: its questions, its limit of requests a minute. The same-PC test client
(/api/wearable/, one shared token) has one; each paired device (device_gateway.py, its own key) has its own."""
import base64
import io
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
import uuid

import calendar_feed
import mail
import permissions
import providers
from devices import DeviceError


def _location(value):
    """A device's position sent with a question (1.0.17, docs/PHONE-ACCESS-1.0.17.md item D): checked here, given to
    that one answer and to directions, kept by the Core nowhere."""
    if not isinstance(value,dict) or set(value)-{'lat','lon','accuracy_m','label'} or 'lat' not in value or 'lon' not in value: raise ValueError('Invalid location.')
    lat,lon=value['lat'],value['lon']
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in (lat,lon)) or not -90<=lat<=90 or not -180<=lon<=180: raise ValueError('Invalid location.')
    out={'lat':float(lat),'lon':float(lon)}
    if 'accuracy_m' in value:
        accuracy=value['accuracy_m']
        if isinstance(accuracy,bool) or not isinstance(accuracy,(int,float)) or not 0<=accuracy<=100000: raise ValueError('Invalid location.')
        out['accuracy_m']=float(accuracy)
    if 'label' in value:
        label=value['label']
        if not isinstance(label,str) or len(label)>80 or re.search(r'[\x00-\x1f]',label): raise ValueError('Invalid location.')
        out['label']=label.strip()
    return out


class Service:
    def __init__(self, app, device_id='local-wearable-client', *, simulated=True, prefix='wearable-', register=True, writes=False, tools=False, approve=False):
        self.app = app
        self.writes = writes      # the owner's tick for a paired device: may it save memories and tasks? (1.0.16)
        self.tools = tools        # the owner's tick: may it use this PC's tools? (1.0.17; set per request by device_gateway.py)
        self.approve = approve    # the owner's tick: may it approve what waits for the owner? (1.0.17)
        self.reads = []           # the light reads (conversations, history, metrics, overview) have their own limit
        self.token = secrets.token_urlsafe(32)
        self.runs = set()
        self.lock = threading.Lock()
        self.calls = []
        self.device_id = device_id
        self.prefix = prefix      # every conversation of this device starts with it
        self.paired = not simulated
        # The same-PC test client announces itself. It is always listed as simulated: only a device the owner
        # paired (devices.py) can be a real one, and its presence is registered by device_gateway.py.
        if register:
            self.app.devices.register(self.device_id,{'camera','microphone','speakers'},simulated=True)

    def dispatch(self, op, body):
        if not isinstance(body,dict): raise ValueError('Expected object.')
        if op=='start' and permissions.stop_phrase(body.get('text')) and self.app.stopped is None:
            # The emergency stop words are never turned away as "busy", "too many requests" or a malformed
            # request: the Core stops first (server.App.start_run) and answers them itself. Once JARVIS is
            # stopped, repeating the words is an ordinary request again, with the bridge's usual limits.
            self.runs={r for r in self.runs if r in self.app.runs}
            conversation=body.get('conversation')
            if not isinstance(conversation,str) or not conversation.startswith(self.prefix):conversation=self.prefix+'local'
            result=self.app.start_run({'text':body['text'],'conversation':conversation},wearable=True,device=self.device_id,writes=self.writes,tools=self.tools)
            self.runs.add(result['run_id']);return result
        if op=='events' and 'after' in body: return self.events_after(body)  # waits outside the lock (below)
        if op in ('approve','reject'): return self.answer_approval(op,body)  # the approved tool runs outside the lock (below)
        if not self.lock.acquire(blocking=False): raise ValueError('Wearable service busy.')
        try:
            self.app.devices.heartbeat('pc')
            if op not in ('disconnect','registry'):self.app.devices.heartbeat(self.device_id)
            if self.paired and op in ('register','registry','disconnect'):raise ValueError('Operation unavailable.')
            if op=='register':
                if set(body)!={'capabilities','ready','simulated'} or type(body['simulated']) is not bool:raise ValueError('Invalid registration.')
                if not isinstance(body['capabilities'],list) or not isinstance(body['ready'],list):raise ValueError('Invalid capabilities.')
                allowed={'microphone','camera','speakers','display'}
                if not set(body['capabilities'])<=allowed:raise ValueError('Unsupported device capabilities.')
                # Whatever the client says about itself, this route is the same-PC test client: listed as simulated.
                self.app.devices.register(self.device_id,body['capabilities'],ready=body['ready'],simulated=True)
                return {'device_id':self.device_id}
            if op=='registry':
                self.app.devices.heartbeat('pc')
                return {'devices':self.app.devices.snapshot()}
            if op=='disconnect':
                self.app.devices.disconnect(self.device_id);return {'disconnected':True}
            if op in ('start','speech','transcribe'):
                now=time.monotonic();self.calls=[t for t in self.calls if now-t<60]
                if len(self.calls)>=20: raise ValueError('Wearable request limit reached. Wait one minute.')
                self.calls.append(now)
            if op in ('conversations','history','metrics','overview','approvals'):
                self.count_read()
                return self.read(op,body)
            if op=='start':
                if set(body)-{'text','image','conversation','location'}: raise ValueError('Unknown fields.')
                text=body.get('text'); conversation=body.get('conversation',self.prefix+'local')
                location=_location(body['location']) if 'location' in body else None
                if not isinstance(conversation,str) or not conversation.startswith(self.prefix): raise ValueError('Wearable conversation required.')
                attachment=None
                if body.get('image'):
                    raw=base64.b64decode(body['image'],validate=True)
                    if len(raw)>2*1024*1024: raise ValueError('Image too large.')
                    from PIL import Image
                    # Decode, check dimensions and re-encode, dropping embedded metadata.
                    try:
                        with Image.open(io.BytesIO(raw)) as picture:
                            if picture.width*picture.height>16_000_000 or picture.format not in ('PNG','JPEG'): raise ValueError('Unsupported image.')
                            picture.load();out=io.BytesIO();picture.convert('RGB').save(out,format='JPEG',quality=85)
                    except Exception:
                        raise ValueError('Unsupported image.') from None  # not a picture, damaged, or far too large
                    ident=uuid.uuid4().hex
                    attachment={'id':ident,'type':'image','name':'wearable-capture.jpg','data':'data:image/jpeg;base64,'+base64.b64encode(out.getvalue()).decode()}
                with self.app.lock:
                    if attachment:self.app.attachments[attachment['id']]=attachment
                    try:
                        result=self.app.start_run({'text':text,'conversation':conversation,**({'attachment':attachment['id']} if attachment else {})},wearable=True,device=self.device_id,writes=self.writes,tools=self.tools,location=location)
                    finally:
                        if attachment:self.app.attachments.pop(attachment['id'],None)
                self.runs={r for r in self.runs if r in self.app.runs}
                self.runs.add(result['run_id']);return result
            if op in ('events','cancel'):
                if set(body)!={'run_id'} or body['run_id'] not in self.runs: raise ValueError('Unknown wearable run.')
                run=self.app.runs.get(body['run_id'])
                if not run: raise ValueError('Run expired.')
                if op=='cancel':run.cancel.set();return {'cancelled':True}
                with run.condition:
                    return {'done':run.done,'events':list(run.events),'measurements':list(run.measurements)}
            if op=='transcribe':
                if set(body)!={'data'}:raise ValueError('Expected PCM data.')
                self.app.require_running()  # while the emergency stop holds, no device's recording is turned into text (1.0.16)
                return self.app.local_stt.transcribe(body)
            if op=='speech':
                if set(body)!={'text'} or not isinstance(body['text'],str) or not 1<=len(body['text'])<=12000:raise ValueError('Invalid speech text.')
                self.app.require_running()  # while the emergency stop holds, nothing is spoken for a device
                started=time.perf_counter()
                audio=self.app.voice_engine.synthesize(body['text'],self.app.store.settings().get('voice_profile','auto'))
                # The voice in use decides the format (the Qwen voice returns WAV): say what it really is.
                return {'audio':base64.b64encode(audio).decode(),'mime':providers.audio_mime(audio),'tts_ms':round((time.perf_counter()-started)*1000)}
            if op=='status':return {'available':True,'protocol':1,'scope':'same-PC wearable analysis','voice_profile':self.app.store.settings().get('voice_profile','auto')}
            raise ValueError('Operation unavailable.')
        finally:self.lock.release()

    def count_read(self):
        """The light reads' limit (1.0.16): 120 a minute, paired devices only. Must hold the lock."""
        if not self.paired: raise ValueError('Operation unavailable.')  # the same-PC test client stays as it was
        now=time.monotonic();self.reads=[t for t in self.reads if now-t<60]
        if len(self.reads)>=120: raise ValueError('Wearable request limit reached. Wait one minute.')
        self.reads.append(now)

    def answer_approval(self, op, body):
        """An approval answered from this device (1.0.17 item A): counted under the lock like the other light reads and
        carried out outside it, so that the approved tool (a file, a song, a page) does not make this device's other
        requests "busy" meanwhile. The stop is never held up either way."""
        if not self.lock.acquire(blocking=False): raise ValueError('Wearable service busy.')
        try: self.count_read()
        finally: self.lock.release()
        return self.read(op,body)

    def events_after(self, body):
        """The events of one of this device's questions after a cursor, waiting up to ten seconds for new ones (as the
        PC window's /api/runs/<id>/events does): a phone on cellular asks a few times, not every tenth of a second.
        Outside the service lock, so a cancel or a stop is never held up by the wait."""
        if set(body)!={'run_id','after'} or body['run_id'] not in self.runs: raise ValueError('Unknown wearable run.')
        after=body['after']
        if type(after) is not int or after<-1: raise ValueError('Supply only run_id and after.')
        run=self.app.runs.get(body['run_id'])
        if not run: raise ValueError('Run expired.')
        with run.condition:
            if len(run.events)<=after+1 and not run.done: run.condition.wait(10)
            return {'done':run.done,'events':list(run.events[max(0,after+1):]),'measurements':list(run.measurements)}

    def read(self, op, body):
        """What a paired device may read about itself and the PC (1.0.16, docs/PHONE-CORE-1.0.16.md): its own
        conversations, one of them, the PC's health as the dashboard has it, and an overview of tasks and reminders.
        Never another device's conversations and never the PC's chats."""
        store=self.app.store
        if op=='conversations':
            if body: raise ValueError('Unknown fields.')
            return {'conversations':store.conversations_for(self.prefix)}
        if op=='history':
            if set(body)-{'conversation','limit'} or 'conversation' not in body: raise ValueError('Unknown fields.')
            conversation=body['conversation'];limit=body.get('limit',60)
            if not isinstance(conversation,str) or not conversation.startswith(self.prefix) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',conversation): raise ValueError('Wearable conversation required.')
            if type(limit) is not int or not 1<=limit<=100: raise ValueError('Unknown fields.')
            return {'conversation':conversation,'messages':[{k:m[k] for k in ('id','role','content','created')} for m in store.history(conversation,limit)]}
        if op=='metrics':
            if body: raise ValueError('Unknown fields.')
            import system_metrics,runtime_paths
            with self.app.lock: timings=list(self.app.timings)
            reading=system_metrics.snapshot(store.root,self.app.started,timings)
            chosen=providers.provider()
            key=os.getenv('DASHSCOPE_API_KEY') if chosen=='qwen' else os.getenv('OPENAI_API_KEY') if chosen=='openai' else None
            reading.update(core_version=runtime_paths.release_id() or 'development '+str(self.app.backend_revision)[:12],ai_ready=bool(key),stopped=self.app.stopped is not None)
            return reading
        if op=='overview':
            if body: raise ValueError('Unknown fields.')
            import workspaces
            open_tasks=store.tasks(include_completed=False);open_ids={t['id'] for t in open_tasks}
            projects=[{'id':p['id'],'name':p['name'],'open_tasks':len([l for l in p['links'] if l['kind']=='task' and l['ref'] in open_ids])} for p in workspaces.listing(store)]
            now=time.time()
            reminders=[{'title':r['title'],'due':r['due'],'fired':bool(r['fired'])} for r in store.reminders() if r['due']<=now+86400]
            # 1.0.17 item G (docs/MAC-REQUESTS-20261007.md): the next day's events and the unread count, read in the background
            # (server.Fresh) so this answer never waits on a feed or a mail server; null until read, null when not connected.
            day=self.app.calendar_day.get() if calendar_feed.configured() else None
            calendar=None if day is None else [{'title':r['title'],'start':r['start_ts'],'end':r['end_ts'],'all_day':r['all_day'],'location':r.get('location')} for r in day[:20]]
            return {'tasks_open':len(open_tasks),'projects':projects[:20],'reminders':reminders[:20],'conversations':len(store.conversations_for(self.prefix,1000)),
                    'calendar_connected':calendar_feed.configured(),'calendar':calendar,'mail_unread':self.app.mail_unread.get() if mail.configured() else None,
                    'scope':'Open tasks, projects and the reminders due within 24 hours, from the PC; the conversations are this device\'s own.'}
        if op in ('approvals','approve','reject'):
            # 1.0.17 (docs/PHONE-ACCESS-1.0.17.md): what waits for the owner, and the owner's answer from the pocket.
            # Only with the tick "may approve for JARVIS"; the same list and the same decision as the PC window
            # (server.App.approve). While the emergency stop holds nothing is listed or answered (the stop has
            # dropped every approval anyway): the stopped sentence, as for every device request.
            if not self.approve: raise DeviceError('Approving is not allowed for this device.')
            self.app.require_running()
            if op=='approvals':
                if body: raise ValueError('Unknown fields.')
                return {'items':self.app.approval_rows()}
            if set(body)!={'id'} or not isinstance(body['id'],str) or not re.fullmatch(r'[a-f0-9]{32}',body['id']): raise ValueError('Unknown fields.')
            return self.app.approve_from_device(body['id'],op=='approve',self.device_id)
        raise ValueError('Operation unavailable.')


def handle(handler):
    service=getattr(handler.server,'wearable_service',None)
    host=f'127.0.0.1:{handler.server.server_port}'
    token=handler.headers.get('X-Jarvis-Wearable','')
    if (not service or handler.headers.get('Host')!=host or handler.headers.get('Origin') not in (None,'http://'+host)
            or handler.headers.get('Sec-Fetch-Site')=='cross-site' or not secrets.compare_digest(token,service.token)):
        handler.close_connection=True;handler.send(403,{'error':'Wearable authorization required.'});return getattr(handler,'discard_body',lambda:None)()
    try:
        size=int(handler.headers.get('Content-Length','0'))
        if handler.headers.get('Transfer-Encoding') or handler.headers.get_content_type()!='application/json' or not 0<size<=3*1024*1024:
            handler.close_connection=True;handler.send(400,{'error':'Invalid bounded JSON request.'});return getattr(handler,'discard_body',lambda:None)()
        body=json.loads(handler.rfile.read(size))
        return handler.send(200,service.dispatch(handler.path.rsplit('/',1)[-1],body))
    except (ValueError,TypeError,KeyError) as exc:
        # The one reason a device is told plainly: JARVIS is stopped until the owner resumes on the PC.
        stopped=str(exc)==permissions.STOPPED_MESSAGE
        return handler.send(400,{'error':permissions.STOPPED_MESSAGE if stopped else 'Invalid, busy, expired or unavailable wearable request.',**({'stopped':True} if stopped else {})})
    except Exception:
        # No provider credentials or raw exceptions cross the bridge.
        return handler.send(503,{'error':'JARVIS service unavailable. Check provider quota, voice configuration or local speech model.'})


def publish_connection(server):
    server.wearable_service=Service(server.app)
    # Only publish discovery for the live data directory, never isolated test instances.
    import runtime_paths
    if server.app.store.root != runtime_paths.data_dir().resolve():return lambda:None
    path=runtime_paths.wearable_connection_file()
    data={'url':f'http://127.0.0.1:{server.server_port}','token':server.wearable_service.token}
    path.write_text(json.dumps(data),encoding='utf-8')
    def cleanup():
        try:
            if json.loads(path.read_text(encoding='utf-8')).get('token')==data['token']:path.unlink()
        except (OSError,ValueError):pass
    return cleanup
