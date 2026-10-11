import pathlib,json,hashlib,subprocess,sys,ast,uuid
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
run=R/('focused-'+uuid.uuid4().hex);run.mkdir()
def execute(command,timeout=90):
 p=subprocess.run(command,cwd=C,capture_output=True,text=True,timeout=timeout)
 path=run/(str(len(list(run.glob('command-*.json')))+1).join(['command-','.json']))
 with path.open('x') as f:json.dump(dict(command=command,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),f,indent=2)
 print(p.stdout,p.stderr);assert p.returncode==0,str(path)
execute([sys.executable,'-B',str(C/'test_coordination_v3.py')])
sys.path.insert(0,str(C));from test_coordination_v3 import fixture
fp=run/'fixture.json';fp.write_text(json.dumps(fixture()))
pwsh=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
execute([pwsh,'-NoProfile','-File',str(R/'test_terminal_control_v3.ps1'),'-Candidate',str(C),'-Fixture',str(fp)])
names=['coordination_v3.py','evidence_support_v3.py','small_binding_v3.py','large_collect_v3.py','traced_collect_v3.py','traced_collect.py','tracker_adapter_v3.py','support_verifier_v3.py','completed_v3.py','small_check_v3.py','small_finalize_v3.py','external_driver_v3.py','test_coordination_v3.py']
for name in names:ast.parse((C/name).read_text(),filename=str(C/name))
ps=run/'syntax.ps1';ps.write_text("$ErrorActionPreference='Stop'\n$files=@("+','.join("'"+str(C/n)+"'" for n in ('small_launch_v3.ps1','terminal_control_v3.ps1'))+")\nforeach($file in $files){$tokens=$null;$errors=$null;[void][Management.Automation.Language.Parser]::ParseFile($file,[ref]$tokens,[ref]$errors);if($errors.Count){$errors|Out-String|Write-Output;throw 'Syntax failure'}}\n'SYNTAX_PASS'\n")
execute([pwsh,'-NoProfile','-File',str(ps)])
# Existing actual authority/coverage/stream rejection tests, no live producer.
execute([sys.executable,'-B','-m','unittest','test_v2.Authority','test_v2.Adapter','test_v2.Finalizer','test_journal'])
with (run/'result.json').open('x') as f:json.dump(dict(status='PASS',pythonSyntaxFiles=names,powershellSyntaxFiles=['small_launch_v3.ps1','terminal_control_v3.ps1'],liveQualification=False),f,indent=2)
print('FOCUSED_RESULT '+str(run))
