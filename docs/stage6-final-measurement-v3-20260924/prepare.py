"""Offline-only preservation and manifest-limited successor copy. No imports of candidate code."""
import pathlib,json,hashlib,zipfile,shutil,datetime
R=pathlib.Path(__file__).parent
D=R.parent
P=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\d45028a56e344926a311c04ba01f6a80\code')
N=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code')
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\a34f91e1db274bf78fc5a80e2a9d417c\code')
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def record(p):
 p=pathlib.Path(p);s=p.stat();assert not s.st_file_attributes&0x400,str(p)
 h=sha(p);t=p.stat();assert (s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns)
 return dict(path=str(p),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=h)
def write(n,x):
 with (R/n).open('x',encoding='utf8') as f:json.dump(x,f,indent=2)
if __name__=='__main__':
 assert not C.exists() and not (R/'before.json').exists()
 records={};archives=[]
 def keep(p):
  r=record(p);records[str(p)]=r;return r
 for x in load(D/'stage6-helper-handoff-v1-20260923'/'before.json')['inputs']:
  r=keep(x['path']);assert r==x,str(x['path'])
 for base in [P,N]:
  for x in load(base/'small-source-v3.json'):
   q=pathlib.PureWindowsPath(x['name']);assert not q.is_absolute() and '..' not in q.parts
   r=keep(base/x['name']);assert (r['bytes'],r['sha256'])==(x['bytes'],x['sha256'])
  keep(base/'small-source-v3.json')
 for base,run in [(P,'protected-4fc436a2cc6543e398388806441f522c'),(N,'protected-5d7e179ca49d461db1e4689d12c60267')]:
  for p in sorted((base/run).rglob('*')):
   if p.is_file():keep(p)
  for p in sorted((base.parent/'preservation-v4'/('FAILURE-EVIDENCE-'+run)).rglob('*')):
   if p.is_file():keep(p)
 for name in ['stage6-helper-handoff-live-20260923','stage6-corrected-trace-diagnostic-v4-20260923','stage6-helper-handoff-v1-20260923','stage6-identity-capacity-recalibration-20260921']:
  folder=D/name
  for p in folder.iterdir():
   if p.is_file():keep(p)
  if (folder/'archive-receipt.json').exists():
   receipt=load(folder/'archive-receipt.json');p=pathlib.Path(receipt['archive']);assert sha(p)==receipt['archiveSHA256'];keep(p)
   for sibling in p.parent.iterdir():
    if sibling.is_file() and sibling.suffix=='.json':keep(sibling)
 # Independently compare old historical inventory, including the original ambiguous/unmatched run.
 hist=load(D/'stage6-identity-capacity-recalibration-20260921'/'freeze.json')
 write('historical-freeze-schema.json',dict(keys=list(hist),statement='Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged; causes UNCONFIRMED'))
 for r in list(records.values()):
  p=pathlib.Path(r['path'])
  if p.suffix=='.zip':
   with zipfile.ZipFile(p) as z:
    assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
    members=[]
    for n in z.namelist():
     with z.open(n) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
     members.append(dict(name=n,sha256=h,bytes=z.getinfo(n).file_size))
    archives.append(dict(path=str(p),sha256=r['sha256'],members=members))
 write('before.json',dict(predecessor=str(P),comparison=str(N),candidate=str(C),inputs=list(records.values()),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),liveRun=False,UAC=False,protectedAccess=False,productionChange=False))
 write('archive-precheck.json',archives)
 C.mkdir(parents=True)
 for x in load(P/'small-source-v3.json'):
  dest=C/x['name'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(P/x['name'],dest);assert sha(dest)==x['sha256']
 shutil.copy2(P/'small-source-v3.json',C/'predecessor-source-v3.json')
 (C/'baseline-allowlist.json').write_text(json.dumps(dict(syntheticRoots=[str(C/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False),indent=2))
 policy=load(C/'preservation-policy-v4.json');policy.update(candidate=str(C),preservationRoot=str(C.parent/'preservation-v4'))
 (C/'preservation-policy-v4.json').write_text(json.dumps(policy,indent=2));(C.parent/'preservation-v4').mkdir()
 print(json.dumps(dict(candidate=str(C),copiedFiles=len(load(P/'small-source-v3.json')),preservedFiles=len(records),archives=len(archives),archiveMembers=sum(len(a['members']) for a in archives))))
