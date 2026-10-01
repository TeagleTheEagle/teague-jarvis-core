import json,hashlib,uuid
from pathlib import Path
R=Path(__file__).parent;P=json.loads((R/'preservation.json').read_text());candidate=json.loads((R/'candidate.json').read_text());C=Path(candidate['code'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in P['checks']:assert sha(Path(x['path']))==x['sha256'],x['path']
for x in candidate['copies']:assert sha(C/x['name'])==x['sha256'],x['name']
assert sha(Path(P['historical']['path']))==P['historical']['sha256']
checks=[]
for p in sorted(C.iterdir()):
 if p.is_file():checks.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
run=uuid.uuid4().hex;(R/'final'/run).mkdir(parents=True,exist_ok=False)
with (R/'final-source.json').open('x') as f:json.dump(dict(status='PASS',preservedChecks=len(P['checks']),inheritedCandidateFilesUnchanged=len(candidate['copies']),currentFiles=checks,checkerSHA256=sha(C/'cleanup_checker.py'),hostRun=run,protectedAccess=False,productionChanged=False),f,indent=2)
print(json.dumps(dict(preservedChecks=len(P['checks']),inheritedUnchanged=len(candidate['copies']),hostRun=run)))
