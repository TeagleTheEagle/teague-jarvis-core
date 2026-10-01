import pathlib,json,hashlib,zipfile,shutil,uuid
R=pathlib.Path(__file__).parent;old=R.parent/'stage6-dual-cleanup-20260920'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((old/'archive-verification.json').read_text());m=json.loads((old/'archive-manifest.json').read_text())
assert sha(old/'evidence.zip')==receipt['zipSHA256']
with zipfile.ZipFile(old/'evidence.zip') as z:
 assert len(z.namelist())==1147
 for x in m['files']:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
before=json.loads((old/'final-source.json').read_text());C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in before:
 p=pathlib.Path(x['path']);assert sha(p)==x['sha256'];shutil.copyfile(p,C/x['name'])
previous=pathlib.Path(before[0]['path']).parent
shutil.copytree(previous/'dual-9aa6b84f76074c83956a1cb4fad811bc',C/'dual-9aa6b84f76074c83956a1cb4fad811bc')
for name,v in [('source-before.json',before),('plan.json',dict(code=str(C),previous=str(previous),report=str(R),archive=r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 DRY INTEGRATION 20260920'))]:
 with (R/name).open('x') as f:json.dump(v,f,indent=2)
print(C)
