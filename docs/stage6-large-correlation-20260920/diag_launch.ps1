param([ValidateSet('ladder','heartbeat')][string]$Mode)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');Assert-LiveCode;Set-Location -LiteralPath $PSScriptRoot
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox|J6Probe|J6KernelTrace|J6BaselineTrace)').Count){throw 'Relevant processes active'}
foreach($x in (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'diagnostic-hashes.json') -Raw|ConvertFrom-Json)){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $x.name)).Hash -ne $x.sha256){throw 'Diagnostic source drift'}}
$Run='correlation-'+$Mode+'-'+[guid]::NewGuid().ToString('N');$root=Join-Path $PSScriptRoot $Run
New-Item -ItemType Directory -Path (Join-Path $root 'temp')|Out-Null;Set-LiveTemp $root
$me=Get-Process -Id $PID;$identity=@{pid=$PID;creationFiletime=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$root};$identity|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher.json')
$py='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe';$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$etw=$null;$app=$null;$workExit=$null;$appExited=$false;$etwExited=$false
function Ready($p,$name){$clock=[Diagnostics.Stopwatch]::StartNew();while(!(Test-Path -LiteralPath (Join-Path $root $name))){if($p.HasExited -or $clock.Elapsed.TotalSeconds -gt 30){throw ('Observer not ready '+$name)};Start-Sleep -Milliseconds 100}}
try {
 & $py -B (Join-Path $PSScriptRoot 'volume_map.py') $root
 if($LASTEXITCODE -ne 0){throw 'Volume map failed'}
 $etw=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6BaselineTrace.exe') -ArgumentList @($root,$PID,$identity.creationFiletime) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $etw 'etw-ready.json';Write-Output ('KERNEL_READY '+$root)
 # Non-elevated fixed gate only paces the second owner prompt; it contains no commands.
 $gateClock=[Diagnostics.Stopwatch]::StartNew()
 while(!(Test-Path -LiteralPath (Join-Path $root 'allow-app-prompt'))){if($etw.HasExited -or $gateClock.Elapsed.TotalSeconds -gt 120){throw 'Second prompt gate expired'};Start-Sleep -Milliseconds 100}
 $app=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'baseline_monitor.ps1'),'-Run',$Run,'-KernelPid',$etw.Id) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $app 'app-ready.json';Ready $app 'app-health.json'
 @{etw=@{pid=$etw.Id;created=$etw.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $PSScriptRoot 'J6BaselineTrace.exe')};app=@{pid=$app.Id;created=$app.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$pwsh}}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $root 'observer-identities.json')
 & $py -B (Join-Path $PSScriptRoot 'diag_collect.py') $Run $Mode 1> (Join-Path $root 'work.stdout') 2> (Join-Path $root 'work.stderr');$workExit=$LASTEXITCODE
}catch{$_.ToString()|Set-Content -LiteralPath (Join-Path $root 'launcher-error.txt')}
finally {
 [IO.File]::WriteAllText((Join-Path $root 'app-stop'),'diagnostic producer returned')
 if($app){$appExited=$app.WaitForExit(60000);@{pid=$app.Id;exited=$appExited;exitCode=$(if($appExited){$app.ExitCode}else{$null})}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'app-exit.json');$app.Dispose()}
 [IO.File]::WriteAllText((Join-Path $root 'etw-stop'),'diagnostic app observer closed')
 if($etw){$etwExited=$etw.WaitForExit(30000);@{pid=$etw.Id;exited=$etwExited;exitCode=$(if($etwExited){$etw.ExitCode}else{$null});workExit=$workExit}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher-result.json');$etw.Dispose()}
 Write-Output $root
}
if(!$appExited -or !$etwExited -or $workExit -ne 0){exit 1}
