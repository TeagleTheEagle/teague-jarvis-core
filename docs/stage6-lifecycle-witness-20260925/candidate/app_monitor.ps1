param([string]$Run)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');$root=Get-LiveRun $Run;Set-LiveTemp $root
Add-Type -Path @((Join-Path $PSScriptRoot 'LoopTiming.cs'),(Join-Path $PSScriptRoot 'event_queue.cs'))
Add-Type -Path (Join-Path $PSScriptRoot 'EventTap.cs')
$s='J6DualStart-'+[guid]::NewGuid().ToString('N');$t='J6DualStop-'+[guid]::NewGuid().ToString('N');$ids=@($s,$t)
$exact=[ExactEventQueue]::new($ExecutionContext.Events.ReceivedEvents,[string[]]$ids)
$receipts=[Collections.Generic.List[object]]::new();$heartbeats=[Collections.Generic.List[object]]::new();$lastEvent=[Diagnostics.Stopwatch]::GetTimestamp();$frequency=[Diagnostics.Stopwatch]::Frequency
$clock=[Diagnostics.Stopwatch]::StartNew();$closingAt=$null;$success=$false;$unsubscribed=$false;$errorRecord=$null;$lastHeartbeat=$lastEvent
function Save($n,$v){[IO.File]::WriteAllText((Join-Path $root $n),($v|ConvertTo-Json -Depth 12))}
function Drain {
 while($null -ne ($entry=$exact.Select())) {
  $ev=$entry.Event;$n=$ev.SourceEventArgs.NewEvent
  if($null -eq $n){throw 'Missing independent CIM event payload'}
  if([string]$n.ProcessName -match '^(VBox|VirtualBox)'){throw 'VirtualBox event detected'}
  $kind=if($ev.SourceIdentifier -eq $s){'start'}else{'stop'}
  $row=@{source='CIM_PROCESS_NOTIFICATION';kind=$kind;pid=[int]$n.ProcessID;parentPid=[int]$n.ParentProcessID;name=[string]$n.ProcessName;nativeTime=[string]$n.TIME_CREATED;eventIdentifier=$ev.EventIdentifier;queueSequence=$entry.QueueSequence;receivedQpc=$entry.EnqueueQpc;drainedQpc=[Diagnostics.Stopwatch]::GetTimestamp()}
  $exact.PersistAndRemove($entry,(Join-Path $root 'app-events.jsonl'),(($row|ConvertTo-Json -Compress)+"`n"))
  $script:lastEvent=[Diagnostics.Stopwatch]::GetTimestamp()
  $receipts.Add(@{queueSequence=$entry.QueueSequence;pid=$row.pid;kind=$kind;persistedQpc=$script:lastEvent;removed=$entry.Removed})
 }
}
try {
 if(@(Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)').Count){throw 'VirtualBox initially active'}
 Register-CimIndicationEvent -Query 'SELECT * FROM Win32_ProcessStartTrace' -SourceIdentifier $s|Out-Null
 Register-CimIndicationEvent -Query 'SELECT * FROM Win32_ProcessStopTrace' -SourceIdentifier $t|Out-Null
 [void][EventTap]::AttachQueue($ExecutionContext.Events.ReceivedEvents,$s,$t)
 foreach($pair in @(@($s,'start'),@($t,'stop'))){$sub=Get-EventSubscriber -SourceIdentifier $pair[0];[void][EventTap]::AttachSource($sub.SourceObject,$sub.EventName,$pair[1])}
 $me=Get-Process -Id $PID
 Save 'app-ready.json' @{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;frequency=$frequency;qpc=[Diagnostics.Stopwatch]::GetTimestamp();source='independent CIM subscriptions; not generated from ETW consumer'}
 while($clock.Elapsed.TotalSeconds -lt 180) {
  if($exact.Failed -or [EventTap]::Errors -or [EventTap]::Overflow){throw 'Application event collector failed'}
  if(@(Get-EventSubscriber|Where-Object SourceIdentifier -in $ids).Count -ne 2){throw 'Subscription lost'}
  Drain
  $now=[Diagnostics.Stopwatch]::GetTimestamp();$interval=($now-$lastHeartbeat)/$frequency
  if($interval -ge 10){throw 'Heartbeat reached fixed 10-second limit'}
  $heartbeats.Add(@{qpc=$now;interval=$interval});$lastHeartbeat=$now
  Save 'app-health.json' @{qpc=$now;frequency=$frequency;pid=$PID;healthy=$true}
  if(Test-Path -LiteralPath (Join-Path $root 'app-stop')) {
   if($null -eq $closingAt){$closingAt=$now}
   if(($now-$closingAt)/$frequency -gt 45){throw 'Fixed finalization deadline exceeded'}
   if(($now-[Math]::Max($lastEvent,$closingAt))/$frequency -ge 4.6 -and $exact.Stats().remaining -eq 0){break}
  }
  Wait-Event -Timeout 1|Out-Null
 }
 if($clock.Elapsed.TotalSeconds -ge 180){throw 'Application monitor bound exceeded'}
 foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction Stop};$unsubscribed=$true
 Drain;$exact.Reconcile()
 $f=[IO.FileStream]::new((Join-Path $root 'app-events.jsonl'),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
 try{$f.Flush($true)}finally{$f.Dispose()}
 $success=$true
}catch{$errorRecord=@{error=$_.Exception.Message;stack=$_.ScriptStackTrace;qpc=[Diagnostics.Stopwatch]::GetTimestamp()}}
finally {
 if(!$unsubscribed){foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue}}
 [EventTap]::Detach()
 Save 'app-receipts.json' @($receipts.ToArray());Save 'app-tap.json' @([EventTap]::Snapshot());Save 'app-heartbeats.json' @($heartbeats.ToArray())
 Save 'app-result.json' @{success=$success;error=$errorRecord;queue=$exact.Stats();tapErrors=[EventTap]::Errors;tapOverflow=[EventTap]::Overflow;source='CIM_PROCESS_NOTIFICATION';durableFinalization=$success;unsubscribed=$unsubscribed}
 $exact.Dispose()
}
if(!$success){exit 1}
