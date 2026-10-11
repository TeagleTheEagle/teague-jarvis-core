import pathlib,json,shutil,hashlib
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'plan.json').read_text())['code'])
names=['dry_contract.py','dry_health.py','dry_hash_worker.py','dry_collect.py','dry_finalize.py','dry_launch.ps1','test_dry_integration.py']
for name in names:
 if (C/name).exists():raise RuntimeError('New candidate file exists; do not overwrite')
 shutil.copyfile(R/name,C/name)
source=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(C.iterdir()) if p.is_file() and p.suffix in ('.py','.ps1','.cs','.cpp','.exe')]
with (C/'integration-source.json').open('x') as f:json.dump(source,f,indent=2)
with (R/'candidate-source.json').open('x') as f:json.dump(source,f,indent=2)
print(json.dumps(dict(code=str(C),frozenFiles=len(source),newFiles=names)))
