"""Post-observer acceptance, immutable evidence archive, never rewrites failures."""
import pathlib,json,os,zipfile,sys
from workspace import run_dir,activate_temp
from dry_contract import load,read,save,sha,state,advance,inventory
from cleanup_checker import evaluate
from probe_policy import validate_lifecycle
from evidence_support import Ledger
def require_ready(root):
 if state(root)['phase']!='OBSERVERS_CLOSED':raise RuntimeError('Observers not finalized')
 if (root/'primary-failure.json').exists() or (root/'hash-failure.json').exists() or (root/'launcher-error.txt').exists():raise RuntimeError('Preserved failure forbids acceptance')
 producer=read(root/'stress-result.json')
 if producer['status']!='DIAGNOSTIC_COMPLETE' or producer.get('primary_failure') or read(root/'launcher-result.json')['workExit']!=0:raise RuntimeError('Producer failure forbids acceptance')
 result=evaluate(root);save(root/'integrated-cleanup.json',result)
 if result['status']!='PASS' or result.get('insufficient') or result.get('primaryFailure'):raise RuntimeError('Dual evidence cleanup failure')
 rows=read(root/'probe-timings.json');handles=read(root/'retained-handle-verification.json');pids={x['pid'] for x in rows}
 events=[json.loads(x) for x in (root/'app-events.jsonl').read_text(encoding='utf-8-sig').splitlines()]
 validate_lifecycle(rows,[x for x in events if x['pid'] in pids],handles)
 if any(x.get('independentObserverFailed') for x in rows):raise RuntimeError('Independent probe observer failed')
 samples=read(root/'hash-health-samples.json')+read(root/'collector-health-samples.json')
 if not samples or any(not 0<=x['age']<10 for x in samples):raise RuntimeError('Missing or stale workload heartbeat')
 first=read(root/'hash-pass-1.json');second=read(root/'hash-pass-2.json')
 if first['files']!=second['files'] or first['endQpcNs']>second['beginQpcNs']:raise RuntimeError('Hash order/content mismatch')
 if read(root/'metadata-verified.json')['status']!='PASS':raise RuntimeError('Metadata verification missing')
 return result
def finalize(root):
 contract=load(root);result=require_ready(root);advance(root,'OBSERVERS_CLOSED','CLEANUP_VERIFIED','integrated-cleanup.json')
 frozen=read(root/'source-hashes.json')
 for x in frozen:
  if sha(root.parent/x['name']).lower()!=x['sha256'].lower():raise RuntimeError('Candidate source drift')
 files=[]
 for p in sorted(root.iterdir()):
  if not p.is_file() or p.name=='state.json':continue
  with p.open('r+b',buffering=0) as f:os.fsync(f.fileno())
  files.append(dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size))
 save(root/'durable-files.json',files);advance(root,'CLEANUP_VERIFIED','FINALIZED')
 manifest=dict(synthetic=True,scenario=contract['scenario'],source=contract['source'],files=read(root/'hash-pass-2.json')['files'],dualEvidence=result,protectedAccess=False)
 save(root/'baseline-manifest.json',manifest);save(root/'baseline-manifest-hash.json',dict(sha256=sha(root/'baseline-manifest.json')))
 advance(root,'FINALIZED','MANIFESTED')
 members=files+[dict(name=n,sha256=sha(root/n),bytes=(root/n).stat().st_size) for n in ('durable-files.json','baseline-manifest.json','baseline-manifest-hash.json')]
 save(root/'archive-manifest.json',members)
 with zipfile.ZipFile(root/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
  for x in members:z.write(root/x['name'],x['name'])
  z.write(root/'archive-manifest.json','archive-manifest.json')
 with (root/'evidence.zip').open('r+b',buffering=0) as f:os.fsync(f.fileno())
 advance(root,'MANIFESTED','ARCHIVED')
 with zipfile.ZipFile(root/'evidence.zip') as z:
  if len(z.namelist())!=len(members)+1:raise RuntimeError('Archive count mismatch')
  import hashlib
  for x in members:
   if hashlib.sha256(z.read(x['name'])).hexdigest()!=x['sha256'] or sha(root/x['name'])!=x['sha256']:raise RuntimeError('Archive/source mismatch')
  if z.read('archive-manifest.json')!=(root/'archive-manifest.json').read_bytes():raise RuntimeError('Archive manifest mismatch')
 if inventory(pathlib.Path(contract['source']))!=contract['inventory']:raise RuntimeError('Post-archive source metadata changed')
 save(root/'archive-verification.json',dict(status='HASH_VERIFIED',members=len(members)+1,sha256=sha(root/'evidence.zip'),manifestSHA256=sha(root/'baseline-manifest.json'),sourceMetadataPreserved=True))
 advance(root,'ARCHIVED','VERIFIED')
 save(root/'integration-result.json',dict(status='MINIATURE_INTEGRATION_PASS' if contract['scenario']=='miniature' else 'DRY_RUN_1_PASS',dryRunExecuted=contract['scenario']=='dry1',identities=result['total'],handleConfirmed=result['handleConfirmed'],postExit=result['kernelPostExit'],unexplained=result['insufficient'],protectedAccess=False))
 return read(root/'integration-result.json')
if __name__=='__main__':
 root=run_dir(sys.argv[1]);activate_temp(root)
 try:print(json.dumps(finalize(root)))
 except BaseException:Ledger(root).fail('integrated-finalization');raise
