import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parent;plan=json.loads((R/'workspace-plan.json').read_text());dest=pathlib.Path(plan['live_code']);base=pathlib.Path('D:/JARVIS-STAGE6-LIVE')
for q in (base,*base.parents):
 if q.exists() and (q.is_symlink() or q.is_junction()):raise RuntimeError('Reparse parent')
dest.mkdir(parents=True,exist_ok=False);manifest=[]
for p in sorted((R/'candidate').iterdir()):
 if not p.is_file() or p.name.startswith('.env'):raise RuntimeError('Unexpected source')
 data=p.read_bytes();target=dest/p.name
 with target.open('xb') as f:f.write(data)
 digest=hashlib.sha256(data).hexdigest()
 if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise RuntimeError('Hash mismatch')
 manifest.append(dict(name=p.name,sha256=digest,size=len(data)))
for p in (R/'candidate-hashes.json',dest/'candidate-hashes.json'):
 with p.open('x') as f:json.dump(manifest,f,indent=2)
print(json.dumps(dict(files=len(manifest),destination=str(dest),status='HASH_VERIFIED')))
