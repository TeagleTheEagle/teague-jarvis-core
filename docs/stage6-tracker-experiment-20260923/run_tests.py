import pathlib,json,subprocess,shutil,uuid,ast
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code']);py=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
shutil.copy2(R/'test_tracker.py',C/'test_tracker.py')
for n in ('evidence_support.py','large_collect.py','test_tracker.py'):ast.parse((C/n).read_text())
p=subprocess.run([py,'-B',str(C/'test_tracker.py')],cwd=C,capture_output=True,text=True,timeout=60)
with (R/('tests-'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(dict(command=[py,'-B',str(C/'test_tracker.py')],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),f,indent=2)
print(p.stdout,p.stderr);raise SystemExit(p.returncode)
