import json,uuid,hashlib
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'preflight.json').read_text());C=Path(pre['code'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in pre['checks']+json.loads((R/'candidate-frozen.json').read_text())['files']:assert sha(Path(x['path']))==x['sha256'],x['path']
tests=json.loads((R/'combined-tests-v2.json').read_text());assert tests['total']==tests['passed']==31
assert json.loads((R/'final'/pre['hostRun']/'final-host-state.json').read_text())['status']=='PASS'
run='identity-'+uuid.uuid4().hex;root=C/run;root.mkdir();(root/'temp').mkdir()
with (R/'run.json').open('x') as f:json.dump(dict(run=run,path=str(root),workload='one worker;16 direct probes;OS helpers;live kernel records through bounded durable sink',combined=True),f,indent=2)
with (R/'adapter-frozen.json').open('x') as f:json.dump(dict(files=[dict(path=str(R/name),sha256=sha(R/name)) for name in ('combined.py','coverage.py','analyze.py','CONTRACT.md','test_combined_v2.py')]),f,indent=2)
print(run)
