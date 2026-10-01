"""Transfer sealed nonsecret evidence, never enumerate original/protected paths."""
import datetime,hashlib,json,os,pathlib,shutil,zipfile
R=pathlib.Path(__file__).resolve().parent
D=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 STOP EVENT DIAGNOSIS 20260920')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root):
 m=json.loads((root/'archive-manifest.json').read_text())
 with zipfile.ZipFile(root/'evidence.zip') as z:
  expected={r['path'] for r in m['files']}|{'archive-manifest.json'}
  if len(z.namelist())!=len(expected) or set(z.namelist())!=expected:raise RuntimeError('Member set mismatch')
  if z.read('archive-manifest.json')!=(root/'archive-manifest.json').read_bytes():raise RuntimeError('Manifest mismatch')
  for row in m['files']:
   content=z.read(row['path'])
   if len(content)!=row['bytes'] or hashlib.sha256(content).hexdigest()!=row['sha256']:raise RuntimeError('Hash mismatch')
  for n in ('REPORT.md','CORRECTION-PROPOSAL.md'):
   if z.read(n)!=(root/n).read_bytes():raise RuntimeError('Report mismatch')
 return len(expected)
if __name__=='__main__':
 if D.exists():raise RuntimeError('Refusing overwrite')
 count=verify(R);D.mkdir(parents=True,exist_ok=False)
 for name in ('evidence.zip','archive-manifest.json','REPORT.md','CORRECTION-PROPOSAL.md'):
  with (R/name).open('rb') as r,(D/name).open('xb') as w:shutil.copyfileobj(r,w);w.flush();os.fsync(w.fileno())
  if sha(R/name)!=sha(D/name):raise RuntimeError('Transfer mismatch')
 if verify(D)!=count:raise RuntimeError('Destination verification mismatch')
 receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(D),'status':'HASH_VERIFIED_DIAGNOSTIC_ARCHIVE',
  'zip_members_hash_verified':count,'source_archive_files_verified_including_receipt':5,
  'zip_sha256':sha(D/'evidence.zip'),'manifest_sha256':sha(D/'archive-manifest.json'),
  'final_status':'STRONG_CAUSAL_EVIDENCE','reproduced_cause':'QUEUE_DRAIN_LOSS','historical_individual_cause':'UNPROVEN',
  'protected_baseline_eligibility':'NOT JUSTIFIED','monitor_acceptance':False}
 data=json.dumps(receipt,indent=2,sort_keys=True).encode()
 for root in (R,D):
  with (root/'archive-verification.json').open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 if sha(R/'archive-verification.json')!=sha(D/'archive-verification.json'):raise RuntimeError('Receipt mismatch')
 print(json.dumps(receipt))
