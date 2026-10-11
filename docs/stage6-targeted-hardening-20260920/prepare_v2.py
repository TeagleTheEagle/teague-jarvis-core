import pathlib,json,uuid,hashlib,shutil
R=pathlib.Path(__file__).parent;old=json.loads((R/'candidate.json').read_text());O=pathlib.Path(old['code'])
for x in old['hashes']:assert hashlib.sha256((O/x['name']).read_bytes()).hexdigest()==x['sha256']
D=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';D.mkdir(parents=True)
for p in O.iterdir():
 if p.is_file() and p.name!='hardening-hashes.json':shutil.copyfile(p,D/p.name)
p=D/'timed_monitor.ps1';before=p.read_text();after=before.replace('function Measure(', 'function Invoke-J6TimedStage(').replace('Measure ', 'Invoke-J6TimedStage ');assert after!=before;p.write_text(after)
manifest=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(D.iterdir()) if p.is_file()]
(D/'hardening-hashes.json').write_text(json.dumps(manifest,indent=2))
with (R/'candidate-v2.json').open('x') as f:json.dump(dict(code=str(D),previous=str(O),correction='PowerShell measure alias shadows Measure function; use unique Invoke-J6TimedStage name.',before=hashlib.sha256(before.encode()).hexdigest(),after=hashlib.sha256(p.read_bytes()).hexdigest(),hashes=manifest),f,indent=2)
print(D)
