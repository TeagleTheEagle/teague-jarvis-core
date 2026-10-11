import pathlib,json,hashlib,zipfile,uuid,shutil
R=pathlib.Path(__file__).resolve().parent
D=R.parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=D/'stage6-checker-v2-20260923'
cfg=load(v/'candidate.json');c=pathlib.Path(cfg['code']);o=pathlib.Path(cfg['original'])
records=[]
def record(p,expected=None):
 s=p.stat();h=sha(p)
 if expected is not None:assert h==expected,str(p)
 records.append(dict(path=str(p),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=h))
for x in cfg['originalFiles']:record(o/x['name'],x['sha256'])
source=load(v/'final-verification.json')['source']
for x in source:record(c/x['name'],x['sha256'])
for folder in ('stage6-two-phase-contract-review-20260923','stage6-two-phase-implementation-boundary-20260923','stage6-helper-cleanup-review-20260923','stage6-small-live-v2-20260923'):
 root=D/folder
 for p in sorted(root.iterdir()):
  if p.is_file():record(p)
 receipt=root/'archive-receipt.json'
 if receipt.exists():
  a=load(receipt);p=pathlib.Path(a['archive']);record(p,a['archiveSHA256'])
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
approval=pathlib.Path(r'C:\Users\jonny\.codex\attachments\d5244eba-93cb-4880-bc40-0017137745ea\Pasted text.txt')
record(approval)
for p in sorted((c/'protected-8145cedf8db843959b8ba58dfd62717b').rglob('*')):
 if p.is_file():record(p)
target=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
target.mkdir(parents=True,exist_ok=False)
for x in source:
 p=target/x['name'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(c/x['name'],p)
 assert sha(p)==x['sha256']
out=dict(candidate=str(target),original=str(c),inputs=records,sourceFiles=len(source),previousOriginalFiles=len(cfg['originalFiles']),protectedVMAccess=False,productionAccess=False)
with (R/'before.json').open('x') as f:json.dump(out,f,indent=2)
shutil.copyfile(approval,R/'owner-approval.txt')
print(json.dumps(dict(candidate=str(target),frozenInputs=len(records),sourceFiles=len(source))))
