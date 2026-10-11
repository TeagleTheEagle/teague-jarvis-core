"""Read-only acceptance checks; write review evidence and an exact commit allowlist."""
from pathlib import Path
import ast,hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[2];D=Path(__file__).parent
S=R/'docs/stage5-continuation-20260917';B=R/'docs/stage5-accepted-baseline-20260917'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *args:subprocess.check_output(['git',*args],cwd=R).decode().strip()
baseline='d6199756f1e1f4495ad6c3de457660cbf1f03e84'
assert git('rev-parse','HEAD')==baseline and not git('diff','--cached','--name-only')
base=json.loads((B/'baseline.json').read_text());app=Path(base['app']);checks=[]
for x in base['source']:
    rel=Path(x['path']).relative_to('accepted-app')
    assert sha(app/rel)==x['sha256']==sha(R/'docs/deployment-completion-20260917/final-blockers'/x['path'])
checks.append({'requirement':'immutable application snapshot','passed':True,'files':len(base['source'])})
package=Path(json.loads((S/'candidate.json').read_text())['package']['package'])
manifest=json.loads((package/'manifest.json').read_text())
assert sha(package/'manifest.json')=='a4aa4f75aa24608dcc22305af8344a3c04f2305592969d3b95b8c4019d76a625'
for x in manifest['files']:assert sha(package/x['path'])==x['sha256']
checks.append({'requirement':'accepted package','passed':True,'files':len(manifest['files'])})
for filename,count in [('prior-campaign/5B-b66773f9a0064c67a98174897db4cb64.json',604),('5C-afd137866ba84ae9aee51567593dd0c1.json',587),('5D-3f9ead9f450843c4855dc314f4df0ccc.json',71),('ack-loss-9811b9c804914053ba91793ec82845a3.json',114)]:
    x=json.loads((S/filename).read_text());assert len(x['records'])==count and all(v['passed'] for v in x['records'])
    checks.append({'requirement':filename,'passed':True,'checks':count})
reg=json.loads((S/'regression-reconciliation.json').read_text());assert reg['groups']==reg['passed']==33 and reg['failed']==0
for x in reg['regressions']:
    assert x['exit']==0 and sha(S/x['log'])==x['sha256']
    for y in x['evidence']:assert sha(S/y['path'])==y['sha256']
archive=json.loads((S/'archive-verification.json').read_text());dest=Path(archive['destination'])
for x in archive['files']:assert sha(S/x['path'])==x['sha256']==sha(dest/x['path'])
checks.append({'requirement':'archive bytes match reviewed evidence','passed':True,'files':len(archive['files'])})
census=json.loads((S/'final-census-1789612441505604600.json').read_text())
assert not census['live'] and not census['uncertain'] and not census['test_processes'] and not census['transient_readiness_artifacts']
assert all(x['integrity']=='ok' and not x.get('errors') and x['before']==x['after'] for x in census['databases'])
checks.append({'requirement':'preserved final cleanup and independent persistence','passed':True,'databases':len(census['databases'])})
paths=sorted([p for folder in (B,S,R/'tests/lifecycle_stage5') for p in folder.rglob('*') if p.is_file()])
allowed={'.py','.json','.md','.log','.png'}
for p in paths:
    assert p.suffix in allowed,p
    if p.suffix=='.png':continue
    text=p.read_text(encoding='utf8');assert not re.search(r'sk-[A-Za-z0-9_-]{20,}|(?m:^-----BEGIN [A-Z ]*PRIVATE KEY-----$)',text),p
    if p.suffix=='.py':ast.parse(text,filename=str(p))
    if p.suffix=='.json':
        def scan(x):
            if isinstance(x,dict):
                for k,v in x.items():
                    assert k.lower() not in ('api_key','server_key','owner_key','private_key','access_token','authorization','token','password','secret'),(p,k)
                    scan(v)
            elif isinstance(x,list):
                for v in x:scan(v)
        scan(json.loads(text))
modified=git('diff','--name-only').splitlines();untracked=git('ls-files','--others','--exclude-standard').splitlines()
state={'head':baseline,'branch':git('branch','--show-current'),'modified_tracked':[{'path':p,'sha256':sha(R/p)} for p in modified],'untracked':untracked,'staged':[]}
(D/'before.json').write_text(json.dumps(state,indent=2))
review={'status':'ACCEPTABLE TEST-ONLY','baseline':baseline,'checks':checks,'regression_groups':33,'unit_tests':reg['unit_tests'],'skips':reg['skips'],'runtime_changed':False,'original_timeout_cause':'UNCONFIRMED','historical_stage1_cause':'UNCONFIRMED','limitations_preserved':True,'selected_files':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p)} for p in paths]}
(D/'review.json').write_text(json.dumps(review,indent=2))
paths+=list(D.glob('*.py'))+list(D.glob('*.json'))+list(D.glob('*.md'))
names=sorted(set(p.relative_to(R).as_posix() for p in paths))
(D/'commit-paths.txt').write_text('\n'.join(names)+'\n')
print(json.dumps({'acceptance':review['status'],'selected_files':len(names),'archive_verified':len(archive['files']),'runtime_files_changed':0,'prior_modified_tracked':len(modified)}))
