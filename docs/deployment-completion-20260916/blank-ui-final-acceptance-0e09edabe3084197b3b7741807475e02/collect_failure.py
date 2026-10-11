"""Read-only post-failure reconciliation. No tests, launches, IPC calls or cleanup."""
import collections,hashlib,json,re,shutil,sqlite3,subprocess,sys,time
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'tests/lifecycle_stage2'))
import pipe_transport as transport
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda n,x:(OUT/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
pre=read(OUT/'preflight.json');records=read(OUT/'regressions.json')
exports=[];documents=[];totals=[]
for entry in records:
    text=Path(entry['log']).read_text(errors='replace')
    paths=re.findall(r'^EVIDENCE (.+\.json)\s*$',text,re.M)
    try:
        obj=json.loads(text)
        if obj.get('evidence'):paths.append(obj['evidence'])
    except (ValueError,AttributeError):pass
    unit=re.search(r'Ran (\d+) tests?',text);skip=re.search(r'OK \(skipped=(\d+)\)',text)
    count=int(unit[1]) if unit else None
    if entry['name']=='desktop':count=int(re.search(r'tests (\d+)',text)[1])
    totals.append({'command':entry['name'],'exit':entry['exit'],'unit_tests':count,'skips':int(skip[1]) if skip else 0})
    for path in paths:
        source=Path(path.strip())
        assert source.resolve().is_relative_to(ROOT) and source.suffix=='.json'
        target=OUT/'raw-evidence'/(entry['name']+'-'+source.name);target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source,target)
        exports.append({'source':str(source),'copy':str(target.relative_to(OUT)),'sha256':digest(source),'match':digest(source)==digest(target)})
        documents.append(read(source))

failed=read(ROOT/'docs/lifecycle-stage4-evidence/restart-campaign-039fa2c9b9794b72b10b208d8095312c.json')
root=Path(failed['roots'][-1]);readiness=[]
for source in root.glob('coordinator-*.json'):
    value=read(source);assert set(value)<= {'identity','peer','endpoint'}
    target=OUT/'raw-evidence'/source.name;shutil.copyfile(source,target)
    readiness.append({'file':str(source),'sha256':digest(source),'size':source.stat().st_size,'mtime_ns':source.stat().st_mtime_ns,'peer':value['peer'],'identity':value['identity']})
    documents.append(value)
save('readiness-observation-after-failure.json',readiness)

# Exact OS identity comparison, not PID-only cleanup; no mutation performed.
identities={}
def walk(value):
    if isinstance(value,dict):
        if isinstance(value.get('pid'),int) and isinstance(value.get('created'),int):
            identities[(value['pid'],value['created'])]={k:value[k] for k in ('pid','created','exe_digest') if k in value}
        for item in value.values():walk(item)
    elif isinstance(value,list):
        for item in value:walk(item)
for document in documents:walk(document)
census=[]
for expected in identities.values():
    row={'expected':expected}
    try:
        actual=transport.identity(expected['pid']);row['actual']=actual
        row['status']='MATCHING_TEST_IDENTITY_LIVE' if all(actual[k]==v for k,v in expected.items()) else 'PID_REUSED_NOT_TARGET'
    except transport.Rejected as e:row.update(status='EXITED',reason=str(e))
    except OSError as e:row.update(status='ABSENT' if e.errno==87 else 'IDENTITY_QUERY_ERROR',errno=e.errno,error=str(e))
    census.append(row)
save('process-census.json',{'at':time.time(),'observed':census,'counts':dict(collections.Counter(x['status'] for x in census)),'no_termination':True})

# Inspect already completed response race data directly; no re-execution.
racefile=ROOT/'tests/lifecycle_stage1/evidence/TEST-STAGE4-f38c6847f988426099399cd371b2b6fd/response-commit-results.json'
race=read(racefile);db=Path(race['root'])/'STAGE4_TEST-data/jarvis.sqlite3'
with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as c:
    c.execute('PRAGMA query_only=ON')
    integrity=c.execute('PRAGMA integrity_check').fetchone()[0]
    rows=c.execute('SELECT response_id,mode,status,text,provenance FROM stage4_response_provenance').fetchall()
    messages=c.execute("SELECT id,content FROM messages WHERE role='assistant'").fetchall()
    successful=[x for x in rows if x[2]=='COMPLETED']
    message_ids={json.loads(x[4])['message_id'] for x in successful if x[1]=='normal'}
    msg_by_id=dict(messages)
    issues=[]
    for rid,mode,status,content,prov in rows:
        if status in ('CANCELLED','FAILED') and (content is not None or prov is not None):issues.append([rid,'non-success answer/provenance'])
        if status=='COMPLETED':
            p=json.loads(prov)
            if not content or not p.get('actual_final_provider'):issues.append([rid,'missing successful answer/provenance'])
            if mode=='normal' and msg_by_id.get(p.get('message_id'))!=content:issues.append([rid,'message/provenance divergence'])
    if set(msg_by_id)!=message_ids:issues.append(['messages','orphan/duplicate links'])
    outcomes=collections.Counter((x['mode'],x['ordering'],x['winner']) for x in race['trials'])
save('response-persistence-inspection.json',{'source':str(db),'read_only':True,'integrity':integrity,'rows':len(rows),'assistant_messages':len(messages),'issues':issues,'trials':len(race['trials']),'assertions':race['checks'],'outcomes':[{'mode':k[0],'ordering':k[1],'winner':k[2],'count':v} for k,v in outcomes.items()]})

source=[]
for item in pre['source_hashes']:
    p=ROOT/item['path'];source.append({**item,'after':digest(p),'unchanged':digest(p)==item['sha256']})
for name in ['tests/lifecycle_stage4/fixtures.py','tests/lifecycle_stage1/harness.py','stage4_runtime.py']:
    target=OUT/'failure-source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
package=Path(pre['candidate']['package']['package']);manifest=read(package/'manifest.json')
bad=[x['path'] for x in manifest['files'] if digest(package/x['path'])!=x['sha256']]
prior=Path(pre['prior_correction']);prior_manifest=read(prior/'SHA256.json')
old_bad=[x['path'] for x in prior_manifest if digest(prior/x['path'])!=x['sha256']]
summary={'command_groups':len(records),'passed_command_groups':sum(x['exit']==0 for x in records),'failed_command_groups':sum(x['exit']!=0 for x in records),
 'unit_test_total':sum(x['unit_tests'] or 0 for x in totals),'unit_tests_skipped':sum(x['skips'] for x in totals),'test_counts':totals,
 'restart_recorded_checks':len(failed['records']),'restart_passed_records':sum(x['passed'] for x in failed['records']),'restart_failed_records':[x for x in failed['records'] if not x['passed']],
 'source_checks':source,'source_drift':[x['path'] for x in source if not x['unchanged']], 'candidate_manifest_sha256':digest(package/'manifest.json'),'candidate_files':len(manifest['files']),'candidate_mismatches':bad,
 'prior_correction_mismatches':old_bad,'head':read(OUT/'git-final.json')['head'],'tree':read(OUT/'git-final.json')['tree'],
 'exports':exports,'live_test_identities':[x for x in census if x['status']=='MATCHING_TEST_IDENTITY_LIVE'],'unknown_process_identity':[x for x in census if x['status']=='IDENTITY_QUERY_ERROR'],
 'production_operations':False,'paid_calls':0,'acceptance_commit':False,'tests_stopped':True}
save('reconciliation.json',summary)
print(json.dumps({k:summary[k] for k in ['command_groups','passed_command_groups','failed_command_groups','unit_test_total','unit_tests_skipped','source_drift','candidate_mismatches','prior_correction_mismatches','live_test_identities','unknown_process_identity']},indent=2))
