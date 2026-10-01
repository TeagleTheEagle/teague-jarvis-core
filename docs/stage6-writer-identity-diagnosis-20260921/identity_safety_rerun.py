from pathlib import Path
import json,hashlib,sys
R=Path(__file__).parent;E=R.parent/'stage6-event-integration-20260921';C=Path(json.loads((R/'freeze.json').read_text())['newCode'])
# Run a relocated copy with a new exclusive report destination. Never execute the historical fixed-output script.
s=(E/'identity_tests.py').read_text().replace("C=pathlib.Path(json.loads((R/'active-workspace.json').read_text())['code'])","C=pathlib.Path(json.loads((R/'freeze.json').read_text())['newCode'])")
sys.path.insert(0,str(R.parent/'stage6-evidence-restoration-20260921'))
exec(compile(s,str(R/'relocated-identity-tests.py'),'exec'),{'__file__':str(R/'relocated-identity-tests.py')})
p=Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code\protected-00a17b2c499c4966a5113c30924b367a\etw-result.json')
k=json.loads(p.read_text());groups={}
for x in k['rows']:groups.setdefault(x['pid'],[]).append(x)
reuse=[{'pid':pid,'instances':[{'created':x['created'],'sequence':x['sequence'],'start':x['startQpc'],'stop':x['stopQpc']} for x in rows]} for pid,rows in groups.items() if len(rows)>1]
with (R/'historical-kernel-reuse.json').open('x') as f:json.dump({'scope':'Historical evidence only, not current acceptance. Does not resolve CIM events.','source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reusedPIDs':reuse},f,indent=2)
