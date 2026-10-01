"""Read-only post-failure census; no attachment, stop, retry or process mutation."""
from pathlib import Path
import hashlib,json,sys
D=Path(__file__).resolve().parent;R=D.parents[1]
baseline=json.loads((D/'baseline.json').read_text());app=Path(baseline['app'])
sys.path.insert(0,str(app/'tests/lifecycle_stage2'))
import pipe_transport as t
pins={};roots=set();results=[]
def walk(x):
    if isinstance(x,dict):
        if isinstance(x.get('pid'),int) and isinstance(x.get('created'),int) and isinstance(x.get('exe_digest'),str):
            pin={k:x[k] for k in ('pid','created','exe_digest')};pins[tuple(pin.values())]=pin
        for v in x.values():walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
for p in sorted(D.glob('5?-*.json')):
    x=json.loads(p.read_text());walk(x);roots.update(x['roots'])
    results.append({'file':p.name,'records':len(x['records']),'pass':sum(bool(r['passed']) for r in x['records']),'fail':sum(not r['passed'] for r in x['records'])})
out=D/'failure-metadata';out.mkdir(exist_ok=True);artifacts=[]
for rootstr in sorted(roots):
    root=Path(rootstr);assert root.is_relative_to(app) and (root/'TEST_ONLY').read_text()=='NO PRODUCTION SERVICES'
    artifacts += [str(p) for p in root.glob('coordinator-*.json*')]
    for p in root.glob('*.json'):
        if p.name in ('core.json','stage4-ready.json') or p.name.startswith('coordinator-') or 'start_verified' in p.name or 'start_spawned' in p.name or 'core_acquired' in p.name:
            x=json.loads(p.read_text());walk(x)
            # Only whitelisted public identity/event records; no grants/configuration/session material.
            if p.name!='stage4-ready.json':
                dest=out/(root.name+'-'+p.name)
                if dest.exists():assert dest.read_bytes()==p.read_bytes()
                else:dest.write_bytes(p.read_bytes())
census=[]
for pin in pins.values():
    try:current=t.identity(pin['pid']);state='LIVE' if current==pin else 'PID_REUSED'
    except Exception as e:
        current={'exception':type(e).__name__,'errno':getattr(e,'errno',None)}
        state='EXITED' if getattr(e,'errno',None)==87 or str(e)=='PROCESS_DEAD' else 'UNCERTAIN'
    census.append({'recorded':pin,'current':current,'state':state})
hashes=[]
for row in baseline['source']:
    p=app/Path(row['path']).relative_to('accepted-app');h=hashlib.sha256(p.read_bytes()).hexdigest()
    hashes.append({'path':row['path'],'sha256':h,'unchanged':h==row['sha256']})
report={'gates':results,'census':census,'live':[x for x in census if x['state']=='LIVE'],'uncertain':[x for x in census if x['state']=='UNCERTAIN'],'readiness_artifacts':artifacts,'source_hashes':hashes,'cleanup':'NO MUTATION; retained identities require review'}
(D/'failure-census.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'gates':results,'live':report['live'],'uncertain':len(report['uncertain']),'readiness':len(artifacts),'source_unchanged':all(x['unchanged'] for x in hashes)},indent=2))
