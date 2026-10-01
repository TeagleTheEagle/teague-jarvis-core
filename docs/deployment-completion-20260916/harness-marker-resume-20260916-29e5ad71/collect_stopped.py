"""Read-only source/state reconciliation and nonsecret evidence preservation; no tests."""
from pathlib import Path
import collections,difflib,hashlib,json,re,sqlite3,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,value):
    p=D/name;assert not p.exists(),p
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2),encoding='utf8')
def preserve(source,target):
    if target.exists():assert target.read_bytes()==source.read_bytes()
    else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
    return dict(source=str(source),copy=target.relative_to(D).as_posix(),sha256=sha(source),match=sha(source)==sha(target))
pre=read(D/'preflight.json');commands=read(D/'acceptance-command.json')
inventory=read(R/'docs/deployment-completion-20260916/blank-ui-final-acceptance-0e09edabe3084197b3b7741807475e02/command-inventory.json')
assert len(commands)==14 and commands[-1]['name']=='native' and commands[-1]['exit']==1
assert all(x['exit']==0 for x in commands[:-1])
exports=[];totals=[];race=None
for command in commands:
    log=Path(command['log']);assert sha(log)==command['sha256'];text=log.read_text(errors='replace')
    paths=re.findall(r'^EVIDENCE (.+\.json)\s*$',text,re.M)
    try:
        obj=json.loads(text)
        if isinstance(obj,dict) and obj.get('evidence'):paths.append(obj['evidence'])
    except ValueError:pass
    unit=re.search(r'Ran (\d+) tests?',text);skip=re.search(r'OK \(skipped=(\d+)\)',text)
    count=int(unit[1]) if unit else None
    if command['name']=='desktop':count=int(re.search(r'tests (\d+)',text)[1])
    totals.append(dict(group=command['name'],exit=command['exit'],unit_tests=count,skipped=int(skip[1]) if skip else 0))
    for value in paths:
        source=Path(value.strip());assert source.resolve().is_relative_to(R) and source.suffix=='.json'
        exports.append(preserve(source,D/'raw-evidence'/(command['name']+'-'+source.name)))
        if command['name']=='response-commit':race=read(source)
        if command['name']=='native':native=read(source)
before=D/'before/test_coordinator_readiness.py';after=R/'tests/lifecycle_stage4/test_coordinator_readiness.py'
assert after.read_text()==before.read_text().replace("write_text('SYNTHETIC HARNESS TEST ONLY')","write_text('NO PRODUCTION SERVICES')",1)
preserve(after,D/'after/test_coordinator_readiness.py')
patch=''.join(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),fromfile='before/tests/lifecycle_stage4/test_coordinator_readiness.py',tofile='after/tests/lifecycle_stage4/test_coordinator_readiness.py'))
assert not (D/'marker-only.patch').exists();(D/'marker-only.patch').write_text(patch,encoding='utf8')
checks=[{**x,'actual':sha(R/x['path']),'unchanged':sha(R/x['path'])==x['sha256']} for x in pre['source_hashes']]
assert all(x['unchanged'] for x in checks)
assert sha(R/'tests/lifecycle_stage4/fixtures.py')=='792d96f09da1b37301d217f817ec1500bfc7821392e5b89a64213242d818d68a'
old=Path(pre['previous_evidence']);receipt=read(old/'archive-verification.json');previous=[]
for x in receipt['files']:
    previous.append(dict(path=x['path'],match=sha(old/x['path'])==sha(Path(receipt['destination'])/x['path'])==x['sha256']))
previous.append(dict(path='archive-verification.json',match=sha(old/'archive-verification.json')==sha(Path(receipt['destination'])/'archive-verification.json')))
assert all(x['match'] for x in previous)
package=R.parent/'deployment-test-releases/TEST-PACKAGE-2966f064bb014c14a13e260937ea4074'
manifest=read(package/'manifest.json');payload=[dict(path=x['path'],sha256=x['sha256'],match=sha(package/x['path'])==x['sha256']) for x in manifest['files']]
assert sha(package/'manifest.json')==pre['candidate_manifest_sha256'] and all(x['match'] for x in payload)
save('final-integrity.json',dict(at=time.time(),source_checks=checks,marker_before=sha(before),marker_after=sha(after),
    changed_source_this_turn=['tests/lifecycle_stage4/test_coordinator_readiness.py'],runtime_changed=False,
    previous_evidence_unchanged=previous,candidate=str(package),candidate_manifest_sha256=sha(package/'manifest.json'),candidate_payload=payload,
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
    tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=R,text=True).strip(),
    index=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).splitlines()))
# Query the already-finished isolated database without reopening any App/Core/Store.
assert race and race['live_workers']==0
db=Path(race['root'])/'STAGE4_TEST-data/jarvis.sqlite3';issues=[]
with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as c:
    c.execute('PRAGMA query_only=ON');integrity=c.execute('PRAGMA integrity_check').fetchone()[0]
    rows=c.execute('SELECT response_id,mode,status,text,provenance FROM stage4_response_provenance').fetchall()
    messages=dict(c.execute("SELECT id,content FROM messages WHERE role='assistant'").fetchall());linked=[]
    for rid,mode,status,content,prov in rows:
        p=json.loads(prov) if prov else {}
        if status in ('CANCELLED','FAILED') and (content is not None or p.get('actual_final_provider') or p.get('actual_final_model')):issues.append([rid,'non-success durable answer/successful attribution'])
        if status=='COMPLETED':
            if not content or not p.get('actual_final_provider') or not p.get('actual_final_model'):issues.append([rid,'incomplete final response/provenance'])
            if mode=='normal':
                linked.append(p.get('message_id'))
                if messages.get(p.get('message_id'))!=content:issues.append([rid,'message/provenance mismatch'])
    if set(messages)!=set(linked) or len(linked)!=len(set(linked)):issues.append(['messages','orphan/duplicate linkage'])
outcomes=collections.Counter((x['mode'],x['ordering'],x['winner']) for x in race['trials'])
save('response-persistence-inspection.json',dict(database=str(db),read_only=True,integrity=integrity,rows=len(rows),assistant_messages=len(messages),
    status_counts=dict(collections.Counter(x[2] for x in rows)),issues=issues,trials=len(race['trials']),assertions=race['checks'],
    outcomes=[dict(mode=k[0],ordering=k[1],winner=k[2],count=v) for k,v in outcomes.items()],
    note='Cancelled/failed records may retain audit metadata; they must not contain a final answer or successful actual provider/model. No database copied.'))
assert integrity=='ok' and not issues
save('stopped-validation.json',dict(at=time.time(),groups_planned=len(inventory),groups_executed=len(commands),groups_passed=13,groups_failed=1,
    groups_not_run=[x['name'] for x in inventory[len(commands):]],totals=totals,
    unit_tests=sum(x['unit_tests'] or 0 for x in totals),unit_skipped=sum(x['skipped'] for x in totals),
    native_checks=len(native),native_passed=sum(x['passed'] for x in native),native_failed=[x for x in native if not x['passed']],
    native_summary_discrepancy='The unconditional console text says native checks 15 PASS; structured records show 14 pass / 1 fail and exit 1.',
    root_cause='UNCONFIRMED. Expected-success case returned PIPE_CONNECT:2; server recorded Rejected; zero frames received. No retry or correction.',
    exports=exports,deferred=['approvals','uploads','physical media'],acceptance_commit=False,production_touched=False,production_activated=False,stage5_started=False,
    further_actual_electron_validation='NOT RUN after required stop',collection_note='A read-only console display earlier hit cp1252 UnicodeEncodeError; ASCII-safe JSON display succeeded. No test/source change resulted.'))
print(json.dumps(dict(groups=14,passed=13,failed=1,not_run=len(inventory)-len(commands),native_passed=14,native_failed=1,
    unit_tests=sum(x['unit_tests'] or 0 for x in totals),unit_skipped=sum(x['skipped'] for x in totals),source_checks=len(checks),candidate_files=len(payload),
    prior_evidence_unchanged=len(previous),database_integrity=integrity,database_issues=issues,exports=len(exports))))
