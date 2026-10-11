"""Read-only TEST process census and nonsecret evidence collection."""
from pathlib import Path
import hashlib,json,re,sys
D=Path(__file__).resolve().parent;R=D.parents[2]
sys.path.insert(0,str(R/'tests/lifecycle_stage2'))
import pipe_transport as transport
files=set()
for p in D.glob('*.log'):
    text=p.read_text(encoding='utf8',errors='replace')
    for line in text.splitlines():
        if line.startswith('EVIDENCE '):files.add(Path(line[9:].strip()))
        if '"evidence":' in line:
            try:files.add(Path(json.loads('{'+line.strip().rstrip(',')+'}')['evidence']))
            except (ValueError,KeyError):pass
files.update(D.glob('coordinator-*.json'))
identities={};roots=set();raw=D/'raw';raw.mkdir(exist_ok=True)
def walk(value):
    if isinstance(value,dict):
        if type(value.get('pid')) is int and type(value.get('created')) is int and type(value.get('exe_digest')) is str:
            pin={k:value[k] for k in ('pid','created','exe_digest')};identities[tuple(pin.values())]=pin
        for x in value.values():walk(x)
    elif isinstance(value,list):
        for x in value:walk(x)
copied=[]
for p in sorted(files):
    if not p.is_absolute():p=R/p
    if not p.is_file():continue
    content=p.read_bytes()
    try:obj=json.loads(content)
    except ValueError:continue
    walk(obj)
    for root in obj.get('roots',[]) if isinstance(obj,dict) else []:roots.add(root)
    target=raw/(hashlib.sha256(str(p).encode()).hexdigest()[:10]+'-'+p.name)
    if target.exists():assert target.read_bytes()==content
    else:target.write_bytes(content)
    copied.append({'source':str(p),'copy':str(target),'sha256':hashlib.sha256(content).hexdigest()})
census=[]
for pin in identities.values():
    try:live=transport.identity(pin['pid']);state='MATCHING_PROCESS_LIVE' if live==pin else 'PID_REUSED_OR_DIFFERENT'
    except Exception as exc:
        live={'exception':type(exc).__name__,'errno':getattr(exc,'errno',None),'message':str(exc)}
        state='ABSENT_OR_EXITED' if getattr(exc,'errno',None)==87 or str(exc)=='PROCESS_DEAD' else 'UNCERTAIN'
    census.append({'recorded':pin,'current':live,'state':state})
artifacts=[]
for root in roots:
    p=Path(root)
    if p.name.startswith('TEST-STAGE4-'):
        artifacts += [str(x) for x in p.glob('coordinator-*.json*')]
report={'census':census,'matching_live':sum(x['state']=='MATCHING_PROCESS_LIVE' for x in census),'remaining_readiness_artifacts':artifacts,'preserved_evidence':copied,'note':'Historical TEST namespace data and diagnostic records retained intentionally. No process termination.'}
(D/'cleanup-reconciliation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'identities':len(census),'matching_live':report['matching_live'],'readiness_artifacts':len(artifacts),'evidence_files':len(copied)}))
