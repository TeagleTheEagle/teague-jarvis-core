"""Independent post-exit inspection; no launches, credentials or production IO."""
import datetime, hashlib, json, pathlib, re, sqlite3, sys
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[1];BASE=ROOT/'docs/lifecycle-stage4-evidence'
sys.path.insert(0,str(ROOT));import stage4_runtime as r
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
reports=list(OUT.glob('integrated-*.json'))
for log in OUT.glob('*.log'):
    for name in re.findall(r'(?:EVIDENCE |"evidence": ")([^\r\n"]+\.json)',log.read_text(errors='replace')):
        p=pathlib.Path(name.replace('\\\\','\\'))
        if p.exists() and p not in reports:reports.append(p)
roots=set();identities={}
def visit(x):
    if isinstance(x,dict):
        if all(k in x for k in ('pid','created','exe_digest')):
            v={k:int(x[k]) if k=='created' else x[k] for k in ('pid','created','exe_digest')};identities[(v['pid'],v['created'])]=v
        for k,v in x.items():
            if k=='root' and isinstance(v,str):roots.add(v)
            if k=='roots' and isinstance(v,list):roots.update(v)
            visit(v)
    elif isinstance(x,list):
        for v in x:visit(v)
for p in reports:visit(load(p))
# Integration helpers also emit a complete JSON report directly to stdout.
for p in OUT.glob('*.log'):
    try:visit(json.loads(p.read_text(encoding='utf-8-sig')))
    except (ValueError,UnicodeError):pass
selected=[]
for name in sorted(roots):
    root=pathlib.Path(name)
    if root.parent==ROOT/'tests/lifecycle_stage1/evidence' and root.name.startswith('TEST-STAGE4-'):
        r.validate_root(root);selected.append(root)
        for p in [root/'stage4-ready.json',*root.glob('coordinator-*.json')]:
            if p.exists():visit(load(p))
cleanup=[]
for ident in identities.values():
    try:
        current=r.transport.identity(ident['pid']);status='RETAINED' if current==ident else 'PID_REUSED_NOT_TOUCHED'
    except (OSError,r.transport.Rejected):
        current=None;status='EXITED' if r.exclusion.process_identity(ident['pid']) is None else 'UNCONFIRMED'
    cleanup.append(dict(expected=ident,observed=current,status=status))
write('cleanup-final.json',cleanup)
databases=[]
for root in selected:
    p=root/'STAGE4_TEST-data/jarvis.sqlite3'
    if not p.exists():continue
    with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as db:
        result=dict(root=str(root),application_id=db.execute('PRAGMA application_id').fetchone()[0],integrity=db.execute('PRAGMA quick_check').fetchone()[0])
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='stage4_response_provenance'").fetchone():
            result.update(response_table='not initialized before expected startup failure',passed=result['application_id']==0x544934 and result['integrity']=='ok');databases.append(result);continue
        rows=db.execute('SELECT response_id,owner,operation,mode,status,text,provenance FROM stage4_response_provenance').fetchall()
        messages=dict(db.execute("SELECT id,content FROM messages WHERE role='assistant'"));refs=[];orphans=0;false_success=0
        for rid,owner,op,mode,status,text,raw in rows:
            proof=json.loads(raw or '{}');mid=proof.get('message_id')
            if status=='COMPLETED':
                if not text or not proof.get('actual_final_provider'):orphans+=1
                if mode=='normal':
                    if mid not in messages or messages.get(mid)!=text:orphans+=1
                    if mid is not None:refs.append(mid)
            elif text or proof.get('actual_final_provider') or proof.get('actual_final_model'):false_success+=1
        result.update(response_rows=len(rows),assistant_rows=len(messages),orphan_provenance=orphans,orphan_messages=len(set(messages)-set(refs)),false_success=false_success,duplicates=len(refs)-len(set(refs)))
        result['passed']=result['application_id']==0x544934 and result['integrity']=='ok' and all(result[k]==0 for k in ('orphan_provenance','orphan_messages','false_success','duplicates'))
        databases.append(result)
write('sqlite-final.json',databases)
baseline=load(BASE/'stage4-acceptance-20260916/source-baseline.json')+load(BASE/'stage4-acceptance-20260916/additional-source-verification.json')
source=[dict(path=x['path'],accepted_sha256=x['sha256'],sha256=sha(ROOT/x['path']),unchanged=sha(ROOT/x['path'])==x['sha256']) for x in baseline]
write('source-final.json',source)
syntax=[]
for p in [ROOT/'tests/lifecycle_stage5/campaign.py',OUT/'run_regressions.py',OUT/'reconcile.py']:
    compile(p.read_bytes(),str(p),'exec');syntax.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),result='PASS',command='compile(source_bytes, filename, exec); no import or bytecode write'))
write('syntax.json',syntax)
summary=dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reports=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in reports],test_roots=len(selected),process_identities=len(cleanup),all_recorded_identities_exited=all(x['status'] in ('EXITED','PID_REUSED_NOT_TOUCHED') for x in cleanup),databases=len(databases),database_failures=[x for x in databases if not x['passed']],frozen_paths=len(source),frozen_source_unchanged=all(x['unchanged'] for x in source),production_database_opened=False,forced_cleanup=False)
write('reconciliation.json',summary)
assert summary['all_recorded_identities_exited'] and not summary['database_failures'] and summary['frozen_source_unchanged'], 'Review required; evidence preserved'
print(json.dumps({k:v for k,v in summary.items() if k!='reports'}))
