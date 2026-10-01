import pathlib
R=pathlib.Path(__file__).resolve().parent
p=R/'monitor.ps1';s=p.read_text()
s=s.replace("Add-Type -Path (Join-Path $PSScriptRoot 'EventTap.cs')", "Add-Type -Path (Join-Path $PSScriptRoot 'EventTap.cs')\nAdd-Type -Path (Join-Path $PSScriptRoot 'event_queue.cs')")
s=s.replace("$nonce=[guid]", "$exact=[ExactEventQueue]::new($ExecutionContext.Events.ReceivedEvents,[string[]]$ids)\n$nonce=[guid]")
start=s.index(' foreach($id in $ids){',s.index('function Drain'))
end=s.index(" Mark 'queue.backlog.begin'",start)
s=s[:start]+''' while($null -ne ($entry=$exact.Select())){
   $ev=$entry.Event;$id=$ev.SourceIdentifier
   Mark 'event.begin';$n=$ev.SourceEventArgs.NewEvent;if($null -eq $n){throw 'Invalid CIM indication'}
   $kind='stop';if($id -eq $s){$kind='start'};Stamp 'drain' $ev $n
   if([string]$n.ProcessName -match '^(VBox|VirtualBox)'){$script:violations++}
   $row=@{queueSequence=$entry.QueueSequence;eventIdentifier=$ev.EventIdentifier;kind=$kind;name=[string]$n.ProcessName;pid=[int]$n.ProcessID;nativeTime=[string]$n.TIME_CREATED;receivedQpc=[Diagnostics.Stopwatch]::GetTimestamp();utc=[DateTime]::UtcNow.ToString('o');queuedUtc=$ev.TimeGenerated.ToUniversalTime().ToString('o')}
   Stamp 'serialize.begin' $ev $n;Mark 'event.serialize.begin';$serialized=($row|ConvertTo-Json -Compress)+"`n";Mark 'event.serialize.end';Stamp 'serialized' $ev $n
   $eventPath=Join-Path $root 'events.jsonl'
   if((Test-Path -LiteralPath $eventPath) -and (Get-Item -LiteralPath $eventPath).Length -gt 1044480){throw 'Event capacity reached'}
   Mark 'event.append.begin';Stamp 'write.begin' $ev $n
   $exact.PersistAndRemove($entry,$eventPath,$serialized)
   Stamp 'persisted' $ev $n;Stamp 'removed' $ev $n;Mark 'event.append.end';$script:count++;Mark 'event.end'
 }
''' +s[end:]
s=s.replace("Mark 'collection.freeze';Mark", "$exact.Reconcile();Mark 'collection.freeze';Mark")
start=s.index('  $discard | Remove-Event')
s=s[:start]+s[start:].replace('  $discard | Remove-Event -ErrorAction SilentlyContinue','  # Preserve residue; never delete pending evidence at teardown.',1)
s=s.replace("[EventTap]::Detach()", "[EventTap]::Detach()\n Save 'queue-state.json' $exact.Stats()\n Save 'queue-entries.json' @($exact.Snapshot()|ForEach-Object {@{queueSequence=$_.QueueSequence;eventId=$_.Event.EventIdentifier;source=$_.Event.SourceIdentifier;enqueueQpc=$_.EnqueueQpc;persisted=$_.Persisted;removed=$_.Removed}})\n try {$exact.Reconcile()} catch {Save 'queue-failure.json' @{error=$_.Exception.Message};$global:LASTEXITCODE=1}\n $exact.Dispose()")
p.write_text(s)
# Separate finalizer condition; old tests still exercise original invariants unchanged.
p=R/'finalize.py';s=p.read_text().replace("for n in ('collector-failure.json','monitor-failure.json','resource-failure.txt'):","for n in ('collector-failure.json','monitor-failure.json','resource-failure.txt','queue-failure.json'):")
s=s.replace("identity=read(root/'ready.json');", "if (root/'queue-state.json').exists():\n  q=read(root/'queue-state.json')\n  if q['failed'] or q['remaining'] or not q['enqueued']==q['selected']==q['persisted']==q['removed']:raise RuntimeError('Queue reconciliation failed')\n identity=read(root/'ready.json');")
p.write_text(s)
