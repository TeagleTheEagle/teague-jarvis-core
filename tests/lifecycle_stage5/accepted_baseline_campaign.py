"""Stage 5 harness: stage exact accepted application bytes, then run ordered gates.

No runtime edits. Historical campaign is reused as test logic only.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,uuid
R=Path(__file__).resolve().parents[2]
D=R/'docs/stage5-accepted-baseline-20260917'
BASE=R/'docs/deployment-completion-20260917/final-blockers'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def prepare():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='d6199756f1e1f4495ad6c3de457660cbf1f03e84'
    D.mkdir(exist_ok=False)
    app=R.parent/('TEST-STAGE5-APP-'+uuid.uuid4().hex);app.mkdir()
    rows=json.loads((BASE/'final-integrity.json').read_text())['accepted_source']
    for row in rows:
        source=BASE/row['path'];assert digest(source)==row['sha256']
        target=app/Path(row['path']).relative_to('accepted-app');target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target);assert digest(target)==row['sha256']
    fixture=R/'tests/lifecycle_stage4/fixtures.py'
    expected=next(x['after'] for x in json.loads((BASE/'final-integrity.json').read_text())['correction_source'] if x['path']=='tests/lifecycle_stage4/fixtures.py')
    assert digest(fixture)==expected
    harness=[]
    for name in ('tests/lifecycle_stage4/fixtures.py','tests/lifecycle_stage5/campaign.py'):
        source=R/name;target=app/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        harness.append({'path':name,'sha256':digest(target),'role':'accepted fixture' if name.endswith('fixtures.py') else 'historical test driver; not historical evidence'})
    for name in ('tests/lifecycle_stage1/evidence','docs/lifecycle-stage4-evidence','docs/lifecycle-stage5-evidence'):(app/name).mkdir(parents=True,exist_ok=True)
    record={'baseline':'d6199756f1e1f4495ad6c3de457660cbf1f03e84','app':str(app),'source':rows,'harness':harness,'historical_evidence_reused':False}
    (D/'baseline.json').write_text(json.dumps(record,indent=2));print(json.dumps({'5A':'PASS','app':str(app),'application_files':len(rows)}))

def gate(mode):
    rec=json.loads((D/'baseline.json').read_text());app=Path(rec['app'])
    for row in rec['source']:assert digest(app/Path(row['path']).relative_to('accepted-app'))==row['sha256']
    sys.path.insert(0,str(app/'tests/lifecycle_stage5'))
    from campaign import Campaign
    class Ordered(Campaign):
        def full(self):
            if mode=='5B':
                for i in range(4):self.race_round(i+1)
                for stage in ('before-intent','intent','claimed'):self.fault_case(stage)
                for i in range(3):self.fault_case('spawned',i+1)
                for i in range(3):self.crash_round(i+1)
                self.unknown()
            elif mode=='5C':
                self.security_capacity()
                for scenario in ('openai','temporary','quota','offline','generation-failure'):self.provider_recovery(scenario)
                for i in range(4):self.reconnect_shutdown_race(i+1)
            else:raise ValueError(mode)
    c=Ordered();c.path=D/(mode+'-'+uuid.uuid4().hex+'.json');c.run('full')
    for row in rec['source']:assert digest(app/Path(row['path']).relative_to('accepted-app'))==row['sha256']

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    else:gate(sys.argv[1])
