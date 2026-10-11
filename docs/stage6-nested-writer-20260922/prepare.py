import hashlib,json,os,uuid,zipfile,difflib
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-telemetry-candidate-20260922'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
prior=load(P/'candidate-frozen.json');old=Path(load(P/'candidate.json')['code']);receipt=load(P/'archive-verification.json');archive=Path(receipt['archive']);manifest=archive.parent/'manifest.json'
for x in prior['files']:assert sha(x['path'])==x['sha256'],x['path']
assert sha(archive)==receipt['archiveSHA256'] and sha(manifest)==receipt['manifestSHA256']
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(set(z.namelist()))==receipt['membersVerified']
 assert z.read('manifest.json')==manifest.read_bytes()
 for x in load(manifest)['files']:
  b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
C=Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
copies=[]
for x in prior['files']:
 p=Path(x['path']);dest=C/p.relative_to(old);assert not p.is_symlink() and not p.is_junction();dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(p.read_bytes())
 copies.append(dict(source=str(p),path=str(dest),sha256=sha(dest)))
target=C/'medium-checker/checker_telemetry.py';before=target.read_bytes();s=before.decode('utf8')
assert s.count("VERSION='stage6-checker-telemetry-v4'")==1
s=s.replace("VERSION='stage6-checker-telemetry-v4'","VERSION='stage6-checker-telemetry-v5'")
needle='def compatibility_view(bundle):\n b=copy.deepcopy(bundle)'
# Universal newline normalization is explicit; reference bytes/hashes are preserved.
s=s.replace('\r\n','\n');assert s.count(needle)==1
s=s.replace(needle,'''def compatibility_view(bundle):
 # Compare the complete raw analyzer duplicate BEFORE removing measurement fields.
 # Canonical JSON retains numeric/bool distinctions that Python == can erase.
 qualification=bundle.get('qualification')
 legacy.need(type(qualification) is dict and type(qualification.get('writer')) is dict and type(bundle.get('writer')) is dict,'NESTED_WRITER_MISSING')
 legacy.need(json.dumps(qualification['writer'],sort_keys=True,allow_nan=False)==json.dumps(bundle['writer'],sort_keys=True,allow_nan=False),'NESTED_WRITER_CONFLICT')
 b=copy.deepcopy(bundle)''')
needle='  for s in b[key][\'segments\']:del s[\'timing\']\n return b';assert s.count(needle)==1
s=s.replace(needle,"  for s in b[key]['segments']:del s['timing']\n # Equality above proves this is the same record; do not silently replace a conflict.\n b['qualification']['writer']=copy.deepcopy(b['writer'])\n return b")
target.write_bytes(s.encode('utf8'))
with (R/'checker_telemetry.py.before').open('xb') as f:f.write(before)
with (R/'checker_telemetry.py.diff').open('x',encoding='utf8') as f:f.write(''.join(difflib.unified_diff(before.decode('utf8').splitlines(True),s.splitlines(True),fromfile=str(old/'medium-checker/checker_telemetry.py'),tofile=str(target))))
save(R/'candidate.json',dict(code=str(C),originalCode=str(old),originalRun=load(P/'run.json'),copies=copies,archive=receipt,change=dict(path=str(target),beforeSHA256=hashlib.sha256(before).hexdigest(),afterSHA256=sha(target)),scope='OFFLINE CHECKER CORRECTION ONLY; no live run binding or launch authorized by this preparation'))
print(json.dumps(dict(code=str(C),originalHashes=len(prior['files']),archiveMembers=receipt['membersVerified'],changed='checker_telemetry.py',version='stage6-checker-telemetry-v5')))
