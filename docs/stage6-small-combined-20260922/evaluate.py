import json
from pathlib import Path
import combined
R=Path(__file__).parent;root=Path(json.loads((R/'run.json').read_text())['path']);host=R/'final'/json.loads((R/'preservation-after.json').read_text())['hostRun']/'final-host-state.json'
b=combined.read_bundle(root,R/'analysis',host);out=combined.validate(b)
with (R/'combined-interface.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ('authoritative','verification','durable')}))
print(json.dumps(dict(authoritative={k:v for k,v in out['authoritative'].items() if k!='identities'},durable={k:v for k,v in out['durable'].items() if k!='segmentManifest'},verification={k:v for k,v in out['verification'].items() if k!='coverage'})))
