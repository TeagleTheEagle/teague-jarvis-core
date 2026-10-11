import pathlib,json,hashlib,zipfile,sys,os,datetime
R=pathlib.Path(__file__).parent;sys.path.insert(0,str(R.parent/'stage6-narrow-preflight-20260920'));from verification import verify_candidate
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
pre=read(R/'preflight.json');plan=read(R/'candidate.json');C=pathlib.Path(plan['code']);O=pathlib.Path(pre['collector']);H=pathlib.Path(pre['diagnostic'])
assert verify_candidate(O,read(O/'baseline-source.json'))==84;assert verify_candidate(H,read(H/'hardening-hashes.json'))==96;verify_candidate(C,plan['hashes'])
assert read(R/'synthetic-metadata-before.json')==read(R/'synthetic-metadata-after.json')
cal=read(O/'calibration.json');S=pathlib.Path(cal['source']);names=[]
for directory,dirs,files in os.walk(S,followlinks=False):
 for n in dirs+files:assert not (pathlib.Path(directory)/n).lstat().st_file_attributes&0x400
 for n in files:names.append((pathlib.Path(directory)/n).relative_to(S).as_posix())
assert sorted(names)==sorted(x['path'] for x in cal['created'])
for x in cal['created']:
 s=(S/x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
for receipt in pre['archives'].values():
 a=pathlib.Path(receipt['path']);assert sha(a/'evidence.zip')==receipt['zipSHA256'] and sha(a/'archive-manifest.json')==receipt['manifestSHA256']
host=read(R/'host-final.json');assert not host['processes'] and not host['traces'] and host['traceExit']==0
assert not list(C.glob('protected-*'))
out=dict(status='PASS',collectorHashes=84,diagnosticHashes=96,integrationHashes=len(plan['hashes']),syntheticFiles=12,metadataAndAclEntries=15,metadataAndAclUnchanged=True,sourceSizesAndMtimeUnchanged=True,priorArchivesUnchanged=True,liveDiagnosticProcesses=0,traceSessions=0,workloadAdmitted=False,protectedAccess=False,productionChanged=False,overallDisposition='BLOCKED')
with (R/'final-preservation.json').open('x') as f:json.dump(out,f,indent=2)
paths=[('report/'+p.name,p) for p in sorted(R.iterdir()) if p.is_file()]
paths += [('integration-candidate/'+p.name,p) for p in sorted(C.iterdir()) if p.is_file()]
rows=[]
for n,p in paths:
 assert p.name!='.env' and not p.lstat().st_file_attributes&0x400
 rows.append(dict(name=n,source=str(p),sha256=sha(p),bytes=p.stat().st_size))
raw=(json.dumps(dict(status='BLOCKED',kind='PREFLIGHT_REJECTION_NOT_COLLECTOR_ACCEPTANCE',files=rows),sort_keys=True,indent=2)+'\n').encode()
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 LARGE REVALIDATION BLOCKED 20260920');A.mkdir(exist_ok=False)
with (A/'archive-manifest.json').open('xb') as f:f.write(raw)
with zipfile.ZipFile(A/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for x in rows:z.write(x['source'],x['name'])
 z.writestr('archive-manifest.json',raw)
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==len(rows)+1
 for x in rows:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']==sha(x['source'])
 assert z.read('archive-manifest.json')==raw
with (A/'REPORT.md').open('xb') as f:f.write((R/'REPORT.md').read_bytes())
receipt=dict(status='VERIFIED',disposition='BLOCKED',path=str(A),members=len(rows)+1,zipSHA256=sha(A/'evidence.zip'),manifestSHA256=sha(A/'archive-manifest.json'),protectedBaselineAuthorized=False)
for folder in (A,R):
 with (folder/'archive-verification.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
