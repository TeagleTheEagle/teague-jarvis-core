param([string]$Run)
$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run;$begin=[DateTime]::UtcNow;$rows=[Collections.Generic.List[object]]::new()
try{
 while(-not(Test-Path -LiteralPath (Join-Path $root 'collector-finished.json')) -and ([DateTime]::UtcNow-$begin).TotalSeconds -lt 590){
  $q=[Diagnostics.Stopwatch]::GetTimestamp()
  $counterStart=[Diagnostics.Stopwatch]::GetTimestamp();$c=Get-Counter -Counter '\Processor(*)\% Processor Time','\PhysicalDisk(*)\% Idle Time','\PhysicalDisk(*)\Current Disk Queue Length','\PhysicalDisk(*)\Avg. Disk sec/Read','\PhysicalDisk(*)\Avg. Disk sec/Write','\PhysicalDisk(*)\Disk Read Bytes/sec','\PhysicalDisk(*)\Disk Write Bytes/sec','\Memory\Available MBytes','\Memory\Pages/sec','\Memory\Page Faults/sec','\System\Context Switches/sec' -MaxSamples 1
  $counterEnd=[Diagnostics.Stopwatch]::GetTimestamp();$processStart=$counterEnd
  $p=@(Get-Process -Name pwsh,python,MsMpEng -ErrorAction SilentlyContinue|ForEach-Object{@{pid=$_.Id;name=$_.ProcessName;cpuSeconds=$_.CPU;workingSet=$_.WorkingSet64;priority=[string]$_.PriorityClass;threads=@($_.Threads|ForEach-Object{@{id=$_.Id;state=[string]$_.ThreadState;priority=$_.CurrentPriority}})}})
  $rows.Add(@{qpc=$q;counterStart=$counterStart;counterEnd=$counterEnd;processStart=$processStart;endQpc=[Diagnostics.Stopwatch]::GetTimestamp();utc=[DateTime]::UtcNow.ToString('o');counters=@($c.CounterSamples|Select-Object Path,CookedValue);processes=$p})
  Start-Sleep -Seconds 1
 }
}catch{[IO.File]::WriteAllText((Join-Path $root 'resource-failure.txt'),$_.Exception.ToString())}
finally{[IO.File]::WriteAllText((Join-Path $root 'resources.json'),(@($rows.ToArray())|ConvertTo-Json -Depth 9));[IO.File]::WriteAllText((Join-Path $root 'resources-complete'),'')}
