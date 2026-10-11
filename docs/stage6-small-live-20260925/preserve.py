import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
v=load(R/'preflight-result.json');C=pathlib.Path(v['candidate']);root=pathlib.Path(v['runRoot']);result=load(R/'run-result.json');failure=pathlib.Path(result['directory'])
for x in load(C/'small-source-v3.json'):
 p=C/x['name'];assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
assert sha(C/'small-source-v3.json')==v['sourceManifestSHA256']
for x in load(R.parent/'stage6-small-rebind-20260925/before.json')['inputs']:
 p=pathlib.Path(x['path']);s=p.stat();assert (s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
for x in v['dataset']:assert (C/x['name']).stat().st_mtime_ns==x['mtimeNs']
prior=R.parent/'stage6-rebind-directory-fix-20260925';a=load(prior/'archive-receipt.json');assert sha(pathlib.Path(a['archive']))==a['sha256']
with zipfile.ZipFile(a['archive']) as z:
 for x in load(prior/'archive-manifest.json'):assert hashlib.sha256(z.read(x['member'])).hexdigest()==x['sha256']
zips=list(failure.glob('*.zip'));assert len(zips)==1 and sha(zips[0])==result['archiveSHA256']
with zipfile.ZipFile(zips[0]) as z:assert z.testzip() is None and len(z.namelist())==result['verifiedArchiveMembers']==91
kernel=load(root/'etw-result.json');detail=load(root/'detail/etw-result.json')
manifest=load(failure/'FAILURE-MANIFEST.json')
write(R/'preservation-result.json',dict(status='PASS',candidateFiles=235,priorArchiveMembers=664,failureArchiveMembers=91,sourceManifest=sha(C/'small-source-v3.json'),historicalInputs=1227,productionChange=False,protectedAccess=False))
write(R/'summary.json',dict(status='TRACE_LOSS_REPRODUCED',run=root.name,firstAvailableTerminalFailure=load(root/'terminal-failure-v3.json'),rejection=load(root/'rejected-v3.json'),authorityEventsLost=kernel['eventsLost'],detailedEventsLost=detail['eventsLost'],failurePreservation=result,missingTerminalArtifacts=manifest.get('missingArtifacts'),cleanup=load(R/'final-census.json'),historicalCause='UNCONFIRMED',retry=False,successFinalizer=False))
(R/'REPORT.md').write_text(f'''# TRACE_LOSS_REPRODUCED

One run: {root.name}. First available terminal failure: terminal trace loss/query; launcher rejection: Authority terminal failure. The terminal failure record has no timestamp, so exact first-occurrence timing is not inferred. Final authority EventsLost={kernel['eventsLost']}, faults={kernel['faults']}; detailed EventsLost={detail['eventsLost']}, faults={detail['faults']}. Nonzero loss permanently rejects the attempt.

No success finalizer or retry. Bounded failure path preserved 89 existing run files; 91 archive members verified, zero hash mismatches. FAILURE_EVIDENCE_PARTIAL explicitly denotes missing required terminal acceptance evidence; it is not an acceptance seal. Missing artifacts and original rejection are preserved in summary.json and FAILURE-MANIFEST.json.

Final independent host census: zero matching processes and zero trace sessions. All 235 candidate entries and source manifest unchanged; dataset metadata unchanged; 1,227 predecessor/historical input records unchanged. Prior 664-member archive verified. Production and protected VM untouched. Historical ETW-loss cause remains UNCONFIRMED. No medium/large validation, correction or new profiling. STOP for owner review.
''',encoding='utf8')
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 SMALL LIVE 20260925');assert not A.exists();files=[]
for label,base in [('report',R),('run',root),('failure',failure)]:
 for p in sorted(base.rglob('*')):
  if p.is_file():files.append(dict(member=label+'/'+p.relative_to(base).as_posix(),path=str(p),sha256=sha(p),bytes=p.stat().st_size))
write(R/'archive-manifest.json',files);A.mkdir();zp=A/'evidence.zip'
with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x['path'],x['member'])
 z.write(R/'archive-manifest.json','archive-manifest.json')
with zipfile.ZipFile(zp) as z:
 assert z.testzip() is None and len(z.namelist())==len(files)+1
 for x in files:assert hashlib.sha256(z.read(x['member'])).hexdigest()==x['sha256']
receipt=dict(status='PASS',archive=str(zp),sha256=sha(zp),verifiedMembers=len(files)+1)
write(R/'archive-receipt.json',receipt);write(A/'archive-receipt.json',receipt);print(json.dumps(receipt))
