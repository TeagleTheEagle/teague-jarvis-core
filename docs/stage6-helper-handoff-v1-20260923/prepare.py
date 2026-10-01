"""Read/hash predecessor and copy ONLY manifest-listed TEST artifacts."""
import pathlib,json,hashlib,shutil,sys
R=pathlib.Path(__file__).parent
P=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code')
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\d45028a56e344926a311c04ba01f6a80\code')
F=P/'protected-5d7e179ca49d461db1e4689d12c60267'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def record(p):
 s=p.stat();assert not s.st_file_attributes&0x400
 return dict(path=str(p),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=sha(p))
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2)
resume=sys.argv[1:]==['--resume-empty-copy']
if resume:assert C.is_dir() and not list(C.iterdir()) and (R/'before.json').is_file()
else:assert not C.exists() and not (R/'before.json').exists()
rows=json.loads((P/'small-source-v3.json').read_text());assert len(rows)==229
inputs=[]
for r in rows:
 p=P/r['name'];assert p.is_relative_to(P) and '..' not in p.parts
 v=record(p);assert (v['bytes'],v['sha256'])==(r['bytes'],r['sha256']);inputs.append(v)
inputs.append(record(P/'small-source-v3.json'))
for p in sorted(F.rglob('*')):
 if p.is_file():inputs.append(record(p))
for p in (R.parent/'stage6-corrected-trace-diagnostic-v4-20260923').glob('*.json'):inputs.append(record(p))
for receipt in ['archive-receipt.json','failure-archive-independent-verification.json']:
 p=R.parent/'stage6-corrected-trace-diagnostic-v4-20260923'/receipt
 # Recorded archive locations are retained; enumerate only explicit archive files below.
for p in [P.parent/'preservation-v4'/('FAILURE-EVIDENCE-'+F.name)/('FAILURE-EVIDENCE-'+F.name+'.zip'),pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TRACE DIAGNOSTIC V4 FAILED 20260923\rejected-trace-diagnostic.zip')]:inputs.append(record(p))
baseline=dict(predecessor=str(P),candidate=str(C),inputs=inputs,liveRun=False)
if resume:assert json.loads((R/'before.json').read_text())==baseline
else:put(R/'before.json',baseline);C.mkdir(parents=True)
for r in rows:
 p=C/r['name'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(P/r['name'],p);assert sha(p)==r['sha256']
shutil.copy2(P/'small-source-v3.json',C/'predecessor-source-v3.json')
(C/'baseline-allowlist.json').write_text(json.dumps(dict(syntheticRoots=[str(C/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False),indent=2))
policy=json.loads((C/'preservation-policy-v4.json').read_text());policy.update(candidate=str(C),preservationRoot=str(C.parent/'preservation-v4'))
for n in ('obligations','acquired','observed'):
 policy['artifactPatterns'].append('helper-handoff-'+n+r'-v1\.json(?:\.pending)?')
(C/'preservation-policy-v4.json').write_text(json.dumps(policy,indent=2));(C.parent/'preservation-v4').mkdir()
print(json.dumps(dict(candidate=str(C),predecessorFiles=len(rows),frozenInputs=len(inputs),observersStarted=False)))
