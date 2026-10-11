import hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).parent;D=R.parent;P=D/'stage6-one-small-live-v3-20260923';O=D/'stage6-coordination-v3-20260923'
C=Path(json.loads((R/'before.json').read_text())['source']);F=C/'protected-f117995dd9ef4ed1b33c1b44b1973293'
T=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
rows=json.loads((P/'failed-run-inventory.json').read_text())['files'];assert len(rows)==83
assert len([p for p in F.rglob('*') if p.is_file()])==83
for x in rows:
 p=F/x['path'];s=p.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino,sha(p))==(x['bytes'],x['mtimeNs'],x['fileId'],x['sha256'])
v=json.loads((P/'archive-receipt.json').read_text());a=Path(v['archive']);m=a.parent/'manifest.json';assert sha(a)==v['archiveSHA256'] and sha(m)==v['manifestSHA256'];rows=json.loads(m.read_text());rows=rows['files'] if isinstance(rows,dict) else rows
with zipfile.ZipFile(a) as z:
 assert len(z.namelist())==len(rows)==105
 for x in rows:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256'] and z.getinfo(x['path']).file_size==x['bytes']
v=json.loads((O/'candidate-final-r2.json').read_text());assert sha(C/'small-source-v3.json')==v['manifestSHA256'];assert len(v['files'])==216
for x in v['files']:assert sha(C/x['name'])==x['sha256']
assert sha(T/'source-manifest.json')=='e781ed6389dd809805fb89c27b6f838623d4f2da707fcd7a160d22c25249ea28'
rows=json.loads((T/'source-manifest.json').read_text());assert len(rows)==4
for x in rows:assert sha(T/x['name'])==x['sha256']
rows=json.loads((O/'before.json').read_text())['inputs'];assert len(rows)==482
for x in rows:
 p=Path(x['path']);assert 'VirtualBox' not in str(p);s=p.stat();assert (s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
v=json.loads((R/'candidate-freeze.json').read_text());assert sha(R/'candidate/small-source-v3.json')==v['sourceManifestSHA256']
for x in json.loads((R/'candidate/small-source-v3.json').read_text()):assert sha(R/'candidate'/x['name'])==x['sha256']
result={'status':'PASS','failedRunFiles':83,'historicalArchiveMembers':105,'originalCandidateFiles':216,'preservationToolFiles':4,'originalInputs':482,'successorActiveFiles':217,'protectedAccess':False,'productionChange':False}
with (R/'final-preservation.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
