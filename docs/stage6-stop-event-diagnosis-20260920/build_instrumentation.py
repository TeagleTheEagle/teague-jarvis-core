"""Generate a separate instrumented copy; original monitor remains unchanged."""
import pathlib
R=pathlib.Path(__file__).resolve().parent
s=(R/'source-snapshot'/'monitor.ps1').read_text()
def replace(old,new):
 global s
 if s.count(old)!=1:raise RuntimeError('Expected one instrumentation anchor: '+old)
 s=s.replace(old,new)
replace("$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run", """$ErrorActionPreference='Stop';$root=Join-Path $PSScriptRoot $Run
Add-Type -Path (Join-Path $PSScriptRoot 'EventTap.cs')
$pipeline=[Collections.Generic.List[object]]::new();$secondary=[Collections.Generic.List[object]]::new()
function Stamp($stage,$ev,$n) {
 if($pipeline.Count -ge 20000){throw 'Pipeline trace capacity reached'}
 $pipeline.Add(@{stage=$stage;eventId=$ev.EventIdentifier;source=$ev.SourceIdentifier;pid=[int]$n.ProcessID;name=[string]$n.ProcessName;nativeTime=[string]$n.TIME_CREATED;qpc=[Diagnostics.Stopwatch]::GetTimestamp();utc=[DateTime]::UtcNow.ToString('o')})
}
""")
replace("$kind='stop';if($id -eq $s){$kind='start'}", "$kind='stop';if($id -eq $s){$kind='start'};Stamp 'drain' $ev $n")
replace("Mark 'event.serialize.begin';$serialized=($row|ConvertTo-Json -Compress)+\"`n\";Mark 'event.serialize.end'", "Stamp 'serialize.begin' $ev $n;Mark 'event.serialize.begin';$serialized=($row|ConvertTo-Json -Compress)+\"`n\";Mark 'event.serialize.end';Stamp 'serialized' $ev $n")
replace("[IO.File]::AppendAllText($eventPath,$serialized);Mark 'event.append.end'", "Stamp 'write.begin' $ev $n;[IO.File]::AppendAllText($eventPath,$serialized);Stamp 'persisted' $ev $n;Mark 'event.append.end'")
replace("Remove-Event -EventIdentifier $ev.EventIdentifier;Mark 'event.remove.end'", "Remove-Event -EventIdentifier $ev.EventIdentifier;Stamp 'removed' $ev $n;Mark 'event.remove.end'")
replace("Mark 'subscription.end';Mark 'enumeration.begin'", """$hookNames=@()
 $hookNames+=[EventTap]::AttachQueue($ExecutionContext.Events.ReceivedEvents,$s,$t)
 foreach($pair in @(@($s,'start'),@($t,'stop'))){$sub=Get-EventSubscriber -SourceIdentifier $pair[0];$hookNames+=[EventTap]::AttachSource($sub.SourceObject,$sub.EventName,$pair[1])}
 # Separate System.Management/COM subscriber, same Windows provider. Not an independent kernel source.
 [void][Reflection.Assembly]::LoadFrom((Join-Path $PSHOME 'System.Management.dll'))
 foreach($pair in @(@('Win32_ProcessStartTrace','start'),@('Win32_ProcessStopTrace','stop'))){
  $watcher=[System.Management.ManagementEventWatcher]::new('root\\cimv2',("SELECT * FROM "+$pair[0]+" WHERE ProcessName LIKE 'J6Probe%'"))
  $hookNames+=[EventTap]::AttachSecondary($watcher,$pair[1]);$watcher.Start();$secondary.Add($watcher)
 }
 Save 'hooks.json' @{hooks=$hookNames;powershell=$PSVersionTable.PSVersion.ToString();observerB='parallel WMI COM subscriber; same native provider';groundTruth='separate retained kernel process handles';callback_tap='attached after original handler; may observe after enqueue'}
 Mark 'subscription.end';Mark 'enumeration.begin'""")
replace("Mark 'loop.begin';Drain", "Mark 'loop.begin';if([EventTap]::Errors -or [EventTap]::Overflow){throw 'Diagnostic hook error/overflow'};Drain")
replace("Mark 'unsubscribe.begin';foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue;Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue|Remove-Event -ErrorAction SilentlyContinue};Mark 'unsubscribe.end'", """Mark 'unsubscribe.begin'
 foreach($id in $ids){
  $pending=@(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue)
  foreach($ev in $pending){if($ev.SourceEventArgs.NewEvent){Stamp 'preunsubscribe.pending' $ev $ev.SourceEventArgs.NewEvent}}
  Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue
  $discard=@(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue)
  foreach($ev in $discard){if($ev.SourceEventArgs.NewEvent){Stamp 'teardown.discard' $ev $ev.SourceEventArgs.NewEvent}}
  $discard | Remove-Event -ErrorAction SilentlyContinue
 }
 Mark 'unsubscribe.end'
 foreach($watcher in $secondary){$watcher.Stop();$watcher.Dispose()}
 [EventTap]::Detach()
 Save 'tap.json' @([EventTap]::Snapshot());Save 'pipeline.json' @($pipeline.ToArray())
 Save 'tap-state.json' @{errors=[EventTap]::Errors;overflow=[EventTap]::Overflow;queue_capacity='existing PowerShell collection; no diagnostic change';diagnostic_capacity=20000;native_drop_counter='not exposed by these temporary subscribers'}""")
with (R/'monitor.ps1').open('x',encoding='utf-8') as f:f.write(s)
print('Created instrumented copy only')
