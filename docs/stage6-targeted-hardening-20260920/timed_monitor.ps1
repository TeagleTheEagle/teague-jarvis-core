param([string]$Run,[int]$KernelPid)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');$root=Get-LiveRun $Run;Set-LiveTemp $root
Add-Type -Path @((Join-Path $PSScriptRoot 'LoopTiming.cs'),(Join-Path $PSScriptRoot 'event_queue.cs'),(Join-Path $PSScriptRoot 'EventTap.cs'))
function Measure([string]$Name,[scriptblock]$Code){$span=[LoopTiming]::Span($Name);try{& $Code}finally{$span.Dispose()}}
function Save($n,$v){Measure ('output.'+$n) {[IO.File]::WriteAllText((Join-Path $root $n),($v|ConvertTo-Json -Depth 12))}}
$s='J6TimedStart-'+[guid]::NewGuid().ToString('N');$t='J6TimedStop-'+[guid]::NewGuid().ToString('N');$ids=@($s,$t)
$exact=[ExactEventQueue]::new($ExecutionContext.Events.ReceivedEvents,[string[]]$ids)
$receipts=[Collections.Generic.List[object]]::new();$heartbeats=[Collections.Generic.List[object]]::new();$lastEvent=[Diagnostics.Stopwatch]::GetTimestamp();$frequency=[Diagnostics.Stopwatch]::Frequency
$clock=[Diagnostics.Stopwatch]::StartNew();$closingAt=$null;$success=$false;$unsubscribed=$false;$errorRecord=$null;$lastHeartbeat=$lastEvent
function Drain {
 while($null -ne ($entry=(Measure 'event.selection' {$exact.Select()}))){
  $n=Measure 'event.source.read' {$entry.Event.SourceEventArgs.NewEvent}
  if($null -eq $n){throw 'Missing independent CIM event payload'}
  if([string]$n.ProcessName -match '^(VBox|VirtualBox)'){throw 'VirtualBox event detected'}
  $row=Measure 'event.metadata' {@{source='CIM_PROCESS_NOTIFICATION';kind=$(if($entry.Event.SourceIdentifier -eq $s){'start'}else{'stop'});pid=[int]$n.ProcessID;parentPid=[int]$n.ParentProcessID;name=[string]$n.ProcessName;nativeTime=[string]$n.TIME_CREATED;eventIdentifier=$entry.Event.EventIdentifier;queueSequence=$entry.QueueSequence;receivedQpc=$entry.EnqueueQpc;drainedQpc=[Diagnostics.Stopwatch]::GetTimestamp()}}
  $serialized=Measure 'event.serialization' {(($row|ConvertTo-Json -Compress)+"`n")}
  $path=Measure 'evidence.path' {Join-Path $root 'app-events.jsonl'}
  Measure 'event.append-and-remove' {$exact.PersistAndRemove($entry,$path,$serialized)}
  $script:lastEvent=[Diagnostics.Stopwatch]::GetTimestamp();$receipts.Add(@{queueSequence=$entry.QueueSequence;pid=$row.pid;kind=$row.kind;persistedQpc=$script:lastEvent;removed=$entry.Removed})
 }
}
try{
 if(@(Measure 'process.inspection.preflight' {Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)'}).Count){throw 'VirtualBox initially active'}
 Measure 'subscription.start' {Register-CimIndicationEvent -Query 'SELECT * FROM Win32_ProcessStartTrace' -SourceIdentifier $s|Out-Null;Register-CimIndicationEvent -Query 'SELECT * FROM Win32_ProcessStopTrace' -SourceIdentifier $t|Out-Null}
 [void][EventTap]::AttachQueue($ExecutionContext.Events.ReceivedEvents,$s,$t)
 foreach($pair in @(@($s,'start'),@($t,'stop'))){$sub=Get-EventSubscriber -SourceIdentifier $pair[0];[void][EventTap]::AttachSource($sub.SourceObject,$sub.EventName,$pair[1])}
 $me=Measure 'process.inspection.identity' {Get-Process -Id $PID}
 Save 'app-ready.json' @{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;frequency=$frequency;qpc=[Diagnostics.Stopwatch]::GetTimestamp();source='independent CIM subscriptions'}
 while($clock.Elapsed.TotalSeconds -lt 1200){
  [LoopTiming]::BeginLoop();Measure 'loop.wake' {[LoopTiming]::Note('awake')}
  Measure 'queue.health' {if($exact.Failed -or [EventTap]::Errors -or [EventTap]::Overflow -or [LoopTiming]::Overflow){throw 'Collector/timing overflow or failure'}}
  $subscriptions=Measure 'event.source.subscription-check' {@(Get-EventSubscriber|Where-Object SourceIdentifier -in $ids).Count}
  if($subscriptions -ne 2){throw 'Subscription lost'}
  Measure 'event.drain' {Drain}
  $now=Measure 'heartbeat.creation' {[Diagnostics.Stopwatch]::GetTimestamp()};$interval=($now-$lastHeartbeat)/$frequency
  if($interval -ge 10){throw 'Heartbeat reached fixed 10-second limit'}
  Measure 'heartbeat.history.append' {$heartbeats.Add(@{qpc=$now;interval=$interval;loop=[LoopTiming]::CurrentLoop})};$lastHeartbeat=$now
  Measure 'heartbeat.publish.overwrite' {Save 'app-health.json' @{qpc=$now;frequency=$frequency;pid=$PID;healthy=$true}}
  $stop=Measure 'control.file.check' {Test-Path -LiteralPath (Join-Path $root 'app-stop')}
  if($stop){
   if($null -eq $closingAt){$closingAt=$now}
   if(($now-$closingAt)/$frequency -gt 45){throw 'Fixed finalization deadline exceeded'}
   if(($now-[Math]::Max($lastEvent,$closingAt))/$frequency -ge 4.6 -and $exact.Stats().remaining -eq 0){break}
  }
  Measure 'wait.event' {Wait-Event -Timeout 1|Out-Null}
 }
 if($clock.Elapsed.TotalSeconds -ge 1200){throw 'Application monitor bound exceeded'}
 Measure 'subscription.close' {foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction Stop}};$unsubscribed=$true
 Measure 'final.event.drain' {Drain};Measure 'queue.reconcile' {$exact.Reconcile()}
 Measure 'flush.durable' {$f=[IO.FileStream]::new((Join-Path $root 'app-events.jsonl'),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read);try{$f.Flush($true)}finally{$f.Dispose()}}
 $success=$true
}catch{$errorRecord=@{error=$_.Exception.Message;stack=$_.ScriptStackTrace;qpc=[Diagnostics.Stopwatch]::GetTimestamp()}}
finally{
 if(!$unsubscribed){foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue}}
 [EventTap]::Detach()
 Save 'app-receipts.json' @($receipts.ToArray());Save 'app-tap.json' @([EventTap]::Snapshot());Save 'app-heartbeats.json' @($heartbeats.ToArray())
 Save 'app-result.json' @{success=$success;error=$errorRecord;queue=$exact.Stats();tapErrors=[EventTap]::Errors;tapOverflow=[EventTap]::Overflow;source='CIM_PROCESS_NOTIFICATION';durableFinalization=$success;unsubscribed=$unsubscribed}
 $exact.Dispose()
 # Frozen memory trace is written only after subscriptions and live collection end.
 $trace=@{frequency=$frequency;overflow=[LoopTiming]::Overflow;spans=@([LoopTiming]::SpanSnapshot());points=@([LoopTiming]::Snapshot());optionalResourceInspection='MOVED_OUT_OF_MONITOR';evidenceExistenceCheck='NONE: append opens directly'}
 [IO.File]::WriteAllText((Join-Path $root 'stage-timing.json'),($trace|ConvertTo-Json -Depth 8))
}
if(!$success){exit 1}
