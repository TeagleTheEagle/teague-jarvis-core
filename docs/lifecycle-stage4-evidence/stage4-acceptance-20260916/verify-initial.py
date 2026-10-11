"""Read-only reconciliation of existing acceptance evidence; no Core/test launch."""
import collections, datetime, hashlib, json, pathlib, sys
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[2]; BASE=OUT.parent
sys.path.insert(0,str(ROOT))
import stage4_runtime as r
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
human=BASE/'human-lifecycle-6738c043c1194d60820000d6a741a479.json'
failed=BASE/'human-lifecycle-7cc0db70a76149c9954eb82fc4c0c5b5.json'
data=load(human); records=data['records']; checks=[]
def check(name,ok,**evidence):
    checks.append(dict(check=name,passed=bool(ok),**evidence));write('verification.json',checks)
    assert ok,name
check('original failed human record unchanged',sha(failed)=='828772b7b257fd60fc1fd494ba20f05c54477e50a8e067edf4d300d720816a2c')
check('all fresh human records pass',all(x['passed'] for x in records),records=len(records),sha256=sha(human))
check('TEST-only no paid calls or physical media',data['test_only'] and not data['production_changed'] and data['paid_calls']==0 and not data['physical_media'])
names=[x['case'] for x in records]
ordered=['human selected exact TEST identity','human explicit DENIAL','human explicit CRASH','human explicit EMERGENCY','human explicit SHUTDOWN','human session completed']
check('operator sequence complete and ordered',[names.index(x) for x in ordered]==sorted(names.index(x) for x in ordered) and all(records[names.index(x)]['operator_input'] for x in ordered))
root=pathlib.Path(data['roots'][0]);r.validate_root(root)
check('fresh namespace distinct from failed run',str(root) not in load(failed)['roots'])
receipt=records[names.index('shutdown reached authority through actual enrolled Electron')]['receipt']
raw=list(root.glob('*-ordinary_shutdown_policy.json'))
check('exact raw policy receipt corroborates report',len(raw)==1 and load(raw[0])==receipt)
check('actual authenticated Electron denied by lifecycle policy',receipt['policy_reached'] and receipt['reason']=='SCOPE' and receipt['state']=='RUNNING' and receipt['authenticated_client']==receipt['session_client']=='teague' and 'lifecycle' not in receipt['scopes'])
drained=list(root.glob('*-stage4_drained.json'))
check('raw drain event records zero outstanding work',len(drained)==1 and load(drained[0])['work']==0 and not load(drained[0])['production'])
baseline=load(BASE/'human-denial-correction-20260915/source-after.json')
source=[]
for item in baseline:
    actual=sha(ROOT/item['path']);source.append(dict(path=item['path'],sha256=actual,expected=item['sha256'],unchanged=actual==item['sha256']))
write('source-baseline.json',source)
check('27 final reviewed source/executable hashes unchanged',len(source)==27 and all(x['unchanged'] for x in source))
additional=[]
for manifest,paths in [('ipc-records-manifest.json',{'tests/lifecycle_stage1/harness.py','tests/lifecycle_stage1/test_stage1.py'}),('core-pin-source-manifest.json',{'stage4_native/peer_identity.cc','stage4_native/CMakeLists.txt'})]:
    for item in load(BASE/manifest)['files']:
        name=item['path'].replace('\\','/')
        if name in paths:additional.append(dict(path=name,sha256=sha(ROOT/name),expected=item['sha256'],baseline=manifest))
write('additional-source-verification.json',additional)
check('accepted IPC and native bridge source unchanged',len(additional)==4 and all(x['sha256']==x['expected'] for x in additional))
identities={}
def visit(x):
    if isinstance(x,dict):
        if all(k in x for k in ('pid','created','exe_digest')):
            v={k:x[k] for k in ('pid','created','exe_digest')};identities[(v['pid'],v['created'])]=v
        for v in x.values():visit(v)
    elif isinstance(x,list):
        for v in x:visit(v)
visit(data);cleanup=[]
for ident in identities.values():
    try:
        now=r.transport.identity(ident['pid']);status='RETAINED' if now==ident else 'PID_REUSED_NOT_TOUCHED'
    except (OSError,r.transport.Rejected):
        now=None;status='EXITED' if r.exclusion.process_identity(ident['pid']) is None else 'UNCONFIRMED'
    cleanup.append(dict(expected=ident,observed=now,status=status))
write('cleanup.json',cleanup)
check('all four human TEST identities exited',len(cleanup)==4 and all(x['status'] in ('EXITED','PID_REUSED_NOT_TOUCHED') for x in cleanup),forced_termination=False)
python=pathlib.Path(sys._base_executable)
check('native Python executable matches recorded Core',sha(python)==receipt['core_identity']['exe_digest'],path=str(python),sha256=sha(python))
matrix=load(BASE/'completion-campaign-20260915/requirement-to-evidence.json')
for row in matrix:
    if row['disposition']=='OPEN':
        check('only pending matrix cell was HUMAN',row['id']=='HUMAN')
        row.update(disposition='PASS',evidence=human.name,limitations='Actual owner-operated SELECT / DENIAL / CRASH / EMERGENCY / SHUTDOWN; no physical voice claim. Source and cleanup verified in stage4-acceptance-20260916/verification.json.')
check('no in-scope acceptance cell remains open or failed',all(x['disposition'] in ('PASS','DEFERRED','LIMITATION') for x in matrix))
write('requirement-to-evidence.json',matrix)
write('summary.json',dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stage4='CLOSED — TEST acceptance',human_report=str(human),human_records=len(records),matrix_counts=dict(collections.Counter(x['disposition'] for x in matrix)),source_paths=len(source)+len(additional),production_changed=False,acceptance_commit_created=False,stage5_authorized=True,checks=len(checks),raw_evidence=[str(x.relative_to(ROOT)) for x in raw+drained],limitations=['Historical failures preserved; exact historical Stage 1 cause unconfirmed.','Physical media, approvals and uploads remain explicitly deferred.','Cross-session/other-user/remote-host limitations unchanged.','Hash reconciliation binds reviewed sources and recorded executable identities, not a retroactive exhaustive binary attestation.']))
print(json.dumps(load(OUT/'summary.json')))
