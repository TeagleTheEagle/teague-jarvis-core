"""Install only reviewed TEST integration artifacts into the fresh small workspace."""
import pathlib,json,hashlib,subprocess,difflib
R=pathlib.Path(__file__).parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(R/'plan.json');C=pathlib.Path(plan['code']);S=pathlib.Path('D:/JARVIS-STAGE6-LIVE/68b6e62890e742b4bedb13cbb0f49e92/code')
for name in ('integration_marks.py','traced_collect.py','traced_hash_worker.py'):(C/name).write_bytes((R/name).read_bytes())
launch=(C/'large_launch.ps1').read_text()
launch=launch.replace('[string]$Source)',"[string]$Source,[ValidateSet('normal','hash-start-failure')][string]$Case='normal')")
launch=launch.replace('J6BaselineTrace','J6StartupTrace')
launch=launch.replace("(Join-Path $PSScriptRoot 'large_collect.py') $Run", "(Join-Path $PSScriptRoot 'traced_collect.py') $Run $Case")
anchor="$etw=$null;$app=$null;"
mark="""$marks=[Collections.Generic.List[object]]::new()
function Mark([string]$event,[object]$detail){$marks.Add(@{event=$event;pid=$PID;created=$identity.creationFiletime;qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;detail=$detail})}
Mark 'LAUNCHER_ENTRY' @{case=$Case}
"""
launch=launch.replace(anchor,mark+anchor)
launch=launch.replace(' $etw=Start-Process'," Mark 'HELPER_INVOCATION' 'kernel-tracer'\n $etw=Start-Process")
launch=launch.replace(" Ready $etw 'etw-ready.json';", " Ready $etw 'etw-ready.json';Mark 'HELPER_CREATED' @{role='kernel-tracer';pid=$etw.Id};")
launch=launch.replace(' $app=Start-Process'," Mark 'HELPER_INVOCATION' 'application-observer'\n $app=Start-Process")
launch=launch.replace(" Ready $app 'app-ready.json';", " Ready $app 'app-ready.json';Mark 'HELPER_CREATED' @{role='application-observer';pid=$app.Id};")
launch=launch.replace(" & $py -B (Join-Path $PSScriptRoot 'traced_collect.py')", " Mark 'HELPER_INVOCATION' 'collector'\n & $py -B (Join-Path $PSScriptRoot 'traced_collect.py')")
launch=launch.replace(' $workExit=$LASTEXITCODE'," $workExit=$LASTEXITCODE;Mark 'HELPER_RETURN' @{role='collector';exitCode=$workExit}")
launch=launch.replace('}catch{$_.ToString()',"}catch{Mark 'EXCEPTION' @{type=$_.Exception.GetType().FullName};$_.ToString()")
launch=launch.replace(' Write-Output $root'," Mark 'FINAL_SHUTDOWN' @{appExited=$appExited;etwExited=$etwExited;workExit=$workExit}\n $marks|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $root 'integration-launcher.json')\n Write-Output $root")
(C/'traced_launch.ps1').write_text(launch)
native=(S/'startup_trace.cpp').read_text()
old=next(x for x in native.splitlines() if x.startswith('static Row* Target'))
new='static Row* Target(DWORD pid,LONGLONG q){for(auto& a:rows){auto&r=a.second;if(r.pid==pid&&q>=r.start&&(!r.stop||q<=r.stop))return &r;}return nullptr;}'
assert native.count(old)==1
native=native.replace(old,new)
(C/'startup_trace.cpp').write_text(native)
# Same validated compiler options; only new output paths and the descendant filter differ.
build=read(R.parent/'stage6-internal-startup-trace-20260921/followup-build.json')[1]['args']
args=[a.replace(str(S),str(C)) for a in build]
result=subprocess.run(args,cwd=C,capture_output=True,text=True)
(R/'build.json').write_text(json.dumps(dict(args=args,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr),indent=2))
assert result.returncode==0,result.stdout+result.stderr
names={x['name'] for x in plan['preChangeHashes']}|{'startup_trace.cpp','J6StartupTrace.exe','integration_marks.py','traced_collect.py','traced_hash_worker.py','traced_launch.ps1'}
hashes=[dict(name=n,sha256=sha(C/n)) for n in sorted(names)]
(C/'run-source.json').write_text(json.dumps(hashes,indent=2));(R/'candidate-hashes.json').write_text(json.dumps(hashes,indent=2))
diffs={}
for n,original in [('traced_launch.ps1',C/'large_launch.ps1'),('startup_trace.cpp',S/'startup_trace.cpp')]:
 diffs[n]=''.join(difflib.unified_diff(original.read_text().splitlines(True),(C/n).read_text().splitlines(True),fromfile=str(original),tofile=str(C/n)))
(R/'integration.diff').write_text('\n'.join(diffs.values()))
print(json.dumps(dict(code=str(C),hashes=len(hashes),build=result.returncode,changed=['baseline-allowlist.json','baseline-limits.json','startup_trace.cpp','J6StartupTrace.exe'],added=['integration_marks.py','traced_collect.py','traced_hash_worker.py','traced_launch.ps1'])))
