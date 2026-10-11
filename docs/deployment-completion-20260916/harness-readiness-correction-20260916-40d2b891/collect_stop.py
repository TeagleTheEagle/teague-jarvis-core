"""Preserve the stopped targeted run, exact source diff and read-only integrity."""
from pathlib import Path
import difflib,hashlib,json,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pre=json.loads((D/'preflight.json').read_text());before=D/'before/fixtures.py';current=R/'tests/lifecycle_stage4/fixtures.py'
diff=''.join(difflib.unified_diff(before.read_text().splitlines(True),current.read_text().splitlines(True),fromfile='before/tests/lifecycle_stage4/fixtures.py',tofile='after/tests/lifecycle_stage4/fixtures.py'))
if (D/'harness-correction.patch').exists():assert (D/'harness-correction.patch').read_text()==diff
else:(D/'harness-correction.patch').write_text(diff,encoding='utf8')
(D/'after').mkdir(exist_ok=True)
paths=['tests/lifecycle_stage4/fixtures.py','tests/lifecycle_stage4/test_coordinator_readiness.py']
for p in paths:
 target=D/'after'/Path(p).name
 if target.exists():assert target.read_bytes()==(R/p).read_bytes()
 else:target.write_bytes((R/p).read_bytes())
src=[{**x,'actual':sha(R/x['path']),'unchanged':sha(R/x['path'])==x['sha256']} for x in pre['source_hashes']]
tracked=[{**x,'actual':sha(R/x['path']),'unchanged':sha(R/x['path'])==x['sha256']} for x in pre['tracked_hashes']]
assert {Path(x['path']).as_posix() for x in src if not x['unchanged']}=={'tests/lifecycle_stage4/fixtures.py'}
assert {Path(x['path']).as_posix() for x in tracked if not x['unchanged']}=={'tests/lifecycle_stage4/fixtures.py'}
original=[]
for entry in pre['preserved_evidence']:
 folder=Path(entry['path']);receipt=json.loads((folder/'archive-verification.json').read_text());archive=Path(receipt['destination'])
 for x in receipt['files']:
  original.append({'path':str(folder/x['path']),'match':sha(folder/x['path'])==sha(archive/x['path'])==x['sha256']})
 original.append({'path':str(folder/'archive-verification.json'),'match':sha(folder/'archive-verification.json')==sha(archive/'archive-verification.json')})
assert all(x['match'] for x in original)
package=R.parent/'deployment-test-releases/TEST-PACKAGE-2966f064bb014c14a13e260937ea4074'
manifest=json.loads((package/'manifest.json').read_text());payload=[{'path':x['path'],'match':sha(package/x['path'])==x['sha256']} for x in manifest['files']]
assert all(x['match'] for x in payload)
tests=json.loads((D/'targeted-results.json').read_text());actual=[c for x in tests['observations'] for c in x['real_coordinators']]
assert not actual
out={'at':time.time(),'changed_sources':[{'path':p,'before':sha(before) if p.endswith('/fixtures.py') else None,'after':sha(R/p)} for p in paths],
 'source_checks':src,'tracked_checks':tracked,'runtime_files_changed':False,'candidate_manifest_sha256':sha(package/'manifest.json'),
 'candidate_payload':payload,'original_evidence':original,'targeted_executed':tests['tests'],'targeted_passed':tests['tests']-tests['failed']-tests['errors'],
 'targeted_assertion_failures':tests['failed'],'targeted_errors':tests['errors'],'targeted_not_run':2,'actual_coordinators_started':len(actual),
 'core_started':False,'restart_rerun':False,'acceptance_rerun':False,'production_changed':False,'paid_calls':0,'acceptance_commit':False,
 'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
 'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=R,text=True).strip(),
 'index':subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).splitlines()}
(D/'final-integrity.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({'executed':out['targeted_executed'],'passed':out['targeted_passed'],'errors':out['targeted_errors'],'changed':out['changed_sources'],'package_files_unchanged':len(payload),'old_evidence_files_unchanged':len(original),'runtime_unchanged':True}))
