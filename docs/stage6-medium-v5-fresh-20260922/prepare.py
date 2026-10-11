import ast,copy,difflib,hashlib,json,os,shutil,sys,uuid,zipfile
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-nested-writer-20260922';T=R.parent/'stage6-telemetry-candidate-20260922'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
old=Path(load(P/'candidate.json')['code']);frozen=load(P/'candidate-freeze.json')['files'];archives=[]
for x in frozen:assert sha(x['path'])==x['sha256'],x['path']
assert load(P/'final-disposition.json')['status']=='CHECKER_CORRECTION_VALIDATED'
for source in (P,T):
 receipt=load(source/'archive-verification.json');a=Path(receipt['archive']);m=a.parent/'manifest.json'
 assert sha(a)==receipt['archiveSHA256'] and sha(m)==receipt['manifestSHA256']
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==len(set(z.namelist()))==receipt['membersVerified'] and z.read('manifest.json')==m.read_bytes()
  for x in load(m)['files']:
   b=z.read(x['name']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 archives.append(receipt)
assert shutil.disk_usage('D:/').free>=2*1024**3
C=Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';C.mkdir(parents=True);copies=[]
for x in frozen:
 p=Path(x['path']);dst=C/p.relative_to(old);assert not p.is_symlink() and not p.is_junction() and p.name!='.env';dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(p.read_bytes())
 copies.append(dict(source=str(p),path=str(dst),sha256=sha(dst)))
run='identity-'+uuid.uuid4().hex;root=C/run;root.mkdir();(root/'temp').mkdir();(root/'analysis').mkdir()
d=load(C/'medium-declaration.json');oldRuntime=Path(d['codeRoot']);d.update(runId=run,codeRoot=str(C),evidenceRoot=str(root));(C/'medium-declaration.json').write_text(json.dumps(d,indent=2),encoding='utf8')
(C/'medium-intent.json').write_text(json.dumps(dict(evidenceRoot=str(root),declarationSHA256=sha(C/'medium-declaration.json')),indent=2),encoding='utf8')
p=C/'qualified_launch.ps1';s=p.read_text(encoding='utf8');a=str(oldRuntime/'J6OwnedEntry.dll').replace('\\','\\\\');b=str(C/'J6OwnedEntry.dll').replace('\\','\\\\');assert s.count(a)==1;p.write_text(s.replace(a,b),encoding='utf8')
K=C/'medium-checker';files=[p for p in C.iterdir() if p.is_file()]+[p for p in K.iterdir() if p.is_file()]
for p in files:
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf8'))
rows=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)]
save(C/'medium-source-freeze.json',dict(schema='stage6-medium-source-freeze-v1',files=rows));save(R/'candidate-frozen.json',dict(files=rows,freezeSHA256=sha(C/'medium-source-freeze.json')))
changes=[]
for x in copies:
 p=Path(x['path'])
 if sha(p)!=x['sha256']:
  changes.append(dict(**x,afterSHA256=sha(p)))
  with (R/(p.name+'.diff')).open('x',encoding='utf8') as f:f.write(''.join(difflib.unified_diff(Path(x['source']).read_text(encoding='utf8').splitlines(True),p.read_text(encoding='utf8').splitlines(True),fromfile=x['source'],tofile=str(p))))
assert {Path(x['path']).name for x in changes}=={'medium-declaration.json','medium-intent.json','qualified_launch.ps1'}
sys.path[:0]=[str(K),str(C)];import fresh_binding as fb;import checker_telemetry as ct
assert ct.VERSION=='stage6-checker-telemetry-v5' and fb.bound(C)[0]==root
tests=[]
def test(name,fn,reject=False):
 try:fn();actual='PASS'
 except (ValueError,KeyError,TypeError,OSError):actual='REJECT'
 expected='REJECT' if reject else 'PASS';tests.append(dict(case=name,expected=expected,actual=actual));assert actual==expected,name
test('exact fresh binding',lambda:fb.bound(C))
test('unsealed new evidence rejected',ct.evaluate,True)
for key,value in [('directProbes',16),('heartbeatSeconds',11),('hardDeadlineSeconds',14),('observerSeconds',16),('queueItems',65537),('pendingSegments',3),('evidenceRoot',str(old)),('runId','identity-'+'0'*32)]:
 bad=copy.deepcopy(d);bad[key]=value;test('reject '+key,lambda bad=bad:fb.validate_declaration(bad,C,root),True)
fixture=load(old/'offline-fixtures/actual-analyzer-fixture.json')
test('corrected checker preserves actual analyzer regression',lambda:ct.rules(fixture['bundle'],fixture['measurements'],fixture['declaration']))
for x in frozen:assert sha(x['path'])==x['sha256']
save(R/'preparation-tests.json',dict(status='PASS',passed=len(tests),tests=tests,fixtureSHA256=sha(old/'offline-fixtures/actual-analyzer-fixture.json')))
host=uuid.uuid4().hex;(R/'final'/host).mkdir(parents=True)
with (R/'host_preflight.ps1').open('xb') as f:f.write((P/'host_preflight.ps1').read_bytes())
save(R/'preflight.json',dict(code=str(C),checker=str(K),root=str(root),old=str(old),copies=copies,changes=changes,archives=archives,hostRun=host,freeD=shutil.disk_usage('D:/').free,sourceFiles=len(rows)))
save(R/'run.json',dict(run=run,path=str(root)))
print(json.dumps(dict(status='PREPARATION_PASS_HOST_PENDING',code=str(C),run=run,sourceFiles=len(rows),checks=len(tests),archiveMembers=[x['membersVerified'] for x in archives],hostRun=host)))
