param([ValidatePattern('^[a-z0-9-]+$')][string]$Run)
$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run
if(-not(Test-Path -LiteralPath $root)){throw 'Prepared diagnostic directory required'}
$trace=[Collections.Generic.List[object]]::new();$stream=$null;$seq=0;$count=0;$violations=0
$s='J6TimingStart-'+[guid]::NewGuid().ToString('N');$t='J6TimingStop-'+[guid]::NewGuid().ToString('N');$ids=@($s,$t)
$nonce=[guid]::NewGuid().ToString('N');$clock=[Diagnostics.Stopwatch]::StartNew()
$created=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToFileTimeUtc().ToString()
function Mark([string]$stage,$detail=$null){
 if($trace.Count -ge 50000){throw 'Diagnostic trace capacity reached'}
 $trace.Add(@{qpc=[Diagnostics.Stopwatch]::GetTimestamp();seq=$script:seq;stage=$stage;detail=$detail})
}
function Save($name,$value){[IO.File]::WriteAllText((Join-Path $root $name),($value|ConvertTo-Json -Depth 8))}
function Drain {
 Mark 'drain.begin';$nBefore=$count
 foreach($id in $ids){
  Mark 'queue.query.begin' $id;$batch=@(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue);Mark 'queue.query.end' @{id=$id;depth=$batch.Count}
  foreach($ev in $batch){
   Mark 'event.begin';$n=$ev.SourceEventArgs.NewEvent;if($null -eq $n){throw 'Invalid CIM indication'}
   $kind='stop';if($id -eq $s){$kind='start'}
   if([string]$n.ProcessName -match '^(VBox|VirtualBox)'){$script:violations++}
   $row=@{kind=$kind;name=[string]$n.ProcessName;pid=[int]$n.ProcessID;nativeTime=[string]$n.TIME_CREATED;receivedQpc=[Diagnostics.Stopwatch]::GetTimestamp();utc=[DateTime]::UtcNow.ToString('o');queuedUtc=$ev.TimeGenerated.ToUniversalTime().ToString('o')}
   Mark 'event.serialize.begin';$serialized=($row|ConvertTo-Json -Compress)+"`n";Mark 'event.serialize.end'
   $eventPath=Join-Path $root 'events.jsonl';Mark 'event.size.begin'
   if((Test-Path -LiteralPath $eventPath) -and (Get-Item -LiteralPath $eventPath).Length -gt 1044480){throw 'Event capacity reached'}
   Mark 'event.size.end';Mark 'event.append.begin';[IO.File]::AppendAllText($eventPath,$serialized);Mark 'event.append.end'
   $script:count++;Mark 'event.remove.begin';Remove-Event -EventIdentifier $ev.EventIdentifier;Mark 'event.remove.end';Mark 'event.end'
  }
 }
 Mark 'queue.backlog.begin';$backlog=0;foreach($id in $ids){$backlog+=@(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue).Count};Mark 'queue.backlog.end' $backlog
 Mark 'drain.end' @{drained=$count-$nBefore;backlog=$backlog}
 if($violations){throw 'VirtualBox event detected'}
}
try{
 Mark 'subscription.begin';$filter="ProcessName LIKE 'VBox%' OR ProcessName LIKE 'VirtualBox%' OR ProcessName LIKE 'J6Probe%'"
 Register-CimIndicationEvent -Query ("SELECT * FROM Win32_ProcessStartTrace WHERE "+$filter) -SourceIdentifier $s
 Register-CimIndicationEvent -Query ("SELECT * FROM Win32_ProcessStopTrace WHERE "+$filter) -SourceIdentifier $t
 Mark 'subscription.end';Mark 'enumeration.begin'
 $initial=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'});Mark 'enumeration.end' $initial.Count
 if($initial.Count){throw 'VirtualBox initially active'}
 Mark 'journal.open.begin';$stream=[IO.FileStream]::new((Join-Path $root 'heartbeat.jsonl'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);Mark 'journal.open.end'
 $self=Get-Process -Id $PID
 $identity=@{run=$nonce;pid=$PID;created=$created;frequency=[Diagnostics.Stopwatch]::Frequency}
 Save 'monitor-config.json' @{identity=$identity;priority=[string]$self.PriorityClass;threads=@($self.Threads|Select-Object Id,BasePriority,CurrentPriority);stopwatchHighResolution=[Diagnostics.Stopwatch]::IsHighResolution;traceMode='bounded memory, written at exit';staleThreshold=10;rotation='not used';osFlush='Live Flush(false); final Flush(true) after collection freezes; all evidence fsync/archive required separately';scriptHash=(Get-FileHash -LiteralPath $PSCommandPath).Hash}
 while($clock.Elapsed.TotalSeconds -lt 600){
  Mark 'loop.begin';Drain
  $seq++;Mark 'record.begin';$q=[Diagnostics.Stopwatch]::GetTimestamp()
  $record=@{run=$nonce;pid=$PID;created=$created;frequency=[Diagnostics.Stopwatch]::Frequency;seq=$seq;pump=$seq;ticks=$q;utc=[DateTime]::UtcNow.ToString('o');state='ACTIVE';violations=$violations;events=$count}
  $bytes=[Text.Encoding]::UTF8.GetBytes((($record|ConvertTo-Json -Compress)+"`n"));Mark 'record.end'
  Mark 'journal.size.begin';if($bytes.Length -gt 4096 -or $stream.Length+$bytes.Length -gt 1048576){throw 'Journal capacity reached'};Mark 'journal.size.end'
  Mark 'journal.write.begin';$stream.Write($bytes,0,$bytes.Length);Mark 'journal.write.end'
  Mark 'journal.flush.begin';$stream.Flush($false);Mark 'journal.flush.end';Mark 'publication.complete'
  if($seq -eq 1){Mark 'ready.begin';Save 'ready.json' $identity;Mark 'ready.end'}
  Mark 'finish.query.begin';$finished=Test-Path -LiteralPath (Join-Path $root 'collector-finished.json');Mark 'finish.query.end'
  if($finished){Mark 'loop.end';break}
  Mark 'wait.begin';Wait-Event -Timeout 1|Out-Null;Mark 'wait.end';Mark 'loop.end' @{gc0=[GC]::CollectionCount(0);gc1=[GC]::CollectionCount(1);gc2=[GC]::CollectionCount(2)}
 }
 if($clock.Elapsed.TotalSeconds -ge 600){throw 'Monitor lifetime bound reached'}
 Mark 'grace.begin';Start-Sleep -Seconds 2;Mark 'grace.end';Drain
 Mark 'final.enumeration.begin';$final=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'});Mark 'final.enumeration.end' $final.Count
 if($final.Count){throw 'VirtualBox active at end'}
 Mark 'collection.freeze';Mark 'durable.flush.begin';$stream.Flush($true);Mark 'durable.flush.end'
 Mark 'journal.close.begin';$stream.Dispose();$stream=$null;Mark 'journal.close.end'
 Save 'monitor-result.json' @{status='LIVE_COLLECTION_CLOSED';run=$nonce;sequences=$seq;events=$count;violations=$violations;journalDurableFlush=$true;acceptance=$false}
}catch{Save 'monitor-failure.json' @{error=$_.Exception.Message;stack=$_.ScriptStackTrace;utc=[DateTime]::UtcNow.ToString('o')};exit 1}
finally{
 if($null -ne $stream){Mark 'journal.close.begin';$stream.Dispose();Mark 'journal.close.end'}
 Mark 'unsubscribe.begin';foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue;Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue|Remove-Event -ErrorAction SilentlyContinue};Mark 'unsubscribe.end'
 Save 'loop-trace.json' @($trace.ToArray())
}
