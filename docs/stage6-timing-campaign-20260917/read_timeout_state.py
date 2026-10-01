from pathlib import Path
import json,sys,hashlib
D=Path(__file__).resolve().parent;S=Path(json.loads((D.parent/'stage6-separated-io-20260917/source.json').read_text())['source']);sys.path.insert(0,str(S))
from deployment_test.contract import read_protected,digest
run=json.loads(next(D.glob('full-normal-*.json')).read_text());control=run['control_processes'][-1];root=Path(control['test_state']);items=[]
for p in (root/'updates').glob('intent-*.dpapi'):
    intent=read_protected(p);target=Path(intent['release']);manifest=json.loads((target/'manifest.json').read_text());checks=[digest(target/x['path'])==x['sha256'] and (target/x['path']).stat().st_size==x['bytes'] for x in manifest['files']]
    items.append({'intent':str(p),'intent_modified_ns':p.stat().st_mtime_ns,'target':str(target),'manifest_pin_matches':digest(target/'manifest.json')==intent['package_hash'],'files_verified':len(checks),'all_files_match':all(checks),'data_id':intent['data_id'],'commit_records':len(list((root/'updates').glob('commit-*.dpapi'))),'enrollment_records':len(list((root/'updates').glob('enrolled-*.dpapi'))),'stop_exists':(root/'stop').exists()})
(D/'late-timeout-state.json').write_text(json.dumps({'control_identity':control['identity'],'late_exit':control.get('cleanup_observed_exit'),'late_elapsed':control.get('cleanup_elapsed'),'items':items,'interpretation':'Read-only post-timeout evidence. Does not turn the failed 35-second wait into PASS or establish the historical cause.'},indent=2));print(json.dumps(items))
