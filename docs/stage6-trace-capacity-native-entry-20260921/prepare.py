import pathlib,json,hashlib,uuid,shutil,collections,math
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=R.parent/'stage6-narrow-startup-integration-20260921';old=read(P/'plan.json');C=pathlib.Path(old['code'])
for x in old['sourceChecks']:assert sha(pathlib.Path(x['path']))==x['sha256']
rows=read(P/'candidate-hashes.json')
for x in rows:assert sha(C/x['name'])==x['sha256']
receipt=read(P/'archive-verification.json');A=pathlib.Path(receipt['path']);assert sha(A/'evidence.zip')==receipt['zipSHA256'];assert sha(A/'archive-manifest.json')==receipt['manifestSHA256']
normal=C/'protected-cda0e6c7d5774746afaef2d4e93602f8';events=read(normal/'startup-events.json')['events'];freq=read(normal/'etw-ready.json')['frequency'];lo=min(x['qpc'] for x in events);hi=max(x['qpc'] for x in events);seconds=(hi-lo)/freq
bins=collections.Counter(int((x['qpc']-lo)/freq) for x in events);peak=max(bins.values());encoded=[len(json.dumps(x,separators=(',',':')).encode())+1 for x in events]
cal=read(pathlib.Path('D:/JARVIS-STAGE6-LIVE/1c1f5d0c390b42cc9ba9f4f6221dabc6/code/calibration.json'))
model=dict(seconds=seconds,records=len(events),recordsPerSecond=len(events)/seconds,peakOneSecond=peak,bytes=sum(encoded),meanRecordBytes=sum(encoded)/len(encoded),maxRecordBytes=max(encoded),byPid=dict(collections.Counter(x['pid'] for x in events)),byProvider=dict(collections.Counter(x['provider'] for x in events)),exactDuplicates=len(events)-len({json.dumps(x,sort_keys=True) for x in events}),expectedDurationSeconds=788,monitorEnvelopeSeconds=1200,priorMeasuredThroughput=cal['bytesPerSecond'],expectedTwoPassSeconds=cal['conservativeTwoPassSeconds'],expectedRecords=math.ceil(len(events)/seconds*788),peakEnvelopeRecords=peak*1200,safetyFactor=2,recordBudget=peak*1200*2,storageBudgetBytes=128*1024**3,queueBudgetBytes=64*1024**2,segmentBytes=8*1024**2,maximumRecordBytes=8192,limitation='Empirical planning envelope, not a universal bound on Windows event production; exceeding any bound fails closed.')
model['conservativeProjectedBytes']=model['recordBudget']*max(encoded)
model['expectedBytes']=math.ceil(model['expectedRecords']*model['meanRecordBytes'])
assert model['conservativeProjectedBytes']<model['storageBudgetBytes']
code=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code';code.mkdir(parents=True)
for x in rows:shutil.copy2(C/x['name'],code/x['name'])
source=code/'small-sacrificial';source.mkdir()
for i in range(12):(source/f'artifact-{i:02d}.bin').write_bytes(bytes([i])*65536)
(code/'baseline-allowlist.json').write_text(json.dumps(dict(approvedProtectedRoots=[],realProtectedAccess=False,syntheticRoots=[str(source)]),indent=2))
plan=dict(code=str(code),source=str(source),prior=str(C),preChangeHashes=rows,model=model,files=[dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in sorted(source.iterdir())])
(R/'plan.json').write_text(json.dumps(plan,indent=2));(R/'capacity-model.json').write_text(json.dumps(model,indent=2))
print(json.dumps(dict(code=str(code),capacity=model),indent=2))
