import pathlib,json,hashlib,shutil,uuid
R=pathlib.Path(__file__).parent;old=json.loads((R/'candidate-v4.json').read_text());O=pathlib.Path(old['code'])
generated={'extended-delay-result.json','probe-handle-regression.json'};changes=[]
for x in old['hashes']:
 h=hashlib.sha256((O/x['name']).read_bytes()).hexdigest()
 if h!=x['sha256']:
  assert x['name'] in generated
  changes.append(dict(name=x['name'],before=x['sha256'],after=h,classification='Generated regression output; source unchanged'))
assert len(changes)==2
(R/'v4-preflight-rejection.json').write_text(json.dumps(dict(reason='Source manifest included mutable regression outputs',changes=changes,observersStarted=False,protectedAccess=False),indent=2))
D=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';D.mkdir(parents=True)
for p in O.iterdir():
 if p.is_file() and p.name!='hardening-hashes.json':shutil.copyfile(p,D/p.name)
manifest=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(D.iterdir()) if p.is_file()]
(D/'hardening-hashes.json').write_text(json.dumps([x for x in manifest if x['name'] not in generated],indent=2))
with (R/'candidate-v5.json').open('x') as f:json.dump(dict(code=str(D),previous=str(O),hashes=manifest,generatedRegressionOutputs=sorted(generated),correction='Manifest distinguishes generated regression outputs from source; no executable/script change from v4.'),f,indent=2)
print(D)
