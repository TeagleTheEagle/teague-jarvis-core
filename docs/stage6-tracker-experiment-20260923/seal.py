import pathlib,json,hashlib,difflib,zipfile
R=pathlib.Path(__file__).resolve().parent;v=json.loads((R/'candidate.json').read_text());C=pathlib.Path(v['code']);O=pathlib.Path(v['original'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes=[];final=[]
for item in v['originalFiles']:
 name=item['name'];old=O/name;new=C/name
 assert sha(old)==item['sha256'],name
 final.append(dict(name=name,sha256=sha(new)))
 if sha(new)!=sha(old):
  assert name in ('evidence_support.py','large_collect.py'),name
  changes.append(dict(file=name,before=sha(old),after=sha(new)))
  (R/(name+'.final.diff')).write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile=str(old),tofile=str(new))))
assert len(changes)==2
with (R/'final-source.json').open('x') as f:json.dump(dict(changes=changes,files=final,originalVerified=len(final),checkerUnchanged=True),f,indent=2)
report='''# Stage 6 — bounded tracker experiment

Disposition: IMPLEMENTED; focused experiment tests PASS. NOT acceptance-qualified.

The isolated candidate adds a collector discovery anchor, excluded from descendant exit waits, and independent live-image evidence. The anchor closes without claiming collector exit. The external native observer remains required for that exit. Missing/failed image capture and empty evidence fail supporting validation. No acceptance-checker rule changed.

Exactly two copied TEST modules changed: evidence_support.py and large_collect.py. Original candidate remains frozen. See final-source.json for before/after SHA-256 and exact original/final diffs. Registration closes an unowned duplicated handle on failure; the first tested revision is preserved. captureEntryQpc labels entry into capture, not the exact OpenProcess/DuplicateHandle return instant.

Validation: first revision 15/15 tests passed; final revision 18/18 tests passed. These are separate runs, not 33 distinct requirements. AST syntax checks passed for both modules and test file. Tests cover default behavior, root/worker discovery, no self-wait, live/post-exit/query/identity failures, construction/thread-start failures, bounded capacity, duplicate-handle cleanup, non-vacuous evidence and exclusive durable-output collision. Commands/stdout/results are in tests-*.json; individual supporting records are archived under candidate/tracker-focused-*.

Final read-only census: zero matching diagnostic/VirtualBox processes; zero diagnostic trace sessions. No elevated observer or acceptance collector was launched. No protected VM/configuration access, production changes, dataset hashing, deadline changes or integrated rerun occurred.

Limitations: this is supporting-only evidence, explicitly kernelQualification NOT_PERFORMED. Kernel/native contradictions, reused/ambiguous parent identities, exact acquisition-return timing, all injected thread/close/durability failure modes, duplicate-record admission and strict fresh-run binding require additional focused verifier coverage before qualification. The 10 ms scanner can still miss short-lived helpers. Successful tiny children do not prove capture of the historical 28 ms helper. Full collector behavior/output equivalence has not been exercised. The copied candidate is intentionally not rebound for integrated execution.

Next step: complete the focused supporting-artifact verifier/negative coverage, then review versioned checker admission against exact kernel creation/parent identity and native/retained-handle contradictions. Do not run integrated or large acceptance yet. Missing evidence remains FAIL.

Rollback: select the unchanged original candidate; retain this separate candidate and evidence. No production rollback required.

Historical failures are unchanged and not reclassified. Historical 21 AMBIGUOUS / 1 UNMATCHED remain. Historical tracing/delay causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
'''
(R/'REPORT.md').write_text(report)
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 TRACKER EXPERIMENT 20260923 978b5ce7');dest.mkdir(exist_ok=False)
pairs=[('report/'+p.relative_to(R).as_posix(),p) for p in R.rglob('*') if p.is_file()]
pairs += [('candidate/'+p.relative_to(C).as_posix(),p) for p in C.rglob('*') if p.is_file()]
pairs.sort();manifest=[dict(path=n,bytes=p.stat().st_size,sha256=sha(p)) for n,p in pairs]
with (dest/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
archive=dest/'evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for n,p in pairs:z.write(p,n)
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(manifest)
 for m in manifest:
  b=z.read(m['path']);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
for m,(_,p) in zip(manifest,pairs):assert sha(p)==m['sha256']
receipt=dict(status='PASS',membersVerified=len(manifest),archive=str(archive),archiveSHA256=sha(archive),manifestSHA256=sha(dest/'manifest.json'),changes=changes,originalVerified=len(final))
for p in (R/'archive-receipt.json',dest/'receipt.json'):
 with p.open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt,indent=2))
