"""One-shot, opt-in OpenAI diagnostic. No retries, raw headers or credentials logged."""
import argparse
import base64
import datetime
import io
import json
import os
from pathlib import Path
import re
import threading
import urllib.error
import urllib.request
from unittest.mock import patch


def sanitize(value):
    value=str(value)[:2000]
    for name,secret in os.environ.items():
        if any(part in name for part in ('KEY','TOKEN','SECRET','PASSWORD')) and len(secret)>5:
            value=value.replace(secret,'[REDACTED]')
    return re.sub(r'\bsk-[A-Za-z0-9_-]+','[REDACTED]',value)


def classify(status, error):
    code=str(error.get('code',''));kind=str(error.get('type',''))
    if code in ('insufficient_quota','credit_balance_exhausted') or kind=='insufficient_quota':return 'QUOTA/CREDITS'
    if 'billing' in code or 'spend_limit' in code or 'usage_limit' in code:return 'BILLING'
    if code=='rate_limit_exceeded':return 'RATE LIMIT'
    if code=='model_not_found':return 'MODEL ACCESS'
    if status in (401,403):return 'PROJECT CONFIGURATION'
    return 'UNKNOWN'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true')
    parser.add_argument('--output',type=Path,help='Optional new dated report; existing files are not overwritten.')
    args=parser.parse_args()
    if not args.live:parser.error('Explicit --live required.')
    if args.output and args.output.exists():parser.error('Output already exists; choose a new report path.')
    from server import load_env
    import providers
    from PIL import Image
    load_env()
    if providers.provider()!='openai' or not os.getenv('OPENAI_API_KEY'):
        print('Configured OpenAI provider/key unavailable. No request made.');return
    report={'checked_at':datetime.datetime.now().astimezone().isoformat(),'requests':[],
            'component':'wearable vision -> existing providers.chat(vision=True); direct diagnostic using synthetic image',
            'scope':'One configured vision request. Text and OpenAI audio not tested; no claim that every endpoint fails.'}
    original=urllib.request.urlopen
    def capture(request,**kwargs):
        endpoint=request.full_url
        if not endpoint.startswith('https://api.openai.com/'):
            raise ValueError('Only official OpenAI endpoint permitted.')
        payload=json.loads(request.data)
        entry={'endpoint':endpoint,'model':payload.get('model'),'modality':'vision'}
        try:
            response=original(request,**kwargs);entry['http_status']=response.status;entry['classification']='SUCCESS';report['requests'].append(entry);return response
        except urllib.error.HTTPError as exc:
            try:body=json.loads(exc.read(65536));error=body.get('error',{})
            except (ValueError,TypeError):error={}
            if not isinstance(error,dict):error={}
            entry.update(http_status=exc.code,error={k:sanitize(error[k]) for k in ('type','code','message') if k in error},
                         headers={k:sanitize(v) for k,v in exc.headers.items() if k.lower() in ('date','x-request-id','retry-after','openai-processing-ms') or k.lower().startswith('x-ratelimit-')},
                         classification=classify(exc.code,error))
            report['requests'].append(entry)
            raise
    image=io.BytesIO();Image.new('RGB',(32,32),'blue').save(image,format='PNG')
    messages=[{'role':'user','content':[{'type':'text','text':'Describe this test image briefly.'},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()}}]}]
    try:
        with patch('urllib.request.urlopen',capture):providers.chat(messages,[],lambda *_:None,threading.Event(),vision=True)
    except providers.ProviderError:
        if not report['requests']:report['transport_error']='No HTTP response captured.'
    destination=args.output or Path(__file__).resolve().parents[1]/'docs/glasses/OPENAI-DIAGNOSIS.json'
    destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
