"""Read-only preservation/syntax verification; writes new action evidence only."""
import pathlib,json,hashlib,ast,difflib,zipfile,datetime
R=pathlib.Path(__file__).parent;v=json.loads((R/'before.json').read_text());P=pathlib.Path(v['predecessor']);C=pathlib.Path(v['candidate'])
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(n,x):
 with (R/n).open('x') as f:json.dump(x,f,indent=2)
for row in v['inputs']:
 p=pathlib.Path(row['path']);s=p.stat();assert (s.st_size,s.st_mtime_ns,sha(p))==(row['bytes'],row['mtimeNs'],row['sha256']),str(p)
old={r['name']:r for r in json.loads((P/'small-source-v3.json').read_text())};rows=json.loads((C/'small-source-v3.json').read_text());changes=[];diff=[];parsed=[]
allowed={'baseline-allowlist.json','preservation-policy-v4.json','evidence_support_v3.py','authority_trace_v3.cpp','J6AuthorityTraceV3.exe','authority_trace_v3.obj','small_finalize_v4.py','failure_preserve_v4.py','test_binding_v4.py','test_successor_v3.py','helper_handoff_v1.py','helper_handoff_v1.hpp','test_handoff_v1.py','native_handoff_fixture.cpp','J6HandoffFixture.exe','native_handoff_fixture.obj'}
for row in rows:
 p=C/row['name'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],str(p)
 if p.suffix=='.py':ast.parse(p.read_bytes(),filename=str(p));parsed.append(str(p))
 prior=old.get(row['name'])
 if not prior or prior['sha256']!=row['sha256']:
  assert row['name'] in allowed,row['name'];changes.append(dict(path=str(p),beforeSHA256=prior['sha256'] if prior else None,afterSHA256=row['sha256'],bytes=row['bytes']))
  if p.suffix in ('.py','.cpp','.hpp','.json'):
   diff.extend(difflib.unified_diff((P/row['name']).read_text().splitlines(True) if prior else [],p.read_text().splitlines(True),fromfile=str(P/row['name']),tofile=str(p)))
for n in ['medium-checker/frozen_reference.py','small_check_v3.py','completed_v3.py','coordination_v3.py','terminal_receipt_v3.hpp','small_launch_v4.ps1','external_driver_v4.py','large_collect_v3.py','traced_collect_v3.py','J6StartupTrace.exe','timed_monitor.ps1','J6OwnedEntry.dll','trace_telemetry.hpp','loss_diagnostic_v2.hpp','durable_sink.hpp']:
 assert sha(C/n)==sha(P/n),n
dataset=[r for r in rows if pathlib.PureWindowsPath(r['name']).parts[0]=='small-synthetic'];assert len(dataset)==12 and sum(r['bytes'] for r in dataset)==786432
archives=[]
for r in v['inputs']:
 p=pathlib.Path(r['path'])
 if p.suffix=='.zip':
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()))
   # Whole-archive SHA matches frozen previously hash-verified archive.
   archives.append(dict(path=str(p),sha256=sha(p),members=len(z.namelist()),wholeArchiveUnchanged=True,CRC='PASS'))
write('changes.json',changes);write('syntax-python.json',dict(method='ast.parse; no imports or bytecode',files=parsed,count=len(parsed),status='PASS'))
with (R/'implementation.diff').open('x',encoding='utf8') as f:f.write(''.join(diff))
write('verification.json',dict(status='PASS',candidate=str(C),candidateFiles=len(rows),candidateManifestSHA256=sha(C/'small-source-v3.json'),frozenCheckerSHA256=sha(C/'medium-checker/frozen_reference.py'),authoritySHA256=sha(C/'J6AuthorityTraceV3.exe'),predecessorFiles=len(old),preservedInputs=len(v['inputs']),archives=archives,datasetFiles=12,datasetBytes=786432,protectedAccess=False,productionChange=False,liveRun=False,UAC=False))
print(json.dumps(dict(files=len(rows),changed=len(changes),preservedInputs=len(v['inputs']),pythonSyntax=len(parsed),archives=archives)))
