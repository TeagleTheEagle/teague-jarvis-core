$ErrorActionPreference='Stop'
$out=Join-Path $PSScriptRoot 'resources.jsonl'
$begin=[DateTime]::UtcNow
try{
 while(-not(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'stop.json')) -and ([DateTime]::UtcNow-$begin).TotalSeconds -lt 420){
  $c=Get-Counter -Counter '\Processor(_Total)\% Processor Time','\PhysicalDisk(*)\% Disk Time','\PhysicalDisk(*)\Current Disk Queue Length','\PhysicalDisk(*)\Avg. Disk sec/Read','\Memory\Available MBytes','\Memory\% Committed Bytes In Use' -MaxSamples 1
  $p=@(Get-Process -Name pwsh,powershell,python -ErrorAction SilentlyContinue|ForEach-Object{[pscustomobject]@{Name=$_.ProcessName;PID=$_.Id;CPU=$_.CPU;WorkingSet=$_.WorkingSet64;Priority=$_.PriorityClass.ToString()}})
  $r=@{Utc=[DateTime]::UtcNow.ToString('o');Counters=@($c.CounterSamples|Select-Object Path,CookedValue);Processes=$p}
  [IO.File]::AppendAllText($out,(($r|ConvertTo-Json -Compress -Depth 6)+"`n"))
  Start-Sleep -Seconds 1
 }
}catch{[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'resources-error.txt'),$_.Exception.Message);exit 1}
