import json,uuid,hashlib
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code']);run='identity-'+uuid.uuid4().hex
(C/run).mkdir();(C/run/'temp').mkdir()
with (R/('identity-run-'+run+'.json')).open('x') as f:json.dump(dict(run=run,path=str(C/run),sources=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(C.iterdir()) if p.is_file() and p.suffix.lower() in ('.py','.ps1','.exe','.dll','.hpp','.cpp','.cs')]),f,indent=2)
print(run)
