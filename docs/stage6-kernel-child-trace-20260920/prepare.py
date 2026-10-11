import pathlib,json,hashlib,zipfile,uuid,shutil
R=pathlib.Path(__file__).resolve().parent;PREV=R.parent/'stage6-cleanup-hardening-20260920'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2)
m=read(PREV/'archive-manifest.json')
with zipfile.ZipFile(PREV/'evidence.zip') as z:
 for x in m['files']:
  b=z.read(x['name']);assert len(b)==x['size'] and hashlib.sha256(b).hexdigest()==x['sha256']
save('historical-archive-before.json',dict(path=str(PREV/'evidence.zip'),sha256=sha(PREV/'evidence.zip'),members=len(m['files'])+1))
old=read(PREV/'final-source.json');assert all(sha(pathlib.Path(x['path']))==x['sha256'] for x in old)
save('source-before.json',old)
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True,exist_ok=False)
for row in old:shutil.copyfile(row['path'],C/row['name'])
save('plan.json',dict(live_code=str(C),previous=read(PREV/'plan.json')['live_code'],report=str(R),archive='C:/Users/jonny/OneDrive/Desktop/TEAGUE INDUSTRIES DATABASE/06 SOURCE RECORDS/STAGE6 KERNEL CHILD TRACE 20260920',protectedBaselineAuthorized=False))
missing=[]
for case in read(PREV/'campaign-summary.json'):
 for row in case['correctedMatching']:
  if row['retainedMatches']==1:continue
  missing.append(dict(run=case['phase'],pid=row['start']['pid'],parentPid=row['start']['parentPid'],imageName=row['start']['name'],startEvent=row['start'],stopMatches=row['stopMatches'],category='UNKNOWN',observerLimitation='Polling observer retained no matching identity. Per-attempt OpenProcess outcome/first discovery time was not recorded; exact reason cannot be reconstructed.'))
assert len(missing)==87
save('historical-87-coverage.json',dict(cases=missing,categories={'UNKNOWN':87},unattributableImageQueryErrors=3,explanation='D trace contains WinError31/5/5 without PID at the failed query, so none may be assigned to a particular missing helper.'))
print(C)
