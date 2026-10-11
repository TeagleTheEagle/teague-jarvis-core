$ErrorActionPreference='Stop'
$all=@(Get-CimInstance Win32_Process -ErrorAction Stop)
$matching=@($all|Where-Object{$_.ProcessId -ne $PID -and ($_.Name -match '^(VBox|VirtualBox|J6)' -or ($_.Name -match '^(python|pwsh|powershell)' -and $_.CommandLine -like '*D:\JARVIS-STAGE6-LIVE*'))}|Select-Object ProcessId,Name,CreationDate,ExecutablePath)
$raw=@(& 'C:\Windows\System32\logman.exe' query -ets 2>&1|ForEach-Object{"$_"})
if($LASTEXITCODE -ne 0){throw 'Trace census unavailable'}
$traces=@($raw|Where-Object{$_ -match '(?i)J6|JARVIS|Stage6'})
$result=@{status=$(if(!$matching.Count -and !$traces.Count){'PASS'}else{'BLOCKED'});utc=[DateTime]::UtcNow.ToString('o');matchingProcesses=$matching;matchingProcessCount=$matching.Count;traceSessions=$traces;traceCount=$traces.Count;protectedVMAccess=$false;productionChange=$false}
$p=Join-Path $PSScriptRoot 'final-census.json'
$f=[IO.FileStream]::new($p,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$b=[Text.Encoding]::UTF8.GetBytes(($result|ConvertTo-Json -Depth 6));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}
$result|ConvertTo-Json -Depth 6
if($result.status -ne 'PASS'){throw 'Unexpected processes/traces; STOP'}

