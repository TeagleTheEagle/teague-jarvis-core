import pathlib,json,hashlib,uuid,shutil
R=pathlib.Path(__file__).parent;p=json.loads((R/'frozen-before.json').read_text());h=json.loads((R/'host-before.json').read_text())
assert not h['matchingLive'] and not h['scopedProcesses'] and not h['traceSessions'] and h['traceQueryExit']==0
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
assert shutil.disk_usage('D:/').free>140*2**30
C.mkdir(parents=True,exist_ok=False)
for x in p['candidateHashes']:
 a=pathlib.Path(x['path']);assert hashlib.sha256(a.read_bytes()).hexdigest()==x['expected'];shutil.copyfile(a,C/x['name'])
shutil.copyfile(pathlib.Path(p['code'])/'integration-source.json',C/'integration-source.json')
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(C),old=p['code'],protectedAccess=False),f,indent=2)
print(C)
