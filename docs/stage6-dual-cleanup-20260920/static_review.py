import pathlib,json,hashlib
r=pathlib.Path(__file__).parent;p=json.loads((r/'plan.json').read_text());code=pathlib.Path(p['live_code']);before=json.loads((r/'source-before.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changes=[];old_ok=[]
for x in before:
 old=pathlib.Path(x['path']);new=code/x['name'];old_ok.append(sha(old)==x['sha256'])
 if sha(new)!=x['sha256']:changes.append(dict(name=x['name'],before=x['sha256'],after=sha(new)))
assert all(old_ok)
syntax=[]
for q in r.glob('*.py'):compile(q.read_bytes(),str(q),'exec');syntax.append(str(q))
result=dict(status='STATIC_CHECKS_PASS',historicalSourceHashesUnchanged=len(old_ok),candidateChanges=changes,newCandidateFiles=[q.name for q in code.iterdir() if q.is_file() and q.name not in {x['name'] for x in before}],pythonSyntax=syntax,cleanupCheckerImplemented=False,liveValidationStarted=False)
with (r/'static-review.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
