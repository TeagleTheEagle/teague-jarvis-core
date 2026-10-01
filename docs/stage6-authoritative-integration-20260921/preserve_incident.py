import pathlib,json,hashlib,zipfile,datetime,shutil
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-instance-stream-design-20260921'
T=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\instance-stream-62cd5dabd4cb46b593990f1fae4b2a28')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
receipt=load(P/'archive-verification.json');base=pathlib.Path(receipt['path']);assert sha(base/'evidence.zip')==receipt['zipSHA256'];assert sha(base/'manifest.json')==receipt['manifestSHA256']
manifest=load(base/'manifest.json');mismatches=[]
with zipfile.ZipFile(base/'evidence.zip') as z:
 assert len(z.namelist())==len(set(z.namelist()))==receipt['members']==143
 for x in manifest['files']:
  with z.open(x['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
  prefix,relative=x['name'].split('/',1);p=(P if prefix=='report' else T)/relative
  actual=sha(p)
  if actual!=x['sha256']:mismatches.append(dict(path=str(p),expected=x['sha256'],actual=actual,member=x['name']))
 original=z.read('report/final-host-state.json')
 with (R/'original-host-state-from-verified-archive.json').open('xb') as f:f.write(original)
current=(P/'final-host-state.json').read_bytes()
with (R/'new-host-state-after-accidental-overwrite.json').open('xb') as f:f.write(current)
freeze=load(P/'freeze.json')
for x in freeze['checks']:assert sha(pathlib.Path(x['path']))==x['sha256'],x['path']
result=dict(status='BLOCKED',reason='LOCAL_HISTORICAL_EVIDENCE_OVERWRITTEN_DURING_PREFLIGHT',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),operation='Reused previous final_host.ps1; its Set-Content replaced previous local final-host-state.json',candidateHashesUnchanged=116,additionalFrozenChecksUnchanged=6,priorArchiveMembersVerified=143,priorArchiveSHA256=receipt['zipSHA256'],priorArchiveUnchanged=True,localEvidenceMismatches=mismatches,originalRecoveredCopySHA256=sha(R/'original-host-state-from-verified-archive.json'),newPreservedCopySHA256=sha(R/'new-host-state-after-accidental-overwrite.json'),noRestorationPerformed=True,newHostCheck=load(R/'new-host-state-after-accidental-overwrite.json'),integrationStarted=False,observersStarted=False,mediumRun=False,largeRun=False,protectedAccess=False,productionChanged=False)
assert len(mismatches)==1 and mismatches[0]['member']=='report/final-host-state.json',mismatches
with (R/'preservation-incident.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
