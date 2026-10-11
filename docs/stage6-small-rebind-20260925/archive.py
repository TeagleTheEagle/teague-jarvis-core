import pathlib,json,zipfile
from prepare import R,S,rec,sha,write
v=json.loads((R/'before.json').read_text());C=pathlib.Path(v['candidate'])
for x in v['inputs']:assert rec(pathlib.Path(x['path']))==x,x['path']
rows=json.loads((C/'small-source-v3.json').read_text())
for x in rows:assert (C/x['name']).stat().st_size==x['bytes'] and sha(C/x['name'])==x['sha256']
write(R/'preservation.json',dict(status='PASS',preservedInputs=len(v['inputs']),candidateFiles=235,matchingProcesses=0,traceSessions=0,productionChanged=False,protectedVMAccess=False,liveRun=False,UAC=False))
(R/'REPORT.md').write_text('''# REBIND_DEFECTIVE

Fresh candidate: `D:\\JARVIS-STAGE6-LIVE\\ea85ed4b4ef14769acbe0b5e750aaed2\\code`.

235 manifest-listed files copied and verified before edits. Only baseline-allowlist.json and preservation-policy-v4.json differ; 233 original files remain byte-identical. New small-source-v3.json binds the successor. Dataset: 12 files / 786,432 bytes, exact original hashes. Runtime/DLL and manifest checks passed. No loss_measurement_v3 or timestamp-reuse-v1 dependency appeared in inspected candidate code/configuration. No observer binary, checker, provider, buffer, deadline or behavior changed.

Focused offline tests: 152 executed, 150 passed, 0 assertion failures, 2 errors, 0 skips. One real-junction creation test was deliberately not selected; mocked reparse rejection coverage ran. The two errors are test_22_fail_missing_sidecar_explicit and test_positive_failure_archive_integration: FileNotFoundError at failure_preserve_v4.py:325, target.mkdir(parents=False). The new bound preservation-v4 parent directory was omitted by this action's preparation script. This is an offline workspace-preparation omission, not evidence of a production defect. Original test output is preserved unchanged. No repair or rerun performed.

The immutable helper-handoff v1, binding v4, coordination v3, launcher/finalizer v4, checker v3, original telemetry v2 and authority/detailed observers remain copied unchanged. Authority and detailed EventsLost nonzero predicates remain unchanged; live acceptance is NOT established. Fresh offline fixture directories are evidence only, never reusable live run identities.

Next proposed action: create only the already-bound empty preservation-v4 destination after containment checks; rerun the affected offline failure-preservation checks, complete remaining verification, and archive results. No source correction, contract change or live run is needed for that preparation correction. Owner review required before continuing.

Historical ETW-loss cause remains UNCONFIRMED. Production and protected VM untouched. Final census and preservation are recorded separately. This candidate is NOT READY for live acceptance.
''',encoding='utf8')
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 SMALL REBIND 20260925');assert not A.exists()
files=[]
for label,root in [('report',R),('candidate',C)]:
 for p in sorted(root.rglob('*')):
  if p.is_file():files.append(dict(member=label+'/'+p.relative_to(root).as_posix(),**rec(p)))
write(R/'archive-manifest.json',files);A.mkdir();zpath=A/'evidence.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x['path'],x['member'])
 z.write(R/'archive-manifest.json','archive-manifest.json')
import hashlib
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None and len(z.namelist())==len(files)+1
 for x in files:assert hashlib.sha256(z.read(x['member'])).hexdigest()==x['sha256']
 assert z.read('archive-manifest.json')==(R/'archive-manifest.json').read_bytes()
receipt=dict(status='PASS',archive=rec(zpath),verifiedMembers=len(files)+1)
write(R/'archive-receipt.json',receipt);write(A/'archive-receipt.json',receipt);print(json.dumps(receipt))
