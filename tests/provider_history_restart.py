"""Fresh TEST Context/App reattaches to existing synthetic data, offline only."""
import json
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import stage4_runtime as runtime
from stage4_provider_fallback import offline_router
root=runtime.validate_root(Path(sys.argv[1]))
data_id=json.loads((root/'STAGE4_TEST-data/STAGE4_TEST.json').read_text())['data_id']
with runtime.exclusion.Lock(root,'core.lock') as lock:
    context=runtime.Context(root,data_id,lock,{'A':['attach','read','request'],'B':['attach','read','request']})
    context.text_router=offline_router()
    app=runtime.construct_app(context)
    authority=runtime.Authority(context,{}, {'A':{},'B':{}})
    def call(client,token,op,args={}):return authority.operation(client,dict(op=op,token=token,args=args),2)
    a=call('A',None,'attach',{'scopes':['attach','read','request']})['token']
    b=call('B',None,'attach',{'scopes':['attach','read','request']})['token']
    result=call('A',a,'last-response-provider')
    assert result['provenance']['final_status']=='COMPLETED'
    assert call('B',b,'last-response-provider')['provenance']['status']=='NO_COMPLETED_RESPONSE'
    with context.response_history.connect() as db:
        operation,response_id=db.execute("SELECT operation,response_id FROM stage4_response_provenance WHERE owner='A' AND mode='text-only' AND status='COMPLETED' ORDER BY timestamp DESC LIMIT 1").fetchone()
    reply=call('A',a,'request-text-only',{'text':'Explain triangles.','operation':operation})
    assert reply['duplicate'] and reply['response_id']==response_id
    assert not context.text_router.records
    assert context.construction_counts=={'App':1,'VoiceEngine':1,'WakeDetector':1,'Store':1}
    evidence={'passed':4,'checks':['fresh process/App history recovery','owner B excluded','duplicate prevented after restart','one App/Store/voice/wake'],
              'scope':'Fresh isolated Context/App process, existing TEST lifetime lock; no named-pipe/Electron/live provider test','last_response':result}
    (root/'fallback-restart-results.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence,indent=2))
