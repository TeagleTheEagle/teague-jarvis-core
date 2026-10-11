import pathlib,json,hashlib,uuid,shutil,zipfile
R=pathlib.Path(__file__).parent;OLD=R.parent/'stage6-kernel-child-trace-20260920'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2)
receipt=json.loads((OLD/'archive-verification.json').read_text());m=json.loads((OLD/'archive-manifest.json').read_text())
assert sha(OLD/'evidence.zip')==receipt['zipSHA256']
with zipfile.ZipFile(OLD/'evidence.zip') as z:
 assert len(z.namelist())==1436
 for x in m['files']:
  b=z.read(x['name']);assert hashlib.sha256(b).hexdigest()==x['sha256']
sources=json.loads((OLD/'final-source.json').read_text())
for x in sources:assert sha(pathlib.Path(x['path']))==x['sha256']
code=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';code.mkdir(parents=True)
for x in sources:shutil.copyfile(x['path'],code/x['name'])
put('plan.json',dict(live_code=str(code),previous=str(pathlib.Path(sources[0]['path']).parent),report=str(R),archive=r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 DUAL CLEANUP 20260920'))
put('source-before.json',sources)
put('historical-classification.json',dict(classification='KERNEL_ONLY_HISTORICAL_EVIDENCE',run='etw-stress-0ecaea118aec42c9b0afcaf56c8686d5',observed=97,retained=94,postExit=3,unexplainedKernelGaps=0,APPLICATION_START_STOP_EVIDENCE='NOT CAPTURED',eligibleForDualEvidence=False,sourceModified=False,archiveSHA256=receipt['zipSHA256'],verifiedMembers=1436,historical87='UNKNOWN',PID13340='CAUSE_UNCONFIRMED',PID9240='CAUSE_UNCONFIRMED'))
shutil.copyfile(code/'kernel_trace.cpp',R/'kernel_trace.cpp')
print(code)
