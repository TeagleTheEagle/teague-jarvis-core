"""Offline provider audit: fake credentials, denied sockets, no App/Store."""
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import threading
import urllib.error
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import providers
from ollama_provider import OllamaProvider

records = []
with patch.dict(os.environ, {'JARVIS_PROVIDER':'openai','OPENAI_API_KEY':'OFFLINE_TEST_ONLY'}, clear=True), patch.object(socket.socket, 'connect', side_effect=AssertionError('Network forbidden')):
    for model in ('gpt-4o-mini', 'gpt-6-audit-fixture'):
        os.environ['OPENAI_MODEL'] = model
        for code in ('rate_limit_exceeded', 'insufficient_quota'):
            events = []
            def denied(req, **kwargs):
                raise urllib.error.HTTPError(req.full_url, 429, 'Simulated', {'retry-after':'7'}, io.BytesIO(json.dumps({'error':{'code':code}}).encode()))
            with patch.object(providers.urllib.request, 'urlopen', side_effect=denied) as request, patch.object(OllamaProvider, 'health_check', side_effect=AssertionError('Unexpected fallback probe')) as health, patch.object(OllamaProvider, 'classify_intent', side_effect=AssertionError('Unexpected shadow execution')) as local:
                try:
                    providers.chat([{'role':'user','content':'Offline fixture'}], [], lambda *args:events.append(args), threading.Event())
                    raise AssertionError('429 incorrectly succeeded')
                except providers.ProviderError as exc:
                    assert 'HTTP 429' in str(exc) and request.call_count == 1 and not events
                    assert health.call_count == local.call_count == 0
                    records.append(dict(case='429',model=model,upstream_code=code,error=str(exc),retry_after=getattr(exc,'retry_after',None),http_calls=request.call_count,ollama_health_calls=health.call_count,ollama_generation_calls=local.call_count,assistant_events=events,key_unchanged=os.environ['OPENAI_API_KEY']=='OFFLINE_TEST_ONLY'))
        payload = {'model':'ACTUAL_RETURNED_MODEL','status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'fixture answer'}]}]} if model.startswith('gpt-6') else {'model':'ACTUAL_RETURNED_MODEL','choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'fixture answer'}}]}
        class Reply(io.BytesIO):
            pass
        with patch.object(providers.urllib.request,'urlopen',return_value=Reply(json.dumps(payload).encode())):
            result=providers.chat([{'role':'user','content':'Offline fixture'}],[],lambda *args:None,threading.Event())
            assert result['content']=='fixture answer'
            assert 'model' not in result and 'provider' not in result
            records.append(dict(case='successful_response_provenance',configured_model=model,upstream_model=payload['model'],returned_fields=list(result),provider_model_retained=False))
    for available in (True,False):
        p=OllamaProvider()
        def fake(path, **kwargs):
            return {'models':[{'name':p.model}]} if available else {'models':[]}
        with patch.object(p,'_request',side_effect=fake):
            result=p.health_check()
            assert result['mode']=='SHADOW'
            assert result['status']==('ONLINE' if available else 'DEGRADED')
            records.append(dict(case='independent_shadow_health',available=available,result=result))

evidence={'scope':'Offline adapter simulation, no Core/App/Store, no real API/Ollama calls; gpt-6 model name is only a branch fixture, not a model availability claim','cases':records,'cases_passed':len(records),'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['providers.py','ollama_provider.py','ollama_shadow.py','server.py','store.py']}}
Path(__file__).with_name('results.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps(evidence,indent=2))
