import pathlib,json,hashlib,subprocess,os
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
cal=json.loads((R/'calibration.json').read_text())
assert cal['campaignSeconds']<=3600 and cal['monitorSeconds']<=3720
def put(n,s):
 with (C/n).open('x',encoding='utf-8') as f:f.write(s)
for n in ('baseline_contract.py','baseline_hash_worker.py','test_baseline.py'):put(n,(R/n).read_text())
put('baseline-allowlist.json',json.dumps(dict(realProtectedAccess=False,approvedProtectedRoots=[],syntheticRoots=[cal['source']]),indent=2))
put('baseline-limits.json',json.dumps(dict(campaign=cal['campaignSeconds'],monitor=cal['monitorSeconds'],hold=cal['longRunTargetSeconds'],heartbeat=10.0,probe=13.6,observer=15.0),indent=2))
# Separate adapters retain all existing lifecycle checks; original sources stay unchanged.
s=(C/'dry_collect.py').read_text().replace('from dry_contract import','from baseline_contract import').replace('CODE/\'dry_hash_worker.py\'','CODE/\'baseline_hash_worker.py\'').replace('frequency()+90',"frequency()+contract['thresholds']['campaign']").replace("producer='dry_collect.py'","producer='baseline_collect.py'")
put('baseline_collect.py',s)
s=(C/'dry_finalize.py').read_text().replace('from dry_contract import','from baseline_contract import')
s=s.replace("manifest=dict(synthetic=True", "manifest=dict(mode='protected_baseline',captureUtc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),limitation='No proof of pre-incident byte identity for artifacts lacking historical hashes',synthetic=contract['synthetic']")
s=s.replace('protectedAccess=False',"protectedAccess=not contract['synthetic']")
s=s.replace("'MINIATURE_INTEGRATION_PASS' if contract['scenario']=='miniature' else 'DRY_RUN_1_PASS'","'SYNTHETIC_PROTECTED_MODE_PASS'")
put('baseline_finalize.py',s)
s=(C/'dry_launch.ps1').read_text().replace("param([ValidateSet('miniature','dry1')][string]$Scenario='miniature')","param([Parameter(Mandatory=$true)][string]$Source)")
s=s.replace('integration-source.json','baseline-source.json').replace('dry_contract.py','baseline_contract.py').replace('prepare $Scenario','prepare $Source').replace('dry_collect.py','baseline_collect.py').replace('dry_finalize.py','baseline_finalize.py').replace('app_monitor.ps1','baseline_monitor.ps1').replace('J6KernelTrace.exe','J6BaselineTrace.exe')
s=s.replace('J6KernelTrace|J6Probe','J6KernelTrace|J6BaselineTrace|J6Probe')
s=s.replace("'-Run',$Run)","'-Run',$Run,'-KernelPid',$etw.Id)")
# Safety failure on VirtualBox, observer identity and unchanged completion protocol remain intact.
put('baseline_launch.ps1',s)
s=(C/'app_monitor.ps1').read_text().replace('param([string]$Run)','param([string]$Run,[int]$KernelPid)');s=s.replace('while($clock.Elapsed.TotalSeconds -lt 180)',f"while($clock.Elapsed.TotalSeconds -lt {cal['monitorSeconds']})").replace('if($clock.Elapsed.TotalSeconds -ge 180)',f"if($clock.Elapsed.TotalSeconds -ge {cal['monitorSeconds']})")
s=s.replace('$receipts=[Collections.Generic.List[object]]::new();', '$resources=[Collections.Generic.List[object]]::new();$receipts=[Collections.Generic.List[object]]::new();')
s=s.replace("Save 'app-health.json'", "$rp=[Diagnostics.Process]::GetCurrentProcess();$rp.Refresh();$kp=[Diagnostics.Process]::GetProcessById($KernelPid);$kp.Refresh();$resources.Add(@{seconds=$clock.Elapsed.TotalSeconds;privateBytes=$rp.PrivateMemorySize64;workingSet=$rp.WorkingSet64;handles=$rp.HandleCount;queueDepth=$exact.Stats().remaining;events=$exact.Stats().persisted;threads=$rp.Threads.Count;kernelPrivateBytes=$kp.PrivateMemorySize64;kernelHandles=$kp.HandleCount;eventBytes=([IO.FileInfo]::new((Join-Path $root 'app-events.jsonl'))).Length});$rp.Dispose();$kp.Dispose()\n  Save 'app-health.json'")
s=s.replace("Save 'app-receipts.json'", "Save 'monitor-resources.json' @($resources.ToArray())\n Save 'app-receipts.json'")
put('baseline_monitor.ps1',s)
s=(C/'kernel_trace.cpp').read_text();assert s.count('static_cast<double>(freq.QuadPart)<180')==1
s=s.replace('static_cast<double>(freq.QuadPart)<180',f"static_cast<double>(freq.QuadPart)<{cal['monitorSeconds']}")
put('baseline_kernel_trace.cpp',s)
vc=pathlib.Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207');sdk=pathlib.Path(r'C:\Program Files (x86)\Windows Kits\10')
args=[str(vc/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/W4',str(C/'baseline_kernel_trace.cpp'),'/I'+str(vc/'include')]
args+=['/I'+str(sdk/'Include/10.0.26100.0'/x) for x in ('um','shared','ucrt')]
args+=['/Fo'+str(C/'baseline_kernel_trace.obj'),'/Fe'+str(C/'J6BaselineTrace.exe'),'/link','/LIBPATH:'+str(vc/'lib/x64')]
args+=['/LIBPATH:'+str(sdk/'Lib/10.0.26100.0'/x/'x64') for x in ('um','ucrt')];args+=['tdh.lib','advapi32.lib','ole32.lib']
env=dict(os.environ,TEMP=str(C/'build-temp'),TMP=str(C/'build-temp'));(C/'build-temp').mkdir()
q=subprocess.run(args,cwd=C,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
with (R/'build.json').open('x') as f:json.dump(dict(command=args,exit=q.returncode,output=q.stdout),f,indent=2)
print(q.stdout);raise SystemExit(q.returncode)
