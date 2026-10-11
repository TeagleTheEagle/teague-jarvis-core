$ErrorActionPreference='Stop'
$code='D:\JARVIS-STAGE6-LIVE\991e246fb08b45a3904e4cadfa8f4e99\code'
$run=Join-Path $code ('etw-smoke-'+[guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory -Path $run)
[void](New-Item -ItemType Directory -Path (Join-Path $run 'temp'))
$env:TEMP=Join-Path $run 'temp';$env:TMP=$env:TEMP
$me=Get-Process -Id $PID
$identity=@{pid=$PID;creationFiletime=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;run=$run}
$identity|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $run 'launcher.json')
$monitor=$null
try {
 $monitor=Start-Process -FilePath (Join-Path $code 'J6KernelTrace.exe') -ArgumentList @($run,$PID,$identity.creationFiletime) -Verb RunAs -WindowStyle Hidden -PassThru
 $end=[datetime]::UtcNow.AddSeconds(30)
 while(!(Test-Path -LiteralPath (Join-Path $run 'etw-ready.json'))){if($monitor.HasExited -or [datetime]::UtcNow -gt $end){throw 'ETW did not become ready'};Start-Sleep -Milliseconds 100}
 & 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B (Join-Path $code 'smoke.py') $run 1> (Join-Path $run 'work.stdout') 2> (Join-Path $run 'work.stderr')
 $workExit=$LASTEXITCODE
} catch { $_.ToString()|Set-Content -LiteralPath (Join-Path $run 'launcher-error.txt') }
finally {
 [IO.File]::WriteAllText((Join-Path $run 'etw-stop'),'diagnostic completion')
 if($monitor){$exited=$monitor.WaitForExit(30000);@{pid=$monitor.Id;exited=$exited;exitCode=$(if($exited){$monitor.ExitCode}else{$null});workExit=$workExit}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $run 'launcher-result.json');$monitor.Dispose()}
 Write-Output $run
}
