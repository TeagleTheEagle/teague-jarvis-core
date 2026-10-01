"""Separate small integration contract; cannot authorize medium/large/protected data."""
import json,hashlib,pathlib,sys,uuid
from workspace import CODE,check_path,run_dir
from baseline_contract import prepare,load,save,inventory
SCHEMA='stage6-small-coordination-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 rows=json.loads((CODE/'small-source-v3.json').read_text())
 for r in rows:
  p=check_path(CODE/r['name'])
  if not p.is_file() or p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:raise ValueError('SOURCE_DRIFT')
 return sha(CODE/'small-source-v3.json')
def validate(root,v):
 expected=dict(schema=SCHEMA,run=root.name,code=str(CODE),source=str(CODE/'small-synthetic'),sourceManifestSHA256=frozen(),case=v.get('case'),inventorySHA256=sha(root/'contract.json'),files=12,bytes=786432,heartbeat=10.0,probe=13.6,observer=15.0,campaign=90.0,kernelCapture=180.0,cleanup=20.0,coordination='stage6-terminal-v3',channels=['kernel-authority','detailed-startup','supporting-CIM'],classes=['collector','hash-worker','secondary-sampler','lifecycle-probe','OS_CONSOLE_HELPER','APPLICATION_OBSERVER','DETAIL_OBSERVER'])
 check_path(root)
 if v!=expected or v['case'] not in ('normal','hash-start-failure'):raise ValueError('SMALL_DECLARATION_MISMATCH')
 contract=load(root)
 if not contract['synthetic'] or contract['source']!=expected['source'] or len(contract['inventory'])!=12 or sum(x['bytes'] for x in contract['inventory'].values())!=786432:raise ValueError('SMALL_SYNTHETIC_ONLY')
 return v
def make(case):
 digest=frozen();root=prepare(str(CODE/'small-synthetic'));(root/'detail').mkdir()
 v=dict(schema=SCHEMA,run=root.name,code=str(CODE),source=str(CODE/'small-synthetic'),sourceManifestSHA256=digest,case=case,inventorySHA256=sha(root/'contract.json'),files=12,bytes=786432,heartbeat=10.0,probe=13.6,observer=15.0,campaign=90.0,kernelCapture=180.0,cleanup=20.0,coordination='stage6-terminal-v3',channels=['kernel-authority','detailed-startup','supporting-CIM'],classes=['collector','hash-worker','secondary-sampler','lifecycle-probe','OS_CONSOLE_HELPER','APPLICATION_OBSERVER','DETAIL_OBSERVER'])
 validate(root,v);save(root/'small-declaration-v3.json',v);return root
if __name__=='__main__':
 if sys.argv[1]=='prepare':print(make(sys.argv[2]))
 elif sys.argv[1]=='verify':
  root=run_dir(sys.argv[2]);validate(root,json.loads((root/'small-declaration-v3.json').read_text()));print('BINDING_PASS')
