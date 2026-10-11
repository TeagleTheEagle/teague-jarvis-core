import ast,difflib,hashlib,json,os,uuid,sys
from pathlib import Path
R=Path(__file__).parent;pre=json.loads((R/'candidate.json').read_text());C=Path(pre['code']);K=C/'medium-checker'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
for x in pre['copies']:assert sha(x['source'])==x['sha256'],x['source']
assert load(R/'preparation-tests.json')['passed']==43
assert any(load(p)['passed']==21 for p in R.glob('native-results-*.json'))
assert any(load(p)['passed']==40 for p in R.glob('telemetry-checks-*.json'))
assert any(load(p)['passed']==21 for p in R.glob('wrapper-checks-*.json'))
files=[p for p in C.iterdir() if p.is_file()]+[p for p in K.iterdir() if p.is_file()]
for p in files:
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf8'))
rows=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)]
save(C/'medium-source-freeze.json',dict(schema='stage6-medium-source-freeze-v1',files=rows))
save(R/'candidate-frozen.json',dict(files=rows,freezeSHA256=sha(C/'medium-source-freeze.json')))
changes=[]
for row in pre['copies']:
 p=Path(row['path'])
 if sha(p)!=row['sha256']:
  changes.append(dict(**row,afterSHA256=sha(p)))
  if p.suffix in ('.py','.hpp','.cpp','.json','.ps1'):
   diff=''.join(difflib.unified_diff(Path(row['source']).read_text(encoding='utf8').splitlines(True),p.read_text(encoding='utf8').splitlines(True),fromfile=row['source'],tofile=str(p)))
   with (R/('final-'+p.name+'.diff')).open('x',encoding='utf8') as f:f.write(diff)
save(R/'changes.json',dict(changed=changes,new=[x for x in rows if x['path'] not in {r['path'] for r in pre['copies']}],originalsVerified=len(pre['copies'])))
sys.path[:0]=[str(K),str(C)];import fresh_binding as fb;import checker_telemetry as ct
assert fb.bound(C)[0]==Path(load(R/'run.json')['path'])
F=Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';F.mkdir(parents=True);fr=F/('identity-'+uuid.uuid4().hex);fr.mkdir()
d=load(C/'medium-declaration.json');d.update(codeRoot=str(F),evidenceRoot=str(fr),runId=fr.name)
save(F/'medium-declaration.json',d);save(F/'medium-intent.json',dict(evidenceRoot=str(fr),declarationSHA256=sha(F/'medium-declaration.json')));save(F/'medium-source-freeze.json',dict(files=[dict(path=str(F/'medium-declaration.json'),sha256=sha(F/'medium-declaration.json'))]))
(fr/'synthetic.txt').write_bytes(b'SYNTHETIC INTAKE ONLY');fb.seal_intake(F);assert fb.verify_intake(F)[0]==fr
tests=[dict(case='fresh intake verifies',status='PASS')]
for name,fn in [('new run unsealed',ct.evaluate),('changed evidence',lambda:(fr/'synthetic.txt').write_bytes(b'changed')),('extra evidence',lambda:(fr/'extra.txt').write_bytes(b'extra')),('unknown manifest version',lambda:None)]:
 if name=='new run unsealed':
  try:fn()
  except (ValueError,FileNotFoundError):tests.append(dict(case=name,status='REJECT'));continue
  raise AssertionError(name)
 if name=='changed evidence':fn()
 elif name=='extra evidence':(fr/'synthetic.txt').write_bytes(b'SYNTHETIC INTAKE ONLY');fn()
 else:
  (fr/'extra.txt').rename(fr/'extra-renamed.txt');x=load(fr/'intake-manifest.json');x['schema']='unknown';(fr/'intake-manifest.json').write_text(json.dumps(x))
 try:fb.verify_intake(F)
 except (ValueError,OSError):tests.append(dict(case=name,status='REJECT'))
 else:raise AssertionError(name)
save(R/'fresh-binding-tests.json',dict(status='PASS',passed=len(tests),tests=tests,fixture=str(F)))
host=uuid.uuid4().hex;(R/'final'/host).mkdir()
save(R/'ready.json',dict(status='FOCUSED_VALIDATION_PASS',native=21,telemetry=40,composition=21,legacy=114,declaration=43,intake=5,total=244,sourceFiles=len(rows),hostRun=host,run=load(R/'run.json'),heartbeatWarnings='NOT CONFIGURED',mediumStarted=False))
print(json.dumps(load(R/'ready.json')))
