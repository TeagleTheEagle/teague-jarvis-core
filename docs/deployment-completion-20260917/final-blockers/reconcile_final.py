"""Read-only identity/artifact census; preserve only reported nonsecret evidence."""
from pathlib import Path
import hashlib,json,re,sys
D=Path(__file__).resolve().parent;R=D.parents[2]
sys.path.insert(0,str(R/'tests/lifecycle_stage2'))
import pipe_transport as transport
records=json.loads((D/'final-suite/commands.json').read_text())
assert len(records)==33 and all(x['exit']==0 for x in records)
files=set(D.glob('*.json'));pins={};roots=set();copied=[]
def walk(o):
    if isinstance(o,dict):
        if isinstance(o.get('pid'),int) and isinstance(o.get('created'),int) and isinstance(o.get('exe_digest'),str):
            p={k:o[k] for k in ('pid','created','exe_digest')};pins[tuple(p.values())]=p
        for v in o.values():walk(v)
    elif isinstance(o,list):
        for v in o:walk(v)
    elif isinstance(o,str) and 'TEST-STAGE4-' in o and ':\\' in o:
        match=re.search(r'([A-Z]:\\[^\r\n"]*?TEST-STAGE4-[0-9a-f]{30,32})(?:\\|$)',o)
        if match:roots.add(Path(match[1]))
for p in (D/'final-suite').glob('*.log'):
    s=p.read_text(errors='replace')
    for line in s.splitlines():
        if line.startswith('EVIDENCE '):files.add(Path(line[9:].strip()))
    try:
        obj=json.loads(s);walk(obj)
        if isinstance(obj,dict) and 'evidence' in obj:files.add(Path(obj['evidence']))
    except ValueError:pass
raw=D/'final-raw';raw.mkdir(exist_ok=True)
for p in sorted(files):
    if not p.is_absolute():p=R/p
    content=p.read_bytes();obj=json.loads(content);walk(obj)
    if p.parent!=D:
        target=raw/(hashlib.sha256(str(p).encode()).hexdigest()[:10]+'-'+p.name)
        if target.exists():assert target.read_bytes()==content
        else:target.write_bytes(content)
        copied.append({'source':str(p),'copy':str(target),'sha256':hashlib.sha256(content).hexdigest()})
census=[]
for pin in pins.values():
    try:
        live=transport.identity(pin['pid']);state='LIVE' if live==pin else 'PID_REUSED'
    except Exception as e:
        live={'exception':type(e).__name__,'errno':getattr(e,'errno',None)}
        state='EXITED' if getattr(e,'errno',None)==87 or str(e)=='PROCESS_DEAD' else 'UNCERTAIN'
    census.append({'recorded':pin,'current':live,'state':state})
artifacts=[];root_rows=[]
for root in sorted(roots):
    assert (root/'TEST_ONLY').read_text()=='NO PRODUCTION SERVICES'
    found=[str(p) for p in root.glob('coordinator-*.json*')]
    found += [str(p) for p in root.glob('*.tmp')]
    artifacts.extend(found)
    root_rows.append({'root':str(root),'artifacts':found,'persistent_test_evidence_retained':True})
out={'identities':census,'live':sum(x['state']=='LIVE' for x in census),'uncertain':sum(x['state']=='UNCERTAIN' for x in census),'roots':root_rows,'stale_readiness_or_temp_artifacts':artifacts,'preserved':copied,'note':'Read-only census. Closed TEST namespaces, synthetic databases and diagnostic files intentionally retained as evidence; no recursive deletion.'}
(D/'final-cleanup.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'identities':len(census),'live':out['live'],'uncertain':out['uncertain'],'namespaces':len(roots),'artifacts':len(artifacts),'raw_evidence':len(copied)}))
assert out['live']==0 and out['uncertain']==0 and not artifacts
