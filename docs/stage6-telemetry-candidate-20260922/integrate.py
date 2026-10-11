import json,uuid,sys
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'candidate.json').read_text());C=Path(pre['code']);K=C/'medium-checker';old=Path(pre['old'])
with (K/'checker_telemetry.py').open('xb') as f:f.write((R/'checker_telemetry.py').read_bytes())
sys.path[:0]=[str(K),str(C)];import checker_telemetry as ct
with (C/'telemetry-policy.json').open('x') as f:json.dump(ct.POLICY,f,indent=2)
run='identity-'+uuid.uuid4().hex;root=C/run;root.mkdir();(root/'temp').mkdir();(root/'analysis').mkdir()
d=json.loads((C/'medium-declaration.json').read_text());d.update(runId=run,codeRoot=str(C),evidenceRoot=str(root))
(C/'medium-declaration.json').write_text(json.dumps(d,indent=2))
import hashlib
(C/'medium-intent.json').write_text(json.dumps(dict(evidenceRoot=str(root),declarationSHA256=hashlib.sha256((C/'medium-declaration.json').read_bytes()).hexdigest()),indent=2))
launch=C/'qualified_launch.ps1';s=launch.read_text();assert str(old/'J6OwnedEntry.dll') in s;s=s.replace(str(old/'J6OwnedEntry.dll'),str(C/'J6OwnedEntry.dll'));launch.write_text(s)
# Reuse the exact existing offline 114+43 preparation drivers in a fresh output location.
prior=R.parent/'stage6-medium-20260922';legacy=Path(json.loads((prior/'preflight.json').read_text())['originalChecker'])
prep=dict(code=str(C),checker=str(K),root=str(root),originalChecker=str(legacy))
with (R/'preflight.json').open('x') as f:json.dump(prep,f,indent=2)
with (R/'validate_preparation.py').open('xb') as f:f.write((prior/'validate_preparation.py').read_bytes())
with (R/'run.json').open('x') as f:json.dump(dict(run=run,path=str(root)),f,indent=2)
print(json.dumps(dict(root=str(root),checker=ct.VERSION,policy=ct.POLICY)))
