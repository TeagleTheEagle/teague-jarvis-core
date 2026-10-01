"""Reconcile passed invocations and select nonsecret evidence for explicit archive."""
from pathlib import Path
import hashlib,json,re,shutil
R=Path(__file__).resolve().parents[2];D=R/'docs/stage5-continuation-20260917';O=D/'regressions'
base=json.loads((R/'docs/stage5-accepted-baseline-20260917/baseline.json').read_text());A=Path(base['app'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
latest={};history=[]
for p in sorted(O.glob('commands-*.json')):
    for item in json.loads(p.read_text()):latest[item['name']]=item;history.append(item)
inventory=json.loads((R/'docs/deployment-completion-20260917/final-blockers/final-suite/commands.json').read_text())
assert set(latest)=={x['name'] for x in inventory}
assert all(x['exit']==0 for x in latest.values())
evidence=D/'regression-evidence';evidence.mkdir(exist_ok=True);rows=[]
def safe(p):
    if p.suffix not in ('.json','.log','.md','.py','.png'):return False
    if p.suffix=='.png':return True
    text=p.read_text(encoding='utf8')
    assert not re.search(r'sk-[A-Za-z0-9_-]{20,}|(?m:^-----BEGIN [A-Z ]*PRIVATE KEY-----$)',text),str(p)
    if p.suffix=='.json':
        value=json.loads(text)
        def walk(x):
            if isinstance(x,dict):
                for k,v in x.items():
                    assert k.lower() not in ('api_key','server_key','owner_key','private_key','access_token','authorization','token','password','secret'),(str(p),k)
                    walk(v)
            elif isinstance(x,list):
                for v in x:walk(v)
        walk(value)
    return True
for name,item in latest.items():
    p=O/(name+'.log');assert sha(p)==item['sha256'];text=p.read_text();refs=[]
    refs.extend(re.findall(r'^EVIDENCE (.+\.json)\s*$',text,re.M))
    try:
        x=json.loads(text)
        if isinstance(x,dict) and isinstance(x.get('evidence'),str):refs.append(x['evidence'])
    except ValueError:pass
    copies=[]
    for index,path in enumerate(refs):
        source=Path(path.strip());assert source.is_relative_to(A) and safe(source)
        target=evidence/(name+'-'+str(index)+'-'+source.name)
        if target.exists():assert target.read_bytes()==source.read_bytes()
        else:shutil.copyfile(source,target)
        copies.append({'path':str(target.relative_to(D)),'sha256':sha(target)})
    row={'name':name,'exit':item['exit'],'log':str(p.relative_to(D)),'sha256':sha(p),'evidence':copies}
    match=re.search(r'Ran (\d+) tests',text)
    if match:
        row['unit_tests']=int(match[1]);skip=re.search(r'skipped=(\d+)',text);row['skipped']=int(skip[1]) if skip else 0
    match=re.search(r'\btests (\d+)',text)
    if match:row['unit_tests']=int(match[1]);row['skipped']=0
    rows.append(row)
out={'baseline':base['baseline'],'groups':len(rows),'passed':len(rows),'failed':0,'regressions':rows,'unit_tests':sum(x.get('unit_tests',0) for x in rows),'skips':sum(x.get('skipped',0) for x in rows),'historical_nonzero_invocations':[{'name':x['name'],'exit':x['exit'],'sha256':x['sha256']} for x in history if x['exit']!=0],'note':'Unit-test counts, campaign assertions and race trials use different units and are not added together.'}
(D/'regression-reconciliation.json').write_text(json.dumps(out,indent=2))
selected=[]
for p in sorted(D.rglob('*')):
    if p.name in ('archive-allowlist.json','archive-verification.json'):continue
    if p.is_file() and safe(p):selected.append({'path':str(p.relative_to(D)),'sha256':sha(p),'bytes':p.stat().st_size})
(D/'archive-allowlist.json').write_text(json.dumps({'files':selected,'exclusions':'No databases, DPAPI files, configurations, enrollments, grants, session tokens, provider credentials or package executables.'},indent=2))
print(json.dumps({'groups':len(rows),'unit_tests':out['unit_tests'],'skips':out['skips'],'archive_files':len(selected),'nonsecret_scan':'PASS'}))
