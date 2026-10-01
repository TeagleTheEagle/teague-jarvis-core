import ast,difflib,hashlib,json,os,shutil,sys,uuid
from pathlib import Path
R=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
pre=load(R/'preflight.json');C=Path(pre['code']);K=Path(pre['checker']);root=Path(pre['root'])
assert load(R/'preparation-tests.json')['passed']==43
for x in pre['checks']:assert sha(x['path'])==x['sha256'],x['path']
files=[p for p in C.iterdir() if p.is_file()]+[p for p in K.iterdir() if p.is_file()]
for p in files:
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf8'))
rows=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)]
save(C/'medium-source-freeze.json',dict(schema='stage6-medium-source-freeze-v1',files=rows))
save(R/'candidate-frozen.json',dict(files=rows,freezeSHA256=sha(C/'medium-source-freeze.json')))
changes=[]
for old in pre['copies']:
 p=Path(old['path'])
 if sha(p)!=old['sha256']:
  changes.append(dict(**old,finalSHA256=sha(p)))
  if p.suffix in ('.py','.ps1','.json'):
   diff=''.join(difflib.unified_diff(Path(old['source']).read_text(encoding='utf8').splitlines(True),p.read_text(encoding='utf8').splitlines(True),fromfile=old['source'],tofile=str(p)))
   (R/(p.parent.name+'-'+p.name+'.diff')).write_text(diff,encoding='utf8')
save(R/'changes.json',dict(changedCopies=changes,newFiles=[x for x in rows if x['path'] not in {y['path'] for y in pre['copies']}],nativeBinariesUnchanged=all(sha(C/p.name)==sha(p) for p in Path(pre['originalRuntime']).glob('*.exe')) and sha(C/'J6OwnedEntry.dll')==sha(Path(pre['originalRuntime'])/'J6OwnedEntry.dll')))
sys.path[:0]=[str(K),str(C)];import fresh_binding as fb;import checker_medium as checker
assert fb.bound(C)[0]==root
try:checker.evaluate()
except FileNotFoundError:unsealed='REJECT'
else:raise AssertionError('UNSEALED_RUN_ACCEPTED')
# Independent miniature intake-only fixture. No real run artifacts are fabricated.
F=Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';F.mkdir(parents=True);fr=F/('identity-'+uuid.uuid4().hex);fr.mkdir()
d=load(C/'medium-declaration.json');d.update(codeRoot=str(F),evidenceRoot=str(fr),runId=fr.name)
save(F/'medium-declaration.json',d);save(F/'medium-intent.json',dict(evidenceRoot=str(fr),declarationSHA256=sha(F/'medium-declaration.json')))
save(F/'medium-source-freeze.json',dict(files=[dict(path=str(F/'medium-declaration.json'),sha256=sha(F/'medium-declaration.json'))]))
(fr/'synthetic-evidence.txt').write_bytes(b'SACRIFICIAL INTAKE FIXTURE; NOT LIVE ACCEPTANCE\n')
fb.seal_intake(F);assert fb.verify_intake(F)[0]==fr
tests=[dict(case='unsealed real run rejected',result=unsealed),dict(case='fresh miniature intake hash verifies',result='PASS')]
for case,action in [('evidence tamper',lambda:(fr/'synthetic-evidence.txt').write_bytes(b'changed')),('extra file',lambda:(fr/'extra.txt').write_bytes(b'extra')),('manifest unknown version',lambda:None)]:
 if case=='evidence tamper':action()
 elif case=='extra file':(fr/'synthetic-evidence.txt').write_bytes(b'SACRIFICIAL INTAKE FIXTURE; NOT LIVE ACCEPTANCE\n');action()
 else:
  (fr/'extra.txt').unlink();value=load(fr/'intake-manifest.json');value['schema']='unknown';(fr/'intake-manifest.json').write_text(json.dumps(value),encoding='utf8')
 try:fb.verify_intake(F)
 except (ValueError,OSError) as e:tests.append(dict(case=case,result='REJECT',reason=str(e)))
 else:raise AssertionError(case)
save(R/'fresh-binding-tests.json',dict(status='PASS',tests=tests,total=5,passed=5,fixture=str(F),fixtureIsNotAcceptance=True))
host=uuid.uuid4().hex;(R/'final'/host).mkdir()
save(R/'ready.json',dict(status='PREPARATION_VALIDATED',regressions=114,mediumChecks=43,intakeChecks=5,sourceFiles=len(rows),freezeSHA256=sha(C/'medium-source-freeze.json'),hostRun=host,freeD=shutil.disk_usage('D:/').free,mediumAttemptStarted=False))
print(json.dumps(load(R/'ready.json')))
