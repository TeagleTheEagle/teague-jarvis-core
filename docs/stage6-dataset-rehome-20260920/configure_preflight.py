"""Only rebind the exact synthetic test root; collector/guard executable bytes unchanged."""
import pathlib,json,hashlib,zipfile,sys,shutil,os,datetime
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-large-revalidation-20260920';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=read(R/'copy-result.json');assert result['status']=='COPY_VERIFIED';C=pathlib.Path(result['workspace']);T=pathlib.Path(result['destination']);S=pathlib.Path(result['source']);copyrun=pathlib.Path(result['run'])
assert T==C/'large-synthetic' and T.is_relative_to(C)
plan=read(P/'candidate.json');O=pathlib.Path(plan['collector']);H=pathlib.Path(plan['diagnostic'])
for root,rows in ((C,plan['hashes']),(O,read(O/'baseline-source.json')),(H,read(H/'hardening-hashes.json'))):
 for x in rows:assert sha(root/x['name'])==x['sha256']
archives={}
for n in ('stage6-dry1-execution-20260920','stage6-dry2-execution-20260920','stage6-protected-integration-20260920','stage6-targeted-hardening-20260920','stage6-large-revalidation-20260920'):
 receipt=read(R.parent/n/'archive-verification.json');A=pathlib.Path(receipt['path']);assert sha(A/'evidence.zip')==receipt['zipSHA256'] and sha(A/'archive-manifest.json')==receipt['manifestSHA256'];m=read(A/'archive-manifest.json');files=m['files'] if isinstance(m,dict) else m
 with zipfile.ZipFile(A/'evidence.zip') as z:
  assert len(z.namelist())==receipt['members']==len(files)+1
  for x in files:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
  assert z.read('archive-manifest.json')==(A/'archive-manifest.json').read_bytes()
 archives[n]=receipt
assert sha(copyrun/'dataset-manifest.json')==result['manifestSHA256']
assert sha(O/'calibration.json')==result['calibrationSHA256']
before=(C/'baseline-allowlist.json').read_bytes();original=read(C/'baseline-allowlist.json');assert original==dict(approvedProtectedRoots=[],realProtectedAccess=False,syntheticRoots=[str(S)])
with (R/'allowlist-before.json').open('xb') as f:f.write(before)
with (R/'run-source-before.json').open('xb') as f:f.write((C/'run-source.json').read_bytes())
changed=dict(original,syntheticRoots=[str(T)])
(C/'baseline-allowlist.json').write_text(json.dumps(changed,indent=2)+'\n')
frozen=read(C/'run-source.json');changedRows=[]
for x in frozen:
 h=sha(C/x['name'])
 if h!=x['sha256']:
  assert x['name']=='baseline-allowlist.json';changedRows.append(dict(name=x['name'],before=x['sha256'],after=h));x['sha256']=h
assert len(changedRows)==1
(C/'run-source.json').write_text(json.dumps(frozen,indent=2)+'\n')
with (R/'configuration-change.json').open('x') as f:json.dump(dict(changes=changedRows,scope='Exact synthetic test source relocation only',oldSource=str(S),newSource=str(T),externalSourceAllowed=False,collectorCodeChanged=False,guardChanged=False),f,indent=2)
sys.path.insert(0,str(C));import baseline_contract as b,baseline_hash_worker as w
assert b.approved(T)==T
try:b.approved(S)
except ValueError:pass
else:raise AssertionError('Old external source still accepted')
inv=b.inventory(T);expected=read(copyrun/'dataset-manifest.json');assert len(inv)==12 and sum(x['bytes'] for x in inv.values())==result['totalBytes']
for x in expected['files']:
 meta=inv[x['path']];assert meta['bytes']==x['bytes'] and meta['mtime_ns']==x['mtime_ns']
 with w.checked_open(T/x['path'],T,meta):pass # Verify canonical opened-handle identity, no content writes.
assert {x['fullPath'] for x in inv.values()}=={str(T/x['path']) for x in expected['files']}
assert shutil.disk_usage(C).free>2**30
out=dict(status='PASS_PENDING_HOST_CHECK',source=str(T),workspace=str(C),collectorHashes=84,diagnosticHashes=96,integrationFiles=len(frozen),unchangedIntegrationCode=True,configurationChange=changedRows,guardUnchanged=True,containment='PASS',oldExternalSourceRejected=True,canonicalOpenedHandlesVerified=12,manifestSHA256=result['manifestSHA256'],fileCount=12,totalBytes=result['totalBytes'],archives=archives,calibrationUnchanged=True,DfreeBytes=shutil.disk_usage(C).free,protectedAccess=False,productionChanged=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (R/'preflight.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='archives'}))
