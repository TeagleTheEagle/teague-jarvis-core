import pathlib,json,hashlib,zipfile,shutil,datetime
R=pathlib.Path(__file__).parent;first=R.parent/'stage6-dry1-execution-20260920';integration=R.parent/'stage6-dry-integration-20260920';repo=R.parent.parent
previous=json.loads((first/'preflight.json').read_text());C=pathlib.Path(previous['code']);firstRun=pathlib.Path(json.loads((first/'run-verification.json').read_text())['run'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2)
checked=[]
for x in previous['candidateHashes']:
 actual=sha(pathlib.Path(x['path']));assert actual==x['expected'];checked.append(dict(x,actual=actual,unchanged=True))
assert json.loads((C/'integration-source.json').read_text())==json.loads((integration/'candidate-source.json').read_text())
receipt=json.loads((first/'archive-verification.json').read_text());A=pathlib.Path(receipt['path']);manifest=json.loads((A/'archive-manifest.json').read_text())
assert sha(A/'evidence.zip')==receipt['zipSHA256'] and sha(A/'archive-manifest.json')==receipt['manifestSHA256']
with zipfile.ZipFile(A/'evidence.zip') as z:
 assert len(z.namelist())==131
 for x in manifest['files']:
  assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
  assert sha(pathlib.Path(x['source']))==x['sha256'],'Archived first-run member changed'
 assert z.read('archive-manifest.json')==(A/'archive-manifest.json').read_bytes()
app=[]
for x in previous['applicationHashes']:
 actual=sha(repo/x['path']);assert actual==x['expected'];app.append(dict(x,actual=actual,unchanged=True))
source=pathlib.Path(previous['source'])
for q in (source,*source.parents):assert not q.is_symlink() and not q.is_junction()
files=sorted(source.iterdir());assert len(files)==12 and all(p.is_file() and p.suffix=='.bin' and not p.is_symlink() and not p.is_junction() for p in files)
inventory=[dict(name=p.name,size=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in files];assert inventory==previous['syntheticInventory']
space=shutil.disk_usage('D:/');assert space.free>sum(x['size'] for x in inventory)*2+1073741824
oldruns=sorted(str(p) for p in C.glob('integrated-dry1-*'));assert oldruns==[str(firstRun)],'Unexpected pre-existing run: stop before repetition'
put('preflight.json',dict(status='PASS_PENDING_PROCESS_CHECK',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),code=str(C),candidateHashes=checked,applicationHashes=app,archive=receipt,archiveVerifiedMembers=131,firstRun=str(firstRun),source=str(source),syntheticInventory=inventory,syntheticBytes=sum(x['size'] for x in inventory),DfreeBytes=space.free,priorDry1Runs=oldruns,protectedAccess=False,productionChanged=False,harnessModified=False,campaignOrdinal=2))
put('campaign-intent.json',dict(ordinal=2,attemptLimit=1,firstRun=str(firstRun),scenario='dry1',rawSuccessLabel='DRY_RUN_1_PASS',interpretation='Second independent campaign execution of the unchanged validated scenario. Raw labels remain unchanged.',protectedBaselineAuthorized=False))
# Reuse proven report-only checks, not any mutable run data or candidate code.
host=(first/'host.ps1').read_text().replace('stage6-dry-integration-20260920\\host-final.json','stage6-dry1-execution-20260920\\host-after.json')
with (R/'host.ps1').open('x') as f:f.write(host)
verify=(first/'verify.py').read_text().replace("run=C/'integrated-dry1-8c2cbaeef9d04a8080b9bcf22fae89cd';repo=R.parent.parent", "fresh=[p for p in C.glob('integrated-dry1-*') if str(p) not in pre['priorDry1Runs']];assert len(fresh)==1;run=fresh[0];repo=R.parent.parent")
verify=verify.replace("kernel=read('etw-result.json');known={}","kernel=read('etw-result.json');known={}\nfirstRun=pathlib.Path(pre['firstRun']);oldKernel=json.loads((firstRun/'etw-result.json').read_text());assert not {(x['pid'],x['created']) for x in kernel['rows']} & {(x['pid'],x['created']) for x in oldKernel['rows']}\noldObservers=json.loads((firstRun/'observer-identities.json').read_text(encoding='utf-8-sig'));newObservers=read('observer-identities.json');assert all((x['pid'],x['created'])!=(oldObservers[k]['pid'],oldObservers[k]['created']) for k,x in newObservers.items())")
verify=verify.replace('dryRun2Executed=False,state=state','dryRun2Executed=True,campaignOrdinal=2,rawHarnessStatus=read(\'integration-result.json\')[\'status\'],freshObservers=True,freshProcessIdentities=True,state=state')
with (R/'verify.py').open('x') as f:f.write(verify)
print(json.dumps(dict(status='PASS_PENDING_PROCESS_CHECK',candidateFiles=len(checked),applicationFiles=len(app),firstArchiveMembers=131,syntheticFiles=len(files),syntheticBytes=sum(x['size'] for x in inventory),DfreeGiB=space.free/2**30)))
