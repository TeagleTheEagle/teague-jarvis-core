param([ValidateSet('miniature','dry1')][string]$Scenario='miniature')
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');Assert-LiveCode;Set-Location -LiteralPath $PSScriptRoot
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox|J6KernelTrace|J6Probe)').Count){throw 'Relevant process still active; preflight blocked'}
$py='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$frozen=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'integration-source.json') -Raw|ConvertFrom-Json
foreach($x in $frozen){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $x.name)).Hash -ne $x.sha256){throw ('Source drift: '+$x.name)}}
$root=& $py -B (Join-Path $PSScriptRoot 'dry_contract.py') prepare $Scenario
if($LASTEXITCODE -ne 0){throw 'Preflight contract/source failed before observers'}
$Run=Split-Path $root -Leaf;Set-LiveTemp $root
$me=Get-Process -Id $PID;$identity=@{pid=$PID;creationFiletime=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$root}
$identity|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher.json')
$etw=$null;$app=$null;$workExit=$null;$appExited=$false;$etwExited=$false
function Ready($p,$name){$end=[Diagnostics.Stopwatch]::StartNew();while(!(Test-Path -LiteralPath (Join-Path $root $name))){if($p.HasExited -or $end.Elapsed.TotalSeconds -gt 30){throw ('Observer not ready: '+$name)};Start-Sleep -Milliseconds 100}}
try {
 & $py -B (Join-Path $PSScriptRoot 'volume_map.py') $root
 if($LASTEXITCODE -ne 0){throw 'Volume map failed'}
 $frozen|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'source-hashes.json')
 $etw=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6KernelTrace.exe') -ArgumentList @($root,$PID,$identity.creationFiletime) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $etw 'etw-ready.json'
 $app=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'app_monitor.ps1'),'-Run',$Run) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $app 'app-ready.json';Ready $app 'app-health.json'
 @{etw=@{pid=$etw.Id;created=$etw.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $PSScriptRoot 'J6KernelTrace.exe')};app=@{pid=$app.Id;created=$app.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$pwsh}}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $root 'observer-identities.json')
 & $py -B (Join-Path $PSScriptRoot 'dry_contract.py') ready $Run
 if($LASTEXITCODE -ne 0){throw 'Ready transition failed'}
 & $py -B (Join-Path $PSScriptRoot 'dry_collect.py') $Run 1> (Join-Path $root 'work.stdout') 2> (Join-Path $root 'work.stderr')
 $workExit=$LASTEXITCODE
}catch{$_.ToString()|Set-Content -LiteralPath (Join-Path $root 'launcher-error.txt')}
finally {
 [IO.File]::WriteAllText((Join-Path $root 'app-stop'),'producer returned; reconcile actual lifecycle before acceptance')
 if($app){$appExited=$app.WaitForExit(60000);@{pid=$app.Id;exited=$appExited;exitCode=$(if($appExited){$app.ExitCode}else{$null})}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'app-exit.json');$app.Dispose()}
 [IO.File]::WriteAllText((Join-Path $root 'etw-stop'),'independent application observer closed')
 if($etw){$etwExited=$etw.WaitForExit(30000);@{pid=$etw.Id;exited=$etwExited;exitCode=$(if($etwExited){$etw.ExitCode}else{$null});workExit=$workExit}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher-result.json');$etw.Dispose()}
 Write-Output $root
}
if(!$appExited -or !$etwExited -or $workExit -ne 0){throw 'Primary/observer failure preserved; no acceptance finalization'}
& $py -B (Join-Path $PSScriptRoot 'dry_contract.py') closed $Run
if($LASTEXITCODE -ne 0){throw 'Lifecycle closure transition failed'}
& $py -B (Join-Path $PSScriptRoot 'dry_finalize.py') $Run
if($LASTEXITCODE -ne 0){throw 'Finalization failed; evidence preserved'}
