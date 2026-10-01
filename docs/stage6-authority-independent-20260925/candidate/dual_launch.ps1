param([switch]$CheckCleanup)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');Assert-LiveCode;Set-Location -LiteralPath $PSScriptRoot
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)').Count){throw 'VirtualBox must remain closed'}
$Run='dual-'+[guid]::NewGuid().ToString('N');$root=Join-Path $PSScriptRoot $Run
New-Item -ItemType Directory -Path (Join-Path $root 'temp')|Out-Null;Set-LiveTemp $root
$me=Get-Process -Id $PID;$identity=@{pid=$PID;creationFiletime=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$root}
$identity|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher.json')
$etw=$null;$app=$null;$workExit=$null;$pwsh='C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
function Ready($p,$name){$end=[datetime]::UtcNow.AddSeconds(30);while(!(Test-Path -LiteralPath (Join-Path $root $name))){if($p.HasExited -or [datetime]::UtcNow -gt $end){throw ('Observer not ready: '+$name)};Start-Sleep -Milliseconds 100}}
try {
 & 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B (Join-Path $PSScriptRoot 'volume_map.py') $root
 if($LASTEXITCODE -ne 0){throw 'Volume mapping failed'}
 $etw=Start-Process -FilePath (Join-Path $PSScriptRoot 'J6KernelTrace.exe') -ArgumentList @($root,$PID,$identity.creationFiletime) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $etw 'etw-ready.json'
 $app=Start-Process -FilePath $pwsh -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'app_monitor.ps1'),'-Run',$Run) -Verb RunAs -WindowStyle Hidden -PassThru
 Ready $app 'app-ready.json'
 @{etw=@{pid=$etw.Id;created=$etw.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $PSScriptRoot 'J6KernelTrace.exe')};app=@{pid=$app.Id;created=$app.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$pwsh}}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $root 'observer-identities.json')
 @(Get-ChildItem -LiteralPath $PSScriptRoot -File|Where-Object Extension -in '.py','.ps1','.cs','.cpp','.exe'|ForEach-Object {@{name=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'source-hashes.json')
 & 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B (Join-Path $PSScriptRoot 'stress.py') $root 1> (Join-Path $root 'work.stdout') 2> (Join-Path $root 'work.stderr')
 $workExit=$LASTEXITCODE
}catch{$_.ToString()|Set-Content -LiteralPath (Join-Path $root 'launcher-error.txt')}
finally {
 [IO.File]::WriteAllText((Join-Path $root 'app-stop'),'producer stopped')
 if($app){$appExited=$app.WaitForExit(60000);@{pid=$app.Id;exited=$appExited;exitCode=$(if($appExited){$app.ExitCode}else{$null})}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'app-exit.json');$app.Dispose()}
 [IO.File]::WriteAllText((Join-Path $root 'etw-stop'),'independent app observer finished')
 if($etw){$etwExited=$etw.WaitForExit(30000);@{pid=$etw.Id;exited=$etwExited;exitCode=$(if($etwExited){$etw.ExitCode}else{$null});workExit=$workExit}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher-result.json');$etw.Dispose()}
 Write-Output $root
}
if($CheckCleanup){
 & 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B (Join-Path $PSScriptRoot 'cleanup_checker.py') $root
 $cleanupExit=$LASTEXITCODE
 @{cleanupExit=$cleanupExit;producerExit=$workExit;acceptance=$false;scope='sacrificial dual-evidence cleanup only'}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'checker-exit.json')
 if($cleanupExit -ne 0 -or $workExit -ne 0){exit 1}
}
