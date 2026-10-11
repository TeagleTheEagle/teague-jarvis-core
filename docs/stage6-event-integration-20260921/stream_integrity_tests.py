import pathlib,json,sys,uuid,hashlib,shutil
from evidence_io import create_json,create_bytes
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'active-workspace.json').read_text())['code']);sys.path.insert(0,str(C))
from application_authority import verify,load_inputs
source=pathlib.Path(json.loads((R/'tap-integration-focused.json').read_text())['run']);base=C/('integrity-'+uuid.uuid4().hex);base.mkdir();checks=[]
def copy_case(name):
 root=base/name;root.mkdir()
 for p in source.glob('app-authority*'):create_bytes(root/p.name,p.read_bytes())
 return root
def rejected(root):
 try:verify(root);return False
 except (ValueError,OSError,AssertionError,KeyError):return True
for name in ('missing','corrupt','duplicate-manifest','reordered-manifest','sequence-gap','partial-row','nonzero-source-loss','writer-fault','admission-loss','traversal','missing-tail'):
 root=copy_case(name);mp=root/'app-authority.json';m=json.loads(mp.read_text());part=root/m['segments'][0]['name']
 if name=='missing':
  # Do not delete evidence: move the generated fixture segment to an explicit missing-artifact sidecar.
  part.rename(root/'preserved-missing-segment.bin')
 elif name=='corrupt':
  with part.open('r+b') as f:f.seek(4);f.write(b'X')
 elif name=='duplicate-manifest':m['segments'].append(m['segments'][0])
 elif name=='reordered-manifest':m['segments'].reverse()
 elif name=='sequence-gap':
  data=part.read_bytes();data=data.replace(b'"seq":1,',b'"seq":0,',1);part.write_bytes(data);m['segments'][0]['sha256']=hashlib.sha256(data).hexdigest()
 elif name=='partial-row':
  data=part.read_bytes()[:-1];part.write_bytes(data);m['segments'][0]['bytes']=len(data);m['segments'][0]['sha256']=hashlib.sha256(data).hexdigest();m['bytes']-=1
 elif name=='nonzero-source-loss':
  # Existing actual cleanup source-loss gate is independently asserted below.
  m['fault']='ETW_LOSS_REPORTED'
 elif name=='writer-fault':m['fault']='WRITE_FAILED'
 elif name=='admission-loss':m['attempted']+=1
 elif name=='traversal':m['segments'][0]['name']='../outside.jsonl'
 elif name=='missing-tail':m['segments'].pop()
 mp.write_text(json.dumps(m)) # Explicitly mutable corruption fixture only.
 assert rejected(root),name;checks.append(dict(case=name,result='REJECTED_AS_REQUIRED'))
v=verify(source);assert v['records']==36000
tap,events,receipts=load_inputs(source);assert len(tap)==24000 and len(events)==len(receipts)==12000
text=(C/'cleanup_checker.py').read_text();assert "tap=read('app-tap.json')" not in text and 'tap,events,receipts=load_inputs(root)' in text
assert "for field in ('faults','eventsLost','realtimeBuffersLost','buffersLost','flushResult','stopResult','consumerResult')" in text
for p in [C/'cleanup_checker.py',C/'baseline_finalize.py',C/'process_instances.py',C/'application_authority.py']:compile(p.read_text(),str(p),'exec')
checks.extend([dict(case='complete unmodified source',result='PASS'),dict(case='complete reader beyond tap',result='PASS'),dict(case='checker tap dependency removed',result='PASS_STATIC_WIRING'),dict(case='source-loss gate preserved',result='PASS_STATIC_WIRING'),dict(case='changed Python syntax',result='PASS')])
create_json(R/'stream-integrity-result.json',dict(checks=checks,total=len(checks),passed=len(checks),scope='Actual authoritative verifier plus explicit static wiring checks; no full lifecycle pass claimed'))
print(json.dumps(dict(checks=len(checks),passed=len(checks))))
