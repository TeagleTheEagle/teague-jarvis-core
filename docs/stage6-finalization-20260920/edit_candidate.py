from pathlib import Path
R=Path(__file__).parent/'candidate'
p=R/'monitor.ps1';s=p.read_text()
s=s.replace("(Join-Path $PSScriptRoot 'event_queue.cs'))","(Join-Path $PSScriptRoot 'event_queue.cs'),(Join-Path $PSScriptRoot 'FinalizationGate.cs'))")
s=s.replace("$nonce=[guid]", "$gate=[FinalizationGate]::new($ExecutionContext.Events.ReceivedEvents,[string[]]$ids,4.6,45)\n$producerClosed=$false;$proofRead=$false;$subscriptionClosed=$false;$success=$false\n$nonce=[guid]")
s=s.replace("   Mark 'entry.properties.begin'", "   $gate.BeginPersistence()\n   try {\n   Mark 'entry.properties.begin'")
s=s.replace("   Stamp 'persisted'", "   $gate.Persisted([int]$n.ProcessID,$kind)\n   Stamp 'persisted'")
s=s.replace("$script:count++;Mark 'event.end'", "$script:count++;Mark 'event.end'\n   } finally {$gate.EndPersistence()}")
s=s.replace("Mark 'publication.complete'", "Mark 'publication.complete';$gate.Heartbeat()")
s=s.replace("  if($finished){Mark 'loop.end';break}", """  if(-not $producerClosed -and (Test-Path -LiteralPath (Join-Path $root 'producer-closed.json'))){
   $producer=Get-Content -LiteralPath (Join-Path $root 'producer-closed.json') -Raw|ConvertFrom-Json
   if($producer.run -ne $nonce){throw 'Producer closure identity mismatch'}
   $gate.ProducersClosed();$producerClosed=$true;Mark 'producers.closed'
  }
  if($finished -and -not $proofRead){
   $proof=Get-Content -LiteralPath (Join-Path $root 'collector-finished.json') -Raw|ConvertFrom-Json
   if(-not $producerClosed -or $proof.run -ne $nonce -or $proof.status -ne 'LIVE_MONITOR_HEALTHY' -or -not $proof.allHandlesExited){throw 'Incomplete or failed producer/handle closure'}
   $gate.ConfirmExits([int[]]@($proof.identities|ForEach-Object{$_.pid}),[string[]]@($proof.identities|ForEach-Object{$_.created}),$true)
   $proofRead=$true;Mark 'handles.confirmed'
  }
  $subscriberHealthy=(@(Get-EventSubscriber|Where-Object SourceIdentifier -in $ids).Count -eq 2)
  if($producerClosed -and $gate.Ready(($exact.Stats().remaining -eq 0),$subscriberHealthy)){Mark 'loop.end';break}""")
start=s.index(" Mark 'grace.begin'");end=s.index("}catch{Save 'monitor-failure.json'",start)
s=s[:start]+""" Mark 'final.enumeration.begin';$final=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'});Mark 'final.enumeration.end' $final.Count
 if($final.Count){throw 'VirtualBox active at end'}
 # Enumeration can take time and events may arrive during it. Revalidate the barrier.
 Drain
 $gate.BeginClose(($exact.Stats().remaining -eq 0),(@(Get-EventSubscriber|Where-Object SourceIdentifier -in $ids).Count -eq 2))
 Mark 'subscription.close.begin'
 foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction Stop}
 $subscriptionClosed=$true;$gate.SubscriptionClosed();Mark 'subscription.close.end'
 Drain;$exact.Reconcile();$gate.FinalDrainComplete(($exact.Stats().remaining -eq 0))
 Mark 'collection.freeze';Mark 'durable.flush.begin';$stream.Flush($true)
 $eventFlush=[IO.FileStream]::new((Join-Path $root 'events.jsonl'),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
 try{$eventFlush.Flush($true)}finally{$eventFlush.Dispose()}
 Mark 'durable.flush.end';$stream.Dispose();$stream=$null
 $exact.Reconcile();$gate.Seal($true,$true);$gate.AssertSealed();$success=$true
"""+s[end:]
s=s.replace(" Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue", " if(-not $subscriptionClosed){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue}")
s=s.replace(" $exact.Dispose()", " Save 'finalization-state.json' $gate.Snapshot()\n $exact.Dispose()")
s += """
# A zero exit and this receipt are both required by external archival verification.
$gate.AssertSealed();$exact.Reconcile()
if(-not $success){throw 'No successful finalization'}
Save 'monitor-result.json' @{status='LIVE_COLLECTION_CLOSED';run=$nonce;sequences=$seq;events=$count;violations=$violations;journalDurableFlush=$true;acceptance=$false;finalization='SEALED'}
$gate.AssertSealed();$gate.Dispose()
"""
p.write_text(s,encoding='utf-8')
p=R/'collect.py';s=p.read_text();s=s.replace(" (out/'workload-stop').touch()", " save('producer-closed.json',dict(run=identity['run'],qpc=ticks(),new_probes_forbidden=True))\n (out/'workload-stop').touch()")
old=" save('collector-finished.json',dict(status=status,error=error,qpc=ticks(),utc=utc(),acceptance=False));reader.close()"
new=""" try:
  for measurement in measured:measurement.finish_observation()
  save('probe-timings.json',[m.row for m in measured])
  verified=[]
  for p in handles:
   if k.WaitForSingleObject(int(p._handle),0)!=0:raise RuntimeError('Probe still active')
   p.poll();ts=times(p)
   verified.append(dict(pid=p.pid,times=ts,exit=p.returncode))
  if len({x['pid'] for x in verified})!=len(verified):raise RuntimeError('Duplicate PID')
  save('retained-handle-verification.json',verified)
 except BaseException:
  status='FAILED_CLOSED';error=traceback.format_exc();save('collector-failure.json',dict(error=error,qpc=ticks()))
  verified=[]
 save('collector-finished.json',dict(run=identity['run'],status=status,error=error,qpc=ticks(),utc=utc(),acceptance=False,
  allHandlesExited=bool(verified) and len(verified)==len(handles),identities=[dict(pid=x['pid'],created=x['times'][0],exited=x['times'][1],exit=x['exit']) for x in verified]))
 reader.close()"""
assert old in s;s=s.replace(old,new)
# Keep retained-handle post-finalization checks as independent final verification.
p.write_text(s,encoding='utf-8')
p=R/'accept_run.py';s=p.read_text();s=s.replace(" result=finalize(R)",""" f=read('finalization-state.json')
 if f['state']!='SEALED' or f['failure'] or f['active'] or not f['allHandlesConfirmed'] or f['expected']!=len(p) or f['starts']!=len(p) or f['stops']!=len(p):raise RuntimeError('Finalization barrier not proved')
 if read('monitor-result.json').get('finalization')!='SEALED':raise RuntimeError('Missing finalization receipt')
 result=finalize(R)""");p.write_text(s)
p=R/'launch.ps1';s=p.read_text().replace("'Dhash')","'Dhash','dry')").replace("purpose='probe diagnosis only'","purpose='bounded finalization sacrificial validation'")
s += "\n& $python -B (Join-Path $PSScriptRoot 'accept_run.py') $Run\nif($LASTEXITCODE){throw 'Durable acceptance failed'}\n"
p.write_text(s)
print('Candidate-only monitor/collector/receipt/launcher edits complete')
