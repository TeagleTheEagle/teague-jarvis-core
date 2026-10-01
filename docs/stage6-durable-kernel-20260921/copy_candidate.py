import json,uuid,hashlib
from pathlib import Path
R=Path(__file__).parent;plan=json.loads((R/'preservation.json').read_text());C=Path(plan['source'])
host=json.loads((R/'final'/plan['hostRun']/'final-host-state.json').read_text());assert host['status']=='PASS'
N=Path(r'D:\JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';N.mkdir(parents=True,exist_ok=False)
rows=[]
for p in sorted(C.iterdir()):
 if p.is_file() and p.suffix.lower() in ('.cs','.py','.ps1','.cpp','.h','.exe','.dll'):
  assert not p.is_symlink();b=p.read_bytes()
  with (N/p.name).open('xb') as f:f.write(b)
  rows.append(dict(name=p.name,sha256=hashlib.sha256(b).hexdigest()))
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(N),copies=rows),f,indent=2)
print(str(N))
