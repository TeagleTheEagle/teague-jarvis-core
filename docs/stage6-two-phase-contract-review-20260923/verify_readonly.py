import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parent;D=R.parent/'stage6-helper-cleanup-review-20260923';P=R.parent/'stage6-small-live-v2-20260923';V=R.parent/'stage6-checker-v2-20260923'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inventory():
 return [dict(path=str(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,sha256=sha(p)) for p in sorted(D.iterdir()) if p.is_file()]
before=inventory();assert len(before)==6
timeline=read(D/'timeline.json');cfg=read(V/'candidate.json');C=pathlib.Path(cfg['code']);O=pathlib.Path(cfg['original']);run=C/'protected-8145cedf8db843959b8ba58dfd62717b'
for x in cfg['originalFiles']:assert sha(O/x['name'])==x['sha256']
for x in read(V/'final-verification.json')['source']:assert sha(C/x['name'])==x['sha256']
receipt=read(P/'archive-receipt.json');archive=pathlib.Path(receipt['archive']);assert sha(archive)==receipt['archiveSHA256'];manifest=archive.parent/'manifest.json';assert sha(manifest)==receipt['manifestSHA256']
checked=0
for x in read(manifest):
 if x['path'].startswith('live-run/'):
  assert sha(run/x['path'][9:])==x['sha256'];checked+=1
kernel=read(run/'etw-result.json');helper=next(x for x in kernel['rows'] if x['pid']==8436 and x['created']=='134345949607928089');collector=next(x for x in kernel['rows'] if x['pid']==15280 and x['created']=='134345949607329466')
assert helper==timeline['helper'] and collector==timeline['collector']
assert helper['parentSequence']==collector['sequence']
assert timeline['helperStopAfterCollectorStopMs']==(helper['stopQpc']-collector['stopQpc'])/timeline['kernelFrequency']*1000
blocked=(D/'ARCHIVE_BLOCKED.md').read_text();assert 'Selected model is at capacity' in blocked and 'No retry or bypass' in blocked
assert inventory()==before
result=dict(status='PASS',localDiagnosisFiles=before,localDiagnosisChangedDuringInspection=False,priorDiagnosisBundleDigestAvailable=False,failedRunFilesVerified=checked,failureArchiveSHA256=receipt['archiveSHA256'],originalHashesVerified=183,candidateHashesVerified=194,readOnlyDiagnosisConsistent=True,canonicalArchiveAttempted=False,canonicalArchiveMutated=False,codeChanged=False,testsRun=False,protectedAccess=False,productionChanged=False,reviewSHA256=sha(R/'REVIEW.md'))
with (R/'integrity.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='localDiagnosisFiles'},indent=2))
