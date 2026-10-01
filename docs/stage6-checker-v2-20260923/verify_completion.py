"""Verification/evidence only. Never imports or executes candidate modules."""
import pathlib,json,hashlib,ast,subprocess,zipfile
R=pathlib.Path(__file__).resolve().parent
cfg=json.loads((R/'candidate.json').read_text());C=pathlib.Path(cfg['code']);O=pathlib.Path(cfg['original'])
record=json.loads((R/'stop-source-hashes.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
census=json.loads((R/'final/1193d162bb7d458d979bb68bc959ad82/final-host-state.json').read_text())
assert census['status']=='PASS' and census['matchingProcessCount']==census['diagnosticTraceCount']==0
changed={x['name']:x['after'] for x in record['changes']}
source=[]
for x in cfg['originalFiles']:
 assert sha(O/x['name'])==x['sha256'],('original',x['name'])
 expect=changed.get(x['name'],x['sha256']);assert sha(C/x['name'])==expect,('candidate',x['name'])
 source.append(dict(name=x['name'],sha256=expect,bytes=(C/x['name']).stat().st_size))
for x in record['newFiles']:
 assert sha(C/x['name'])==x['sha256'],x['name']
 source.append(dict(x,bytes=(C/x['name']).stat().st_size))
assert sha(C/'small-source-v2.json')==record['candidateSourceManifestSHA256']
frozen=json.loads((C/'small-source-v2.json').read_text())
for x in frozen:
 assert sha(C/x['name'])==x['sha256'] and (C/x['name']).stat().st_size==x['bytes'],x['name']
syntax=[]
for name in ['evidence_support.py','large_collect.py']+[x['name'] for x in record['newFiles'] if x['name'].endswith('.py')]:
 p=C/name;ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p));syntax.append(dict(file=str(p),status='PASS',method='ast.parse (no execution/bytecode)'))
pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
script="$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile('"+str(C/'small_launch_v2.ps1')+"',[ref]$tokens,[ref]$errors) | Out-Null; if ($errors.Count) { $errors | ForEach-Object { $_.Message }; exit 1 }; 'POWERSHELL_SYNTAX_PASS'"
p=subprocess.run([pwsh,'-NoProfile','-Command',script],capture_output=True,text=True,timeout=30)
assert p.returncode==0,(p.stdout,p.stderr)
syntax.append(dict(file=str(C/'small_launch_v2.ps1'),status='PASS',method='PowerShell Parser.ParseFile only',command=[pwsh,'-NoProfile','-Command',script],stdout=p.stdout,stderr=p.stderr))
receipt=json.loads((R/'local-archive-receipt.json').read_text());archive=pathlib.Path(receipt['archive']);assert sha(archive)==receipt['sha256']
with zipfile.ZipFile(archive) as z:
 old=json.loads(z.read('archive-input-manifest.json'))
 for x in old:
  b=z.read(x['name']);assert hashlib.sha256(b).hexdigest()==x['sha256'];assert sha(R/x['name'])==x['sha256']
prior=[]
for name in ('stage6-tracker-experiment-20260923','stage6-support-verifier-20260923','stage6-checker-integration-review-20260923'):
 v=json.loads((R.parent/name/'archive-receipt.json').read_text());assert sha(pathlib.Path(v['archive']))==v['archiveSHA256'];prior.append(v['archiveSHA256'])
value=dict(status='PASS',originalFilesVerified=len(cfg['originalFiles']),candidateFilesVerified=len(source),candidateManifestEntriesVerified=len(frozen),candidateManifestSHA256=sha(C/'small-source-v2.json'),source=source,syntax=syntax,cleanup=census,stoppedArchiveVerified=receipt,priorArchivesVerified=prior,testsRerun=False,implementationChanged=False)
with (R/'final-verification.json').open('x') as f:json.dump(value,f,indent=2)
(R/'FINAL_VERIFICATION.md').write_text('''# Stage 6 v2 TEST action — final verification

CURRENT ACTION COMPLETE — STOP FOR OWNER REVIEW. Stage 6 remains INCOMPLETE.

The approved host-context read-only cleanup census passed: zero matching diagnostic/VirtualBox processes and zero diagnostic trace sessions at 2026-09-22T23:49:12.5568586Z. No UAC prompt, Administrator launch, process termination or VM operation occurred. The earlier access-denied attempt and partial file are preserved unchanged.

Previously completed tests remain 27 offline checker/binding/finalizer methods and 21 tiny-process tracker methods PASS (48 total). They were NOT rerun in this verification pass. No integrated acceptance run has occurred. Synthetic fixture success does not establish actual combined kernel-authority qualification.

Final verification: 12 Python files parsed with ast.parse and one PowerShell launcher parsed with Parser.ParseFile; no candidate module imported/executed. Exact paths, commands and results are in final-verification.json. All 183 original files, 194 recorded candidate files and all existing candidate source-manifest entries hash-verified. The candidate source manifest is unchanged; separately recorded tracker regression files are included in the full verification record. Frozen v1 checker/native/authority files remain unchanged. No implementation rerun or correction made.

The prior stopped archive was verified against every archived member and current historical source evidence. Three preceding archive digests verified unchanged. A new canonical archive preserves this candidate, all focused test artifacts, previous failures, final census, syntax results, source hashes and report. See canonical-archive-receipt.json for archive path, member count and SHA-256. Canonical archive success is reported only after full member/hash verification.

Production unchanged. Protected VM/configuration not accessed. No backup/restore, medium/large/59.7 GB validation, new UAC requirement, frozen-checker replacement or new Stage 6 gate.

Rollback: retain/select original D:\\JARVIS-STAGE6-LIVE\\978b5ce769244ec9a580fb0846f9bfdc\\code; preserve the separate candidate and all evidence. No production rollback required.

Next action for owner review only: authorize the bounded fresh small integrated normal and controlled-startup-failure validation procedure for this versioned TEST candidate, including its established per-run observer approvals. No such run is authorized or started by this verification report.

Historical causes remain UNCONFIRMED. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
''')
print(json.dumps(dict(status='PASS',pythonFiles=len(syntax)-1,powershellFiles=1,originalFiles=len(cfg['originalFiles']),candidateFiles=len(source),manifestEntries=len(frozen),priorStoppedMembers=len(old)),indent=2))
