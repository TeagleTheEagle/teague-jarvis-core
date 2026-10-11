"""Independent read-only verification of this campaign's selected TEST records."""
import ast,hashlib,json,pathlib,re,sqlite3,sys,datetime,subprocess,os
ROOT=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));BASE=ROOT/'docs/lifecycle-stage4-evidence';OUT=pathlib.Path(__file__).resolve().parent
import stage4_runtime as runtime
reports=[BASE/name for name in ['restart-campaign-3b1852cbca224289b2f6c86b4810c60b.json','restart-campaign-5e280039f6114a95be8ae9449d6f41a1.json','restart-campaign-993dfb64fbec46a18e17e20fe3c89952.json','restart-campaign-5a9ac2730cbe4c1da318e710793af901.json','client-state-media-df0270f08af54384bc2fbd82dd4b4328.json','client-state-media-a9cbccc28f354831aee61a48f2d2727d.json','electron-app-probe-6425a1f8fb814e4b83ed6c48250ec55a.json']]
for log in OUT.glob('*.log'):
 text=log.read_text(errors='replace')
 for match in re.findall(r'(?:EVIDENCE |"evidence": ")([^\r\n"]+\.json)',text):
  path=pathlib.Path(match.replace('\\\\','\\'))
  if path.exists() and path not in reports:reports.append(path)
roots=set();identities={}
def visit(value):
 if isinstance(value,dict):
  if all(k in value for k in ('pid','created','exe_digest')):identities[(value['pid'],int(value['created']))]={k:(int(value[k]) if k=='created' else value[k]) for k in ('pid','created','exe_digest')}
  for k,v in value.items():
   if k=='root' and isinstance(v,str):roots.add(v)
   if k=='roots' and isinstance(v,list):roots.update(v)
   visit(v)
 elif isinstance(value,list):
  for x in value:visit(x)
for report in reports:visit(json.loads(report.read_text()))
allowed=ROOT/'tests/lifecycle_stage1/evidence';selected=[]
for root in sorted(roots):
 path=pathlib.Path(root)
 if path.parent==allowed and path.name.startswith('TEST-STAGE4-'):
  runtime.validate_root(path);selected.append(path)
  for p in [path/'stage4-ready.json',*path.glob('coordinator-*.json')]:
   if p.exists():visit(json.loads(p.read_text()))
processes=[]
for old in identities.values():
 try:
  now=runtime.transport.identity(old['pid']);status='RETAINED' if now==old else 'PID_REUSED_NOT_TOUCHED'
 except (OSError,runtime.transport.Rejected):
  now=None;status='EXITED' if runtime.exclusion.process_identity(old['pid']) is None else 'UNCONFIRMED'
 processes.append({'expected':old,'observed':now,'status':status})
OUT.joinpath('process-cleanup-final.json').write_text(json.dumps({'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'processes':processes,'forced_termination':False,'all_recorded_identities_exited':all(x['status'] in ('EXITED','PID_REUSED_NOT_TOUCHED') for x in processes)},indent=2))
databases=[]
for root in selected:
 path=root/'STAGE4_TEST-data/jarvis.sqlite3'
 if not path.exists():continue
 with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
  tables=[x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
  result={'root':str(root),'application_id':db.execute('PRAGMA application_id').fetchone()[0],'integrity':db.execute('PRAGMA quick_check').fetchone()[0]}
  if 'stage4_response_provenance' not in tables:result['response_table']='not initialized before failed startup';databases.append(result);continue
  responses=db.execute('SELECT response_id,owner,operation,mode,status,text,provenance FROM stage4_response_provenance').fetchall()
  messages={x[0]:x[1] for x in db.execute("SELECT id,content FROM messages WHERE role='assistant'")}
  refs=[];orphans=0;false_success=0
  for rid,owner,op,mode,status,text,raw in responses:
   provenance=json.loads(raw or '{}');message=provenance.get('message_id')
   if status=='COMPLETED':
    if not text or not provenance.get('actual_final_provider'):orphans+=1
    if mode=='normal':
     if message not in messages or messages.get(message)!=text:orphans+=1
     if message is not None:refs.append(message)
   elif text or provenance.get('actual_final_provider') or provenance.get('actual_final_model'):false_success+=1
  result.update(response_rows=len(responses),assistant_rows=len(messages),orphan_messages=len(set(messages)-set(refs)),orphan_provenance=orphans,false_success=false_success,duplicates=len(refs)-len(set(refs)))
  result['passed']=result['application_id']==0x544934 and result['integrity']=='ok' and all(result[k]==0 for k in ('orphan_messages','orphan_provenance','false_success','duplicates'))
  databases.append(result)
OUT.joinpath('independent-sqlite-final.json').write_text(json.dumps(databases,indent=2))
prior=json.loads((BASE/'response-commit-final-validation-20260915/source-after.json').read_text());changed={'stage4_runtime.py','stage4_client.cjs','tests/lifecycle_stage4/fixtures.py','tests/lifecycle_stage4/test_stage4.py','desktop/test/stage4-client.test.cjs'}
hashes=[]
for entry in prior:
 path=pathlib.Path(entry['path']);path=path if path.is_absolute() else ROOT/path
 sha=hashlib.sha256(path.read_bytes()).hexdigest();expected=entry['after']
 hashes.append({'path':entry['path'],'prior':expected,'sha256':sha,'unchanged':sha==expected,'reviewed_change':entry['path'] in changed})
for name in changed:
 if name not in [x['path'] for x in hashes]:hashes.append({'path':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),'reviewed_change':True})
OUT.joinpath('final-source-hashes.json').write_text(json.dumps(hashes,indent=2))
protected=[x for x in hashes if not x['reviewed_change']]
summary={'selected_reports':[str(p) for p in reports],'test_roots':len(selected),'process_identities':len(processes),'all_exited':all(x['status'] in ('EXITED','PID_REUSED_NOT_TOUCHED') for x in processes),'databases':len(databases),'database_failures':[x['root'] for x in databases if x.get('passed') is False],'protected_files':len(protected),'protected_unchanged':all(x['unchanged'] for x in protected),'production_database_opened':False}
OUT.joinpath('reconciliation-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
