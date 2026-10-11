"""Offline regression selection only; no live tracker/observer/probe campaign."""
import pathlib,json,subprocess,sys,uuid,shutil,os
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate']);O=R/('regressions-'+uuid.uuid4().hex);O.mkdir()
legacy=O/'preservation';legacy.mkdir()
for n in ('test_failure_preserve_v1.py','failure_preserve_v1.py','one_run_v1.py','policy.json'):shutil.copy2(R.parent/'stage6-workspace-binding-v4-20260923'/n,legacy/n)
env=os.environ.copy();temp=C/('offline-temp-'+uuid.uuid4().hex);temp.mkdir();env['TEMP']=env['TMP']=str(temp)
ps="""$ErrorActionPreference='Stop';$files=@('small_launch_v4.ps1','terminal_control_v3.ps1','timed_monitor.ps1','runtime_scope_v4.ps1','candidate_dll_v4.ps1');foreach($n in $files){$t=$null;$e=$null;[void][Management.Automation.Language.Parser]::ParseFile((Join-Path $PWD $n),[ref]$t,[ref]$e);if($e.Count){throw ($e|Out-String)}};@{status='PASS';files=$files;executed=$false}|ConvertTo-Json -Compress"""
steps=[('authority-adapter-finalizer',[sys.executable,'-B','-m','unittest','-v','test_v2.Authority','test_v2.Adapter','test_v2.Finalizer'],C),('local-image',[sys.executable,'-B','-m','unittest','-v','test_tracker.Capture'],C),('journal',[sys.executable,'-B',str(C/'test_journal.py')],C),('telemetry',[sys.executable,'-B',str(R.parent/'stage6-loss-telemetry-v2-20260923/test_diagnostic.py')],R),('failure-preservation',[sys.executable,'-B',str(legacy/'test_failure_preserve_v1.py')],legacy),('powershell-syntax',[r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe','-NoProfile','-Command',ps],C)]
for label,args,cwd in steps:
 p=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,timeout=240)
 with (O/(label+'.json')).open('x') as f:json.dump(dict(command=args,cwd=str(cwd),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,offline=True),f,indent=2)
 print(label,p.returncode,p.stdout,p.stderr,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
print('EVIDENCE',O)
