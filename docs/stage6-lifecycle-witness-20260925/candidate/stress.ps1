$ErrorActionPreference='Stop'
$code=$PSScriptRoot;Set-Location -LiteralPath $code
if($code -notlike 'D:\JARVIS-STAGE6-LIVE\*\code'){throw 'Bounded D code required'}
if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)').Count){throw 'VirtualBox must remain closed'}
$run=Join-Path $code ('etw-stress-'+[guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory -Path (Join-Path $run 'temp'))
$env:TEMP=Join-Path $run 'temp';$env:TMP=$env:TEMP
$me=Get-Process -Id $PID
$identity=@{pid=$PID;creationFiletime=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$run}
$identity|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $run 'launcher.json')
$monitor=$null;$workExit=$null
try {
 $monitor=Start-Process -FilePath (Join-Path $code 'J6KernelTrace.exe') -ArgumentList @($run,$PID,$identity.creationFiletime) -Verb RunAs -WindowStyle Hidden -PassThru
 $end=[datetime]::UtcNow.AddSeconds(30)
 while(!(Test-Path -LiteralPath (Join-Path $run 'etw-ready.json'))){if($monitor.HasExited -or [datetime]::UtcNow -gt $end){throw 'ETW did not become ready'};Start-Sleep -Milliseconds 100}
 & 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B (Join-Path $code 'stress.py') $run 1> (Join-Path $run 'work.stdout') 2> (Join-Path $run 'work.stderr')
 $workExit=$LASTEXITCODE
} catch { $_.ToString()|Set-Content -LiteralPath (Join-Path $run 'launcher-error.txt') }
finally {
 [IO.File]::WriteAllText((Join-Path $run 'etw-stop'),'diagnostic completion')
 if($monitor){$exited=$monitor.WaitForExit(30000);@{pid=$monitor.Id;exited=$exited;exitCode=$(if($exited){$monitor.ExitCode}else{$null});workExit=$workExit}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $run 'launcher-result.json');$monitor.Dispose()}
 Write-Output $run
}
