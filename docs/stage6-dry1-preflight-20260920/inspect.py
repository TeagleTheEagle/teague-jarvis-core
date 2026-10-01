"""Read-only candidate/preflight inspection; creates report evidence only."""
import pathlib,json,hashlib,zipfile,shutil,ast
R=pathlib.Path(__file__).parent;prior=R.parent/'stage6-dual-cleanup-20260920'
plan=json.loads((prior/'plan.json').read_text());C=pathlib.Path(plan['live_code']);repo=R.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2)
sources=json.loads((prior/'final-source.json').read_text());checked=[]
for x in sources:checked.append(dict(path=x['path'],expected=x['sha256'],actual=sha(pathlib.Path(x['path'])),unchanged=sha(pathlib.Path(x['path']))==x['sha256']))
receipt=json.loads((prior/'archive-verification.json').read_text());manifest=json.loads((prior/'archive-manifest.json').read_text());arc=pathlib.Path(receipt['path'])
assert sha(arc/'evidence.zip')==receipt['zipSHA256'];assert sha(arc/'archive-manifest.json')==receipt['manifestSHA256']
with zipfile.ZipFile(arc/'evidence.zip') as z:
 assert len(z.namelist())==receipt['members']
 for x in manifest['files']:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
 assert z.read('archive-manifest.json')==(arc/'archive-manifest.json').read_bytes()
app=[]
for x in json.loads((prior/'application-preservation.json').read_text())['files']:
 actual=sha(repo/x['path']);app.append(dict(path=x['path'],sha256=actual,unchanged=actual==x['sha256']))
synthetic=repo/'docs/stage6-heartbeat-journal-20260918/sacrificial'
artifacts=[dict(path=str(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,reparse=p.is_symlink() or p.is_junction()) for p in sorted(synthetic.iterdir()) if p.is_file()]
usage=shutil.disk_usage('D:/')
evidence=[]
for n in ('launch.ps1','collect.py','collect_hardened.py','dual_launch.ps1','cleanup_checker.py','dry_worker.py','stress.py','probe_timing.py'):
 p=C/n;text=p.read_text();evidence.append(dict(path=str(p),sha256=sha(p),lines=[dict(line=i,text=line) for i,line in enumerate(text.splitlines(),1) if any(s in line for s in ("mode=$Mode","collect.py","import collect_hardened","phase=config",'stress.py','cleanup_checker.py','stress-result.json','hardDeadlineFailure','wait_approved','dry_worker.py'))]))
assert all(x['unchanged'] for x in checked+app)
put('preflight.json',dict(status='BLOCKED',candidateHashes=checked,archive=dict(verifiedMembers=receipt['members'],zipSHA256=receipt['zipSHA256'],path=str(arc)),applicationHashes=app,disk=dict(free=usage.free,total=usage.total),syntheticInventory=artifacts,syntheticTotalBytes=sum(x['bytes'] for x in artifacts),syntheticHashesPerformed=False,protectedAccess=False,productionChanged=False,sourceChanged=False,monitorsStarted=False,dryRunStarted=False,blockers=['launch.ps1 writes mode; collect.py imports collect_hardened which requires phase A-E before its protected try/finally','dual_launch.ps1 runs stress.py only, not the complete baseline/hash workflow','cleanup_checker expects stress-specific producer/observer evidence; accepted dry launcher does not collect that evidence'],codeEvidence=evidence))
print(json.dumps(dict(status='BLOCKED',candidateHashes=len(checked),applicationHashes=len(app),archiveMembers=receipt['members'],syntheticFiles=len(artifacts),syntheticBytes=sum(x['bytes'] for x in artifacts),DfreeGiB=usage.free/2**30)))
