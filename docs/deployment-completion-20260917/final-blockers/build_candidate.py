"""New TEST candidate from frozen accepted packaging; no install/production code."""
from pathlib import Path
import hashlib,json,shutil,sys,uuid
D=Path(__file__).resolve().parent;R=D.parents[2]
baseline=R.parent/'deployment-test-releases/TEST-PACKAGE-2966f064bb014c14a13e260937ea4074'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(baseline/'manifest.json')=='fcbd0381f3b4d2b0acd89c15e373418dc27172a60456e3e1698a1963fec091e3'
old=json.loads((baseline/'manifest.json').read_text())
for row in old['files']:assert digest(baseline/row['path'])==row['sha256']
source=R.parent/'deployment-test-releases'/('TEST-SOURCE-'+uuid.uuid4().hex)
shutil.copytree(baseline/'app',source)
shutil.copyfile(R/'stage4_runtime.py',source/'stage4_runtime.py')
sys.path.insert(0,str(source))
from deployment_test import package
target=R.parent/'deployment-test-releases'/('TEST-PACKAGE-'+uuid.uuid4().hex)
electron=(R/'desktop/node_modules/electron/dist').resolve()
result=package.build(source,target,node=baseline/'node/node.exe',native=baseline/'native/peer_identity.node',electron=electron,expected_electron_hash=digest(baseline/'electron/electron.exe'))
new=json.loads((target/'manifest.json').read_text());before={x['path']:x['sha256'] for x in old['files']};after={x['path']:x['sha256'] for x in new['files']}
changed=[k for k in sorted(before.keys()|after.keys()) if before.get(k)!=after.get(k)]
record={'package':result,'baseline':str(baseline),'staged_source':str(source),'differences':changed,'runtime_sha256':digest(R/'stage4_runtime.py')}
(D/'candidate.json').write_text(json.dumps(record,indent=2))
assert set(changed)<={'app/stage4_runtime.py','native-manifest.json'},changed
print(json.dumps(record,indent=2))
