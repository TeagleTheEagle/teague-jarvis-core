"""Post-diagnostic preservation and archive only; never runs monitor/VM/hash worker."""
import pathlib,json,hashlib,zipfile,sys,os,datetime
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-narrow-preflight-20260920';sys.path.insert(0,str(P))
from verification import verify_archive,verify_candidate,verify_hash
receipt=json.loads((P/'archive-verification.json').read_text());prior=pathlib.Path(receipt['path']);old=verify_archive(prior,receipt)
for row in old['files']:verify_hash(pathlib.Path(row['source']),row['sha256'])
original=pathlib.Path(json.loads((P/'candidate.json').read_text())['code']);assert verify_candidate(original,json.loads((original/'baseline-source.json').read_text()))==84
D=pathlib.Path(json.loads((R/'diagnostic-workspace.json').read_text())['code'])
new=json.loads((D/'diagnostic-hashes.json').read_text());assert verify_candidate(D,new)==len(new)
cal=json.loads((original/'calibration.json').read_text());source=pathlib.Path(cal['source'])
for x in cal['created']:
 s=(source/x['path']).lstat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns'] and not s.st_file_attributes&0x400
live=json.loads((R/'final-live-check.json').read_text(encoding='utf-8-sig'));assert not live['matchingLive'] and not live['processes'] and not live['traces'] and live['traceExit']==0
verify=dict(originalCandidateHashes=84,diagnosticFileHashes=len(new),priorArchiveMembers=receipt['members'],allPriorArchivedSourcesUnchanged=True,syntheticFileMetadata=12,realProtectedAccess=False,productionModified=False,liveIdentityChecks=live['checked'],liveMatches=0,traceSessions=0,status='INCONCLUSIVE',utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (R/'final-preservation.json').open('x') as f:json.dump(verify,f,indent=2)
# Preserve the supplemental mtime/clock estimate separately from exact monotonic spans.
F=original/'protected-3aec3ce0062c42a19077a2bad0571bd7'
p=next(x for x in json.loads((F/'probe-timings.json').read_text()) if x['pid']==24516);b=p['clockBefore'];q=(b['qpcBefore']+b['qpcAfter'])/2;ft=int(b['filetime']);origin=p['launchRequestedQpc']
est={n:dict(mtime_ns=(F/n).stat().st_mtime_ns,estimatedSecondsFromProbeLaunch=((F/n).stat().st_mtime_ns//100+116444736000000000-ft+q-origin)/1e7) for n in ('app-health.json','app-stop','workload-stop','hash-failure.json')}
with (R/'supplemental-mtime-estimates.json').open('x') as f:json.dump(dict(clockBridge=b,estimates=est,limitation='Filesystem timestamp/QPC mapping only; not measured operation spans or independently verified clock stability.'),f,indent=2)
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 LARGE FAILURE CORRELATION 20260920')
paths=[]
for p in sorted(R.iterdir()):
 if p.is_file():paths.append(('report/'+p.name,p))
for p in sorted(D.iterdir()):
 if p.is_file():paths.append(('diagnostic-code/'+p.name,p))
for F in sorted(D.glob('correlation-*')):
 for d,dirs,files in os.walk(F,followlinks=False):
  for n in dirs+files:
   if (pathlib.Path(d)/n).lstat().st_file_attributes&0x400:raise ValueError('Reparse evidence refused')
  for n in files:
   p=pathlib.Path(d)/n;paths.append(('runs/'+F.name+'/'+p.relative_to(F).as_posix(),p))
for n in ('evidence.zip','archive-manifest.json','archive-verification.json'):paths.append(('original-failure-archive/'+n,prior/n))
assert len({n for n,p in paths})==len(paths)
def sha(b):return hashlib.sha256(b).hexdigest()
rows=[]
for n,p in paths:
 assert p.name!='.env';s=p.stat();rows.append(dict(name=n,source=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p.read_bytes())))
raw=(json.dumps(dict(kind='DIAGNOSIS_NOT_ACCEPTANCE',files=rows),sort_keys=True,indent=2)+'\n').encode()
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
out=dict(status='VERIFIED',path=str(A),members=len(rows)+1,zipSHA256=sha((A/'evidence.zip').read_bytes()),manifestSHA256=sha(raw),archiveType='DIAGNOSIS_NOT_ACCEPTANCE',sourcePreservation='UNCHANGED')
for p in (R,A):
 with (p/'archive-verification.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
