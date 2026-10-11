"""Read-only preflight of immutable evidence; writes only new review records."""
import pathlib,json,hashlib,zipfile,collections
R=pathlib.Path(__file__).parent
OLD=R.parent/'stage6-kernel-child-trace-20260920'
CODE=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\991e246fb08b45a3904e4cadfa8f4e99\code')
RUN='etw-stress-0ecaea118aec42c9b0afcaf56c8686d5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,data):
 with (R/name).open('x',encoding='utf-8') as f:json.dump(data,f,sort_keys=True,indent=2)
receipt=json.loads((OLD/'archive-verification.json').read_text());manifest=json.loads((OLD/'archive-manifest.json').read_text())
assert sha(OLD/'evidence.zip')==receipt['zipSHA256']
assert sha(OLD/'archive-manifest.json')==receipt['manifestSHA256']
inventory=[]
with zipfile.ZipFile(OLD/'evidence.zip') as z:
 assert len(z.namelist())==receipt['members']==1436
 assert set(z.namelist())=={x['name'] for x in manifest['files']}|{'archive-manifest.json'}
 assert z.read('archive-manifest.json')==(OLD/'archive-manifest.json').read_bytes()
 for x in manifest['files']:
  data=z.read(x['name']);assert len(data)==x['size'] and hashlib.sha256(data).hexdigest()==x['sha256']
  if x['name'].startswith('live/'+RUN+'/'):inventory.append(x)
 prefix='live/'+RUN+'/'
 kernel=json.loads(z.read(prefix+'etw-result.json'));prior=json.loads(z.read(prefix+'kernel-reconciliation.json'))
 stress=json.loads(z.read(prefix+'stress-result.json'));tree=json.loads(z.read(prefix+'tree-handles.json'))
 assert len(kernel['rows'])==prior['observed']==97
 assert prior['retained']==94 and prior['justifiedNonretained']==3 and prior['unknown']==0
 assert z.read('live/stress.py')==(CODE/'stress.py').read_bytes()
 assert z.read('live/stress.ps1')==(CODE/'stress.ps1').read_bytes()
 independent=[x['name'] for x in inventory if pathlib.PurePosixPath(x['name']).name in ('events.jsonl','tap.json','queue-state.json','queue-entries.json')]
 assert not independent
put('prior-archive-verification.json',dict(members=1436,sha256=receipt['zipSHA256'],manifestSHA256=receipt['manifestSHA256'],verified=True,unchanged=True))
put('97-run-file-inventory.json',inventory)
sources=[]
for x in json.loads((OLD/'final-source.json').read_text()):
 p=pathlib.Path(x['path']);sources.append(dict(path=str(p),expected=x['sha256'],sha256=sha(p),unchanged=sha(p)==x['sha256']))
assert all(x['unchanged'] for x in sources)
put('source-prechange-hashes.json',sources)
per_identity=[dict(pid=x['pid'],created=x['created'],kernelSequence=x['sequence'],parentPid=x['parentPid'],image=x['image'],priorKernelEvidence=x['retentionReason'],kernelIdentityStatus=x['kernelIdentityCoverage'],newCleanupEvidenceClass='INSUFFICIENT_EVIDENCE',reason='Independent application-level persisted START/STOP evidence was not collected by this stress harness; kernel events cannot substitute under C5.') for x in prior['rows']]
put('97-identity-preflight.json',dict(status='BLOCKED',recordedIdentities=97,priorRetained=94,priorPostExitKernel=3,priorUnexplainedKernelGaps=0,requiredIndependentLifecycleEvidenceMissing=97,fullCleanupAccepted=0,independentStreamsPresent=independent,identityResults=per_identity,freshStressAuthorizedToProceed=False,historicalEvidenceReclassified=False))
put('disposition.json',dict(status='BLOCKED',blocker='C5 independent START/STOP evidence absent for immutable C8 replay; C8 mandates STOP if any case cannot be justified.',checkerChanged=False,productionChanged=False,protectedAccess=False,freshStress='NOT RUN',focusedTests='NOT RUN',regressions='NOT RUN',protectedBaselineEligible=False))
print(json.dumps(dict(status='BLOCKED',verifiedArchiveMembers=1436,sourceHashesUnchanged=len(sources),priorKernelCounts=[97,94,3,0],independentApplicationEventStreams=independent,cleanupEligibleUnderC5=0)))
