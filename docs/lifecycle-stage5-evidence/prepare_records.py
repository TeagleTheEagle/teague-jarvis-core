"""Finalize TEST evidence disposition and prepare a fixed nonsecret copy list."""
import collections, hashlib, json, pathlib, shutil
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
summary=load(OUT/'reconciliation.json');regressions=load(OUT/'regressions-081519.json')
assert summary['all_recorded_identities_exited'] and not summary['database_failures'] and summary['frozen_source_unchanged']
assert len(regressions)==29 and all(x['exit']==0 for x in regressions)
integrated='integrated-f22acb95e72142b6bae0404e5c0df31f.json';records=load(OUT/integrated)['records']
assert len(records)==1152 and all(x['passed'] for x in records)
actual=ROOT/'docs/lifecycle-stage4-evidence/client-state-media-07ed541b098c4ae198b618f4813f23de.json'
client=load(actual);assert len(client['records'])==74 and all(x['passed'] for x in client['records'])
integration_counts={}
for name in ('fallback-integration','deep-integration'):
    report=load(OUT/(name+'-081519.log'));checks=report['checks'];assert all(x['passed'] for x in checks)
    integration_counts[name]=len(checks)
assert integration_counts=={'fallback-integration':12,'deep-integration':14}
matrix=[]
def row(id,name,evidence,limitations='',status='PASS'):
    matrix.append(dict(id=id,requirement=name,disposition=status,evidence=evidence,limitations=limitations))
row('S5-01','Concurrent startup / exactly one lifetime owner',[integrated],'Four rounds of eight real TEST contenders; production shortcuts not executed.')
row('S5-02','Coordinator loss / adoption / interrupted start intent',[integrated],'Three post-spawn losses plus before-intent, intent, claimed fault boundaries; no automatic intent reuse.')
row('S5-03','Core crash / new epoch / state recovery',[integrated],'Three identity-bound TEST self-exits; old authority rejected, conservative recovery state preserved.')
row('S5-04','Disconnect / reconnect / shutdown races',[integrated,str(actual.relative_to(ROOT))],'Four simultaneous reconnects all lost to drain; attachment-before-stop also covered by controlled cases.')
row('S5-05','Canonical persistent versus transient state',[integrated,'sqlite-final.json',str(actual.relative_to(ROOT))],'Synthetic records only, fresh presence, no resurrected grants or replayed work.')
row('S5-06','Spoofing / malformed authenticated IPC / session isolation',[integrated,'stage2-081519.log','native-081519.log'],'PID/creation/executable mismatch tested; does not force arbitrary Windows PID reuse.')
row('S5-07','Provider failure plus duplicate / reconnect / restart',[integrated,'providers-081519.log','fallback-integration-081519.log','deep-integration-081519.log'],'Actual TEST Core with deterministic provider generation/failure; no live-provider billing or performance claims.')
row('S5-08','Client crash / media failure / watchdog / stale callbacks',[str(actual.relative_to(ROOT)),'desktop-081519.log'],'Actual Electron; media signals/partition modeled, physical voice deferred.')
row('S5-09','Resource exhaustion / bounded client queues',[integrated,'desktop-081519.log'],'Actual 128-session admission boundary plus real queue-class limit/deadline tests; not a universal resource-metering claim.')
row('S5-10','Interrupted persistence / WAL / corruption / UNKNOWN recovery',[integrated,'stage3-081519.log','deadline-081519.log'],'Real TEST journal/start interruptions and unchanged migration fault fixtures; no production restoration.')
row('S5-11','Inspection and synthetic repair cleanup / accounting',['inspection-cancel-081519.log','inspection-detach-081519.log','inspection-emergency-081519.log','repair-cancel-081519.log','repair-detach-081519.log','repair-emergency-081519.log','repair-drain-081519.log'],'Actual tracked TEST workers; no real repair, no invented refund.')
row('S5-12','Response commit / cancellation / polling consistency',['response-commit-081519.log','event-polling-081519.log','sqlite-final.json'],'306 trials / 4748 assertions; mode-aware post-exit persistence inspection.')
row('S5-13','Required regression reconciliation',['regressions-081519.json'],'29 successful commands. Existing two platform skips remain limits, not passes.')
row('S5-14','Final source / TEST cleanup / production preservation',['source-final.json','cleanup-final.json','reconciliation.json'],'31 frozen path hashes match; 194 recorded process identities exited; production database not opened.')
row('S5-L1','Other-user / cross-session / actual remote-host coverage',['stage1-081519.log','stage2-081519.log'],'Existing two skips retained; deployment security requires separate reviewed disposition.','LIMITATION')
row('S5-L2','Historical Windows and restricted-context findings',['../lifecycle-stage4-evidence/stage4-acceptance-20260916/REVIEW.md'],'Historical PermissionError cause and exact restricted-context missing DLL remain unconfirmed.','LIMITATION')
row('S5-D1','Physical media and live voice parity',[],'Existing explicit hardware deferral.','DEFERRED')
row('S5-D2','Authenticated approval workflows',[],'Workflow absent from approved TEST surface.','DEFERRED')
row('S5-D3','Authenticated upload workflows',[],'Separate route/authority/persistence review required.','DEFERRED')
write('requirement-to-evidence.json',matrix)
write('completion.json',dict(stage4='CLOSED — approved TEST acceptance',stage5='ISOLATED VALIDATION COMPLETE / PASS',matrix_counts=dict(collections.Counter(x['disposition'] for x in matrix)),integrated_checks=1152,actual_client_checks=74,regression_commands=29,source_paths=31,process_identities=194,test_databases=summary['databases'],source_runtime_changed=False,production_changed=False,paid_calls=0,acceptance_commit_created=False,next_review='Relocatable deployment/bootstrap and enrollment/protocol contract; Stage 6/7 cutover/install remain incomplete.'))
write('top-level-commands.json',[
    dict(command='.venv/Scripts/python.exe -B tests/lifecycle_stage5/campaign.py',context='ordinary',exit=1,evidence='integrated-1ac9ef43a83d48eaa858e09a70aab920.json',note='Mode-specific verifier assumption corrected; failure preserved.'),
    dict(command='.venv/Scripts/python.exe -B tests/lifecycle_stage5/campaign.py',context='ordinary',exit=0,evidence=integrated),
    dict(command='.venv/Scripts/python.exe -B tests/lifecycle_stage4/fixtures.py --client-state-media',context='approved host context',exit=0,log='actual-client-media-01.log'),
    dict(command='.venv/Scripts/python.exe -B docs/lifecycle-stage5-evidence/run_regressions.py',context='ordinary',exit=0,evidence='regressions-081519.json'),
    dict(command='.venv/Scripts/python.exe -B docs/lifecycle-stage5-evidence/reconcile.py',context='ordinary read-only',exit=0,evidence='reconciliation.json')])
doc=ROOT/'docs/CORE-COMPLETION-CHECKLIST.md';s=doc.read_text(encoding='utf-8');lines=s.splitlines()
for i,line in enumerate(lines):
    if line.startswith('| S5-01 |'):
        lines[i]='| S5-01 | 5 | CLOSED — approved isolated reliability validation PASS | [1,152 integrated checks, 74 actual Electron checks, 29 regression commands](lifecycle-stage5-evidence/REVIEW.md); [final matrix](lifecycle-stage5-evidence/requirement-to-evidence.json) | No for isolated scope | Retain platform/physical-media limits; deployment/enrollment contract remains the next review boundary |'
    if line.startswith('| S4-01 |'):lines[i]=line.replace('No at prior baseline','No').replace('Preserve boundary; affected final regressions after approved startup changes','Frozen boundary retained; Stage 5 final regressions passed')
    if line.startswith('| S4-04 |'):lines[i]=line.replace('CLOSED at prior baseline','CLOSED').replace('No at prior baseline','No').replace('Required final affected regressions;','Stage 5 final affected regressions passed;')
s='\n'.join(lines)+'\n'
s+='\n2026-09-16 final checkpoint: [Stage 5 report](lifecycle-stage5-evidence/REVIEW.md). All required Stage 4 human evidence and isolated Stage 5 validation are complete. Production/release remains blocked by the reviewed deployment/enrollment dependency; no new runtime authority or acceptance commit. Latest campaign cleanup: 194 recorded identities exited; 45 selected TEST databases verified; 31 frozen paths unchanged.\n'
doc.write_text(s,encoding='utf-8')
review=OUT/'REVIEW.md';review.write_text(review.read_text(encoding='utf-8').replace('43 selected isolated TEST databases','45 selected isolated TEST databases'),encoding='utf-8')
files=[p for p in OUT.iterdir() if p.is_file() and p.suffix in ('.py','.md','.json','.log') and p.name not in ('manifest.json','archive-verification.json')]
files += [ROOT/'tests/lifecycle_stage5/campaign.py',doc,ROOT/'docs/STAGE4-REMAINING-REQUIREMENTS-20260915.md']
files += [ROOT/x['path'] for x in summary['reports']]
for rec in client['records']:
    if rec.get('file','').endswith('.png'):files.append(pathlib.Path(rec['file']))
bundle=OUT/'selected-records';entries=[]
for p in sorted(set(files)):
    rel=p.relative_to(ROOT)
    assert p.suffix in ('.py','.md','.json','.log','.png') and '.env' not in p.name
    target=bundle/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    digest=sha(p);assert sha(target)==digest
    entries.append(dict(path=rel.as_posix(),sha256=digest,bytes=p.stat().st_size))
write('manifest.json',dict(files=entries,purpose='Selected Stage 5 TEST reliability evidence; excludes credentials, runtime databases, profiles and binary dependencies'))
copy=(ROOT/'docs/lifecycle-stage4-evidence/human-denial-correction-20260915/Copy-SelectedEvidence.ps1').read_text()
copy=copy.replace('CANONICAL CORE STAGE 4\\HUMAN DENIAL DRIVER CORRECTION 2026-09-15','CANONICAL CORE STAGE 5\\ISOLATED RELIABILITY 2026-09-16')
(OUT/'Copy-SelectedEvidence.ps1').write_text(copy)
print(json.dumps(dict(files=len(entries),manifest_sha256=sha(OUT/'manifest.json'),status='Stage 5 isolated PASS; archive pending')))
