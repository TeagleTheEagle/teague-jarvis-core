param([string]$Run,[int]$KernelPid)
$ErrorActionPreference='Stop';. (Join-Path $PSScriptRoot 'workspace.ps1');$root=Get-LiveRun $Run;Set-LiveTemp $root
. (Join-Path $PSScriptRoot 'health_publication.ps1')
$healthPublisher=$null
Add-Type -Path @((Join-Path $PSScriptRoot 'AuthoritativeEvents.cs'),(Join-Path $PSScriptRoot 'WriterTiming.cs'),(Join-Path $PSScriptRoot 'LoopTiming.cs'),(Join-Path $PSScriptRoot 'event_queue.cs'),(Join-Path $PSScriptRoot 'EventTap.cs'))
function Invoke-J6TimedStage([string]$Name,[scriptblock]$Code){$span=[LoopTiming]::Span($Name);try{& $Code}finally{$span.Dispose()}}
function Save($n,$v){Invoke-J6TimedStage ('output.'+$n) {$mode=[IO.FileMode]::CreateNew;$f=[IO.FileStream]::new((Join-Path $root $n),$mode,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$b=[Text.Encoding]::UTF8.GetBytes(($v|ConvertTo-Json -Depth 12));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}}}
$s='J6TimedStart-'+[guid]::NewGuid().ToString('N');$t='J6TimedStop-'+[guid]::NewGuid().ToString('N');$ids=@($s,$t)
$exact=[ExactEventQueue]::new($ExecutionContext.Events.ReceivedEvents,[string[]]$ids,$true)
[EventTap]::Initialize($root)
$receipts=[Collections.Generic.List[object]]::new();$heartbeats=[Collections.Generic.List[object]]::new();$lastEvent=[Diagnostics.Stopwatch]::GetTimestamp();$frequency=[Diagnostics.Stopwatch]::Frequency
$clock=[Diagnostics.Stopwatch]::StartNew();$closingAt=$null;$success=$false;$unsubscribed=$false;$errorRecord=$null;$lastHeartbeat=$lastEvent
function Drain {
 while($null -ne ($entry=(Invoke-J6TimedStage 'event.selection' {$exact.Select()}))){
  $n=Invoke-J6TimedStage 'event.source.read' {$entry.Event.SourceEventArgs.NewEvent}
  if($null -eq $n){throw 'Missing independent CIM event payload'}
  if([string]$n.ProcessName -match '^(VBox|VirtualBox)'){throw 'VirtualBox event detected'}
  $row=Invoke-J6TimedStage 'event.metadata' {@{source='CIM_PROCESS_NOTIFICATION';kind=$(if($entry.Event.SourceIdentifier -eq $s){'start'}else{'stop'});pid=[int]$n.ProcessID;parentPid=[int]$n.ParentProcessID;name=[string]$n.ProcessName;nativeTime=[string]$n.TIME_CREATED;eventIdentifier=$entry.Event.EventIdentifier;queueSequence=$entry.QueueSequence;receivedQpc=$entry.EnqueueQpc;drainedQpc=[Diagnostics.Stopwatch]::GetTimestamp()}}
  $serialized=Invoke-J6TimedStage 'event.serialization' {(($row|ConvertTo-Json -Compress)+"`n")}
  $path=Invoke-J6TimedStage 'evidence.path' {Join-Path $root 'app-events.jsonl'}
  Invoke-J6TimedStage 'event.append-and-remove' {$exact.PersistAndRemove($entry,$path,$serialized)}
  $script:lastEvent=[Diagnostics.Stopwatch]::GetTimestamp();$receipt=@{queueSequence=$entry.QueueSequence;pid=$row.pid;kind=$row.kind;persistedQpc=$script:lastEvent;removed=$entry.Removed};$receipts.Add($receipt);[EventTap]::Persisted(($row|ConvertTo-Json -Compress),($receipt|ConvertTo-Json -Compress))
 }
}
try{
 if(@(Invoke-J6TimedStage 'process.inspection.preflight' {Get-Process|Where-Object ProcessName -match '^(VBox|VirtualBox)'}).Count){throw 'VirtualBox initially active'}
 Invoke-J6TimedStage 'subscription.start' {Register-CimIndicationEvent -Query 'SELECT * FROM Win32_ProcessStartTrace' -SourceIdentifier $s|Out-Null;Register-CimIndicationEvent -Query 'SELECT * FROM Win32_ProcessStopTrace' -SourceIdentifier $t|Out-Null}
 [void][EventTap]::AttachQueue($ExecutionContext.Events.ReceivedEvents,$s,$t)
 foreach($pair in @(@($s,'start'),@($t,'stop'))){$sub=Get-EventSubscriber -SourceIdentifier $pair[0];[void][EventTap]::AttachSource($sub.SourceObject,$sub.EventName,$pair[1])}
 $me=Invoke-J6TimedStage 'process.inspection.identity' {Get-Process -Id $PID}
 $ready=@{pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$me.Path;frequency=$frequency;qpc=[Diagnostics.Stopwatch]::GetTimestamp();source='independent CIM subscriptions'}
 $healthPublisher=New-J6HealthPublisher $root @{run=$Run;pid=$PID;created=$ready.created;frequency=$frequency}
 while($clock.Elapsed.TotalSeconds -lt 1200){
  [LoopTiming]::BeginLoop();Invoke-J6TimedStage 'loop.wake' {[LoopTiming]::Note('awake')}
  Invoke-J6TimedStage 'queue.health' {if($exact.Failed -or [EventTap]::Errors -or [EventTap]::StreamFailure -or [LoopTiming]::Overflow){throw 'Collector/timing overflow or failure'}}
  $subscriptions=Invoke-J6TimedStage 'event.source.subscription-check' {@(Get-EventSubscriber|Where-Object SourceIdentifier -in $ids).Count}
  if($subscriptions -ne 2){throw 'Subscription lost'}
  Invoke-J6TimedStage 'event.drain' {Drain}
  $now=Invoke-J6TimedStage 'heartbeat.creation' {[Diagnostics.Stopwatch]::GetTimestamp()};$interval=($now-$lastHeartbeat)/$frequency
  if($interval -ge 10){throw 'Heartbeat reached fixed 10-second limit'}
  Invoke-J6TimedStage 'heartbeat.history.append' {$heartbeats.Add(@{qpc=$now;interval=$interval;loop=[LoopTiming]::CurrentLoop})};$lastHeartbeat=$now
  Invoke-J6TimedStage 'heartbeat.publish.append' {Write-J6HealthRecord $healthPublisher $now}
  if($healthPublisher.Sequence -eq 1){Invoke-J6TimedStage 'ready.publish.complete' {Publish-J6Ready $root $healthPublisher $ready}}
  $stop=Invoke-J6TimedStage 'control.file.check' {Test-Path -LiteralPath (Join-Path $root 'app-stop')}
  if($stop){
   if($null -eq $closingAt){$closingAt=$now}
   if(($now-$closingAt)/$frequency -gt 45){throw 'Fixed finalization deadline exceeded'}
   if(($now-[Math]::Max($lastEvent,$closingAt))/$frequency -ge 4.6 -and $exact.Stats().remaining -eq 0){break}
  }
  Invoke-J6TimedStage 'wait.event' {Wait-Event -Timeout 1|Out-Null}
 }
 if($clock.Elapsed.TotalSeconds -ge 1200){throw 'Application monitor bound exceeded'}
 Invoke-J6TimedStage 'subscription.close' {foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction Stop}};$unsubscribed=$true
 Invoke-J6TimedStage 'final.event.drain' {Drain};Invoke-J6TimedStage 'queue.reconcile' {$exact.Reconcile()}
 Invoke-J6TimedStage 'flush.durable' {$f=[IO.FileStream]::new((Join-Path $root 'app-events.jsonl'),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read);try{$f.Flush($true)}finally{$f.Dispose()}}
 Close-J6HealthPublisher $healthPublisher
 $success=$true
}catch{$errorRecord=@{error=$_.Exception.Message;stack=$_.ScriptStackTrace;qpc=[Diagnostics.Stopwatch]::GetTimestamp()}}
finally{
 if($null -ne $healthPublisher -and !$healthPublisher.Closed){try{Close-J6HealthPublisher $healthPublisher}catch{$success=$false;$errorRecord=@{error=$_.Exception.Message}}}
 if(!$unsubscribed){foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue}}
 [EventTap]::Detach()
 try{[EventTap]::Finish();if([EventTap]::StreamFailure){$success=$false;$errorRecord=@{error=[EventTap]::StreamFailure}}}catch{$success=$false;$errorRecord=@{error=$_.Exception.Message}}
 Save 'app-receipts.json' @($receipts.ToArray());Save 'app-tap.json' @([EventTap]::Snapshot());Save 'app-heartbeats.json' @($heartbeats.ToArray())
 Save 'app-result.json' @{success=$success;error=$errorRecord;queue=$exact.Stats();tapErrors=[EventTap]::Errors;tapOverflow=[EventTap]::Overflow;tapTruncated=[EventTap]::Truncated;authoritativeManifest="app-authority.json";source='CIM_PROCESS_NOTIFICATION';durableFinalization=$success;unsubscribed=$unsubscribed}
 $exact.Dispose()
 # Frozen memory trace is written only after subscriptions and live collection end.
 $trace=@{frequency=$frequency;overflow=[LoopTiming]::Overflow;spans=@([LoopTiming]::SpanSnapshot());points=@([LoopTiming]::Snapshot());optionalResourceInspection='MOVED_OUT_OF_MONITOR';evidenceExistenceCheck='NONE: append opens directly'}
 Save 'stage-timing.json' $trace
}
if(!$success){exit 1}
