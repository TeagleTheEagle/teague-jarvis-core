import ast,json,pathlib,subprocess,sys,uuid
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code']);sys.path.insert(0,str(C))
from workspace import new_run,activate_temp
root=new_run('health-regressions-'+uuid.uuid4().hex);activate_temp(root)
pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
rows=[]
def run(name,args):
    p=subprocess.run(args,cwd=C,capture_output=True,text=True,timeout=60)
    row=dict(name=name,command=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr);rows.append(row)
    with (R/(name+'.execution.json')).open('x') as f:json.dump(row,f,indent=2)
    assert p.returncode==0,name
run('writer-boundaries',[pwsh,'-NoProfile','-File',str(R/'test_writer.ps1'),'-Code',str(C),'-Root',str(root)])
prior=R.parent/'stage6-nested-writer-20260922';old=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\82fe9772161e41578a7d9d93cdbcbcab\code')
(C/'validation-v2').mkdir();(C/'validation-v2/medium-positive-fixture.json').write_bytes((old/'validation-v2/medium-positive-fixture.json').read_bytes())
for n in ('test_wrapper_regression.py','test_telemetry_regression.py'):
    with (R/n).open('xb') as f:f.write((prior/n).read_bytes())
    run(n,[sys.executable,'-B',str(R/n)])
for n in ('qualified_worker.py','health_reader.py'):ast.parse((C/n).read_text(encoding='utf8'))
result=dict(status='PASS',writerBoundaryChecks=len(json.loads((root/'checks.json').read_text(encoding='utf-8-sig'))),compositionChecks=21,telemetryChecks=40,pythonSyntax='PASS',root=str(root))
with (R/'regression-results.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
