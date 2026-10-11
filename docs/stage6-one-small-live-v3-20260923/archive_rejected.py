"""Read-only failed-run preservation after independent eventual cleanup.
Does not rerun the preservation component, checker, finalizer or live validation.
"""
from pathlib import Path
import hashlib,json,os,sys,zipfile
R=Path(__file__).parent
O=R.parent/'stage6-coordination-v3-20260923'
P=R.parent/'stage6-failure-preservation-v1-20260923'
T=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2')
RUN=Path(r'D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code\protected-f117995dd9ef4ed1b33c1b44b1973293')
FAIL=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\preservation')/('FAILURE-EVIDENCE-'+RUN.name)
DEST=Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 ONE SMALL LIVE REJECTED 20260923 F117995D')
sys.path.insert(0,str(T));import failure_preserve_v1 as f
f.verify_candidate(f.cli_policy())
for x in json.loads((T/'source-manifest.json').read_text()):
 if f.sha(T/x['name'])!=x['sha256']:raise ValueError('PRESERVER_DRIFT')
if f.sha(T/'source-manifest.json')!='e781ed6389dd809805fb89c27b6f838623d4f2da707fcd7a160d22c25249ea28':raise ValueError('MANIFEST_DRIFT')
inputs=json.loads((O/'before.json').read_text())['inputs']
for x in inputs:
 p=Path(x['path'])
 if 'VirtualBox' in str(p):raise ValueError('PROTECTED_PATH')
 s=p.stat()
 if (s.st_size,s.st_mtime_ns,f.sha(p))!=(x['bytes'],x['mtimeNs'],x['sha256']):raise ValueError('ORIGINAL_DRIFT')
for rp in (O/'archive-receipt.json',P/'final-receipt.json'):
 a=json.loads(rp.read_text())
 if f.sha(Path(a['archive']))!=a['archiveSHA256']:raise ValueError('HISTORICAL_ARCHIVE_DRIFT')
provisional=FAIL/('FAILURE-EVIDENCE-'+RUN.name+'.zip')
if f.sha(provisional)!='bc5a01896fabbea6c76e12243c76a800abfd6710672c95b0f5d7639267d4b365':raise ValueError('PROVISIONAL_DRIFT')
verified=f.verify_archive(provisional,(FAIL/'FAILURE-MANIFEST.json').read_bytes())
census=f.host_census(R);f.write_new(R/'archive-time-host-census.json',census)
if not f.census_clean(census,R):raise ValueError('CLEANUP_UNPROVEN')
objects={n:json.loads((RUN/n).read_text(encoding='utf-8-sig')) for n in (
 'etw-result.json','detail/etw-result.json','observer-identities.json','launcher-identity.json','tree-handles.json','tree-image-support.json')}
instances=f.instance_census(objects);f.write_new(R/'archive-time-instance-census.json',instances)
if not instances['clean']:raise ValueError('RECORDED_INSTANCE_LIVE_OR_UNKNOWN')
before=json.loads((R/'failed-run-inventory.json').read_text())['files']
for x in before:
 p=RUN/x['path']
 if f.metadata(p)!={k:x[k] for k in ('bytes','mtimeNs','fileId','volume','links')} or f.sha(p)!=x['sha256']:
  raise ValueError('FAILED_RUN_CHANGED')
f.write_new(R/'post-source-verification.json',dict(candidateFiles=216,toolFiles=4,preservedInputs=482,
  historicalArchivesUnchanged=True,failedRunFiles=len(before),failedRunUnchanged=True,
  partialArchiveUnchanged=True,partialArchiveMembersVerified=verified['verifiedArchiveMembers'],
  productionChange=False,protectedAccess=False,checkerInvoked=False,successFinalizerInvoked=False,
  status='READ_ONLY_PRESERVATION_VERIFIED'))
DEST.mkdir(exist_ok=False)
rows=[];sources={}
for base,prefix in ((R,'action'),(RUN,'rejected-run'),(FAIL,'original-partial-preservation')):
 for p in sorted(base.rglob('*')):
  if p.is_dir():continue
  f.safe_path(p,base)
  if p.stat().st_nlink!=1 or p.name=='.env':raise ValueError('NONSECRET_REGULAR_EVIDENCE_ONLY')
  name=prefix+'/'+p.relative_to(base).as_posix()
  rows.append(dict(path=name,bytes=p.stat().st_size,sha256=f.sha(p)));sources[name]=p
f.write_new(DEST/'manifest.json',dict(label='NON-ACCEPTANCE SUPPLEMENTAL REJECTED-RUN EVIDENCE',
 run=RUN.name,acceptance_seal=False,runOutcome='REJECTED',originalPreservationStatus='CLEANUP_UNPROVEN',files=rows))
archive=DEST/'rejected-run-evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in rows:z.write(sources[x['path']],x['path'])
with archive.open('r+b') as stream:os.fsync(stream.fileno())
with zipfile.ZipFile(archive) as z:
 if len(z.namelist())!=len(rows):raise ValueError('COUNT')
 for x in rows:
  with z.open(x['path']) as stream:h=hashlib.file_digest(stream,'sha256').hexdigest()
  if h!=x['sha256'] or z.getinfo(x['path']).file_size!=x['bytes'] or f.sha(sources[x['path']])!=x['sha256']:
   raise ValueError('ARCHIVE_MEMBER_HASH')
for x in before:
 if f.metadata(RUN/x['path'])!={k:x[k] for k in ('bytes','mtimeNs','fileId','volume','links')}:raise ValueError('METADATA_CHANGED')
f.verify_candidate(f.cli_policy())
receipt=dict(status='SMALL_LIVE_INTEGRATION_FAILED',reason='AUTHORITATIVE_TRACE_LOSS',run=RUN.name,
 archive=str(archive),archiveSHA256=f.sha(archive),manifestSHA256=f.sha(DEST/'manifest.json'),
 membersVerified=len(rows),rawFailedRunFiles=len(before),originalPartialArchiveUnchanged=True,
 originalPreservationStatus='CLEANUP_UNPROVEN',acceptance_seal=False,
 eventualHostCleanupProven=True,knownInstancesChecked=instances['knownInstanceCount'],
 matchingProcesses=0,traceSessions=0,candidateFilesUnchanged=216,toolFilesUnchanged=4,
 originalInputsUnchanged=482,retries=0,productionChange=False,protectedAccess=False)
f.write_new(DEST/'receipt.json',receipt);f.write_new(R/'archive-receipt.json',receipt)
print(json.dumps(receipt))
