$ErrorActionPreference='Stop'
$out=Join-Path $PSScriptRoot ('queue-tests-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $out|Out-Null
try{
 Add-Type -Path @((Join-Path $PSScriptRoot 'event_queue.cs'),(Join-Path $PSScriptRoot 'queue_tests.cs'))
 $result=[QueueTests]::Run($out)
 $s='SyntheticStart-'+[guid]::NewGuid();$t='SyntheticStop-'+[guid]::NewGuid()
 $q=$ExecutionContext.Events.ReceivedEvents;$x=[ExactEventQueue]::new($q,[string[]]@($s,$t))
 $a=New-Event -SourceIdentifier $s;$b=New-Event -SourceIdentifier $t
 [Management.Automation.PSEventArgs].GetProperty('EventIdentifier').SetValue($b,$a.EventIdentifier)
 $one=$x.Select();if(-not[Object]::ReferenceEquals($a,$one.Event)){throw 'Session Get/New-Event reference mismatch'}
 $path=Join-Path $out 'session.txt';$x.PersistAndRemove($one,$path,"one`n")
 $two=$x.Select();if(-not[Object]::ReferenceEquals($b,$two.Event)){throw 'Sibling reference lost'}
 $x.PersistAndRemove($two,$path,"two`n");$x.Reconcile();$x.Dispose()
 @{status='PASS';concreteType=$q.GetType().FullName;sessionReferenceProof=$true;results=$result}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $out 'result.json')
 Write-Output $out
}catch{
 @{status='FAIL';error=$_.ToString();stack=$_.ScriptStackTrace}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $out 'failure.json')
 throw
}
