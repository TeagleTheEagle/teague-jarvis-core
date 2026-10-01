import pathlib,json,subprocess,sys,uuid,hashlib
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
run='queue-regression-'+uuid.uuid4().hex;(C/run/'temp').mkdir(parents=True)
commands=[['python-syntax',[sys.executable,'-B','-c',"import ast,pathlib; files="+repr([str(C/n) for n in ('dry_health.py','small_binding.py','small_check.py','small_coverage.py','traced_collect.py','test_small_binding.py')])+";[ast.parse(pathlib.Path(p).read_text(),filename=p) for p in files];print('6 Python syntax checks PASS')"]],['powershell-syntax',[pwsh,'-NoProfile','-Command',"$tok=$null;$err=$null;[void][Management.Automation.Language.Parser]::ParseFile('"+str(C/'small_launch.ps1')+"',[ref]$tok,[ref]$err);if($err){$err;exit 1};'PowerShell syntax PASS'"]],['monitor',[sys.executable,'-B',str(C/'run_focused.py')]],['queue',[pwsh,'-NoProfile','-File',str(C/'queue_regression.ps1'),'-Code',str(C),'-Run',run]],['finalization',[pwsh,'-NoProfile','-File',str(C/'test_finalization_gate.ps1')]]]
rows=[]
for name,args in commands:
 p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=C);out,err=p.communicate()
 row=dict(name=name,command=args,pid=p.pid,exit=p.returncode,stdout=out.decode(errors='replace'),stderr=err.decode(errors='replace'))
 with (R/(name+'.execution.json')).open('x') as f:json.dump(row,f,indent=2)
 rows.append(row);print(name,p.returncode,out.decode(errors='replace')[-600:],flush=True)
 if p.returncode:break
with (R/'regression-results.json').open('x') as f:json.dump(rows,f,indent=2)
sys.exit(any(x['exit'] for x in rows))
