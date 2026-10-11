"""Real isolated Context/App integration with offline transports, no live APIs."""
import json
import os
from pathlib import Path
import sys
import time
import traceback
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import stage4_runtime as runtime
from stage4_provider_fallback import offline_router
from stage4_response_history import History

root=runtime.exclusion.BASE/('TEST-STAGE4-'+uuid.uuid4().hex)
root.mkdir()
(root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
data_id='TEST-'+uuid.uuid4().hex
runtime.provision(root,data_id)
records=[]
with runtime.exclusion.Lock(root,'core.lock') as lock:
    context=runtime.Context(root,data_id,lock,{'A':['attach','read','request'],'B':['attach','read','request']})
    app=runtime.construct_app(context)
    authority=runtime.Authority(context,{}, {'A':{},'B':{}})
    def call(client,token,op,args={}):
        return authority.operation(client,dict(op=op,token=token,args=args),2)
    a=call('A',None,'attach',{'scopes':['attach','read','request']})['token']
    b=call('B',None,'attach',{'scopes':['attach','read','request']})['token']
    def wait(reply):
        wid=reply['request_id']
        assert context.owners.work[wid].done.wait(5), 'worker deadline'
        return call('A',a,'request-status',{'request_id':wid})['events']
    def check(name,fn):
        try:fn();records.append({'check':name,'passed':True})
        except Exception:records.append({'check':name,'passed':False,'traceback':traceback.format_exc()})
    def request(scenario):
        context.text_router=offline_router(scenario)
        reply=call('A',a,'request-text-only',{'text':'Explain triangles.','operation':uuid.uuid4().hex})
        return reply,wait(reply)
    def success(scenario,provider,model,reason):
        reply,events=request(scenario)
        assert sum(e['event']=='assistant.completed' for e in events)==1
        assert not any(e['event'].startswith('tool.') for e in events)
        r=call('A',a,'last-response-provider')['provenance']
        assert r['response_id']==reply['response_id']
        assert r['actual_final_provider']==provider and r['actual_final_model']==model
        assert r['fallback_reason']==reason and r['request_mode']=='text-only'
    check('A I OpenAI actual model persisted',lambda:success('openai','OpenAI','openai-offline-fixture',None))
    check('B J K temporary429 Qwen provenance',lambda:success('temporary','Ollama','qwen3:4b','temporary_rate_limit'))
    check('C quota429 Qwen provenance',lambda:success('quota','Ollama','qwen3:4b','quota_exhausted'))
    def fails(scenario):
        before=call('A',a,'last-response-provider')['provenance']['response_id']
        reply,events=request(scenario)
        assert any(e['event']=='run.failed' for e in events)
        assert not any(e['event']=='assistant.completed' for e in events)
        assert call('A',a,'last-response-provider')['provenance']['response_id']==before
    check('D offline fails honestly',lambda:fails('offline'))
    check('E generation failure not successful',lambda:fails('generation-failure'))
    def isolation():
        assert call('B',b,'last-response-provider')['provenance']['status']=='NO_COMPLETED_RESPONSE'
        try:call('B',a,'last-response-provider')
        except runtime.Denied:pass
        else:raise AssertionError('foreign token accepted')
    check('M owner isolation and token binding',isolation)
    def no_tools():
        reply,events=request('openai')
        run=context.runs[reply['request_id']]
        try:context.check_tool('time_now',run)
        except runtime.Denied as e:assert str(e)=='TEXT_ONLY_NO_TOOLS'
        else:raise AssertionError('tool allowed')
    check('G tool guard rejects text-only',no_tools)
    def normal():
        reply=call('A',a,'request',{'text':'what time is it'})
        events=wait(reply)
        assert any(e['event']=='tool.completed' for e in events)
        assert any(e['event']=='assistant.completed' for e in events)
        assert call('A',a,'last-response-provider')['provenance']['request_mode']=='normal'
    check('F H normal tools unchanged',normal)
    def duplicate():
        context.text_router=offline_router('openai');op=uuid.uuid4().hex
        args={'text':'Explain triangles.','operation':op}
        reply=call('A',a,'request-text-only',args);wait(reply)
        duplicate=call('A',a,'request-text-only',args)
        assert duplicate['duplicate'] and duplicate['response_id']==reply['response_id']
        assert len(context.text_router.records)==1
    check('O duplicate does not execute again',duplicate)
    def cancel():
        context.text_router=offline_router('openai')
        def primary(messages,model,signal,deadline):
            signal.wait(2)
            return {'content':'must not publish','model':'fixture','complete':True}
        context.text_router.primary=primary
        reply=call('A',a,'request-text-only',{'text':'cancel me','operation':uuid.uuid4().hex})
        call('A',a,'cancel',{'request_id':reply['request_id']});events=wait(reply)
        assert not any(e['event']=='assistant.completed' for e in events)
    check('N cancelled response never completed',cancel)
    def restart():
        previous=call('A',a,'last-response-provider')['provenance']
        context.response_history=History(context.data/'jarvis.sqlite3')
        assert call('A',a,'last-response-provider')['provenance']==previous
        newtoken=call('A',None,'attach',{'scopes':['attach','read','request']})['token']
        assert call('A',newtoken,'last-response-provider')['provenance']==previous
        assert 'model:' in call('A',newtoken,'last-response-provider')['answer']
    check('L P deterministic query storage reopen and reauthenticated owner',restart)
    check('ONE App retained',lambda: (_ for _ in ()).throw(AssertionError(context.construction_counts)) if context.construction_counts!={'App':1,'VoiceEngine':1,'WakeDetector':1,'Store':1} else None)
    for worker in context.lifecycle.workers.values():worker.join(5)
    assert not any(w.is_alive() for w in context.lifecycle.workers.values())
    result={'checks':records,'passed':sum(r['passed'] for r in records),'total':len(records),
            'scope':'Real isolated App/Context; trusted authenticated dispatcher seam, no live named-pipe or Electron test. Storage reopen and new authenticated session, not process restart.',
            'root':str(root),'production_changed':False,'live_provider_calls':0}
    (root/'fallback-integration-results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
sys.exit(0 if all(r['passed'] for r in records) else 1)
