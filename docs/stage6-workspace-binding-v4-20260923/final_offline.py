"""Only syntax, load-without-invocation, and offline unittest execution."""
import json,pathlib,subprocess,sys,uuid,shutil,os
R=pathlib.Path(__file__).parent
C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
PWSH=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
O=R/('verification-'+uuid.uuid4().hex);O.mkdir()
TEMP=C/('offline-load-'+uuid.uuid4().hex);TEMP.mkdir()
env=os.environ.copy();env['TEMP']=env['TMP']=str(TEMP)
ps=r'''$ErrorActionPreference='Stop'
$files=@('small_launch_v4.ps1','candidate_dll_v4.ps1','runtime_scope_v4.ps1','timed_monitor.ps1')
foreach($name in $files){$tokens=$null;$errors=$null;[void][Management.Automation.Language.Parser]::ParseFile((Join-Path $PWD $name),[ref]$tokens,[ref]$errors);if($errors.Count){throw ($errors|Out-String)}}
. (Join-Path $PWD 'runtime_scope_v4.ps1')
Set-J6RuntimeScope
. (Join-Path $PWD 'candidate_dll_v4.ps1')
Initialize-J6CandidateBridge
@{syntaxFiles=$files;dllLoadOnly='PASS';collectorInvoked=$false;runtimeModule=(Get-Module CimCmdlets).Path;temp=$env:TEMP}|ConvertTo-Json -Compress
'''
reg=O/'preservation-original';reg.mkdir()
for n in ('failure_preserve_v1.py','one_run_v1.py','policy.json','test_failure_preserve_v1.py'):shutil.copy2(R/n,reg/n)
steps=[('powershell-syntax-dll-load',[PWSH,'-NoProfile','-Command',ps],C),
       ('coordination',[sys.executable,'-B',str(C/'test_coordination_v3.py')],C),
       ('telemetry',[sys.executable,'-B',str(R.parent/'stage6-loss-telemetry-v2-20260923/test_diagnostic.py')],R),
       ('preservation-original',[sys.executable,'-B',str(reg/'test_failure_preserve_v1.py')],reg)]
for label,args,cwd in steps:
 p=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,timeout=240)
 (O/(label+'.json')).write_text(json.dumps(dict(args=args,cwd=str(cwd),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,liveRun=False),indent=2))
 print(label,p.returncode,p.stdout,p.stderr,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
print('FINAL_OFFLINE_REPORT '+str(O))
