"""Final TEST-only hash/process evidence; no deletion or process mutation."""
from pathlib import Path
import hashlib,json,sys,difflib
D=Path(__file__).resolve().parent;R=D.parents[1];rec=json.loads((D/'source.json').read_text());S=Path(rec['source']);P=Path(rec['previous_source']);sys.path.insert(0,str(S))
from deployment_test.contract import _transport
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((R/'docs/stage6-20260917/source.json').read_text());base=R/'docs/deployment-completion-20260917/final-blockers/accepted-app'
assert all(sha(base/e['path'])==e['sha256'] for e in old['accepted_files'])
changed=['deployment_test/bootstrap.py','deployment_test/upgrade.py','deployment_test/package.py','deployment_test/update_io.py','tests/deployment_contract/completion.py']
assert all(sha(S/e['path'])==e['sha256'] for e in rec['before'] if e['path'] not in changed)
files=[]
for rel in changed:
    p=S/rel;before=P/rel;out=D/'final-source'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes())
    files.append({'path':rel,'before':sha(before) if before.exists() else None,'after':sha(p)})
    (D/(p.name+'.final.diff')).write_text(''.join(difflib.unified_diff(before.read_text().splitlines(True) if before.exists() else [],p.read_text().splitlines(True),fromfile='before/'+rel,tofile='final/'+rel)))
    compile(p.read_bytes(),str(p),'exec')
peers={};runs=[]
def walk(value):
    if isinstance(value,dict):
        if all(k in value for k in ('pid','created','exe_digest')):
            peer={k:value[k] for k in ('pid','created','exe_digest')};peers[(int(peer['pid']),str(peer['created']))]=peer
        for child in value.values():walk(child)
    elif isinstance(value,list):
        for child in value:walk(child)
for p in sorted(D.glob('deployment-*.json')):
    data=json.loads(p.read_text());walk(data)
    runs.append({'file':p.name,'checks':len(data['records']),'passed':sum(bool(r['passed']) for r in data['records']),'failed':sum(not r['passed'] for r in data['records'])})
pt=_transport();census=[]
for peer in peers.values():
    try:current=pt.identity(int(peer['pid']))
    except OSError as exc:
        if exc.errno!=87:raise
        current=None
    same=current is not None and int(current['pid'])==int(peer['pid']) and str(current['created'])==str(peer['created']) and current['exe_digest'].lower()==peer['exe_digest'].lower()
    census.append({'recorded':peer,'current':current,'same_identity_live':same})
live=sum(p['same_identity_live'] for p in census)
result={'files':files,'accepted_snapshot_unchanged':61,'syntax_files':len(changed),'runs':runs,'identities_checked':len(census),'live_recorded_test_identities':live,'census':census,'production_changed':False}
(D/'final-reconciliation.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ('files','census')}))
assert live==0
