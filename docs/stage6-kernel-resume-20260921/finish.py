import json,hashlib,uuid
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-durable-kernel-20260921';C=Path(json.loads((R/'preflight.json').read_text())['code'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((P/'archive-verification.json').read_text());manifest=json.loads((Path(receipt['archive']).parent/'manifest.json').read_text())
for x in manifest['files']:assert sha(Path(x['source']))==x['sha256'],x['source']
checks=json.loads((P/'preservation.json').read_text())['checks']
for x in checks:assert sha(Path(x['path']))==x['sha256']
run=uuid.uuid4().hex;(R/'final'/run).mkdir(parents=True,exist_ok=False)
with (R/'preservation-after.json').open('x') as f:json.dump(dict(status='PASS',sourceFilesUnchanged=len(manifest['files']),frozenChecks=len(checks),checkerSHA256=sha(C/'cleanup_checker.py'),qualifierSHA256=sha(P/'qualification.py'),hostRun=run,productionChanged=False,protectedAccess=False),f,indent=2)
print(run)
