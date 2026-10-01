import json,hashlib,zipfile,uuid
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-durable-kernel-20260921'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((P/'archive-verification.json').read_text());archive=Path(receipt['archive']);mf=archive.parent/'manifest.json'
assert sha(archive)==receipt['archiveSHA256'] and sha(mf)==receipt['manifestSHA256']
rows=json.loads(mf.read_text())['files']
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==402 and set(z.namelist())=={x['name'] for x in rows}|{'manifest.json'}
 assert z.read('manifest.json')==mf.read_bytes()
 for x in rows:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],x['name']
  assert sha(Path(x['source']))==x['sha256'],x['source']
checks=json.loads((P/'preservation.json').read_text())['checks']
for x in checks:assert sha(Path(x['path']))==x['sha256'],x['path']
run=uuid.uuid4().hex;(R/'final'/run).mkdir(parents=True,exist_ok=False)
with (R/'host_preflight.ps1').open('xb') as f:f.write((P/'host_preflight.ps1').read_bytes())
C=Path(json.loads((P/'candidate.json').read_text())['code'])
with (R/'preflight.json').open('x') as f:json.dump(dict(status='PASS',archive=receipt,membersVerified=402,sourceFilesVerified=len(rows),frozenChecks=len(checks),code=str(C),checkerSHA256=sha(C/'cleanup_checker.py'),hostRun=run,protectedAccess=False,productionChanged=False),f,indent=2)
print(json.dumps(dict(hostRun=run,members=402,sourceFiles=len(rows),frozenChecks=len(checks))))
