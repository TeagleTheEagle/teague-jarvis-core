"""Narrow same-PC bridge into the already-running App. Never starts another brain."""
import base64
import io
import json
from pathlib import Path
import secrets
import threading
import time
import uuid

import permissions


class Service:
    def __init__(self, app):
        self.app = app
        self.token = secrets.token_urlsafe(32)
        self.runs = set()
        self.lock = threading.Lock()
        self.calls = []
        self.device_id = 'local-wearable-client'
        self.app.devices.register(self.device_id,{'camera','microphone','speakers'},simulated=True)

    def dispatch(self, op, body):
        if not isinstance(body,dict): raise ValueError('Expected object.')
        if op=='start' and permissions.stop_phrase(body.get('text')) and self.app.stopped is None:
            # The emergency stop words are never turned away as "busy", "too many requests" or a malformed
            # request: the Core stops first (server.App.start_run) and answers them itself. Once JARVIS is
            # stopped, repeating the words is an ordinary request again, with the bridge's usual limits.
            self.runs={r for r in self.runs if r in self.app.runs}
            conversation=body.get('conversation')
            if not isinstance(conversation,str) or not conversation.startswith('wearable-'):conversation='wearable-local'
            result=self.app.start_run({'text':body['text'],'conversation':conversation},wearable=True)
            self.runs.add(result['run_id']);return result
        if not self.lock.acquire(blocking=False): raise ValueError('Wearable service busy.')
        try:
            self.app.devices.heartbeat('pc')
            if op not in ('disconnect','registry'):self.app.devices.heartbeat(self.device_id)
            if op=='register':
                if set(body)!={'capabilities','ready','simulated'} or type(body['simulated']) is not bool:raise ValueError('Invalid registration.')
                if not isinstance(body['capabilities'],list) or not isinstance(body['ready'],list):raise ValueError('Invalid capabilities.')
                allowed={'microphone','camera','speakers','display'}
                if not set(body['capabilities'])<=allowed:raise ValueError('Unsupported device capabilities.')
                self.app.devices.register(self.device_id,body['capabilities'],ready=body['ready'],simulated=body['simulated'])
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
            if op=='start':
                if set(body)-{'text','image','conversation'}: raise ValueError('Unknown fields.')
                text=body.get('text'); conversation=body.get('conversation','wearable-local')
                if not isinstance(conversation,str) or not conversation.startswith('wearable-'): raise ValueError('Wearable conversation required.')
                attachment=None
                if body.get('image'):
                    raw=base64.b64decode(body['image'],validate=True)
                    if len(raw)>2*1024*1024: raise ValueError('Image too large.')
                    from PIL import Image
                    # Decode, check dimensions and re-encode, dropping embedded metadata.
                    with Image.open(io.BytesIO(raw)) as picture:
                        if picture.width*picture.height>16_000_000 or picture.format not in ('PNG','JPEG'): raise ValueError('Unsupported image.')
                        picture.load();out=io.BytesIO();picture.convert('RGB').save(out,format='JPEG',quality=85)
                    ident=uuid.uuid4().hex
                    attachment={'id':ident,'type':'image','name':'wearable-capture.jpg','data':'data:image/jpeg;base64,'+base64.b64encode(out.getvalue()).decode()}
                with self.app.lock:
                    if attachment:self.app.attachments[attachment['id']]=attachment
                    try:
                        result=self.app.start_run({'text':text,'conversation':conversation,**({'attachment':attachment['id']} if attachment else {})},wearable=True)
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
                return self.app.local_stt.transcribe(body)
            if op=='speech':
                if set(body)!={'text'} or not isinstance(body['text'],str) or not 1<=len(body['text'])<=12000:raise ValueError('Invalid speech text.')
                self.app.require_running()  # while the emergency stop holds, nothing is spoken for a device
                started=time.perf_counter()
                audio=self.app.voice_engine.synthesize(body['text'],self.app.store.settings().get('voice_profile','auto'))
                return {'audio':base64.b64encode(audio).decode(),'mime':'audio/mpeg','tts_ms':round((time.perf_counter()-started)*1000)}
            if op=='status':return {'available':True,'protocol':1,'scope':'same-PC wearable analysis','voice_profile':self.app.store.settings().get('voice_profile','auto')}
            raise ValueError('Operation unavailable.')
        finally:self.lock.release()


def handle(handler):
    service=getattr(handler.server,'wearable_service',None)
    host=f'127.0.0.1:{handler.server.server_port}'
    token=handler.headers.get('X-Jarvis-Wearable','')
    if (not service or handler.headers.get('Host')!=host or handler.headers.get('Origin') not in (None,'http://'+host)
            or handler.headers.get('Sec-Fetch-Site')=='cross-site' or not secrets.compare_digest(token,service.token)):
        handler.close_connection=True;return handler.send(403,{'error':'Wearable authorization required.'})
    try:
        size=int(handler.headers.get('Content-Length','0'))
        if handler.headers.get('Transfer-Encoding') or handler.headers.get_content_type()!='application/json' or not 0<size<=3*1024*1024:
            handler.close_connection=True;return handler.send(400,{'error':'Invalid bounded JSON request.'})
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
