import pathlib,json,hashlib,zipfile,os,shutil
from evidence_io import create_bytes,create_json,create_report
from restore_evidence import archives,metadata,snapshot,TARGET,ORIGINAL,OVERWRITTEN
R=pathlib.Path(__file__).parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
frozen=load(R/'freeze.json');restored=load(R/'restoration-result.json');tests=load(R/'focused-tests.json');preflight=load(R/'preflight-validation.json');audit=load(R/'output-audit.json')
assert tests['executed']==tests['passed']==18 and tests['failed']==tests['errored']==0
assert preflight['status']=='PASS' and not preflight['duplicateChangedBytes'] and not preflight['duplicateChangedHash']
assert preflight['liveDiagnosticProcesses']==preflight['traceSessions']==0
assert sha(TARGET)==ORIGINAL
files=[p for p in R.iterdir() if p.suffix in ('.py','.ps1','.md') and p.name!='REPORT.md']
create_json(R/'hardened-source-hashes.json',[metadata(p) for p in sorted(files)])
values=[
('Canonical evidence file path',str(TARGET)),
('Overwritten local SHA-256',OVERWRITTEN),
('Authoritative archived SHA-256',ORIGINAL),
('Restored local SHA-256',sha(TARGET)),
('Authoritative-source proof','AUTHORITATIVE_RESTORATION_SOURCE_CONFIRMED. Archive manifest finalized2026-09-21T02:36:35.586137+00:00, before accidental host check02:41:15.8810587Z. Archive/member trusted hashes match; independent incident record and both separately preserved copies agree. No conflicting equally authoritative original found in the recorded evidence set.'),
('Overwritten-version preservation path',restored['preservedOverwritten']['path']),
('Byte-for-byte restoration result',f"PASS;494 bytes, equal to archived member. New local LastWriteTimeUtc={restored['target']['LastWriteTimeUtc']}; historical timestamp not recreated."),
('Surrounding directory preservation result','PASS. Complete before/after filename,size,hash,mtime comparison of both relevant evidence directories: only the authorized target changed. No neighboring rename,deletion,content or timestamp change.'),
('Historical archive integrity result','PASS;143/143 members verified. Archive SHA-256:46dddb7c33c87154325778989f51fda265e9833f8f50d550b9506fdc770dc1a5. Archive unchanged.'),
('Incident archive integrity result','PASS;8/8 members verified, every member hash recorded in freeze.json. Archive SHA-256:a18270f1aee8510ba0895d794fb66a95f0c52f473477b1db3f5f836c06c7bec1. Archive unchanged.'),
('Exact overwrite code path',str(R.parent/'stage6-instance-stream-design-20260921'/'final_host.ps1')+':9. Top-level operation uses $r=$PSScriptRoot then Join-Path $r final-host-state.json and Set-Content, which truncates/replaces an existing file on repeated invocation.'),
('Exclusive-create correction','New host_preflight.ps1 accepts a required32-hex RunId, confines output to its own precreated final/run-id directory, rejects reparse output directories and atomically FileMode.CreateNew-reserves before any host queries. Existing path explicitly fails; no truncate/delete/suffix retry. Python create_bytes/create_json/create_report use xb and flush/fsync. create_run uses exist_ok=False. Historical script is preserved unchanged and retired from reuse by POLICY.md.'),
('Other vulnerable output paths found','47 relevant operations audited:18 UNSAFE_OVERWRITE,13 SAFE_EXCLUSIVE_CREATE,9 SAFE_UNIQUE_RUN_PATH,6 INTENTIONAL_MUTABLE_RUNTIME_FILE,1 UNKNOWN. Fixed result paths include prior plan,measurements,reconciliation,hash listings,diff,REPORT,probe/check and capacity-test summaries. Monitor Save mixes mutable health and final outputs; broader hardening documented only. Exact file/line inventory in output-audit.json. Archived scripts were not edited or reexecuted.'),
('Focused test totals','18/18 PASS;0 failures,0 errors,0 skipped. Includes15 requested cases and runtime/final separation,run reuse/traversal rejection. Sixteen concurrent creators yielded exactly one successful creator. Actual PowerShell path separately checked below.'),
('Duplicate-write rejection result','PASS for final JSON,reports,incident copies,restoration-source copies and archive receipts. Original bytes,hash,mtime and file identity preserved where tested. No delete/recreate fallback.'),
('Narrow preflight result','PASS:2 fresh final host checks through established PowerShell7.6.5; original restored hash,116 candidate hashes and both historical archives reverified. Initial Windows PowerShell5.1 invocation was blocked by its execution policy before script execution; failed invocation/source preserved. No policy was changed or bypass flag used.'),
('Repeated-preflight overwrite protection','PASS:repeat of first real preflight output rejected with FINAL_EVIDENCE_CREATE_REJECTED before host queries; bytes,hash and timestamp unchanged. A second explicit run ID produced a separate valid result.'),
('Candidate hash result','PASS:116 frozen candidate hashes plus6 additional frozen checks unchanged. No identity/stream/runtime candidate edited.'),
('Live-process result','0 matching diagnostic/VirtualBox processes at final completed host query. No observers or validation workloads launched. Short-lived preflight shell and filesystem-test threads exited normally.'),
('Trace-session result','0 diagnostic trace sessions; logman query -ets succeeded. No trace session started.'),
('Protected VM access result','NOT ACCESSED. No protected configuration/hash/VM/snapshot operation. This is an operation-scope statement, not a newly acquired protected-file hash proof.'),
('Production-change result','UNCHANGED by this pass. No production source/configuration/provider/credential/security changes or launch.'),
('Remaining limitations','Immutability applies to the tested new entry points, not arbitrary programs/owner edits or frozen legacy scripts. No ACL enforcement added. A failed new write may leave a partial artifact that must be preserved; no automatic retry. One-off fixed-target restoration is an explicit approved exception, guarded by overwritten hash and refuses replay. Existing integration/identity/capacity blockers remain open.'),
('Final status','EVIDENCE_RESTORATION_COMPLETE')]
assert len(values)==24
text='# Stage6 single evidence restoration and immutable preflight\n\n**EVIDENCE_RESTORATION_COMPLETE**\n\nINCIDENT OCCURRED → DETECTED → FAIL CLOSED → BOTH VERSIONS PRESERVED → AUTHORITATIVE ORIGINAL RESTORED → OVERWRITE PATH HARDENED → VERIFICATION PASSED.\n\n'
text+='The overwrite was an agent error caused by reexecuting a historical host-check script with a fixed output path. This report preserves that fact. The original143-member archive and8-member incident archive remain unchanged. Restoration was explicitly authorized for one local file only.\n\n'
for n,(label,value) in enumerate(values,1):text+=f'{n}. **{label}:** {value}\n\n'
text+='## Restoration method and metadata\n\nBefore restoration the overwritten file was494 bytes, LastWriteTimeUtc2026-09-21T02:41:15.921175+00:00. Its current bytes were copied with exclusive creation to the new incident path. The original archive member was materialized into a separate exclusive-created file and hashed. Only after both copies and the restoration intent were recorded was the exact canonical target opened r+b; the current handle bytes were hash-checked, replaced with the archived original, truncated to its exact length and flushed durably. Byte equality and surrounding-directory preservation were then verified. No broad extraction, deletion or timestamp fabrication occurred.\n\n'
text+='## Changed files and commands\n\nThe only pre-existing changed file is the explicitly restored canonical file. New hardening: evidence_io.py,host_preflight.ps1,POLICY.md. New restoration/audit/validation/report tooling: restore_evidence.py,audit_outputs.py,test_evidence_io.py,verify_preflight.py,finish.py. All reside in this new evidence directory. hardened-source-hashes.json records their hashes; the archive manifest covers all resulting artifacts.\n\n'
text+='Commands: bundled Python with -B ran restore_evidence.py freeze/restore/verify, test_evidence_io.py,audit_outputs.py and verify_preflight.py. preflight-validation.json and per-invocation command records contain exact PowerShell executable/arguments,exit codes and output. No execution-policy option was supplied.\n\n'
text+='## Evidence\n\n'
for name in ('freeze.json','restoration-intent.json','restoration-result.json','final-preservation.json','focused-tests.json','output-audit.json','POLICY.md','preflight-validation.json','winps-policy-failure.json','hardened-source-hashes.json'):
    text+=f'- [{name}]({(R/name).as_posix()})\n'
text+='\nNew archive verification is recorded in archive-verification.json outside its own archive to avoid circular hashing. Both overwritten versions and the separately materialized original are retained. Historical delay causes remain UNCONFIRMED. HISTORICAL STAGE1 CAUSE: UNCONFIRMED.\n\n'
text+='## Owner review only — proposed resume point\n\n**AUTHORITATIVE EVENT STREAM + INDEPENDENT PROCESS-INSTANCE IDENTITY INTEGRATION**\n\nBegin with the new immutable preflight against a fresh run ID, reconcile116 candidate hashes and prior evidence, then resume the previously requested dataflow/design review. This pass stops here. No identity/stream integration, medium/large validation or protected baseline capture has been resumed.\n'
create_report(R/'REPORT.md',text)
entries=[]
for p in sorted(R.rglob('*')):
    if p.is_file():
        assert not p.is_symlink() and not (p.stat().st_file_attributes&0x400)
        entries.append(dict(name=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
manifest=dict(status='EVIDENCE_RESTORATION_COMPLETE',files=entries)
manifest_bytes=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
archive=R.parent/'stage6-evidence-restoration-20260921.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for row in entries:z.write(R/row['name'],row['name'])
    z.writestr('manifest.json',manifest_bytes)
with archive.open('r+b') as f:os.fsync(f.fileno())
def verify(p):
    with zipfile.ZipFile(p) as z:
        assert len(z.namelist())==len(set(z.namelist()))==len(entries)+1
        assert z.read('manifest.json')==manifest_bytes
        for x in entries:
            with z.open(x['name']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
verify(archive)
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 EVIDENCE RESTORATION 20260921')
A.mkdir(exist_ok=False)
with archive.open('rb') as src,(A/'evidence.zip').open('xb') as dest:
    shutil.copyfileobj(src,dest,1024*1024);dest.flush();os.fsync(dest.fileno())
create_bytes(A/'manifest.json',manifest_bytes)
assert sha(A/'evidence.zip')==sha(archive);verify(A/'evidence.zip')
archives()
after=snapshot();before=frozen['beforeDirectoryState'];assert set(before)==set(after)
assert all(before[p]==after[p] for p in before if p!=str(TARGET));assert metadata(TARGET)==restored['target']
for x in entries:assert sha(R/x['name'])==x['sha256']
receipt=dict(status='HASH_VERIFIED',acceptance='EVIDENCE_RESTORATION_COMPLETE',members=len(entries)+1,path=str(A),zipSHA256=sha(A/'evidence.zip'),reportSHA256=sha(R/'REPORT.md'),manifestSHA256=sha(A/'manifest.json'),priorArchiveMembersVerified=[143,8],candidateHashesUnchanged=116,onlyHistoricalChange=str(TARGET),focusedTests=18,preflight='PASS',duplicateOutputRejected=True)
create_json(R/'archive-verification.json',receipt);create_json(A/'archive-verification.json',receipt)
print(json.dumps(receipt))
