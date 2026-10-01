$ErrorActionPreference='Stop'
$output=Join-Path $PSScriptRoot 'final-host-census.json'
$all=@(Get-CimInstance Win32_Process -ErrorAction Stop)
$matching=@($all|Where-Object{$_.ProcessId -ne $PID -and ($_.Name -match '^(VBox|VirtualBox|J6)' -or ($_.Name -match '^(python|pwsh|powershell)' -and $_.CommandLine -like '*D:\JARVIS-STAGE6-LIVE*'))}|Select-Object ProcessId,Name,CreationDate,ExecutablePath)
$raw=@(& logman query -ets 2>&1|ForEach-Object{"$_"})
if($LASTEXITCODE -ne 0){throw 'Trace enumeration unavailable; counts unknown'}
$traces=@($raw|Where-Object{$_ -match '(?i)J6|JARVIS|Stage6'})
$result=@{status=$(if($matching.Count -eq 0 -and $traces.Count -eq 0){'PASS'}else{'BLOCKED'});utc=[DateTime]::UtcNow.ToString('o');matchingProcessCount=$matching.Count;matchingProcesses=$matching;traceCount=$traces.Count;traces=$traces;protectedVMAccess=$false;productionChange=$false;readOnly=$true}
$f=[IO.FileStream]::new($output,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$b=[Text.Encoding]::UTF8.GetBytes(($result|ConvertTo-Json -Depth 6));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}
$result|ConvertTo-Json -Depth 6
if($result.status -ne 'PASS'){throw 'Unexpected diagnostic process or trace; no cleanup operation authorized by this census'}
