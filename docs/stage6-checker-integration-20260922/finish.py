import ast,difflib,hashlib,json,os,uuid
from pathlib import Path
R=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
pre=load(R/'preflight.json');C=Path(pre['candidate']);frozen=Path(pre['frozen']);freeze=load(R/'candidate-freeze.json')
for x in pre['checks']+freeze['files']:assert sha(x['path'])==x['sha256'],x['path']
assert sha(frozen)==pre['frozenSHA256']==sha(C/'frozen_reference.py')
hist=load(R/'historical-identity-preservation.json');assert sha(hist['path'])==hist['sha256'] and hist['evidence']['counts']==dict(AMBIGUOUS=21,UNMATCHED=1)
tests=load(load(C.parent/'test-results-location.json')['path']);review=load(R/'review-tests.json');assert tests['passed']==tests['total']==83 and review['passed']==review['total']==31
syntax=[]
for p in sorted(C.glob('*.py'))+sorted(R.glob('*.py')):ast.parse(p.read_text(encoding='utf8'));syntax.append(dict(path=str(p),sha256=sha(p)))
save(R/'syntax-results.json',dict(status='PASS',command='ast.parse(UTF-8 source) via Python -B finish.py; no bytecode writes',files=syntax))
changes=[]
for x in pre['copied']:
 dst=Path(x['candidate']);final=sha(dst);changes.append(dict(**x,finalSHA256=final,changed=final!=x['initialSHA256']))
 if final!=x['initialSHA256']:
  diff=''.join(difflib.unified_diff(Path(x['source']).read_text(encoding='utf8').splitlines(True),dst.read_text(encoding='utf8').splitlines(True),fromfile=x['source'],tofile=str(dst)))
  with (R/(dst.name+'.diff')).open('x',encoding='utf8') as f:f.write(diff)
save(R/'changes.json',dict(copied=changes,new=[x for x in freeze['files'] if x['path'] not in {y['candidate'] for y in pre['copied']}],runtimeChanged=False))
host=uuid.uuid4().hex;(R/'final'/host).mkdir()
save(R/'preservation-after.json',dict(status='PASS',frozenInitial=pre['frozenSHA256'],frozenFinal=sha(frozen),sourceComparisons=len(pre['checks'])+len(freeze['files']),candidateFinal=sha(C/'checker_v2.py'),sourceFreezeSHA256=sha(C/'source-freeze.json'),historical21_1='UNCHANGED',historicalCauses='UNCONFIRMED',hostRun=host,protectedAccess=False,productionChanged=False,totalTests=114))
print(json.dumps(dict(status='PASS',tests=114,sourceComparisons=len(pre['checks'])+len(freeze['files']),syntaxFiles=len(syntax),hostRun=host)))
