param([Parameter(Mandatory=$true)][string]$Run)
$ErrorActionPreference='Stop'
$code=$PSScriptRoot;$root=Join-Path $code $Run
if($Run -notmatch '^startup-[a-f0-9]{32}$' -or !(Test-Path -LiteralPath $root -PathType Container)){throw 'Exact prepared run required'}
$frozen=Get-Content -LiteralPath (Join-Path $code 'startup-source.json') -Raw|ConvertFrom-Json
foreach($x in $frozen){if((Get-FileHash -LiteralPath (Join-Path $code $x.name)).Hash -ne $x.sha256){throw ('Diagnostic source drift: '+$x.name)}}
$me=Get-Process -Id $PID;$created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString()
@{pid=$PID;created=$created;image=$me.Path}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher.json')
$etw=$null;$rc=$null;$closed=$false
try {
 $etw=Start-Process -FilePath (Join-Path $code 'J6StartupTrace.exe') -ArgumentList @($root,$PID,$created) -Verb RunAs -WindowStyle Hidden -PassThru
 $clock=[Diagnostics.Stopwatch]::StartNew()
 while(!(Test-Path -LiteralPath (Join-Path $root 'etw-ready.json'))){if($etw.HasExited -or $clock.Elapsed.TotalSeconds -gt 30){throw 'Kernel observer not ready'};Start-Sleep -Milliseconds 100}
 @{pid=$etw.Id;created=$etw.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=(Join-Path $code 'J6StartupTrace.exe')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'observer-identity.json')
 Write-Output ('KERNEL_READY '+$root)
 & 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B (Join-Path $code 'startup_driver.py') $Run
 $rc=$LASTEXITCODE
}catch{$_.ToString()|Set-Content -LiteralPath (Join-Path $root 'launcher-error.txt')}
finally{
 [IO.File]::WriteAllText((Join-Path $root 'etw-stop'),'bounded diagnostic producer stopped')
 if($etw){$clock=[Diagnostics.Stopwatch]::StartNew();$closed=$etw.WaitForExit(30000);@{exited=$closed;pid=$etw.Id;exitCode=$(if($closed){$etw.ExitCode}else{$null});shutdownWaitSeconds=$clock.Elapsed.TotalSeconds}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'observer-exit.json');$etw.Dispose()}
 @{driverExit=$rc;observerClosed=$closed;root=$root}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'launcher-result.json')
 Write-Output ('TRACE_ENDED '+$root)
}
if(!$closed -or $rc -ne 0){throw 'Diagnostic failure preserved; do not retry'}
