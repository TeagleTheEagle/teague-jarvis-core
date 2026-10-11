"""Read-only source/process verification; writes only this diagnostic report."""
import ast
import datetime
import hashlib
import json
import pathlib
import sys

OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[2]
BASE=OUT.parent
sys.path.insert(0,str(ROOT))
import stage4_runtime as runtime

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2),encoding='utf-8')

before=load(OUT/'before-hashes.json')
changed={'stage4_client.cjs','tests/lifecycle_stage4/fixtures.py'}
source=[]
for item in before['validated_baseline']:
    actual=sha(ROOT/item['path'])
    source.append({'path':item['path'],'before':item['sha256'],'sha256':actual,
                   'unchanged':actual==item['sha256'],'reviewed_change':item['path'] in changed})
    assert actual==item['sha256'] or item['path'] in changed,item['path']
failed=pathlib.Path(before['failed_human_evidence']['path'])
assert sha(failed)==before['failed_human_evidence']['sha256']
write('source-after.json',source)

reports=[failed,BASE/'human-denial-probe-975dc5ebc14240ba9a3ff8839f604b92.json',
         BASE/'electron-app-probe-993086388f7546c2b0865e27c9eb2863.json']
identities={}
def visit(value):
    if isinstance(value,dict):
        if all(k in value for k in ('pid','created','exe_digest')):
            record={k:int(value[k]) if k=='created' else value[k] for k in ('pid','created','exe_digest')}
            identities[(record['pid'],record['created'])]=record
        for item in value.values():visit(item)
    elif isinstance(value,list):
        for item in value:visit(item)
for path in reports:
    data=load(path);visit(data)
    for name in data.get('roots',[]) + ([data['root']] if 'root' in data else []):
        root=pathlib.Path(name);runtime.validate_root(root)
        ready=root/'stage4-ready.json'
        if ready.exists():visit(load(ready))
statuses=[]
for record in identities.values():
    try:
        now=runtime.transport.identity(record['pid'])
        status='RETAINED' if now==record else 'PID_REUSED_NOT_TOUCHED'
    except (OSError,runtime.transport.Rejected):
        now=None
        status='EXITED' if runtime.exclusion.process_identity(record['pid']) is None else 'UNCONFIRMED'
    statuses.append({'expected':record,'observed':now,'status':status})
write('cleanup.json',{'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'identities':statuses,'forced_termination':False})
assert all(item['status'] in ('EXITED','PID_REUSED_NOT_TOUCHED') for item in statuses)

functions_before={n.name:ast.dump(n,include_attributes=False) for n in ast.parse((OUT/'before/tests/lifecycle_stage4/fixtures.py').read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
functions_after={n.name:ast.dump(n,include_attributes=False) for n in ast.parse((ROOT/'tests/lifecycle_stage4/fixtures.py').read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
write('scope-verification.json',{'modified_existing_fixture_symbols':[name for name in functions_before if functions_before[name]!=functions_after.get(name)],
 'added_fixture_symbols':sorted(set(functions_after)-set(functions_before)),
 'protected_unchanged':sum(item['unchanged'] for item in source),'source_paths_checked':len(source),
 'original_failed_human_sha256':sha(failed),'human_acceptance':'OPEN — fresh human sequence required',
 'production_changed':False,'stage5_started':False})
print(json.dumps({'recorded_identities':len(statuses),'all_exited':True,'source_paths':len(source),
                  'protected_unchanged':sum(item['unchanged'] for item in source),'failed_human_unchanged':True}))
