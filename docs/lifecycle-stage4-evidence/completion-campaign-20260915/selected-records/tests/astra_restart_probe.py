"""Fresh offline TEST Core composition verifies durable review provenance."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import stage4_runtime as r
from stage4_deep_review import Engine,fixture_transport
root=r.validate_root(Path(sys.argv[1]));data=json.loads((root/'STAGE4_TEST-data/STAGE4_TEST.json').read_text())['data_id']
prior=json.loads((root/'astra-integration.json').read_text())
original=prior['comparison']['deep_review']['provider_provenance']
with r.exclusion.Lock(root,'core.lock') as lock:
 c=r.Context(root,data,lock,{'A':['attach','read','request'],'B':['attach','read']});r.construct_app(c)
 c.deep_reviewer=Engine(fixture_transport,mode='STAGE4_TEST');auth=r.Authority(c,{}, {'A':{},'B':{}})
 def call(owner,token,op,args={}):return auth.operation(owner,{'op':op,'token':token,'args':args},2)
 a=call('A',None,'attach',{'scopes':['attach','read','request']})['token'];b=call('B',None,'attach',{'scopes':['attach','read']})['token']
 rid=original['provenance']['response_id'];assert call('A',a,'response-provider',{'response_id':rid})==original
 try:call('B',b,'response-provider',{'response_id':rid})
 except ValueError:pass
 else:raise AssertionError('foreign provenance')
 with c.response_history.connect() as db:operation=db.execute('SELECT operation FROM stage4_response_provenance WHERE response_id=?',(rid,)).fetchone()[0]
 review=prior['fixed_task'];review['operation']=operation
 duplicate=call('A',a,'deep-review',{'review':review});assert duplicate['duplicate'] and duplicate['response_id']==rid and not c.lifecycle.workers
 assert c.construction_counts=={'App':1,'Store':1,'VoiceEngine':1,'WakeDetector':1}
 print(json.dumps({'passed':4,'checks':['fresh TEST App provenance by ID','owner isolation','idempotency survives restart without execution','one TEST App/Store/Voice/Wake'],'production_changed':False}))
