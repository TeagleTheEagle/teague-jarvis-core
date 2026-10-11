"""Offline integrity, fsync and archive gate for synthetic runs only."""
import pathlib,json,os,hashlib,shutil,sys,time
from journal import Reader,MAX_BYTES
R=pathlib.Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sync_file(p):
 with p.open('r+b',buffering=0) as f:os.fsync(f.fileno())
def durable_write(p,value,sync=sync_file):
 data=json.dumps(value,sort_keys=True,indent=2).encode()
 with p.open('xb') as f:f.write(data);f.flush()
 sync(p)
def verify_journal(root,identity):
 p=root/'heartbeat.jsonl';raw=p.read_bytes()
 if not raw or len(raw)>MAX_BYTES or not raw.endswith(b'\n'):raise RuntimeError('Incomplete/bounded journal required')
 rows=[json.loads(s) for s in raw.splitlines()]
 # Offline integrity is separate from live freshness; publisher is already closed.
 r=Reader(p,identity,clock=lambda:rows[-1]['ticks'])
 try:r.poll();assert not r.pending
 finally:r.close()
 gaps=[(b['ticks']-a['ticks'])/identity['frequency'] for a,b in zip(rows,rows[1:])]
 if any(g>=10 for g in gaps):raise RuntimeError('Heartbeat interval exceeded acceptance bound')
 return rows
def finalize(root,sync=sync_file,copy=shutil.copyfile):
 from workspace import check_path
 root=check_path(pathlib.Path(root))
 if root.parent!=R.resolve():raise RuntimeError('Synthetic run root required')
 if (root/'EVIDENCE-DURABLY-FINALIZED.json').exists() or (root/'archive').exists():raise RuntimeError('Do not overwrite finalization evidence')
 for n in ('primary-failure.json','collector-failure.json','monitor-failure.json','resource-failure.txt','queue-failure.json'):
  if (root/n).exists():raise RuntimeError('Preserved failure blocks acceptance: '+n)
 if (root/'queue-state.json').exists():
  q=read(root/'queue-state.json')
  if q['failed'] or q['remaining'] or not q['enqueued']==q['selected']==q['persisted']==q['removed']:raise RuntimeError('Queue reconciliation failed')
 identity=read(root/'ready.json');live=read(root/'collector-finished.json');monitor=read(root/'monitor-result.json');exited=read(root/'monitor-exit.json')
 if live['status']!='LIVE_MONITOR_HEALTHY' or monitor['status']!='LIVE_COLLECTION_CLOSED' or not monitor['journalDurableFlush']:raise RuntimeError('Collection/final flush did not succeed')
 if exited['exit_code']!=0 or exited['identity']!=identity or monitor['run']!=identity['run']:raise RuntimeError('Monitor exit identity invalid')
 rows=verify_journal(root,identity)
 if monitor['sequences']!=len(rows) or monitor['violations']!=0:raise RuntimeError('Sequence/state mismatch')
 events=[json.loads(s) for s in (root/'events.jsonl').read_text(encoding='utf-8-sig').splitlines()]
 probes=read(root/'probes.json')
 if len({p['pid'] for p in probes})!=len(probes):raise RuntimeError('Ambiguous probe PID reuse')
 if len(events)!=monitor['events'] or len(events)!=2*len(probes):raise RuntimeError('Event count mismatch')
 for p in probes:
  if p['exit']!=0:raise RuntimeError('Probe failed')
  for kind in ('start','stop'):
   if sum(e['pid']==p['pid'] and e['kind']==kind and e['name'].lower()=='j6probe.exe' for e in events)!=1:raise RuntimeError('Probe event mismatch')
 samples=read(root/'collector-samples.json')
 if not samples or any(not 0<=s['age']<=10 for s in samples):raise RuntimeError('Live reader state invalid')
 if not (root/'resources.json').exists() or not read(root/'resources.json'):raise RuntimeError('Resource evidence missing')
 if root.name.startswith('dry'):
  before=read(root/'source-before.json');after=read(root/'source-after.json')
  if before!=after or len(before)!=12:raise RuntimeError('Synthetic source changed or incomplete')
 files=sorted(p for p in root.iterdir() if p.is_file())
 if any(p.suffix in ('.exe','.bin') for p in files):raise RuntimeError('Unexpected binary evidence')
 manifest=[]
 for p in files:
  sync(p);manifest.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
 durable_write(root/'evidence-manifest.json',manifest,sync)
 archive=root/'archive';archive.mkdir()
 for entry in manifest:
  src=root/entry['path'];dest=archive/entry['path'];copy(src,dest);sync(dest)
  if sha(src)!=entry['sha256'] or sha(dest)!=entry['sha256']:raise RuntimeError('Evidence hash mismatch')
 copy(root/'evidence-manifest.json',archive/'evidence-manifest.json');sync(archive/'evidence-manifest.json')
 if sha(root/'evidence-manifest.json')!=sha(archive/'evidence-manifest.json'):raise RuntimeError('Manifest hash mismatch')
 result={'status':'EVIDENCE_DURABLY_FINALIZED','live_status':live['status'],'identity':identity,'files_verified':len(manifest)+1,'manifest_sha256':sha(root/'evidence-manifest.json'),'expected_starts':len(probes),'captured_starts':len(probes),'expected_stops':len(probes),'captured_stops':len(probes),'acceptance_requires_receipt_validation':True}
 durable_write(root/'EVIDENCE-DURABLY-FINALIZED.json',result,sync)
 copy(root/'EVIDENCE-DURABLY-FINALIZED.json',archive/'EVIDENCE-DURABLY-FINALIZED.json');sync(archive/'EVIDENCE-DURABLY-FINALIZED.json')
 if sha(root/'EVIDENCE-DURABLY-FINALIZED.json')!=sha(archive/'EVIDENCE-DURABLY-FINALIZED.json'):raise RuntimeError('Receipt hash mismatch')
 return result
def accepted(root,finalizer_exit_code=None):
 root=pathlib.Path(root)
 if finalizer_exit_code!=0:return False
 if (root/'finalization-failure.json').exists():return False
 try:
  receipt=read(root/'EVIDENCE-DURABLY-FINALIZED.json');archive=root/'archive'
  if receipt['status']!='EVIDENCE_DURABLY_FINALIZED' or sha(root/'EVIDENCE-DURABLY-FINALIZED.json')!=sha(archive/'EVIDENCE-DURABLY-FINALIZED.json'):return False
  if receipt['manifest_sha256']!=sha(root/'evidence-manifest.json') or sha(root/'evidence-manifest.json')!=sha(archive/'evidence-manifest.json'):return False
  for entry in read(root/'evidence-manifest.json'):
   if entry['path']!=pathlib.Path(entry['path']).name:return False
   if sha(root/entry['path'])!=entry['sha256'] or sha(archive/entry['path'])!=entry['sha256']:return False
  return True
 except (OSError,KeyError,ValueError):return False
if __name__=='__main__':
 import traceback
 root=R/sys.argv[1]
 try:print(json.dumps(finalize(root)))
 except BaseException:
  from evidence_support import Ledger
  Ledger(root).fail('finalization/archive')
  raise
