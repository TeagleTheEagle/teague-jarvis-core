param([string]$Code,[string]$Root)
$ErrorActionPreference='Stop'
. (Join-Path $Code 'health_publication.ps1')
$checks=[Collections.Generic.List[object]]::new()
function Assert($Name,$Value){$checks.Add(@{name=$Name;pass=[bool]$Value});if(!$Value){throw $Name}}
function Reject($Name,[scriptblock]$Action){$caught=$false;try{& $Action}catch{$caught=$true};Assert $Name $caught}
Add-Type @'
using System;
using System.IO;
public class HealthFaultStream : MemoryStream {
 public bool FailWrite, FailFlush;
 public override void Write(byte[] b,int o,int n){if(FailWrite)throw new IOException("injected write failure");base.Write(b,o,n);}
 public override void Flush(){if(FailFlush)throw new IOException("injected flush failure");base.Flush();}
 public void Flush(bool disk){Flush();}
}
'@
$i=@{run='synthetic';pid=$PID;created='123';frequency=[Diagnostics.Stopwatch]::Frequency}
function Pub($Stream){return @{Stream=$Stream;Identity=$i;Sequence=0;Failed=$false;Closed=$false}}
try {
 $f=[HealthFaultStream]::new();$p=Pub $f;$f.FailWrite=$true
 Reject 'write failure rejects' {Write-J6HealthRecord $p 1};Assert 'write failure latches' $p.Failed
 $f.FailWrite=$false;Reject 'failed publisher cannot resume' {Write-J6HealthRecord $p 2};$f.Dispose()
 $f=[HealthFaultStream]::new();$p=Pub $f;$f.FailFlush=$true
 Reject 'flush failure rejects' {Write-J6HealthRecord $p 1};Assert 'flush failure latches' $p.Failed;$f.Dispose()
 $f=[HealthFaultStream]::new();$p=Pub $f;$f.SetLength(1048576);$f.Position=$f.Length
 Reject 'journal cap rejects' {Write-J6HealthRecord $p 1};Assert 'cap does not append' ($f.Length -eq 1048576);$f.Dispose()
 $f=[HealthFaultStream]::new();$p=Pub $f;$p.Identity=@{}+$i;$p.Identity.run='x'*4096
 Reject 'record cap rejects' {Write-J6HealthRecord $p 1};Assert 'record cap writes no bytes' ($f.Length -eq 0);$f.Dispose()
 $p=New-J6HealthPublisher $Root $i
 Reject 'exclusive creation rejects stale journal' {New-J6HealthPublisher $Root $i}
 Reject 'ready before first record rejects' {Publish-J6Ready $Root $p $i}
 Assert 'ready initially absent' (!(Test-Path -LiteralPath (Join-Path $Root 'app-ready.json')))
 Write-J6HealthRecord $p 1;Publish-J6Ready $Root $p $i
 $before=[IO.File]::ReadAllBytes((Join-Path $Root 'app-ready.json'))
 Assert 'ready complete JSON' (([Text.Encoding]::UTF8.GetString($before)|ConvertFrom-Json).pid -eq $PID)
 Reject 'ready cannot overwrite accepted identity' {Publish-J6Ready $Root $p @{pid=1}}
 Assert 'original ready bytes preserved' ([Convert]::ToBase64String($before) -eq [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $Root 'app-ready.json'))))
 Close-J6HealthPublisher $p;Assert 'stream closes' $p.Closed
 Reject 'closed writer rejects' {Write-J6HealthRecord $p 2}
 $f=[HealthFaultStream]::new();$p=Pub $f;$f.FailFlush=$true
 Reject 'final flush fails closed' {Close-J6HealthPublisher $p};Assert 'failed finalization closes stream' ($p.Closed -and !$f.CanWrite)
}finally{
 $checks|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $Root 'checks.json')
}
@{passed=$checks.Count;failed=0}|ConvertTo-Json
