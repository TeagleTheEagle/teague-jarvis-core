import pathlib,json,shutil,hashlib,subprocess,sys,uuid,ast
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
for name in ('test_v2.py','tracker_adapter_v2.py','small_finalize_v2.py'):shutil.copy2(R/name,C/name)
shutil.copy2(R.parent/'stage6-support-verifier-20260923/test_verifier.py',C/'fixture_support.py')
for name in ('small_binding_v2.py','small_check_v2.py','small_coverage_v2.py','small_finalize_v2.py','tracker_adapter_v2.py','evidence_support.py','large_collect.py','test_v2.py'):ast.parse((C/name).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=C/'small-source-v2.json'
if not manifest.exists():
 files=[p for p in C.rglob('*') if p.is_file()];rows=[dict(name=p.relative_to(C).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]
 manifest.write_text(json.dumps(rows,indent=2))
else:
 rows=json.loads(manifest.read_text())
 # Test-source refinements are recorded per invocation, not accepted-source edits.
 for x in rows:x.update(bytes=(C/x['name']).stat().st_size,sha256=sha(C/x['name']))
 manifest.write_text(json.dumps(rows,indent=2))
p=subprocess.run([sys.executable,'-B',str(C/'test_v2.py')],cwd=C,capture_output=True,text=True,timeout=90)
with (R/('tests-'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(dict(command=[sys.executable,'-B',str(C/'test_v2.py')],manifestSHA256=sha(manifest),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),f,indent=2)
print(p.stdout,p.stderr);sys.exit(p.returncode)
