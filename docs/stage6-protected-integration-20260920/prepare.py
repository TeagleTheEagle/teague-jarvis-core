import pathlib,json,hashlib,zipfile,uuid,shutil
R=pathlib.Path(__file__).parent
old=R.parent/'stage6-dry2-execution-20260920'
p=json.loads((old/'preflight.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in p['candidateHashes']:assert sha(pathlib.Path(x['path']))==x['expected']
for name in ('stage6-dry1-execution-20260920','stage6-dry2-execution-20260920'):
 receipt=json.loads((R.parent/name/'archive-verification.json').read_text());a=pathlib.Path(receipt['path'])
 assert sha(a/'evidence.zip')==receipt['zipSHA256'] and sha(a/'archive-manifest.json')==receipt['manifestSHA256']
 with zipfile.ZipFile(a/'evidence.zip') as z:
  m=json.loads(z.read('archive-manifest.json'));assert len(z.namelist())==receipt['members']
  for x in m['files']:assert hashlib.sha256(z.read(x['name'])).hexdigest()==x['sha256']
host=(old/'host.ps1').read_text().replace('stage6-dry1-execution-20260920\\host-after.json','stage6-dry2-execution-20260920\\host-after.json')
with (R/'host.ps1').open('x') as f:f.write(host)
with (R/'frozen-before.json').open('x') as f:json.dump(p,f,indent=2)
print('73 frozen hashes and both historical archives verified; host preflight required next')
