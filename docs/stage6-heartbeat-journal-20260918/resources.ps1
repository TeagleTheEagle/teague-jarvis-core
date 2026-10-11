param([ValidateSet('dry1','dry2')][string]$Run)
$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run;$begin=[DateTime]::UtcNow
try {
 while(-not(Test-Path -LiteralPath (Join-Path $root 'collector-finished.json')) -and ([DateTime]::UtcNow-$begin).TotalSeconds -lt 300){
  $c=Get-Counter -Counter '\Processor(_Total)\% Processor Time','\PhysicalDisk(*)\% Disk Time','\PhysicalDisk(*)\% Idle Time','\PhysicalDisk(*)\Current Disk Queue Length','\Memory\Available MBytes' -MaxSamples 1
  $row=@{utc=[DateTime]::UtcNow.ToString('o');counters=@($c.CounterSamples|Select-Object Path,CookedValue)}
  [IO.File]::AppendAllText((Join-Path $root 'resources.jsonl'),(($row|ConvertTo-Json -Depth 5 -Compress)+"`n"));Start-Sleep -Seconds 1
 }
}catch{[IO.File]::WriteAllText((Join-Path $root 'resources-error.txt'),$_.Exception.Message);exit 1}
