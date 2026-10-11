"""Read-only input verification. Does not launch, build, or benchmark candidates."""
import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).parent
P=R.parent/'stage6-timestamp-reuse-v1-20260924'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(x):
 p=pathlib.Path(x['path']);s=p.stat()
 assert sha(p)==x['sha256'],str(p)
 assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtimeNs'],str(p)
before=load(P/'before.json')['inputs']
candidate=load(P/'final-candidate-manifest.json')['files']
for x in before+candidate:verify(x)
receipt=load(P/'archive-receipt.json');archive=pathlib.Path(receipt['archive'])
assert sha(archive)==receipt['sha256']
manifest=load(P/'archive-manifest.json')
assert sha(P/'archive-manifest.json')==receipt['manifestSHA256']
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==receipt['verifiedMembers'] and z.testzip() is None
 for x in manifest:
  verify(x)
  with z.open(x['member']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
 assert z.read('archive-manifest.json')==(P/'archive-manifest.json').read_bytes()
generated=load(P/'generated-code-review.json')
assert generated['eligibleEnabledReference']==3 and generated['eligibleEnabledReuse']==2
root=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\timestamp-reuse-v1-20260924')
source=(root/'code'/'loss_measurement_fixture_v3.cpp').read_text()
assert 'int main(){try{' in source and 'GetThreadTimes' not in source
assert '#include "trace_telemetry.hpp"' in source
body=(root/'code'/'callback-bodies.inc').read_text()
assert 'namespace old_authority' in body and 'j6t::CallbackScope timing' in body
record=dict(status='BLOCKED',benchmarkExecutions=0,benchmarkAttemptStarted=False,sourceBuilds=0,
 blocker='Reviewed three-arm qualification harness/workload/binary binding is absent; current semantic-test binary has no benchmark mode and uses successor CallbackScope even for its old callback comparison.',
 procedure=str(P/'FINAL-OVERHEAD-SCREEN-OWNER-REVIEW.md'),
 procedureRequirement='Step 1 requires separately reviewed same-input fixture and unchanged predecessor baseline before timing. Final paragraph explicitly says present binary is not the executable protocol.',
 predecessorFilesVerified=len(before),candidateFilesVerified=len(candidate),implementationArchiveMembersVerified=receipt['verifiedMembers'],
 implementationArchiveSHA256=receipt['sha256'],generatedCodeBindingVerified=True,
 benchmarkHarnessIdentity='NOT AVAILABLE',callbackBenchmarkWorkloadIdentity='NOT AVAILABLE',
 historicalCause='UNCONFIRMED',UAC=False,liveETW=False,protectedAccess=False,productionChanged=False)
with (R/'preflight.json').open('x') as f:json.dump(record,f,indent=2)
print(json.dumps(record))
