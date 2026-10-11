import json
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'candidate.json').read_text());C=Path(pre['code']);old=Path(pre['old']);K=C/'medium-checker'
with (R/'integration-preparation-failure.json').open('x') as f:json.dump(dict(reason='Preparation expected a single-backslash path, but the embedded C# DllImport uses escaped double backslashes. Failed before any live run; continue only path rebinding.',sourceScript='integrate.py'),f,indent=2)
p=C/'qualified_launch.ps1';s=p.read_text();a=str(old/'J6OwnedEntry.dll').replace('\\','\\\\');b=str(C/'J6OwnedEntry.dll').replace('\\','\\\\');assert s.count(a)==1;s=s.replace(a,b);p.write_text(s)
d=json.loads((C/'medium-declaration.json').read_text());root=Path(d['evidenceRoot']);assert root.parent==C and list(root.iterdir()) and not (root/'launcher-identity.json').exists()
prior=R.parent/'stage6-medium-20260922';legacy=Path(json.loads((prior/'preflight.json').read_text())['originalChecker'])
with (R/'preflight.json').open('x') as f:json.dump(dict(code=str(C),checker=str(K),root=str(root),originalChecker=str(legacy)),f,indent=2)
with (R/'validate_preparation.py').open('xb') as f:f.write((prior/'validate_preparation.py').read_bytes())
with (R/'run.json').open('x') as f:json.dump(dict(run=root.name,path=str(root)),f,indent=2)
print(str(root))
