param([ValidateSet('dry1','dry2')][string]$Run)
$ErrorActionPreference='Stop'
$root=Join-Path $PSScriptRoot $Run
if(-not(Test-Path -LiteralPath $root)){throw 'Prepared run directory required'}
$s='J6JournalStart-'+[guid]::NewGuid().ToString('N');$t='J6JournalStop-'+[guid]::NewGuid().ToString('N')
$ids=@($s,$t);$seq=0;$count=0;$violations=0;$stream=$null
$nonce=[guid]::NewGuid().ToString('N');$begin=[DateTime]::UtcNow;$clock=[Diagnostics.Stopwatch]::StartNew()
$created=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToFileTimeUtc().ToString()
function Write-New($name,$data){[IO.File]::WriteAllText((Join-Path $root $name),($data|ConvertTo-Json -Depth 7))}
function Drain {
 foreach($id in $ids){foreach($ev in @(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue)){
  $n=$ev.SourceEventArgs.NewEvent;if($null -eq $n){throw 'Invalid CIM indication/subscription error'}
  $kind='stop';if($id -eq $s){$kind='start'}
  if([string]$n.ProcessName -match '^(VBox|VirtualBox)'){$script:violations++}
  $row=@{kind=$kind;name=[string]$n.ProcessName;pid=[int]$n.ProcessID;nativeTime=[string]$n.TIME_CREATED;utc=[DateTime]::UtcNow.ToString('o')}
  $eventPath=Join-Path $root 'events.jsonl'
  if((Test-Path -LiteralPath $eventPath) -and (Get-Item -LiteralPath $eventPath).Length -gt 1044480){throw 'Event evidence capacity reached'}
  [IO.File]::AppendAllText($eventPath,(($row|ConvertTo-Json -Compress)+"`n"))
  $script:count++;Remove-Event -EventIdentifier $ev.EventIdentifier
 }}
 if($violations){throw 'VirtualBox process event'}
}
try{
 $filter="ProcessName LIKE 'VBox%' OR ProcessName LIKE 'VirtualBox%' OR ProcessName LIKE 'J6Probe%'"
 Register-CimIndicationEvent -Query ("SELECT * FROM Win32_ProcessStartTrace WHERE "+$filter) -SourceIdentifier $s
 Register-CimIndicationEvent -Query ("SELECT * FROM Win32_ProcessStopTrace WHERE "+$filter) -SourceIdentifier $t
 $initial=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'})
 if($initial.Count){throw 'VirtualBox initially active'}
 $stream=[IO.FileStream]::new((Join-Path $root 'heartbeat.jsonl'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 $identity=@{run=$nonce;pid=$PID;created=$created;frequency=[Diagnostics.Stopwatch]::Frequency}
 while($clock.Elapsed.TotalSeconds -lt 600){
  Drain
  $seq++;$q=[Diagnostics.Stopwatch]::GetTimestamp()
  $record=@{run=$nonce;pid=$PID;created=$created;frequency=[Diagnostics.Stopwatch]::Frequency;seq=$seq;pump=$seq;ticks=$q;utc=[DateTime]::UtcNow.ToString('o');state='ACTIVE';violations=$violations;events=$count}
  $bytes=[Text.Encoding]::UTF8.GetBytes((($record|ConvertTo-Json -Compress)+"`n"))
  if($bytes.Length -gt 4096 -or $stream.Length+$bytes.Length -gt 1048576){throw 'Heartbeat journal capacity reached'}
  $stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)
  if($seq -eq 1){Write-New 'ready.json' $identity}
  if(Test-Path -LiteralPath (Join-Path $root 'collector-finished.json')){break}
  Wait-Event -Timeout 1|Out-Null
 }
 if($clock.Elapsed.TotalSeconds -ge 600){throw 'Monitor lifetime bound exceeded'}
 Start-Sleep -Seconds 2;Drain
 if(@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'}).Count){throw 'VirtualBox active at end'}
 Write-New 'monitor-result.json' @{status='PASS';sequences=$seq;events=$count;violations=$violations;utc=[DateTime]::UtcNow.ToString('o');run=$nonce}
}catch{Write-New 'monitor-failure.json' @{status='FAIL';error=$_.Exception.Message;utc=[DateTime]::UtcNow.ToString('o')};exit 1}
finally{if($null -ne $stream){$stream.Dispose()};foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue;Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue|Remove-Event -ErrorAction SilentlyContinue}}
