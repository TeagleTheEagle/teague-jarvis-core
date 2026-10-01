"""Small TEST v2 only. No legacy baseline finalizer or production entry point."""
import os,json,re,hashlib,zipfile,ctypes,ctypes.wintypes as w,subprocess
from pathlib import Path
from workspace import check_path
from small_binding_v2 import frozen

OUTPUTS={'v2-input-manifest.json','v2-check-result.json','v2-seal.json','v2-evidence.zip','v2-archive-receipt.json'}
TOP=set('allow-app-prompt allow-detail-prompt app-authority.json app-events.jsonl app-health.jsonl app-heartbeats.json app-ready.json app-receipts.json app-result.json app-stop app-tap.json collector-health-samples.json contract.json etw-ready.json etw-result.json etw-stop hash-health-samples.json hash-pass-1.json hash-pass-2.json hash-worker-cleanup.json hash-worker-stderr.bin hash-worker-stderr.bin.json hash-worker-stdout.bin hash-worker-stdout.bin.json integration-launcher.json kernel-authority-manifest.json kernel-authority-result.json kernel-authority-seal.json kernel-authority-telemetry.json launcher-identity.json launcher-result.json loss-telemetry.json metadata-verified.json native-bridge-cleanup.json observer-identities.json probe-timings.json release-handles retained-handle-verification.json sampler-results.json small-declaration-v2.json stage-timing.json state.json stress-result.json tree-handles.json tree-image-support.json work.stderr work.stdout workload-stop primary-failure.json hash-failure.json secondary-failures.jsonl warnings.jsonl'.split())
PAT=r'(?:early-image|native)-[0-9]+-[0-9]+\.json|integration-(?:collector|hash-worker|sampler)-[0-9]+\.json|kernel-authority-[0-9]+\.jsonl|app-authority-[0-9]+\.jsonl'
DETAIL={'etw-ready.json','etw-result.json','etw-stop','startup-events.json','stage-timing.json','loss-telemetry.json'}
def need(v,m):
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,value):
 with p.open('x',encoding='utf8') as f:json.dump(value,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())
def inventory(root,exclude_outputs=False):
 check_path(root);rows=[]
 for base,dirs,names in os.walk(root,followlinks=False):
  for name in dirs+names:
   p=Path(base)/name;check_path(p);need(not p.lstat().st_file_attributes&0x400,'REPARSE')
  for name in names:
   p=Path(base)/name;rel=p.relative_to(root).as_posix()
   if exclude_outputs and rel in OUTPUTS:continue
   need(p.stat().st_nlink==1,'HARDLINK')
   if '/' not in rel:need(name in TOP or re.fullmatch(PAT,name),'UNEXPECTED_ARTIFACT:'+rel)
   else:need(rel.startswith('detail/') and (rel[7:] in DETAIL or re.fullmatch(r'trace-[0-9]{5}\.jsonl',rel[7:])),'UNEXPECTED_NESTED_ARTIFACT:'+rel)
   rows.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p)))
 need(rows and len({r['path'].casefold() for r in rows})==len(rows),'EMPTY_DUPLICATE')
 return sorted(rows,key=lambda r:r['path'])

def no_live_identities(root):
 from evidence_support import K,times
 rows=load(root/'etw-result.json')['rows']+[load(root/'launcher-identity.json')]
 for row in rows:
  h=K.OpenProcess(0x100000|0x1000,False,row['pid'])
  if not h:
   need(ctypes.get_last_error()==87,'PROCESS_INSPECTION_UNCERTAIN');continue
  try:
   if times(h)[0]==row['created']:need(K.WaitForSingleObject(h,0)==0,'LIVE_IDENTITY')
  finally:need(K.CloseHandle(h),'CENSUS_HANDLE_CLOSE')
 p=subprocess.run(['logman','query','-ets'],capture_output=True,text=True,timeout=10)
 need(p.returncode==0,'TRACE_CENSUS_FAILED')
 need(not re.search(r'(?i)J6|JARVIS|Stage6',p.stdout+p.stderr),'TRACE_STILL_ACTIVE')

def finalize(root):
 from small_check_v2 import check
 root=check_path(Path(root));need(not any((root/n).exists() for n in OUTPUTS),'FINALIZATION_ALREADY_STARTED')
 frozen();before=inventory(root);result=check(root)
 normal=result['status']=='SMALL_NORMAL_PASS_PENDING_ARCHIVE'
 need(normal or result['status']=='CONTROLLED_FAILURE_REJECTED_PENDING_ARCHIVE','CHECKER_NOT_PASS')
 if normal:need(not any((root/n).exists() for n in ('primary-failure.json','hash-failure.json','secondary-failures.jsonl')),'PRESERVED_FAILURE')
 no_live_identities(root)
 need(inventory(root)==before,'CHANGED_DURING_CHECK')
 for row in before:
  with (root/row['path']).open('r+b',buffering=0) as f:os.fsync(f.fileno())
 need(inventory(root)==before,'CHANGED_DURING_FLUSH');frozen()
 write(root/'v2-input-manifest.json',dict(run=root.name,files=before))
 write(root/'v2-check-result.json',dict(result=result,inputManifestSHA256=sha(root/'v2-input-manifest.json')))
 write(root/'v2-seal.json',dict(run=root.name,contract='stage6-small-tracker-integration-v2',inputManifestSHA256=sha(root/'v2-input-manifest.json'),resultSHA256=sha(root/'v2-check-result.json')))
 members=before+[dict(path=n,bytes=(root/n).stat().st_size,sha256=sha(root/n)) for n in ('v2-input-manifest.json','v2-check-result.json','v2-seal.json')]
 archive=root/'v2-evidence.zip'
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for r in members:z.write(root/r['path'],r['path'])
 with archive.open('r+b',buffering=0) as f:os.fsync(f.fileno())
 with zipfile.ZipFile(archive) as z:
  need(len(z.namelist())==len(members),'ARCHIVE_COUNT')
  for r in members:
   b=z.read(r['path']);need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'] and sha(root/r['path'])==r['sha256'],'ARCHIVE_HASH')
 need(inventory(root,True)==before,'FINAL_INPUT_DRIFT');frozen()
 receipt=dict(status='SMALL_NORMAL_PASS' if normal else 'CONTROLLED_FAILURE_REJECTION_VALIDATED',run=root.name,archiveSHA256=sha(archive),members=len(members),largeEligible=False,protectedEligible=False)
 write(root/'v2-archive-receipt.json',receipt);return receipt
