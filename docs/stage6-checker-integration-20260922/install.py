import hashlib,json,os,sys
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-small-combined-20260922'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def save(p,v):write(p,json.dumps(v,indent=2,allow_nan=False).encode())
pre=load(R/'preflight.json');C=Path(pre['candidate']);assert load(R/'final'/pre['hostRun']/'final-host-state.json')['status']=='PASS'
sys.path.insert(0,str(P));import combined
run=Path(load(P/'run.json')['path']);host=P/'final'/load(P/'preservation-after.json')['hostRun']/'final-host-state.json'
bundle=combined.read_bundle(run,P/'analysis',host);payload=combined.validate(bundle)
assert payload==load(P/'combined-interface.json')
base=dict(schema='stage6-checker-input-v2',contract='STAGE6-TEST-KERNEL-INSTANCE-20260921-v1',adapter='stage6-small-combined-v1',runId=run.name,evidenceRoot=str(run),payload=payload,bundle=bundle)
def shape(x):
 if isinstance(x,dict):return dict(type='object',required=list(x),additionalProperties=False,properties={k:shape(v) for k,v in x.items()})
 if isinstance(x,list):
  variants={json.dumps(shape(v),sort_keys=True):shape(v) for v in x}
  return dict(type='array',items={'anyOf':list(variants.values())} if variants else False)
 if x is None:return dict(type='null')
 if type(x) is bool:return dict(type='boolean')
 if type(x) is int:return dict(type='integer')
 if type(x) is float:return dict(type='number')
 if type(x) is str:return dict(type='string')
 raise TypeError(type(x))
schema=shape(base);schema.update({'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:jarvis:stage6:checker-input:v2', 'description':'Closed small-evidence adapter schema. Semantic checks and pinned original artifacts are additionally mandatory.'})
for field in ('schema','contract','adapter'):schema['properties'][field]['const']=base[field]
save(C/'schema.json',schema);save(C/'positive-fixture.json',base)
# Schema/contract is persisted BEFORE candidate implementation.
config=dict(reference=str(Path(pre['frozen'])),referenceSHA256=pre['frozenSHA256'],archive=pre['archive'],seal=str(P/'acceptance-seal.json'),sealSHA256=sha(P/'acceptance-seal.json'),review=str(P),root=str(run),analysis=str(P/'analysis'),host=str(host),runId=run.name,
 allowedRoots=[str(R.parent),str(Path(pre['source']).parent.parent)],preflight=str(R/'preflight.json'))
save(C/'binding.json',config)
before={p.name:sha(p) for p in C.iterdir() if p.is_file()}
adapter=(C/'combined.py').read_text(encoding='utf8');old="R.parent/'stage6-durable-kernel-20260921/qualification.py'";assert old in adapter
(C/'combined.py').write_text(adapter.replace(old,"R/'qualification.py'"),encoding='utf8')
(C/'checker_v2.py').write_bytes((R/'checker_template.py').read_bytes())
for name in ('test_candidate.py',):write(C/name,(R/name).read_bytes())
files=[dict(path=str(p),name=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in sorted(C.iterdir()) if p.is_file()]
save(C/'source-freeze.json',dict(files=files));save(R/'candidate-freeze.json',dict(files=files,initial=before,referenceUnchanged=sha(Path(pre['frozen']))==pre['frozenSHA256'],schemaPersistedBeforeImplementation=True))
print(json.dumps(dict(candidate=str(C),files=len(files),schemaBytes=(C/'schema.json').stat().st_size,initialChecker=before['checker_v2.py'],finalChecker=sha(C/'checker_v2.py'))))
