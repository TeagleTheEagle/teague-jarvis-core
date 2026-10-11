import pathlib
R=pathlib.Path(__file__).parent
s=(R.parent/'stage6-dry1-execution-20260920'/'archive.py').read_text()
s=s.replace('STAGE6 DRY RUN 1 20260920','STAGE6 DRY RUN 2 20260920').replace('DRY_RUN_1_PASS','DRY_RUN_2_PASS').replace('dryRun2Executed=False','dryRun2Executed=True').replace('PROPOSED-DRY-RUN-2.md','PROPOSED-PROTECTED-BASELINE.md')
s=s.replace('files=[]', '''# Reverify the entire first-run canonical archive and original evidence without mutation.
prior=pre['archive'];old=pathlib.Path(prior['path'])
assert sha(old/'evidence.zip')==prior['zipSHA256'] and sha(old/'archive-manifest.json')==prior['manifestSHA256']
oldmanifest=json.loads((old/'archive-manifest.json').read_text())
with zipfile.ZipFile(old/'evidence.zip') as z:
 assert len(z.namelist())==131
 for item in oldmanifest['files']:
  assert hashlib.sha256(z.read(item['name'])).hexdigest()==item['sha256']
  assert sha(pathlib.Path(item['source']))==item['sha256']
 assert z.read('archive-manifest.json')==(old/'archive-manifest.json').read_bytes()
files=[]''')
with (R/'archive.py').open('x',encoding='utf-8') as f:f.write(s)
print('Prepared archive-only script; no candidate/runtime changes')
