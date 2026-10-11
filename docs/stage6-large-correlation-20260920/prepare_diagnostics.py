import pathlib,json,hashlib,uuid,shutil,ast
R=pathlib.Path(__file__).parent;C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\1c1f5d0c390b42cc9ba9f4f6221dabc6\code')
D=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
rows=json.loads((C/'baseline-source.json').read_text())
for x in rows:assert hashlib.sha256((C/x['name']).read_bytes()).hexdigest()==x['sha256']
for n in ('diag_hash.py','diag_collect.py'):ast.parse((R/n).read_text())
D.mkdir(parents=True,exist_ok=False)
for x in rows:shutil.copyfile(C/x['name'],D/x['name'])
for n in ('diag_hash.py','diag_collect.py','diag_launch.ps1','diag_resources.ps1'):shutil.copyfile(R/n,D/n)
contract=json.loads((C/'protected-3aec3ce0062c42a19077a2bad0571bd7'/'contract.json').read_text())
meta=contract['inventory']['Snapshots/child.vdi'];p=pathlib.Path(meta['fullPath']);s=p.stat();assert s.st_size==meta['bytes'] and s.st_mtime_ns==meta['mtime_ns'] and s.st_ino==meta['fileId']
(D/'diagnostic-plan.json').write_text(json.dumps(dict(file=str(p),metadata=meta,boundedSeconds=[0,5,12,20,30],maxBytesPerCase=8*2**30,fullCampaign=False),indent=2))
hashes=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(D.iterdir()) if p.is_file()]
(D/'diagnostic-hashes.json').write_text(json.dumps(hashes,indent=2))
with (R/'diagnostic-workspace.json').open('x') as f:json.dump(dict(code=str(D),frozenCopiedFiles=len(rows),hashes=hashes),f,indent=2)
print(str(D))
