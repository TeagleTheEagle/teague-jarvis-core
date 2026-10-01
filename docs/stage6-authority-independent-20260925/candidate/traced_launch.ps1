param([Parameter(Mandatory=$true)][string]$Source,[ValidateSet('normal','hash-start-failure')][string]$Case='normal')
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');Assert-LiveCode;Set-Location -LiteralPath $PSScriptRoot
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox|J6KernelTrace|J6StartupTrace|J6Probe)').Count){throw 'Relevant process still active; preflight blocked'}
$py='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$frozen=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'run-source.json') -Raw|ConvertFrom-Json
foreach($x in $frozen){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $x.name)).Hash -ne $x.sha256){throw ('Source drift: '+$x.name)}}
$root=& $py -B (Join-Path $PSScriptRoot 'baseline_contract.py') prepare $Source
if($LASTEXITCODE -ne 0){throw 'Preflight contract/source failed before observers'}
$Run=Split-Path $root -Leaf;Set-LiveTemp $root
$me=Get-Process -Id $PID;$identity=@{pid=$PID;creationFiletime=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$root}
$identity|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher.json')
$marks=[Collections.Generic.List[object]]::new()
function Mark([string]$event,[object]$detail){$marks.Add(@{event=$event;pid=$PID;created=$identity.creationFiletime;qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;detail=$detail})}
Mark 'LAUNCHER_ENTRY' @{case=$Case}
$etw=$null;$app=$null;$workExit=$null;$appExited=$false;$etwExited=$false
function Ready($p,$name){$end=[Diagnostics.Stopwatch]::StartNew();while(!(Test-Path -LiteralPath (Join-Path $root $name))){if($p.HasExited -or $end.Elapsed.TotalSeconds -gt 30){throw ('Observer not ready: '+$name)};Start-Sleep -Milliseconds 100}}
try {
 & $py -B (Join-Path $PSScriptRoot 'volume_map.py') $root
 if($LASTEXITCODE -ne 0){throw 'Volume map failed'}
 $frozen|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'source-hashes.json')
 Mark 'HELPER_INVOCATION' 'kernel-tracer'
 $etw=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6StartupTrace.exe') -ArgumentList @($root,$PID,$identity.creationFiletime) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $etw 'etw-ready.json';Mark 'HELPER_CREATED' @{role='kernel-tracer';pid=$etw.Id};Write-Output ('KERNEL_READY '+$root)
 $gateClock=[Diagnostics.Stopwatch]::StartNew()
 while(!(Test-Path -LiteralPath (Join-Path $root 'allow-app-prompt'))){if($etw.HasExited -or $gateClock.Elapsed.TotalSeconds -gt 120){throw 'Second observer prompt gate expired'};Start-Sleep -Milliseconds 100}
 Mark 'HELPER_INVOCATION' 'application-observer'
 $app=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'timed_monitor.ps1'),'-Run',$Run,'-KernelPid',$etw.Id) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $app 'app-ready.json';Mark 'HELPER_CREATED' @{role='application-observer';pid=$app.Id};Ready $app 'app-health.json'
 @{etw=@{pid=$etw.Id;created=$etw.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $PSScriptRoot 'J6StartupTrace.exe')};app=@{pid=$app.Id;created=$app.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$pwsh}}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $root 'observer-identities.json')
 & $py -B (Join-Path $PSScriptRoot 'baseline_contract.py') ready $Run
 if($LASTEXITCODE -ne 0){throw 'Ready transition failed'}
 Mark 'HELPER_INVOCATION' 'collector'
 Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
public static class J6OwnChild { [DllImport("D:\\JARVIS-STAGE6-LIVE\\f469b94b665e4808af1c5bb6aa46b207\\code\\J6OwnedEntry.dll",CharSet=CharSet.Unicode)] public static extern int RunCollector(string root,string mode); }
'@
 $global:LASTEXITCODE=[J6OwnChild]::RunCollector($root,$Case)
 $workExit=$LASTEXITCODE;Mark 'HELPER_RETURN' @{role='collector';exitCode=$workExit}
}catch{Mark 'EXCEPTION' @{type=$_.Exception.GetType().FullName};$_.ToString()|Set-Content -LiteralPath (Join-Path $root 'launcher-error.txt')}
finally {
 [IO.File]::WriteAllText((Join-Path $root 'app-stop'),'producer returned; reconcile actual lifecycle before acceptance')
 if($app){$appExited=$app.WaitForExit(60000);@{pid=$app.Id;exited=$appExited;exitCode=$(if($appExited){$app.ExitCode}else{$null})}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'app-exit.json');$app.Dispose()}
 [IO.File]::WriteAllText((Join-Path $root 'etw-stop'),'independent application observer closed')
 if($etw){$etwExited=$etw.WaitForExit(30000);@{pid=$etw.Id;exited=$etwExited;exitCode=$(if($etwExited){$etw.ExitCode}else{$null});workExit=$workExit}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher-result.json');$etw.Dispose()}
 Mark 'FINAL_SHUTDOWN' @{appExited=$appExited;etwExited=$etwExited;workExit=$workExit}
 $marks|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $root 'integration-launcher.json')
 Write-Output $root
}
if(!$appExited -or !$etwExited -or $workExit -ne 0){throw 'Primary/observer failure preserved; no acceptance finalization'}
& $py -B (Join-Path $PSScriptRoot 'baseline_contract.py') closed $Run
if($LASTEXITCODE -ne 0){throw 'Lifecycle closure transition failed'}
Write-Output ('OBSERVERS_CLOSED_PENDING_INDEPENDENT_REVIEW '+$root)
