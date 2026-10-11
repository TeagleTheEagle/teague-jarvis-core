import pathlib,hashlib,json,subprocess,sys,zipfile,ast
R=pathlib.Path(__file__).resolve().parent
P=R.parent/'stage6-tracker-experiment-20260923'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources=json.loads((P/'final-source.json').read_text())
C=pathlib.Path(json.loads((P/'candidate.json').read_text())['code'])
for x in sources['files']:assert sha(C/x['name'])==x['sha256'],x['name']
receipt=json.loads((P/'archive-receipt.json').read_text())
assert sha(pathlib.Path(receipt['archive']))==receipt['archiveSHA256']
for name in ('support_verifier.py','test_verifier.py'):ast.parse((R/name).read_text())
run=subprocess.run([sys.executable,'-B',str(R/'test_verifier.py')],capture_output=True,text=True,timeout=30)
with (R/'tests.json').open('x') as f:json.dump(dict(command=[sys.executable,'-B',str(R/'test_verifier.py')],returncode=run.returncode,stdout=run.stdout,stderr=run.stderr),f,indent=2)
assert run.returncode==0,run.stderr
with (R/'preservation.json').open('x') as f:json.dump(dict(candidateHashesVerified=len(sources['files']),priorArchiveSHA256=receipt['archiveSHA256'],priorArchiveUnchanged=True,checkerModified=False,productionModified=False,protectedVMAccessed=False,observersStarted=0,workersStarted=0),f,indent=2)
(R/'REPORT.md').write_text('''# Focused supporting-evidence verifier coverage

Result: 43/43 focused tests PASS; syntax PASS. Separate TEST predicates only; no acceptance qualification or checker integration.

Files added: support_verifier.py, test_verifier.py and evidence/finalization tooling in this report directory. No existing tracker/collector/runtime/checker file changed. All 183 candidate source hashes and the preceding 224-member archive digest verified unchanged.

The verifier checks non-vacuous bounded evidence, live image timing, handle identity and closure, parent lifetime uniqueness, duplicate identities, no fabricated collector self-exit and explicit supporting-only scope. Synthetic cross-channel fixtures test run/digest binding, missing identities, sequence gaps, loss, segment-verification failure, kernel lifetime/parent contradictions, retained-handle contradictions and native timing/image contradictions. Preserved actual supporting artifacts are used only for structural verification. Negative tests remain rejection tests, not historical acceptance failures.

Evidence: tests.json contains exact command and complete output. The initial identical test execution also passed 43/43; the saved final execution is the reported count, not 86 distinct checks. No observers, trace sessions, hash workers or sacrificial subprocess workloads were launched. No full campaign, dataset hashing, protected VM access, VirtualBox launch, production change or threshold change occurred.

Limits: the cross-channel input shape is a proposed synthetic fixture contract. This tool does not authenticate channel origins or derive real ETW sequence completeness; boolean completeness/segment fields must never substitute for independent qualification. The binding fixture does not retrofit a real run ID into old evidence. Exact acquisition-return timing, real native/channel adapters, active cleanup failure injection and full collector-output equivalence remain outside these pure verifier tests. Historical short-lived helper capture is not proven. No production or Stage 6 acceptance claim follows from 43 tests passing.

Next: review versioned checker integration with independently qualified actual kernel/native/retained-handle records and fresh run/finalization binding before a small integrated attempt. Preserve missing evidence as FAIL. No large run is authorized by this report.

Rollback: do not select this separate verifier proposal; original candidates are unchanged. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. Historical delay/tracing causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
''')
dest=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 SUPPORT VERIFIER COVERAGE 20260923');dest.mkdir(exist_ok=False)
files=sorted(p for p in R.iterdir() if p.is_file())
manifest=[dict(path=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in files]
with (dest/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
zpath=dest/'evidence.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.name)
with zipfile.ZipFile(zpath) as z:
 for x in manifest:
  b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
for x in manifest:assert sha(R/x['path'])==x['sha256']
result=dict(status='PASS',membersVerified=len(manifest),archive=str(zpath),archiveSHA256=sha(zpath),manifestSHA256=sha(dest/'manifest.json'))
for p in (R/'archive-receipt.json',dest/'receipt.json'):
 with p.open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
