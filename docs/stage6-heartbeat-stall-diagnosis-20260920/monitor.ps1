param([ValidatePattern('^[a-z0-9-]+$')][string]$Run)
$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run
Add-Type -Path (Join-Path $PSScriptRoot 'EventTap.cs')
Add-Type -Path @((Join-Path $PSScriptRoot 'LoopTiming.cs'),(Join-Path $PSScriptRoot 'event_queue.cs'))
$config=Get-Content -LiteralPath (Join-Path $root 'case.json') -Raw|ConvertFrom-Json
$journalPath=Join-Path $root 'heartbeat.jsonl'
if($config.journalVolume -eq 'D'){$journalPath=Join-Path ('D:\JARVIS-STAGE6-HEARTBEAT-STALL-20260920\'+$Run) 'heartbeat.jsonl'}
[LoopTiming]::StartObserver()
$pipeline=[Collections.Generic.List[object]]::new();$secondary=[Collections.Generic.List[object]]::new()
function Stamp($stage,$ev,$n) {
 if($pipeline.Count -ge 20000){throw 'Pipeline trace capacity reached'}
 $pipeline.Add(@{stage=$stage;eventId=$ev.EventIdentifier;source=$ev.SourceIdentifier;pid=[int]$n.ProcessID;name=[string]$n.ProcessName;nativeTime=[string]$n.TIME_CREATED;qpc=[Diagnostics.Stopwatch]::GetTimestamp();utc=[DateTime]::UtcNow.ToString('o')})
}

if(-not(Test-Path -LiteralPath $root)){throw 'Prepared diagnostic directory required'}
$trace=[Collections.Generic.List[object]]::new();$stream=$null;$seq=0;$count=0;$violations=0
$s='J6TimingStart-'+[guid]::NewGuid().ToString('N');$t='J6TimingStop-'+[guid]::NewGuid().ToString('N');$ids=@($s,$t)
$exact=[ExactEventQueue]::new($ExecutionContext.Events.ReceivedEvents,[string[]]$ids)
$nonce=[guid]::NewGuid().ToString('N');$clock=[Diagnostics.Stopwatch]::StartNew()
$created=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToFileTimeUtc().ToString()
function Mark([string]$stage,$detail=$null){
 if($trace.Count -ge 50000){throw 'Diagnostic trace capacity reached'}
 $trace.Add(@{qpc=[Diagnostics.Stopwatch]::GetTimestamp();seq=$script:seq;stage=$stage;detail=$detail})
 [LoopTiming]::Note($stage)
}
function Save($name,$value){[IO.File]::WriteAllText((Join-Path $root $name),($value|ConvertTo-Json -Depth 8))}
function Drain {
 Mark 'drain.begin';$nBefore=$count
 while($true){
  Mark 'queue.select.begin';$entry=$exact.Select();Mark 'queue.select.end'
  if($null -eq $entry){break}
   $ev=$entry.Event;$id=$ev.SourceIdentifier
   Mark 'event.begin';$n=$ev.SourceEventArgs.NewEvent;if($null -eq $n){throw 'Invalid CIM indication'}
   $kind='stop';if($id -eq $s){$kind='start'};Stamp 'drain' $ev $n
   if([string]$n.ProcessName -match '^(VBox|VirtualBox)'){$script:violations++}
   $row=@{queueSequence=$entry.QueueSequence;eventIdentifier=$ev.EventIdentifier;kind=$kind;name=[string]$n.ProcessName;pid=[int]$n.ProcessID;nativeTime=[string]$n.TIME_CREATED;receivedQpc=[Diagnostics.Stopwatch]::GetTimestamp();utc=[DateTime]::UtcNow.ToString('o');queuedUtc=$ev.TimeGenerated.ToUniversalTime().ToString('o')}
   Stamp 'serialize.begin' $ev $n;Mark 'event.serialize.begin';$serialized=($row|ConvertTo-Json -Compress)+"`n";Mark 'event.serialize.end';Stamp 'serialized' $ev $n
   Mark 'event.path.begin';$eventPath=Join-Path $root 'events.jsonl';Mark 'event.path.end'
   Mark 'event.exists.begin';$exists=Test-Path -LiteralPath $eventPath;Mark 'event.exists.end'
   if($exists){Mark 'event.stat.begin';$length=(Get-Item -LiteralPath $eventPath).Length;Mark 'event.stat.end';if($length -gt 1044480){throw 'Event capacity reached'}}
   Mark 'event.append.begin';Stamp 'write.begin' $ev $n
   $exact.PersistAndRemove($entry,$eventPath,$serialized)
   Stamp 'persisted' $ev $n;Stamp 'removed' $ev $n;Mark 'event.append.end';$script:count++;Mark 'event.end'
 }
 Mark 'queue.backlog.begin';$backlog=0;foreach($id in $ids){$backlog+=@(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue).Count};Mark 'queue.backlog.end' $backlog
 Mark 'drain.end' @{drained=$count-$nBefore;backlog=$backlog}
 if($violations){throw 'VirtualBox event detected'}
}
try{
 Mark 'subscription.begin';$filter="ProcessName LIKE 'VBox%' OR ProcessName LIKE 'VirtualBox%' OR ProcessName LIKE 'J6Probe%'"
 Register-CimIndicationEvent -Query ("SELECT * FROM Win32_ProcessStartTrace WHERE "+$filter) -SourceIdentifier $s
 Register-CimIndicationEvent -Query ("SELECT * FROM Win32_ProcessStopTrace WHERE "+$filter) -SourceIdentifier $t
 $hookNames=@()
 $hookNames+=[EventTap]::AttachQueue($ExecutionContext.Events.ReceivedEvents,$s,$t)
 foreach($pair in @(@($s,'start'),@($t,'stop'))){$sub=Get-EventSubscriber -SourceIdentifier $pair[0];$hookNames+=[EventTap]::AttachSource($sub.SourceObject,$sub.EventName,$pair[1])}
 # Separate System.Management/COM subscriber, same Windows provider. Not an independent kernel source.
 [void][Reflection.Assembly]::LoadFrom((Join-Path $PSHOME 'System.Management.dll'))
 foreach($pair in @(@('Win32_ProcessStartTrace','start'),@('Win32_ProcessStopTrace','stop'))){
  $watcher=[System.Management.ManagementEventWatcher]::new('root\cimv2',("SELECT * FROM "+$pair[0]+" WHERE ProcessName LIKE 'J6Probe%'"))
  $hookNames+=[EventTap]::AttachSecondary($watcher,$pair[1]);$watcher.Start();$secondary.Add($watcher)
 }
 Save 'hooks.json' @{hooks=$hookNames;powershell=$PSVersionTable.PSVersion.ToString();observerB='parallel WMI COM subscriber; same native provider';groundTruth='separate retained kernel process handles';callback_tap='attached after original handler; may observe after enqueue'}
 Mark 'subscription.end';Mark 'enumeration.begin'
 $initial=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'});Mark 'enumeration.end' $initial.Count
 if($initial.Count){throw 'VirtualBox initially active'}
 Mark 'journal.open.begin';$stream=[IO.FileStream]::new($journalPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);Mark 'journal.open.end'
 $self=Get-Process -Id $PID
 $identity=@{run=$nonce;pid=$PID;created=$created;frequency=[Diagnostics.Stopwatch]::Frequency}
 Save 'monitor-config.json' @{identity=$identity;priority=[string]$self.PriorityClass;threads=@($self.Threads|Select-Object Id,BasePriority,CurrentPriority);stopwatchHighResolution=[Diagnostics.Stopwatch]::IsHighResolution;traceMode='bounded memory, written at exit';staleThreshold=10;rotation='not used';osFlush='Live Flush(false); final Flush(true) after collection freezes; all evidence fsync/archive required separately';scriptHash=(Get-FileHash -LiteralPath $PSCommandPath).Hash}
 while($clock.Elapsed.TotalSeconds -lt 600){
  Mark 'loop.begin';Mark 'health.begin';if([EventTap]::Errors -or [EventTap]::Overflow -or [LoopTiming]::Overflow){throw 'Diagnostic hook error/overflow'};Mark 'health.end';Drain
  $seq++;Mark 'record.begin';$q=[Diagnostics.Stopwatch]::GetTimestamp()
  $record=@{run=$nonce;pid=$PID;created=$created;frequency=[Diagnostics.Stopwatch]::Frequency;seq=$seq;pump=$seq;ticks=$q;utc=[DateTime]::UtcNow.ToString('o');state='ACTIVE';violations=$violations;events=$count}
  $bytes=[Text.Encoding]::UTF8.GetBytes((($record|ConvertTo-Json -Compress)+"`n"));Mark 'record.end'
  Mark 'journal.size.begin';if($bytes.Length -gt 4096 -or $stream.Length+$bytes.Length -gt 1048576){throw 'Journal capacity reached'};Mark 'journal.size.end'
  Mark 'journal.write.begin';$stream.Write($bytes,0,$bytes.Length);Mark 'journal.write.end'
  Mark 'journal.flush.begin';$stream.Flush($false);Mark 'journal.flush.end';Mark 'publication.complete'
  if($seq -eq 1){Mark 'ready.begin';Save 'ready.json' $identity;Mark 'ready.end'}
  Mark 'runtime.telemetry.begin';if($config.telemetry -eq 'full'){[LoopTiming]::RuntimeSample()};Mark 'runtime.telemetry.end'
  Mark 'finish.query.begin';$finished=Test-Path -LiteralPath (Join-Path $root 'collector-finished.json');Mark 'finish.query.end'
  if($finished){Mark 'loop.end';break}
  Mark 'wait.begin';Wait-Event -Timeout 1|Out-Null;Mark 'wait.end';Mark 'loop.end' @{gc0=[GC]::CollectionCount(0);gc1=[GC]::CollectionCount(1);gc2=[GC]::CollectionCount(2)}
 }
 if($clock.Elapsed.TotalSeconds -ge 600){throw 'Monitor lifetime bound reached'}
 Mark 'grace.begin';Start-Sleep -Seconds 2;Mark 'grace.end';Drain
 Mark 'final.enumeration.begin';$final=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'});Mark 'final.enumeration.end' $final.Count
 if($final.Count){throw 'VirtualBox active at end'}
 $exact.Reconcile();Mark 'collection.freeze';Mark 'durable.flush.begin';$stream.Flush($true);Mark 'durable.flush.end'
 Mark 'journal.close.begin';$stream.Dispose();$stream=$null;Mark 'journal.close.end'
 Save 'monitor-result.json' @{status='LIVE_COLLECTION_CLOSED';run=$nonce;sequences=$seq;events=$count;violations=$violations;journalDurableFlush=$true;acceptance=$false}
}catch{Save 'monitor-failure.json' @{error=$_.Exception.Message;stack=$_.ScriptStackTrace;utc=[DateTime]::UtcNow.ToString('o')};exit 1}
finally{
 if($null -ne $stream){Mark 'journal.close.begin';$stream.Dispose();Mark 'journal.close.end'}
 Mark 'unsubscribe.begin'
 foreach($id in $ids){
  $pending=@(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue)
  foreach($ev in $pending){if($ev.SourceEventArgs.NewEvent){Stamp 'preunsubscribe.pending' $ev $ev.SourceEventArgs.NewEvent}}
  Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue
  $discard=@(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue)
  foreach($ev in $discard){if($ev.SourceEventArgs.NewEvent){Stamp 'teardown.discard' $ev $ev.SourceEventArgs.NewEvent}}
  # Preserve residue; never delete pending evidence at teardown.
 }
 Mark 'unsubscribe.end'
 foreach($watcher in $secondary){$watcher.Stop();$watcher.Dispose()}
 [EventTap]::Detach()
 Save 'queue-state.json' $exact.Stats()
 Save 'queue-entries.json' @($exact.Snapshot()|ForEach-Object {@{queueSequence=$_.QueueSequence;eventId=$_.Event.EventIdentifier;source=$_.Event.SourceIdentifier;enqueueQpc=$_.EnqueueQpc;persisted=$_.Persisted;removed=$_.Removed}})
 try {$exact.Reconcile()} catch {Save 'queue-failure.json' @{error=$_.Exception.Message};$global:LASTEXITCODE=1}
 $exact.Dispose()
 Save 'tap.json' @([EventTap]::Snapshot());Save 'pipeline.json' @($pipeline.ToArray())
 Save 'tap-state.json' @{errors=[EventTap]::Errors;overflow=[EventTap]::Overflow;queue_capacity='existing PowerShell collection; no diagnostic change';diagnostic_capacity=20000;native_drop_counter='not exposed by these temporary subscribers'}
 [LoopTiming]::StopObserver()
 Save 'loop-trace.json' @($trace.ToArray())
 Save 'fine-trace.json' @([LoopTiming]::Snapshot())
 Save 'runtime-samples.json' @([LoopTiming]::RuntimeSnapshot())
 Save 'scheduler-observer.json' @([LoopTiming]::ObserverSnapshot())
 Save 'timing-state.json' @{overflow=[LoopTiming]::Overflow;journalPath=$journalPath;telemetry=$config.telemetry;observerMeaning='100ms independent diagnostic sleep observer, not a health publisher; jitter is not proof of CPU starvation'}
}
