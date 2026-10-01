param([Parameter(Mandatory=$true)][string]$Code,[Parameter(Mandatory=$true)][string]$Run)
$ErrorActionPreference='Stop'
if($Code -notmatch '^D:\\JARVIS-STAGE6-LIVE\\[a-f0-9]{32}\\code$'){throw 'Invalid candidate path'}
$root=Join-Path $Code $Run
$env:TEMP=Join-Path $root 'temp';$env:TMP=$env:TEMP
Add-Type -Path @((Join-Path $Code 'LoopTiming.cs'),(Join-Path $Code 'event_queue.cs'),(Join-Path $Code 'queue_tests.cs'))
$result=[QueueTests]::Run($root)
$streaming=[ExactEventQueue]::new($ExecutionContext.Events.ReceivedEvents,[string[]]@('sacrificial-stream'),$true)
try {
 for($i=0;$i -lt 100;$i++) {
  $ev=New-Event -SourceIdentifier 'sacrificial-stream'
  $entry=$streaming.Select()
  if(![Object]::ReferenceEquals($entry.Event,$ev)){throw 'Reference mismatch'}
  $streaming.PersistAndRemove($entry,(Join-Path $root 'streaming.txt'),("$i`n"))
 }
 $streaming.Reconcile()
 if($streaming.Snapshot().Count -ne 0){throw 'Completed references retained in streaming mode'}
 $summary=@{regression=$result;streamingStats=$streaming.Stats();streamingCompletedReferences=0;timingOverflow=[LoopTiming]::Overflow;scope='Concrete PowerShell queue; no process observer'}
 $f=[IO.FileStream]::new((Join-Path $root 'queue-regression.json'),[IO.FileMode]::CreateNew)
 try{$b=[Text.Encoding]::UTF8.GetBytes(($summary|ConvertTo-Json -Depth 12));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}
 $summary|ConvertTo-Json -Depth 12
}finally{$streaming.Dispose()}
