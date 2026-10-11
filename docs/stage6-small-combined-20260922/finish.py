import json,hashlib,uuid
from pathlib import Path
R=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pre=json.loads((R/'preflight.json').read_text());frozen=json.loads((R/'candidate-frozen.json').read_text());adapter=json.loads((R/'adapter-frozen.json').read_text())
for x in pre['checks']+frozen['files']+adapter['files']:assert sha(Path(x['path']))==x['sha256'],x['path']
assert json.loads((R/'analysis/qualification-result.json').read_text())['status']=='PASS'
host=uuid.uuid4().hex;(R/'final'/host).mkdir()
with (R/'preservation-after.json').open('x') as f:json.dump(dict(status='PASS',historicalChecks=len(pre['checks']),qualifiedSourceChecks=len(frozen['files']),adapterChecks=len(adapter['files']),hostRun=host,checkerSHA256=sha(Path(pre['code'])/'cleanup_checker.py'),candidateChanged=False,protectedAccess=False,productionChanged=False),f,indent=2)
print(host)
