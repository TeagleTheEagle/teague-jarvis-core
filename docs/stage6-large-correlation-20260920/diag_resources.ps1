param([string]$Run)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');$root=Get-LiveRun $Run;Set-LiveTemp $root
$rows=[Collections.Generic.List[object]]::new();$errors=[Collections.Generic.List[object]]::new();$clock=[Diagnostics.Stopwatch]::StartNew()
try {
 while($clock.Elapsed.TotalSeconds -lt 180 -and !(Test-Path -LiteralPath (Join-Path $root 'resource-stop'))){
  $begin=[Diagnostics.Stopwatch]::GetTimestamp()
  try{
   $v=Get-Counter -Counter '\Processor(_Total)\% Processor Time','\PhysicalDisk(*)\% Idle Time','\PhysicalDisk(*)\Current Disk Queue Length','\PhysicalDisk(*)\Avg. Disk sec/Read','\PhysicalDisk(*)\Avg. Disk sec/Write','\PhysicalDisk(*)\Disk Read Bytes/sec','\PhysicalDisk(*)\Disk Write Bytes/sec','\Memory\Available MBytes','\Memory\Pages/sec','\System\Context Switches/sec' -MaxSamples 1
   $rows.Add(@{begin=$begin;end=[Diagnostics.Stopwatch]::GetTimestamp();counters=@($v.CounterSamples|Select-Object Path,CookedValue,Status)})
  }catch{$errors.Add(@{qpc=[Diagnostics.Stopwatch]::GetTimestamp();error=$_.Exception.Message});break}
  Start-Sleep -Milliseconds 500
 }
}finally{[IO.File]::WriteAllText((Join-Path $root 'diagnostic-resources.json'),(@{rows=@($rows.ToArray());errors=@($errors.ToArray());frequency=[Diagnostics.Stopwatch]::Frequency}|ConvertTo-Json -Depth 8))}
