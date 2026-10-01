import pathlib,json,hashlib,zipfile,ast
R=pathlib.Path(__file__).parent;C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\ea85ed4b4ef14769acbe0b5e750aaed2\code');S=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\d45028a56e344926a311c04ba01f6a80\code')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
rows=read(C/'small-source-v3.json');old=read(S/'small-source-v3.json');diff=[]
for x,y in zip(rows,old):
 assert x['name']==y['name'];p=C/x['name'];assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
 if x['sha256']!=y['sha256']:diff.append(x['name'])
assert len(rows)==235 and set(diff)=={'baseline-allowlist.json','preservation-policy-v4.json'}
assert sha(S/'small-source-v3.json')=='6a86a4f287388c8c58b3df4333792217b5205305f2157043a5a2ba5456c0b15b'
for x in rows:
 p=C/x['name']
 if p.suffix in ('.py','.ps1','.hpp','.cpp','.json','.cs'):
  assert 'loss_measurement_v3' not in p.read_text(errors='replace'),p
q=(C/'medium-checker/qualification.py').read_text();d=(C/'small_check_v3.py').read_text()
assert "'eventsLost'" in q and "require(kernel[field]==0,'KERNEL_'+field)" in q
assert "'eventsLost'" in d and "q.require(detail[field]==0,'DETAIL_'+field)" in d
assert 'loss-diagnostic-v2.json' in (C/'small_finalize_v4.py').read_text()
assert read(C/'baseline-allowlist.json')==dict(syntheticRoots=[str(C/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False)
for p in R.glob('*.py'):ast.parse(p.read_text())
write(R/'acceptance-invariants.json',dict(status='PASS',unchangedFiles=233,onlyPriorPathChanges=diff,authorityNonzeroEventsLost='FAIL',detailNonzeroEventsLost='FAIL',deferredDependency=False,sourceManifest=sha(S/'small-source-v3.json'),successorManifest=sha(C/'small-source-v3.json'),method='byte identity and read-only source checks; no new live validation'))
text=(R.parent/'stage6-helper-handoff-v1-20260923/ONE-RUN-OWNER-REVIEW.md').read_text()
text=text.replace(str(S),str(C)).replace('6a86a4f287388c8c58b3df4333792217b5205305f2157043a5a2ba5456c0b15b',sha(C/'small-source-v3.json'))
text += '\n## Directory correction and prospective run boundary\n\nThe bound preservation-v4 sibling directory now exists. It contains offline failure-preservation fixtures; do not delete, reuse or interpret them as live evidence. Generate an entirely new live run identity. No prior protected-* fixture, receipt or seal may be reused. Verify this report archive and all successor hashes before preparation. The deferred final-measurement branch must remain absent. Authority and detailed EventsLost > 0 remain failure. Historical ETW loss cause remains UNCONFIRMED. A successful small run permits only an owner-reviewed proposal for medium validation; no automatic advancement.\n'
(R/'ONE-RUN-OWNER-REVIEW.md').write_text(text,encoding='utf8')
(R/'REPORT.md').write_text('''# SMALL_LIVE_ACCEPTANCE_CANDIDATE_READY

Created only the already-bound preservation-v4 directory under D:\\JARVIS-STAGE6-LIVE\\ea85ed4b4ef14769acbe0b5e750aaed2. It was empty at creation, within the approved workspace and free of reparse points. The unchanged failure-preservation routine requires the parent before exclusive archive-directory creation. No candidate code, binaries, manifest, dataset, deadlines, providers or acceptance predicates were changed.

Two formerly errored tests: 2/2 PASS. Narrow follow-up checks: 15/15 PASS. Original 150 passing tests and 2 errors remain historical evidence; the broad suite was not rerun. Fixtures test failure/success archive interactions with controlled lifecycle dependencies; they are NOT live acceptance. No observer was launched. All fixtures remain preserved and must not be reused for the next live run.

235 successor manifest entries verified, including 12 dataset files / 786,432 bytes and candidate-local DLL. Original source manifest remains 6a86a4f287388c8c58b3df4333792217b5205305f2157043a5a2ba5456c0b15b; successor manifest remains 5966bdb43ed1efaa85f6956dd0552c7459f2eef4e1d7970e5143ac1376b316ef. The two hashes intentionally differ only because the prior approved rebind changed two path-policy files.

233 original files remain byte-identical, including helper handoff, observers, workspace binding, versioned/frozen checker, launcher/finalizer, terminal coordination, durability, native/handle verification, telemetry v2, ETW settings and deadlines. Nonzero authority/detailed EventsLost still fails. No loss_measurement_v3 dependency. Synthetic-only allowlist; no protected roots. Runtime and stale-workspace checks passed.

1,227 predecessor/historical inputs and the previous report remain unchanged. Prior 592-member failure archive verified. Final census: zero matching processes/traces. Production and protected VM untouched. Historical ETW loss cause remains UNCONFIRMED. No UAC, small-live, medium or large validation. Stage 6 is not complete.

ONE-RUN-OWNER-REVIEW.md specifies the fresh-run procedure and exactly three expected observer prompts for separate owner authorization. Stop here.
''',encoding='utf8')
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 REBIND DIRECTORY FIX 20260925');assert not A.exists();files=[]
for label,root in [('report',R),('workspace',C.parent)]:
 for p in sorted(root.rglob('*')):
  if p.is_file():
   assert not p.lstat().st_file_attributes&0x400
   files.append(dict(member=label+'/'+p.relative_to(root).as_posix(),path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
write(R/'archive-manifest.json',files);A.mkdir();zpath=A/'evidence.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x['path'],x['member'])
 z.write(R/'archive-manifest.json','archive-manifest.json')
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None and len(z.namelist())==len(files)+1
 for x in files:assert hashlib.sha256(z.read(x['member'])).hexdigest()==x['sha256']
 assert z.read('archive-manifest.json')==(R/'archive-manifest.json').read_bytes()
v=dict(status='PASS',archive=str(zpath),sha256=sha(zpath),verifiedMembers=len(files)+1)
write(R/'archive-receipt.json',v);write(A/'archive-receipt.json',v);print(json.dumps(v))
