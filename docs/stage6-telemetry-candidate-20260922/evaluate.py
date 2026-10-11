import json,hashlib,sys,shutil
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'candidate.json').read_text());C=Path(pre['code']);root=Path(json.loads((R/'run.json').read_text())['path'])
host=R/'final/39b9d22f9d574c7fa1874c9bd29594e6/final-host-state.json';assert json.loads(host.read_text())['status']=='PASS'
with (root/'final-host-state.json').open('xb') as f:f.write(host.read_bytes())
sys.path[:0]=[str(C/'medium-checker'),str(C)];import fresh_binding as fb;import checker_telemetry as ct
fb.seal_intake(C)
try:result=ct.evaluate()
except BaseException as e:
 with (R/'checker-failure.json').open('x') as f:json.dump(dict(status='REJECT',error=repr(e)),f,indent=2)
 raise
with (R/'checker-result.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(status=result['status'],schema=result['schema'],telemetry=result['rules']['telemetry'],counts=result['rules']['lifecycle']['counts'])))
