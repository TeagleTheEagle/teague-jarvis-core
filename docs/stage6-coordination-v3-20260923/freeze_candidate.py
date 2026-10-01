import pathlib,json,hashlib,shutil
R=pathlib.Path(__file__).resolve().parent;cfg=json.loads((R/'before.json').read_text());C=pathlib.Path(cfg['candidate'])
shutil.copyfile(R/'test_successor_v3.py',C/'test_successor_v3.py')
oldnames=[x['name'] for x in json.loads((R.parent/'stage6-checker-v2-20260923'/'final-verification.json').read_text())['source']]
names=set(oldnames)
for p in C.iterdir():
 if p.is_file():names.add(p.name)
rows=[]
for name in sorted(names):
 p=C/name;rows.append(dict(name=name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
with (C/'small-source-v3.json').open('x') as f:json.dump(rows,f,indent=2)
with (R/'candidate-frozen.json').open('x') as f:json.dump(dict(candidate=str(C),sourceFiles=len(rows),manifestSHA256=hashlib.sha256((C/'small-source-v3.json').read_bytes()).hexdigest(),files=rows),f,indent=2)
print('FROZEN_CANDIDATE_FILES',len(rows))
