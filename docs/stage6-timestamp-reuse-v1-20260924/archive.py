from prepare import *
import ast,zipfile
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TIMESTAMP REUSE V1 20260924')
assert not A.exists()
for x in load(R/'before.json')['inputs']:assert rec(x['path'])==x
for x in load(R/'final-candidate-manifest.json')['files']:assert rec(x['path'])==x
census=load(R/'final-census.json');assert census['processCount']==0 and census['traceCount']==0
syntax=[]
for p in sorted(R.glob('*.py')):ast.parse(p.read_text());syntax.append(dict(path=str(p),sha256=sha(p),result='PASS'))
write(R/'final-syntax.json',syntax)
write(R/'final-reference-binding.json',dict(reference=rec(C.parent/'reference'/'trace_telemetry.hpp'),successor=rec(C/'trace_telemetry.hpp'),referenceOnlyDifference='conditional extra diagnostic completion QPC; publish that diagnostic value',historical=False))
write(R/'preservation-policy.json',dict(schema='j6.timestamp-reuse.preservation.v1',report=str(R),candidate=str(C),reference=str(C.parent/'reference'),historicalPolicy='before.json all entries immutable',scope='offline TEST only',protectedRoots=[],productionAccess=False,frozenChecker='unchanged',include='all regular report/candidate/reference artifacts; assembly alternate streams have hash-verified ordinary copies',secrets='none'))
write(R/'final-status.json',dict(status='TIMESTAMP_REUSE_IMPLEMENTED_AND_TESTED',successorAssertions=602,referenceAssertions=600,sourceDerivedCasesEach=58,staticSyntaxPreservationChecks=1197,liveRun=False,performanceQualified=False,benchmarkRun=False,processes=0,traces=0,protectedAccess=False,productionChanged=False,priorFilesUnchanged=1120,archivePending=True))
members=[]
for label,root in [('report',R),('successor',C),('reference',C.parent/'reference')]:
 for p in sorted(root.iterdir()):
  if p.is_file():members.append(dict(member=label+'/'+p.name,**rec(p)))
write(R/'archive-manifest.json',members)
A.mkdir(parents=True)
zpath=A/'evidence.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for x in members:z.write(x['path'],x['member'])
 z.write(R/'archive-manifest.json','archive-manifest.json')
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None and len(z.namelist())==len(members)+1
 for x in members:
  with z.open(x['member']) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  assert h==x['sha256'] and z.getinfo(x['member']).file_size==x['bytes']
 assert z.read('archive-manifest.json')==(R/'archive-manifest.json').read_bytes()
receipt=dict(status='PASS',archive=str(zpath),sha256=sha(zpath),verifiedMembers=len(members)+1,manifestSHA256=sha(R/'archive-manifest.json'),productionChanged=False,protectedAccess=False)
write(R/'archive-receipt.json',receipt);write(A/'archive-receipt.json',receipt)
shutil.copy2(R/'archive-manifest.json',A/'archive-manifest.json')
assert sha(A/'archive-manifest.json')==receipt['manifestSHA256']
print(json.dumps(receipt))
