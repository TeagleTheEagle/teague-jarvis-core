"""Read-only final integrity/process verification, not a test execution."""
from pathlib import Path
import hashlib,json,sys,time
D=Path(__file__).resolve().parent;R=D.parents[2]
A=R/'docs/deployment-completion-20260916/blank-ui-final-acceptance-0e09edabe3084197b3b7741807475e02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if '--processes' in sys.argv:
 sys.path.insert(0,str(R/'tests/lifecycle_stage2'));import pipe_transport as pt
 d=json.loads((D/'minimal-result.json').read_text());peers=[x['live_peer'] for x in d['trials']]
 peers.extend({k:x['core_identity'][k] for k in ('pid','created','exe_digest')} for x in d['trials'] if 'core_identity' in x)
 result=[]
 for peer in peers:
  row={'expected':peer}
  try:current=pt.identity(peer['pid']);row.update(current=current,status='SAME_PROCESS_LIVE' if current==peer else 'PID_REUSED_NOT_TOUCHED')
  except OSError as e:row.update(status='ABSENT' if e.errno in (87,1168) else 'UNKNOWN',errno=e.errno,winerror=getattr(e,'winerror',None))
  except pt.Rejected as e:row.update(status='ABSENT' if str(e)=='PROCESS_DEAD' else 'UNKNOWN',reason=str(e))
  result.append(row)
 out={'at':time.time(),'observations':result,'no_termination':True}
 name='final-process-verification.json'
else:
 pre=json.loads((A/'preflight.json').read_text());sources=[{**x,'actual':sha(R/x['path']),'match':sha(R/x['path'])==x['sha256']} for x in pre['source_hashes']]
 package=Path(pre['candidate']['package']['package']);manifest=json.loads((package/'manifest.json').read_text())
 payload=[{'path':x['path'],'match':sha(package/x['path'])==x['sha256']} for x in manifest['files']]
 preserved=json.loads((D/'preservation.json').read_text());arch=Path(preserved['archive'])
 original=[{'path':x['path'],'match':sha(A/x['path'])==sha(arch/x['path'])==x['local']} for x in preserved['original_files_plus_receipt']]
 root=R/'tests/lifecycle_stage1/evidence/TEST-STAGE4-54d0867bae6a4d5b85a687940dbb36fd'
 historical=[{'path':x['path'],'match':sha(root/x['path'])==x['sha256']} for x in json.loads((D/'historical-file-inventory.json').read_text())]
 out={'at':time.time(),'source_entries':sources,'candidate_manifest_sha256':sha(package/'manifest.json'),'candidate_files':payload,'prior_evidence':original,'historical_test_namespace':historical,'source_and_evidence_unchanged':all(x['match'] for x in sources+payload+original+historical)}
 name='final-integrity.json'
(D/name).write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({'file':name,'process_results':[x['status'] for x in out.get('observations',[])],'source_and_evidence_unchanged':out.get('source_and_evidence_unchanged')}))
