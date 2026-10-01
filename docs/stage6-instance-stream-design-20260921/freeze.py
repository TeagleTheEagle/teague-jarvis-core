import pathlib,json,hashlib,zipfile,datetime
R=pathlib.Path(__file__).parent
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f469b94b665e4808af1c5bb6aa46b207\code')
P=R.parent/'stage6-identity-capacity-recalibration-20260921'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
old=read(P/'freeze.json');checks=[]
for row in old['candidateHashes']:
 assert sha(C/row['name'])==row['sha256'];checks.append(dict(path=str(C/row['name']),sha256=row['sha256']))
for n in ('EVENTS.md','events-22.json','capacity-measurement.json','capacity-plan.json','final-preservation.json','archive-verification.json'):
 checks.append(dict(path=str(P/n),sha256=sha(P/n)))
archives=[]
for report,manifestName in [(R.parent/'stage6-trace-capacity-native-entry-20260921','archive-manifest.json'),(P,'manifest.json')]:
 receipt=read(report/'archive-verification.json');a=pathlib.Path(receipt['path']);manifest=read(a/manifestName)
 assert sha(a/'evidence.zip')==receipt['zipSHA256'];assert sha(a/manifestName)==receipt['manifestSHA256']
 with zipfile.ZipFile(a/'evidence.zip') as z:
  assert len(z.infolist())==receipt['members']==len(manifest)+1
  assert z.read(manifestName)==(a/manifestName).read_bytes()
  for x in manifest:
   with z.open(x['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
 archives.append(receipt)
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=str(C),candidateCount=116,checks=checks,archives=archives,protectedAccess=False,productionChanges=False)
with (R/'freeze.json').open('x') as f:json.dump(out,f,indent=2)
print('116 candidate hashes, 1078 + 155 archive members verified')
