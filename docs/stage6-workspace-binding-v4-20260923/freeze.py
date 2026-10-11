import pathlib,json,hashlib,shutil,ast
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate']);N=pathlib.Path(json.loads((R/'before.json').read_text())['predecessor'])
for n in ('workspace_binding_v4.py','candidate_dll_v4.ps1','test_binding_v4.py'):shutil.copy2(R/n,C/n)
old=json.loads((N/'small-source-v3.json').read_text());names={x['name'] for x in old}
names.update(p.name for p in C.iterdir() if p.is_file() and (p.name.endswith('_v4.py') or p.name.endswith('_v4.ps1') or p.name.endswith('-v4.json')))
rows=[]
for n in sorted(names):
 p=C/n;b=p.read_bytes()
 if p.suffix=='.py':ast.parse(b,filename=str(p))
 rows.append(dict(name=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
with (C/'small-source-v3.json').open('w') as f:json.dump(rows,f,indent=2,sort_keys=True)
print(json.dumps(dict(files=len(rows),manifestSHA256=hashlib.sha256((C/'small-source-v3.json').read_bytes()).hexdigest(),syntax='PASS')))
