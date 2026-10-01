"""Read-only final TEST identity, source, package and persistence reconciliation."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,time,re
R=Path(__file__).resolve().parents[2];D=R/'docs/stage5-continuation-20260917';B=R/'docs/stage5-accepted-baseline-20260917'
base=json.loads((B/'baseline.json').read_text());A=Path(base['app'])
sys.path.insert(0,str(A/'tests/lifecycle_stage2'));import pipe_transport as transport
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={};roots=set();records=[]
def walk(x):
    if isinstance(x,dict):
        if isinstance(x.get('pid'),int) and isinstance(x.get('created'),int) and isinstance(x.get('exe_digest'),str):
            p={k:x[k] for k in ('pid','created','exe_digest')};pins[tuple(p.values())]=p
        for v in x.values():walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
for folder,pattern in ((B,'5?-*.json'),(D,'5?-*.json'),(D,'ack-loss-*.json'),(D,'actual-client-*.json')):
    for p in folder.glob(pattern):
        x=json.loads(p.read_text());walk(x)
        if isinstance(x,dict):roots.update(x.get('roots',[]))
for p in (A/'docs/lifecycle-stage4-evidence').glob('*.json'):
    try:walk(json.loads(p.read_text()))
    except ValueError:pass
for log in (D/'regressions').glob('*.log'):
    for name in re.findall(r'^EVIDENCE (.+\.json)\s*$',log.read_text(),re.M):
        p=Path(name.strip())
        if p.is_relative_to(A) and p.exists():walk(json.loads(p.read_text()))
# Snapshot-owned TEST namespaces only. Never scan production data or credentials.
for p in (A/'tests/lifecycle_stage1/evidence').glob('TEST-STAGE4-*/TEST_ONLY'):
    roots.add(str(p.parent))
artifacts=[];databases=[];terminal=[]
for name in sorted(roots):
    root=Path(name)
    assert root.name.startswith('TEST-STAGE4-') and (root/'TEST_ONLY').read_text()=='NO PRODUCTION SERVICES'
    assert root.is_relative_to(A) or root.is_relative_to(R.parent/'deployment-test-releases')
    for pattern in ('coordinator-*.json*','*.tmp','*.replace'):
        artifacts.extend(str(p) for p in root.glob(pattern))
    for p in root.glob('*.json'):
        if p.name in ('stage4-ready.json','core.json') or any(s in p.name for s in ('start_spawned','start_verified','core_acquired')):
            walk(json.loads(p.read_text()))
            if p.name=='stage4-ready.json':terminal.append({'path':str(p),'sha256':sha(p),'role':'retained last-instance identity; not live authority'})
    database=root/'STAGE4_TEST-data/jarvis.sqlite3'
    if not database.exists():continue
    row={'path':str(database),'before':sha(database)}
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as db:
        row['integrity']=db.execute('PRAGMA quick_check').fetchone()[0]
        tables={x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'stage4_response_provenance' in tables:
            messages=dict(db.execute("SELECT id,content FROM messages WHERE role='assistant'"));linked=[];errors=[]
            responses=db.execute('SELECT response_id,status,text,provenance,mode FROM stage4_response_provenance').fetchall()
            for rid,status,text,raw,mode in responses:
                proof=json.loads(raw or '{}');mid=proof.get('message_id')
                if status=='COMPLETED':
                    if mode=='normal':
                        linked.append(mid)
                        if mid not in messages or messages[mid]!=text:errors.append({'response_id':rid,'error':'message/provenance mismatch'})
                    elif mode not in ('text-only','deep-review') or not text or not proof.get('actual_final_provider') or not proof.get('actual_final_model') or mid is not None:errors.append({'response_id':rid,'error':'invalid mode provenance'})
                elif text is not None or mid or proof.get('actual_final_provider'):errors.append({'response_id':rid,'error':'false success'})
            if len(linked)!=len(set(linked)) or set(linked)!=set(messages):errors.append({'error':'orphan/duplicate message'})
            row.update(responses=len(responses),assistant_messages=len(messages),errors=errors)
    row['after']=sha(database);databases.append(row)
ps="Get-CimInstance Win32_Process | ForEach-Object { [pscustomobject]@{pid=$_.ProcessId;created=$_.CreationDate.ToFileTimeUtc();name=$_.Name;test=($_.CommandLine -like '*TEST-STAGE5-APP-9b0e19778db44f1287851eec9f860311*' -or $_.CommandLine -like '*deployment-test-releases*TEST-INSTALL-*')} } | ConvertTo-Json -Compress"
proc=json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',ps],text=True));by_pid={p['pid']:p for p in proc};census=[]
for pin in pins.values():
    try:
        actual=transport.identity(pin['pid']);state='LIVE' if actual==pin else 'PID_REUSED'
    except Exception as exc:
        current=by_pid.get(pin['pid']);actual={'exception':type(exc).__name__,'errno':getattr(exc,'errno',None)}
        if current is None:state='EXITED'
        elif current['created']!=pin['created']:state='PID_REUSED';actual['creation_time']=current['created']
        else:state='UNCERTAIN'
    census.append({'recorded':pin,'current':actual,'state':state})
source=[]
for x in base['source']:
    rel=Path(x['path']).relative_to('accepted-app');snapshot=R/'docs/deployment-completion-20260917/final-blockers'/x['path']
    source.append({'path':str(rel),'expected':x['sha256'],'actual':sha(A/rel),'baseline_snapshot':sha(snapshot)})
package=Path(json.loads((D/'candidate.json').read_text())['package']['package']);manifest=json.loads((package/'manifest.json').read_text())
package_errors=[x['path'] for x in manifest['files'] if sha(package/x['path'])!=x['sha256']]
live=[x for x in census if x['state']=='LIVE'];uncertain=[x for x in census if x['state']=='UNCERTAIN']
test_processes=[p for p in proc if p['test'] and p['name'].lower() in ('python.exe','pythonw.exe','electron.exe','node.exe') and p['pid']!=__import__('os').getpid()]
out={'at':time.time(),'source':source,'source_unchanged':all(x['expected']==x['actual']==x['baseline_snapshot'] for x in source),'package_files':len(manifest['files']),'package_manifest_sha256':sha(package/'manifest.json'),'package_errors':package_errors,'identity_census':census,'live':live,'uncertain':uncertain,'test_processes':test_processes,'transient_readiness_artifacts':artifacts,'retained_terminal_identity_evidence':terminal,'databases':databases,'roots':sorted(roots),'production_modified':False}
p=D/('final-census-'+str(time.time_ns())+'.json');p.write_text(json.dumps(out,indent=2))
print(json.dumps({'evidence':str(p),'source_unchanged':out['source_unchanged'],'package_errors':package_errors,'live':len(live),'uncertain':len(uncertain),'processes':test_processes,'artifacts':artifacts,'databases':len(databases),'database_errors':[x for x in databases if x.get('errors') or x['integrity']!='ok' or x['before']!=x['after']]}))
