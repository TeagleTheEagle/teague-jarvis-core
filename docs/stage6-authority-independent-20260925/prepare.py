import pathlib,json,hashlib,shutil,difflib,zipfile,datetime
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-witness-live-20260925'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
v=load(P/'preflight-result.json');S=pathlib.Path(v['candidate']);C=R/'candidate'
assert sha(S/'small-source-v3.json')==v['sourceManifestSHA256']=='bfd34014f74be206cd727f81f71ac7fefe1f0f610c70384178772d331488a3c0'
assert sha(S/'witness-source-v1.json')==v['witnessManifestSHA256']
rows=load(S/'small-source-v3.json');assert len(rows)==245
before=[]
for row in rows:
 p=S/row['name'];assert not p.is_symlink() and not p.is_junction() and p.stat().st_nlink==1
 assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
 before.append(dict(**row,mtimeNs=p.stat().st_mtime_ns))
history=[]
for report in (P,R.parent/'stage6-lifecycle-witness-20260925'):
 receipt=load(report/'archive-receipt.json');archive=pathlib.Path(receipt['archive']);assert sha(archive)==receipt['sha256']
 with zipfile.ZipFile(archive) as z:
  assert len(z.namelist())==receipt['verifiedMembers'] and z.testzip() is None
  for row in load(report/'archive-manifest.json'):assert hashlib.sha256(z.read(row['member'])).hexdigest()==row['sha256']
 history.append(receipt)
save(R/'before.json',dict(predecessor=str(S),manifestSHA256=v['sourceManifestSHA256'],files=before,historicalArchives=history,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
C.mkdir(exist_ok=False)
for row in rows:
 dst=C/row['name'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/row['name'],dst)
old=b'p->LogFileMode=EVENT_TRACE_REAL_TIME_MODE;'
new=b'p->LogFileMode=EVENT_TRACE_REAL_TIME_MODE|EVENT_TRACE_INDEPENDENT_SESSION_MODE;'
p=C/'authority_trace_v3.cpp';raw=p.read_bytes();assert raw.count(old)==1 and b'EVENT_TRACE_INDEPENDENT_SESSION_MODE' not in raw
p.write_bytes(raw.replace(old,new))
(R/'configuration.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),p.read_text().splitlines(True),fromfile='predecessor/authority_trace_v3.cpp',tofile='successor/authority_trace_v3.cpp')),encoding='utf-8')
save(R/'preparation-result.json',dict(status='PASS',candidate=str(C),predecessor=str(S),sourceChange='authority LogFileMode OR EVENT_TRACE_INDEPENDENT_SESSION_MODE only',copiedFiles=len(rows),historicalArchiveMembers=[x['verifiedMembers'] for x in history],liveRun=False,UAC=False))
print('PREPARED 245 files; one authority expression changed; histories verified')
