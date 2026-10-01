"""Stage 6 preparation using the unchanged approved Stage 3 synthetic tooling."""
import hashlib,json,pathlib,shutil,sqlite3,sys,traceback,uuid
ROOT=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tests/lifecycle_stage3'))
import fixtures,migration,verify
out=pathlib.Path(__file__).resolve().parent;records=[];root=None;db=None

def current_fixture():
 root,db=fixtures.create()
 # Fixed approved TEST fixture, never a live production data source. Only the
 # five reviewed table definitions are read; no historical user rows are copied.
 schema_source=ROOT/'tests/lifecycle_stage1/evidence/TEST-STAGE4-2d7ac034d71140319ceb09ea5ca6700c/STAGE4_TEST-data/jarvis.sqlite3'
 names=('inspection_records','inspection_findings','inspection_finding_events','inspection_finding_sources','stage4_response_provenance')
 with sqlite3.connect(schema_source.as_uri()+'?mode=ro',uri=True) as source:
  for name in names:
   statement=source.execute('SELECT sql FROM sqlite_master WHERE type=? AND name=?',('table',name)).fetchone()[0]
   if not statement.startswith('CREATE TABLE '+name+'('):raise ValueError('UNEXPECTED_TEST_DDL')
   db.execute(statement)
 db.execute("INSERT INTO inspection_records VALUES ('TEST-inspection','TEST-date','TEST-project','{}','SYNTHETIC finding','persistent/inspection.json')")
 db.execute("INSERT INTO inspection_findings VALUES ('TEST-finding','TEST-fingerprint','TEST-panel','SYNTHETIC description','normal','SYNTHETIC recommendation')")
 db.execute("INSERT INTO inspection_finding_events(finding,status,evidence,created) VALUES ('TEST-finding','open','SYNTHETIC evidence','TEST-date')")
 db.execute("INSERT INTO inspection_finding_sources VALUES ('TEST-finding','TEST-inspection')")
 message=db.execute("INSERT INTO messages(conversation,role,content,created) VALUES ('TEST-provenance','assistant','SYNTHETIC completed answer',6)").lastrowid
 provenance={'actual_final_provider':'fixture','actual_final_model':'offline-migration-fixture','simulated':True,'message_id':message}
 db.execute("INSERT INTO stage4_response_provenance VALUES ('TEST-response','TEST-owner','TEST-original-session','TEST-operation','TEST-fingerprint','normal','COMPLETED',6,'SYNTHETIC completed answer',?)",(json.dumps(provenance),))
 db.commit()
 (root/'source/persistent/inspection.json').write_text('{"mode":"SYNTHETIC_TEST","inspection":"TEST-inspection"}')
 expected=verify.inventory(root/'source')
 migration.write(root/'fixture-policy.json',{'schema':expected['database']['schema'],'artifacts':sorted(expected['artifacts'])})
 return root,db

def check(name,ok,**fields):
 records.append({'case':name,'passed':bool(ok),**fields})
 if not ok:raise AssertionError(name)
try:
 root,db=current_fixture()
 db.execute("INSERT INTO messages(conversation,role,content,created) VALUES ('TEST-stage6-WAL','user','synthetic recovery sentinel',6)");db.commit()
 check('uncheckpointed WAL present',(root/'source/jarvis.sqlite3-wal').stat().st_size>32)
 expected=verify.inventory(root/'source');result=migration.migrate(root)
 check('isolated canonical mapping published',result['status']=='ACTIVE_TEST_ONLY')
 check('source backup and canonical logical inventory agree',all(verify.inventory(root/n)==expected for n in ('source','backup','canonical')))
 restored=root/'restored';restored.mkdir();(restored/'persistent').mkdir()
 # Exercise actual SQLite restore plus artifact restoration; hash existence is insufficient.
 source=sqlite3.connect((root/'backup/jarvis.sqlite3').as_uri()+'?mode=ro',uri=True)
 target=sqlite3.connect(restored/'jarvis.sqlite3')
 try:source.backup(target)
 finally:target.close();source.close()
 for original in (root/'backup/persistent').rglob('*'):
  if original.is_file():
   destination=restored/original.relative_to(root/'backup');destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,destination)
 shutil.copy2(root/'backup/identity.json',restored/'identity.json')
 check('restored DB and all artifacts independently verified',verify.inventory(restored)==expected,result=verify.verify(restored,expected))
 with sqlite3.connect((restored/'jarvis.sqlite3').as_uri()+'?mode=ro',uri=True) as restored_db:
  check('restored committed WAL row readable',restored_db.execute("SELECT count(*) FROM messages WHERE conversation='TEST-stage6-WAL'").fetchone()[0]==1)
  check('current provenance linked to restored assistant',restored_db.execute("SELECT count(*) FROM stage4_response_provenance p JOIN messages m ON m.id=json_extract(p.provenance,'$.message_id') WHERE p.status='COMPLETED' AND p.text=m.content").fetchone()[0]==1)
  check('inspection references and events restored',restored_db.execute("SELECT count(*) FROM inspection_finding_sources s JOIN inspection_records r ON r.id=s.inspection JOIN inspection_findings f ON f.id=s.finding JOIN inspection_finding_events e ON e.finding=f.id").fetchone()[0]==1)
 check('ephemeral secrets cache not restored',all(not (restored/n).exists() for n in ('runtime','secrets','cache')))
 rolled=migration.rollback(root)
 check('rollback without new writes returns old mapping',rolled['status']=='ROLLED_BACK_WITHOUT_NEW_WRITES' and migration.read(root/'mapping.json')['active']=='source')
 root2,db2=current_fixture()
 try:
  migration.migrate(root2)
  with sqlite3.connect(root2/'canonical/jarvis.sqlite3') as live:live.execute("INSERT INTO settings VALUES ('TEST-stage6-new-write','must-survive')")
  try:migration.rollback(root2)
  except ValueError as e:check('naive rollback after new writes refused',str(e)=='NEW_WRITES_ROLLBACK_REFUSED')
  else:check('naive rollback after new writes refused',False)
  check('newer mapping retained',migration.read(root2/'mapping.json')['active']=='canonical')
  with sqlite3.connect((root2/'canonical/jarvis.sqlite3').as_uri()+'?mode=ro',uri=True) as live:check('newer write preserved',live.execute("SELECT value FROM settings WHERE key='TEST-stage6-new-write'").fetchone()[0]=='must-survive')
 finally:db2.close()
 records.append({'case':'scope limits','passed':True,'restored_and_queried':True,'clean_machine_boot_not_performed':True,'current_stage4_schema_synthetic_preservation':True,'actual_stage4_identity_and_runtime_migration_not_validated':True,'production_cutover':False})
except BaseException as e:records.append({'case':'rehearsal failure','passed':False,'traceback':traceback.format_exc()})
finally:
 if db:db.close()
 result={'root':str(root),'records':records,'mode':'SYNTHETIC_CURRENT_19_TABLE_SCHEMA','production_read_or_changed':False,'source_tooling_unchanged':True}
 path=out/('cutover-rehearsal-'+uuid.uuid4().hex+'.json');path.write_text(json.dumps(result,indent=2));print(path);print('checks',sum(x['passed'] for x in records),'failures',sum(not x['passed'] for x in records))
 if any(not x['passed'] for x in records):raise SystemExit(1)
