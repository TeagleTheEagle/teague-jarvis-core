"""Same-PC client. Provider credentials remain exclusively in the running server."""
import asyncio
import base64
import json
from pathlib import Path
import re
import time
import urllib.request
import urllib.error
from .contracts import WearableError


class RealCore:
    def __init__(self, connection=None):
        if connection is None:
            try:connection=json.loads((Path(__file__).resolve().parents[1]/'.env.wearable-connection.json').read_text(encoding='utf-8'))
            except (OSError,ValueError):raise WearableError('START_OR_RESTART_PC_JARVIS') from None
        self.url=connection['url'];self.token=connection['token']
        if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]{1,5}',self.url):raise WearableError('LOOPBACK_REQUIRED')
        self.measurements=[]
        self.tts_ms=None
        self.last_failure=None

    def request(self,op,body):
        request=urllib.request.Request(self.url+'/api/wearable/'+op,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Jarvis-Wearable':self.token})
        # Ignore system proxies: loopback credentials must never leave this PC.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):raise WearableError('REDIRECT_DENIED')
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        try:
            with opener.open(request,timeout=125) as response:return json.load(response)
        except (OSError,ValueError,urllib.error.URLError):raise WearableError('JARVIS_SERVICE_UNAVAILABLE') from None

    async def transcribe(self,audio):
        result=await asyncio.to_thread(self.request,'transcribe',{'data':base64.b64encode(audio.validate().pcm).decode()})
        return result['text']

    async def respond(self,text,image=None,conversation='wearable-local'):
        body={'text':text,'conversation':conversation}
        if image:body['image']=base64.b64encode(image.validate().data).decode()
        start=asyncio.create_task(asyncio.to_thread(self.request,'start',body))
        try:result=await asyncio.shield(start)
        except asyncio.CancelledError:
            try:
                result=await start
                await asyncio.to_thread(self.request,'cancel',{'run_id':result['run_id']})
            except WearableError:pass
            raise
        run_id=result['run_id'];deadline=time.monotonic()+130
        try:
            while time.monotonic()<deadline:
                report=await asyncio.to_thread(self.request,'events',{'run_id':run_id})
                if report['done']:
                    self.measurements=report['measurements']
                    for event in report['events']:
                        if event['event'] in ('run.failed','run.cancelled'):
                            message=event['data'].get('message','')
                            match=re.search(r'HTTP\s+(\d{3})',message)
                            self.last_failure={'http_status':int(match[1]) if match else None,
                                               'quota_or_rate_limit':bool(re.search(r'quota|rate limit|credits',message,re.I)),
                                               'configuration':bool(re.search(r'configure|model|key',message,re.I))}
                            raise WearableError('JARVIS_RESPONSE_FAILED')
                    completed=[e['data']['text'] for e in report['events'] if e['event']=='assistant.completed']
                    if not completed:raise WearableError('NO_JARVIS_ANSWER')
                    return completed[-1]
                await asyncio.sleep(.1)
            raise WearableError('JARVIS_TIMEOUT')
        finally:
            if 'report' not in locals() or not report.get('done'):
                try:await asyncio.to_thread(self.request,'cancel',{'run_id':run_id})
                except WearableError:pass

    async def describe(self,text,image):return await self.respond(text,image)

    async def synthesize(self,text):
        from .output import EncodedAudio
        result=await asyncio.to_thread(self.request,'speech',{'text':text})
        self.tts_ms=result['tts_ms']
        return EncodedAudio(base64.b64decode(result['audio'],validate=True),result['mime']).validate()
