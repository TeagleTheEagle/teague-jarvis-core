"""Copy finalized nonsecret rejected-run evidence; no acceptance finalization."""
import pathlib,os,stat,json,hashlib,zipfile
R=pathlib.Path(__file__).parent
v=json.loads((R/'preflight-result.json').read_text());C=pathlib.Path(v['candidate']);root=pathlib.Path(v['runRoot'])
P=C.parent/'preservation-v4'/('FAILURE-EVIDENCE-'+v['run'])
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 HELPER HANDOFF LIVE FAILED 20260923')
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def stable(p):
 s=p.stat();h=sha(p);t=p.stat();assert (s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns)
 return s.st_size,s.st_mtime_ns,h
assert json.loads((R/'final-census.json').read_text())['status']=='PASS'
assert not A.exists(),'No archive overwrite'
items=[]
for base,prefix in ((R,'review'),(P,'original-failure-preservation')):
 for directory,dirs,names in os.walk(base,followlinks=False):
  d=pathlib.Path(directory)
  for name in dirs+names:assert not (d/name).lstat().st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT,'REPARSE'
  for name in names:
   p=d/name;assert not name.lower().startswith('.env'),'ENV_FILE_FORBIDDEN'
   size,mtime,h=stable(p);items.append(dict(member=prefix+'/'+p.relative_to(base).as_posix(),source=str(p),bytes=size,mtimeNs=mtime,sha256=h))
items.sort(key=lambda x:x['member']);assert len(items)==len({x['member'].casefold() for x in items})
payload=(json.dumps(dict(label='NON-ACCEPTANCE FAILURE EVIDENCE',run=v['run'],acceptance=False,files=items),indent=2)+'\n').encode()
A.mkdir(parents=True,exist_ok=False)
with (A/'archive-manifest.json').open('xb') as f:f.write(payload)
zpath=A/'rejected-helper-handoff-live.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('archive-manifest.json',payload)
 for row in items:z.write(row['source'],row['member'])
with zipfile.ZipFile(zpath) as z:
 assert len(z.namelist())==len(items)+1==len(set(z.namelist()))
 assert z.read('archive-manifest.json')==payload
 for row in items:
  with z.open(row['member']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
  assert stable(pathlib.Path(row['source']))==(row['bytes'],row['mtimeNs'],row['sha256'])
for row in json.loads((C/'small-source-v3.json').read_text()):assert sha(C/row['name'])==row['sha256']
assert sha(C/'small-source-v3.json')==v['sourceManifestSHA256']
pm=json.loads((P/'FAILURE-MANIFEST.json').read_text())
for row in pm['preserved']:assert sha(root/row['path'])==row['sha256']
out=dict(status='VERIFIED_NON_ACCEPTANCE_COPY',run=v['run'],runStatus='TRACE_DIAGNOSTIC_RUN_FAILED',acceptance=False,archive=str(zpath),archiveBytes=zpath.stat().st_size,archiveSHA256=sha(zpath),manifestSHA256=sha(A/'archive-manifest.json'),verifiedMembers=len(items)+1,originalFailureArchiveMembers=95,originalFailurePreserverStatus='FAILURE_EVIDENCE_PARTIAL',candidateFilesUnchanged=235,liveProcesses=0,traceSessions=0,protectedAccess=False,productionChange=False)
data=(json.dumps(out,indent=2)+'\n').encode()
for p in (A/'archive-receipt.json',R/'archive-receipt.json'):
 with p.open('xb') as f:f.write(data)
assert sha(A/'archive-receipt.json')==sha(R/'archive-receipt.json')
print(json.dumps(out))
