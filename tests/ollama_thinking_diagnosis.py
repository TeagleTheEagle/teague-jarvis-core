"""Two bounded diagnostic local requests, differing ONLY in think flag."""
import json,sys,time,threading,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage4_ollama_transport import Transport,MODEL
dest=Path(__file__).resolve().parents[1]/'docs/ollama-acceptance-diagnosis';dest.mkdir(exist_ok=True)
transport=Transport(mode='STAGE4_TEST');records=[]
for think in (False,True):
 payload={'model':MODEL,'messages':[{'role':'system','content':'Text-only TEST response. No tools, browsing, device actions or external actions are available. Do not claim to have performed them.'},{'role':'user','content':'What is 2 plus 2? Answer only with the number.'}],
  'think':think,'stream':False,'keep_alive':30,'options':{'num_predict':256,'num_ctx':4096,'temperature':0}}
 start=time.monotonic()
 try:
  response=transport.request('/api/chat',payload,threading.Event(),start+20)
  path=dest/('raw-think-'+str(think).lower()+'.json');path.write_text(json.dumps(response,indent=2))
  message=response.get('message',{});content=message.get('content','');thinking=message.get('thinking','')
  records.append({'think_requested':think,'elapsed_seconds':time.monotonic()-start,'message_fields':list(message),
   'thinking_characters':len(thinking),'content_characters':len(content),'content_is_4':content.strip()=='4',
   'content_has_closing_think': '</think>' in content,'done':response.get('done'),'done_reason':response.get('done_reason'),
   'model':response.get('model'),'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 except Exception as exc:records.append({'think_requested':think,'failure':type(exc).__name__,'detail':str(exc),'elapsed_seconds':time.monotonic()-start})
 (dest/'thinking-comparison.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
