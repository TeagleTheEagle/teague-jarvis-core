"""Approved isolated reliability combinations against unchanged Stage 4 runtime.

No production launch, provider network, secret archive, forced process cleanup,
or authentication/clock/runtime override. Reuses the reviewed TEST coordinator.
"""
import concurrent.futures, hashlib, json, os, pathlib, sqlite3, sys, threading, time, traceback, uuid
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/lifecycle_stage4'))
from fixtures import RestartCampaign
OUT=ROOT/'docs/lifecycle-stage5-evidence';OUT.mkdir(exist_ok=True)

class Campaign(RestartCampaign):
    def __init__(self):
        super().__init__();self.path=OUT/('integrated-'+uuid.uuid4().hex+'.json')
    def status(self,core,identity,owner,token,work):
        until=time.monotonic()+8
        while True:
            status=self.core_call(core,identity,owner,'request-status',{'request_id':work},token)
            if status.get('done'):return status
            if time.monotonic()>until:raise TimeoutError('Bounded TEST request completion')
            time.sleep(.01)
    def inspect_db(self,root):
        with sqlite3.connect((root/'STAGE4_TEST-data/jarvis.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
            self.check('SQLite integrity after combined faults',db.execute('PRAGMA quick_check').fetchone()[0]=='ok')
            rows=db.execute('SELECT response_id,owner,session,status,text,provenance FROM stage4_response_provenance').fetchall()
            messages=dict(db.execute("SELECT id,content FROM messages WHERE role='assistant'"))
            completed=[]
            for rid,owner,session,status,text,raw in rows:
                proof=json.loads(raw or '{}')
                if status=='COMPLETED':
                    mid=proof.get('message_id');completed.append(mid)
                    self.check('durable completed response and provenance agree',mid in messages and messages[mid]==text,response_id=rid,owner=owner,status=status,message_id=mid)
                else:
                    self.check('failed/cancelled/pending response has no false success',text is None and not proof.get('message_id') and not proof.get('actual_final_provider'),response_id=rid,status=status)
            self.check('no orphan or duplicate assistant messages',len(set(completed))==len(completed) and set(completed)==set(messages),responses=len(rows),assistant_messages=len(messages))
            return {'response_rows':len(rows),'assistant_messages':len(messages),'statuses':[x[3] for x in rows]}
    def security_capacity(self):
        root,data=self.namespace();core=self.core_config(data);c,identity=self.start(root,core)
        controller=self.attach(core,identity,'controller');a=self.attach(core,identity,'teague');b=self.attach(core,identity,'intelligence')
        for label,owner,op,args,token in [
            ('foreign token binding','intelligence','shared',{},a),
            ('ordinary shutdown','teague','shutdown',{'operation':uuid.uuid4().hex},a),
            ('scope escalation','teague','attach',{'scopes':['attach','lifecycle']},None),
            ('malformed text','teague','request',{'text':[]},a),
            ('oversized text','teague','request',{'text':'x'*12001},a),
            ('extra request authority','teague','request',{'text':'what time is it','owner':'controller'},a),
            ('unknown operation','teague','not-an-operation',{},a)]:
            self.check('authenticated malformed/authority request denied: '+label,self.denied(lambda:self.core_call(core,identity,owner,op,args,token)))
        self.check('malformed requests preserve lifecycle service',self.core_call(core,identity,'controller','lifecycle-status',token=controller)['state']=='RUNNING')
        response=self.core_call(core,identity,'teague','request',{'text':'what time is it'},a)
        status=self.status(core,identity,'teague',a,response['request_id'])
        self.check('valid request still succeeds after rejected inputs',status['response_status']=='COMPLETED')
        self.check('foreign stream inspection denied',self.denied(lambda:self.core_call(core,identity,'intelligence','request-status',{'request_id':response['request_id']},b)))
        self.check('foreign cancellation denied',self.denied(lambda:self.core_call(core,identity,'intelligence','cancel',{'request_id':response['request_id']},b)))
        # Reach the actual Core's 128-session boundary, not a model substitute.
        tokens=[]
        for _ in range(125):tokens.append(self.attach(core,identity,'teague'))
        self.check('128-session actual runtime limit rejects excess',self.denied(lambda:self.core_call(core,identity,'teague','attach',{'scopes':core['enrollments']['teague']['scopes']})))
        self.check('preexisting controller survives session exhaustion',self.core_call(core,identity,'controller','lifecycle-status',token=controller)['state']=='RUNNING')
        self.check('detach frees exhausted session capacity',self.core_call(core,identity,'teague','detach',token=a)['result']=='DETACHED')
        fresh=self.attach(core,identity,'teague')
        self.check('detached token stays rejected after capacity recovery',self.denied(lambda:self.core_call(core,identity,'teague','shared',token=a)))
        self.check('fresh session cannot inspect old request',self.denied(lambda:self.core_call(core,identity,'teague','request-status',{'request_id':response['request_id']},fresh)))
        result=self.core_call(core,identity,'controller','shutdown',{'operation':uuid.uuid4().hex},controller)
        self.check('reserved controller can drain at full session limit',result['state'] in ('DRAINING','FINALIZING'))
        self.wait_dead(root,identity);self.close(c);self.inspect_db(root)
    def provider_recovery(self,scenario):
        root,data=self.namespace();core=self.core_config(data);core['text_provider_scenario']=scenario
        c,identity=self.start(root,core);a=self.attach(core,identity,'teague');b=self.attach(core,identity,'intelligence')
        operation=uuid.uuid4().hex;args={'operation':operation,'text':'Explain that this is a simulated TEST response without taking any action.'}
        result=self.core_call(core,identity,'teague','request-text-only',args,a)
        status=self.status(core,identity,'teague',a,result['request_id'])
        expected='FAILED' if scenario in ('offline','generation-failure') else 'COMPLETED'
        self.check('actual TEST provider failure/success classified',status['response_status']==expected,scenario=scenario,status=status['response_status'])
        duplicate=self.core_call(core,identity,'teague','request-text-only',args,a)
        self.check('duplicate provider request never generates twice',duplicate['duplicate'] is True and duplicate['response_id']==result['response_id'])
        self.check('idempotency content conflict denied',self.denied(lambda:self.core_call(core,identity,'teague','request-text-only',{**args,'text':'different'},a)))
        self.check('foreign response provenance denied',self.denied(lambda:self.core_call(core,identity,'intelligence','response-provider',{'response_id':result['response_id']},b)))
        proof=self.core_call(core,identity,'teague','last-response-provider',token=a)['provenance']
        if expected=='COMPLETED':
            provider='OpenAI' if scenario=='openai' else 'Ollama'
            self.check('persisted final provider truthful and simulated',proof['actual_final_provider']==provider and proof['simulated'] is True,scenario=scenario,actual_provider=proof['actual_final_provider'],actual_model=proof['actual_final_model'],fallback_reason=proof.get('fallback_reason'))
            self.check('cancellation cannot erase committed response',self.core_call(core,identity,'teague','cancel',{'request_id':result['request_id']},a)['response_status']=='COMPLETED')
        else:self.check('provider failure does not invent successful last response',proof['status']=='NO_COMPLETED_RESPONSE')
        self.core_call(core,identity,'teague','detach',token=a)
        fresh=self.attach(core,identity,'teague')
        self.check('reconnect does not restore request authority',self.denied(lambda:self.core_call(core,identity,'teague','cancel',{'request_id':result['request_id']},fresh)))
        self.stop(root,core,identity);self.close(c);before=self.snapshot(root);self.inspect_db(root)
        next_core=self.core_config(data);c,new=self.start(root,next_core,identity)
        self.fresh_state(root,next_core,new,a,result['request_id'])
        token=self.attach(next_core,new,'teague');after=self.core_call(next_core,new,'teague','last-response-provider',token=token)['provenance']
        self.check('provider result survives restart without stale authority',after==proof,scenario=scenario)
        self.stop(root,next_core,new);self.close(c)
        self.check('provider recovery preserves persistent state',before==self.snapshot(root));self.inspect_db(root)
    def reconnect_shutdown_race(self,round_):
        root,data=self.namespace();core=self.core_config(data);c,identity=self.start(root,core)
        a=self.attach(core,identity,'teague');controller=self.attach(core,identity,'controller')
        self.core_call(core,identity,'teague','detach',token=a)
        gate=threading.Barrier(2)
        def attach():
            gate.wait()
            try:return self.core_call(core,identity,'teague','attach',{'scopes':core['enrollments']['teague']['scopes']})
            except (OSError,self.r.authentication.Denied,self.r.Denied):return {'result':'DISCONNECTED'}
        def stop():
            gate.wait();return self.core_call(core,identity,'controller','shutdown',{'operation':uuid.uuid4().hex},controller)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            f=pool.submit(attach);s=pool.submit(stop);attachment=f.result();shutdown=s.result()
        self.check('shutdown/reconnect race has legal ordering',attachment.get('result') in ('ATTACHED','DENIED','DISCONNECTED') and shutdown['state'] in ('DRAINING','FINALIZING'),round=round_,attach_outcome=attachment.get('result'),shutdown_state=shutdown['state'])
        self.wait_dead(root,identity);self.close(c);next_core=self.core_config(data);c,new=self.start(root,next_core,identity)
        self.fresh_state(root,next_core,new,attachment.get('token',a))
        self.check('restart race produces distinct epoch',new['startup_epoch']!=identity['startup_epoch'])
        self.stop(root,next_core,new);self.close(c);self.inspect_db(root)
    def full(self):
        self.security_capacity()
        for scenario in ('openai','temporary','quota','offline','generation-failure'):self.provider_recovery(scenario)
        for i in range(4):self.reconnect_shutdown_race(i+1)
        # Existing exact real-process fault fixtures, without changing semantics.
        for i in range(4):self.race_round(i+1)
        for stage in ('before-intent','intent','claimed'):self.fault_case(stage)
        for i in range(3):self.fault_case('spawned',i+1)
        for i in range(3):self.crash_round(i+1)
        self.unknown()

if __name__=='__main__':
    campaign=Campaign();campaign.run('full')
