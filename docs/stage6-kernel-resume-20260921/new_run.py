import json,uuid
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'preflight.json').read_text());C=Path(pre['code'])
assert json.loads((R/'final'/pre['hostRun']/'final-host-state.json').read_text())['status']=='PASS'
run='identity-'+uuid.uuid4().hex;root=C/run;root.mkdir();(root/'temp').mkdir()
with (R/'run.json').open('x') as f:json.dump(dict(run=run,path=str(root)),f,indent=2)
print(run)
