"""Read-only source/process reconciliation and nonsecret review evidence."""
from pathlib import Path
import hashlib,json,sys
D=Path(__file__).resolve().parent;R=D.parents[1]
source=json.loads((D/'source.json').read_text());S=Path(source['source']);sys.path.insert(0,str(S))
from deployment_test.contract import _transport
t=_transport();seen={};summaries=[]
def walk(value):
    if isinstance(value,dict):
        if all(k in value for k in ('pid','created','exe_digest')):
            peer={k:value[k] for k in ('pid','created','exe_digest')};seen[(str(peer['pid']),str(peer['created']))]=peer
        for v in value.values():walk(v)
    elif isinstance(value,list):
        for v in value:walk(v)
for p in sorted(D.glob('deployment-*.json')):
    v=json.loads(p.read_text());walk(v)
    summaries.append({'file':p.name,'checks':len(v['records']),'failed':sum(not x['passed'] for x in v['records']),'roots':v['roots']})
observations=[]
for peer in seen.values():
    try:live=t.identity(int(peer['pid']))
    except OSError as exc:
        if exc.errno!=87:raise
        live=None
    observations.append({'recorded':peer,'current':live,'same_identity_live':live==peer})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[];changes={x['path']:x for x in source['deployment_changes']}
for entry in source['accepted_files']:
    rel=entry['path'];expected=changes[rel]['candidate'] if rel in changes else entry['sha256']
    rows.append({'path':rel,'candidate_matches':sha(S/rel)==expected,'accepted_snapshot_matches':sha(R/'docs/deployment-completion-20260917/final-blockers/accepted-app'/rel)==entry['sha256']})
out={'runs':summaries,'processes':observations,'live_recorded_test_identities':sum(x['same_identity_live'] for x in observations),'source':rows,'fresh_windows_available':False,'production_changed':False,'historical_stage1_cause':'UNCONFIRMED','original_stage5_timeout_cause':'UNCONFIRMED'}
(D/'reconciliation.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'runs':summaries,'identities_checked':len(observations),'live':out['live_recorded_test_identities'],'source_files':len(rows),'source_pass':all(x['candidate_matches'] and x['accepted_snapshot_matches'] for x in rows)}))
