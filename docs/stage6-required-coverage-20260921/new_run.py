import json,uuid,hashlib
from pathlib import Path
R=Path(__file__).parent;frozen=json.loads((R/'candidate-frozen.json').read_text());C=Path(frozen['code'])
for x in frozen['files']:assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256']
assert json.loads((R/'coverage-tests.json').read_text())['passed']==26
name='identity-'+uuid.uuid4().hex;p=C/name;p.mkdir();(p/'temp').mkdir()
with (R/'run.json').open('x') as f:json.dump(dict(run=name,path=str(p)),f,indent=2)
print(name)
