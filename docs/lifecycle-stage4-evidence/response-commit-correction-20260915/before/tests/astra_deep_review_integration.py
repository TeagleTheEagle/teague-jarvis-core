"""Offline real TEST App/ownership/history integration. Never reads an API key."""
import json,sys,time,uuid,traceback,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import stage4_runtime as r
from stage4_deep_review import Engine,fixture_transport
root=r.exclusion.BASE/('TEST-STAGE4-'+uuid.uuid4().hex);root.mkdir();(root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
data='TEST-'+uuid.uuid4().hex;r.provision(root,data);checks=[];comparison={}
with r.exclusion.Lock(root,'core.lock') as lock:
 c=r.Context(root,data,lock,{'A':['attach','read','request'],'B':['attach','read','request']});r.construct_app(c)
 c.deep_reviewer=Engine(fixture_transport,mode='STAGE4_TEST');auth=r.Authority(c,{}, {'A':{},'B':{}})
 def call(owner,token,op,args={}):return auth.operation(owner,{'op':op,'token':token,'args':args},2)
 a=call('A',None,'attach',{'scopes':['attach','read','request']})['token'];b=call('B',None,'attach',{'scopes':['attach','read','request']})['token']
 review={'mode':'DEEP_REVIEW','effort':'medium','operation':uuid.uuid4().hex,'task':'Distinguish facts, hypotheses and missing evidence. Propose the smallest read-only follow-up.',
  'evidence':[{'id':'E1','title':'Synthetic incident','text':'Historical root cause unconfirmed. Investigation records one spawn, one acquisition, RECOVERY_REQUIRED and no replacement start. The original traceback and WinError were not recorded. These are recorded findings, not independently verified raw events.'}]}
 def wait(reply):
  assert c.owners.work[reply['request_id']].done.wait(5)
  return call('A',a,'request-status',{'request_id':reply['request_id']})
 def check(label,ok):
  checks.append({'check':label,'passed':bool(ok)})
  assert ok,label
 try:
  start=time.monotonic();ordinary=call('A',a,'request',{'text':json.dumps({'task':review['task'],'evidence':review['evidence']})});ordinary_result=wait(ordinary)
  comparison['routine']={'elapsed_fixture_seconds':time.monotonic()-start,'result':ordinary_result,'provider_provenance':call('A',a,'last-response-provider'),'actual_model_quality':None,'actual_provider_latency':None,'actual_usage':None,'actual_cost':None}
  start=time.monotonic();reply=call('A',a,'deep-review',{'review':review});result=wait(reply)
  provenance=call('A',a,'response-provider',{'response_id':reply['response_id']})
  comparison['deep_review']={'elapsed_fixture_seconds':time.monotonic()-start,'result':result,'provider_provenance':provenance,'actual_model_quality':None,'actual_provider_latency':None,'actual_usage':None,'actual_cost':None}
  check('completed response with persisted actual envelope identity',provenance['provenance']['final_status']=='COMPLETED' and provenance['provenance']['provider_response_id']=='resp_fixture_final')
  check('simulation never claimed live',provenance['provenance']['simulated'] is True and provenance['answer'].startswith('TEST simulation:'))
  check('explicit routing reason and effort',provenance['provenance']['routing_reason']=='explicit_DEEP_REVIEW' and provenance['provenance']['reasoning_effort']=='medium')
  check('only packet reader used',provenance['provenance']['tool_reads']==['E1'])
  check('no general tools executed',not any(e['event'].startswith('tool.') for e in result['events']))
  try:c.check_tool('time_now',c.runs[reply['request_id']])
  except r.Denied:check('general tool guard denies deep review',True)
  else:check('general tool guard denies deep review',False)
  try:call('B',b,'response-provider',{'response_id':reply['response_id']})
  except ValueError:check('foreign owner provenance denied',True)
  else:check('foreign owner provenance denied',False)
  try:call('B',b,'request-status',{'request_id':reply['request_id']})
  except r.Denied:check('foreign request status denied',True)
  else:check('foreign request status denied',False)
  dup=call('A',a,'deep-review',{'review':review});check('duplicate operation no new generation',dup['duplicate'] and dup['response_id']==reply['response_id'])
  from stage4_response_history import History
  c.response_history=History(c.data/'jarvis.sqlite3');a=call('A',None,'attach',{'scopes':['attach','read','request']})['token']
  check('provenance survives history reopen and new authenticated session',call('A',a,'response-provider',{'response_id':reply['response_id']})==provenance)
  normal=call('A',a,'request',{'text':'what time is it'});normal_events=wait(normal)['events']
  check('ordinary tools unchanged',any(e['event']=='tool.completed' for e in normal_events))
  started=threading.Event()
  def slow(payload,cancel,deadline):started.set();cancel.wait(2);return fixture_transport(payload,cancel,deadline)
  c.deep_reviewer=Engine(slow,mode='STAGE4_TEST');review['operation']=uuid.uuid4().hex
  cancelreply=call('A',a,'deep-review',{'review':review});assert started.wait(2)
  call('A',a,'cancel',{'request_id':cancelreply['request_id']});cancelled=wait(cancelreply)
  check('cancellation no successful final',not any(e['event']=='assistant.completed' for e in cancelled['events']) and call('A',a,'response-provider',{'response_id':cancelreply['response_id']})['provenance']['final_status']=='CANCELLED')
  check('one App Store Voice Wake',c.construction_counts=={'App':1,'Store':1,'VoiceEngine':1,'WakeDetector':1})
 except Exception:checks.append({'check':'integration exception','passed':False,'traceback':traceback.format_exc()})
 finally:
  for worker in c.lifecycle.workers.values():worker.join(5)
  check('all TEST workers ended',not any(w.is_alive() for w in c.lifecycle.workers.values()))
  report={'checks':checks,'comparison':comparison,'fixed_task':review,'rubric':[
   'Cites record IDs accurately','Distinguishes findings from hypotheses','Does not infer historical cause from later evidence',
   'Identifies missing traceback/native error','Proposes read-only next step without claiming execution'],
   'comparison_status':'OFFLINE_CONTRACT_ONLY; no model-quality superiority claim; paid A/B not authorized',
   'root':str(root),'live_API_calls':0,'credential_read':False}
  (root/'astra-integration.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
sys.exit(0 if all(x['passed'] for x in checks) else 1)
