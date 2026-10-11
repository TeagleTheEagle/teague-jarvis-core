"""Bounded TEST harness reconciliation of an uncertain execute acknowledgement."""
from pathlib import Path
import hashlib,json,sys,time,uuid,traceback
R=Path(__file__).resolve().parents[2];D=R/'docs/stage5-continuation-20260917'
baseline=json.loads((R/'docs/stage5-accepted-baseline-20260917/baseline.json').read_text());APP=Path(baseline['app'])
for row in baseline['source']:
    assert hashlib.sha256((APP/Path(row['path']).relative_to('accepted-app')).read_bytes()).hexdigest()==row['sha256']
sys.path.insert(0,str(APP/'tests/lifecycle_stage5'))
from campaign import Campaign
MODE=sys.argv[1]
class Continued(Campaign):
    def __init__(self):
        super().__init__();self.path=D/(MODE+'-'+uuid.uuid4().hex+'.json');self.timeline=[]
    def stamp(self,event,**fields):
        self.timeline.append({'event':event,'time_ns':time.time_ns(),'monotonic_ns':time.monotonic_ns(),**fields})
        (D/(self.path.stem+'-timeline.json')).write_text(json.dumps(self.timeline,indent=2))
    def start(self,root,core,prior=None):
        c=self.coordinator(root,core);g=self.issue(c,prior);operation=g['operation']
        self.stamp('T0 execute request',operation=operation,namespace=root.name)
        try:
            reply=self.execute(c,g)
            self.stamp('T8 execute reply',operation=operation,result=reply.get('result'))
            if MODE=='ack-loss' and reply.get('result')=='AUTHORIZATION_CONSUMED':
                self.stamp('TEST injected acknowledgement loss',operation=operation)
                raise self.r.transport.Rejected('IO_TIMEOUT')
            self.check('authorization durably consumed',reply.get('result')=='AUTHORIZATION_CONSUMED')
            state=self.settle(c)
        except self.r.transport.Rejected as exc:
            if str(exc)!='IO_TIMEOUT':raise
            self.stamp('T8 timeout; execute NOT replayed',operation=operation,synthetic=MODE=='ack-loss')
            # Existing authenticated status only, with unchanged bounded settle.
            state=self.settle(c)
            self.check('uncertain execute reconciles same operation',state.get('operation')==operation and state.get('result')=='STARTED')
            intent=self.r._start_read(root,operation,'intent');verified=self.r._start_read(root,operation,'verified')
            self.check('reconciled intent is consumed and bound',intent.get('grant_consumed') is True and intent['operation']==operation and intent['coordinator']==c['ready']['identity'] and intent['namespace']==root.name and intent['data_id']==core['data_id'])
            self.check('reconciled authenticated identity matches durable verification',verified['identity']==state['identity'])
        self.check('actual TEST Core started',state['result']=='STARTED',state=state)
        identity=state['identity'];self.cores.append((root,core,identity))
        self.stamp('verified Core tracked for cleanup',operation=operation,identity=identity)
        self.check('replayed authorization denied',self.execute(c,g).get('result')=='DENIED')
        ready=self.r.exclusion.read(root/'stage4-ready.json')
        self.check('exactly one App Store VoiceEngine WakeDetector',all(ready[k]==1 for k in ('app_instances','store_instances','voice_instances','wake_instances')))
        return c,identity
    def full(self):
        if MODE=='ack-loss':
            for _ in range(2):self.smoke()
        elif MODE=='5C':
            self.security_capacity()
            for scenario in ('openai','temporary','quota','offline','generation-failure'):self.provider_recovery(scenario)
            for i in range(4):self.reconnect_shutdown_race(i+1)
        else:raise ValueError(MODE)
if __name__=='__main__':
    c=Continued();c.run('full')
    for row in baseline['source']:
        assert hashlib.sha256((APP/Path(row['path']).relative_to('accepted-app')).read_bytes()).hexdigest()==row['sha256']
