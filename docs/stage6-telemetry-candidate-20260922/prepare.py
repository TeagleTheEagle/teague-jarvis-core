import hashlib,json,os,uuid,zipfile,shutil
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-medium-20260922'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
old=Path(load(P/'preflight.json')['code']);rows=load(P/'candidate-frozen.json')['files']
for x in rows:assert sha(x['path'])==x['sha256'],x['path']
receipt=load(P/'archive-verification.json');a=Path(receipt['archive']);m=a.parent/'manifest.json'
assert sha(a)==receipt['archiveSHA256'] and sha(m)==receipt['manifestSHA256']
with zipfile.ZipFile(a) as z:
 assert len(z.namelist())==len(set(z.namelist()))==receipt['membersVerified']
 assert z.read('manifest.json')==m.read_bytes()
 for x in load(m)['files']:
  data=z.read(x['name']);assert len(data)==x['bytes'] and hashlib.sha256(data).hexdigest()==x['sha256']
assert shutil.disk_usage('D:/').free>2*1024**3
C=Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
copies=[]
for x in rows:
 src=Path(x['path']);rel=src.relative_to(old);dst=C/rel
 assert not src.is_symlink() and '.env' not in rel.parts
 dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(src.read_bytes())
 copies.append(dict(source=str(src),path=str(dst),sha256=sha(dst)))
host=uuid.uuid4().hex;(R/'final'/host).mkdir(parents=True)
with (R/'host_preflight.ps1').open('xb') as f:f.write((P/'host_preflight.ps1').read_bytes())
save(R/'candidate.json',dict(code=str(C),old=str(old),copies=copies,priorArchive=receipt,verifiedSourceCount=len(rows),hostRun=host,freeD=shutil.disk_usage('D:/').free))
print(json.dumps(dict(code=str(C),sourceHashes=len(rows),archiveMembers=receipt['membersVerified'],hostRun=host)))
