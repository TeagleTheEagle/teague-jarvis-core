"""Archive only current report, frozen source and this failed synthetic run."""
import pathlib,json,hashlib,zipfile,os,datetime
R=pathlib.Path(__file__).parent
C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
F=C/'protected-3aec3ce0062c42a19077a2bad0571bd7'
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 NARROW PREFLIGHT MONITORED FAILURE 20260920')
def sha(b):return hashlib.sha256(b).hexdigest()
paths=[]
for p in sorted(R.iterdir()):
 if p.is_file():paths.append(('report/'+p.name,p))
for row in json.loads((C/'baseline-source.json').read_text()):paths.append(('candidate/'+row['name'],C/row['name']))
paths.append(('candidate/baseline-source.json',C/'baseline-source.json'))
for d,dirs,files in os.walk(F,followlinks=False):
 for n in dirs+files:
  if (pathlib.Path(d)/n).lstat().st_file_attributes&0x400:raise ValueError('Reparse point in failed run')
 for n in files:
  p=pathlib.Path(d)/n;paths.append(('failed-run/'+p.relative_to(F).as_posix(),p))
assert len({n for n,p in paths})==len(paths)
rows=[]
for n,p in paths:
 if p.name=='.env':raise ValueError('Forbidden secret file')
 b=p.read_bytes();s=p.stat();rows.append(dict(name=n,source=str(p),bytes=len(b),mtime_ns=s.st_mtime_ns,sha256=sha(b)))
manifest=dict(kind='FAILED_SYNTHETIC_RUN_EVIDENCE_NOT_ACCEPTANCE',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rows)
raw=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
A.mkdir(exist_ok=False)
with (A/'archive-manifest.json').open('xb') as f:f.write(raw)
with zipfile.ZipFile(A/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for row in rows:
  b=pathlib.Path(row['source']).read_bytes();assert sha(b)==row['sha256'];z.writestr(row['name'],b)
 z.writestr('archive-manifest.json',raw)
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(rows)+1
 for row in rows:assert sha(z.read(row['name']))==row['sha256']
 assert z.read('archive-manifest.json')==raw
for row in rows:
 p=pathlib.Path(row['source']);s=p.stat();assert s.st_size==row['bytes'] and s.st_mtime_ns==row['mtime_ns'] and sha(p.read_bytes())==row['sha256']
receipt=dict(status='VERIFIED',path=str(A),members=len(rows)+1,zipSHA256=sha((A/'evidence.zip').read_bytes()),manifestSHA256=sha(raw),sourcePreservation='ALL_ARCHIVED_ORIGINALS_UNCHANGED',archiveType='FAILURE_EVIDENCE_ONLY')
for folder in (A,R):
 with (folder/'archive-verification.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
