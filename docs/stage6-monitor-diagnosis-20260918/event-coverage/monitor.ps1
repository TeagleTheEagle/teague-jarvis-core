$ErrorActionPreference='Stop'
$ids=@('J6CoverageStart-'+[guid]::NewGuid().ToString('N'),'J6CoverageStop-'+[guid]::NewGuid().ToString('N'))
try{
 $filter="ProcessName LIKE 'Stage6%' OR ProcessName LIKE 'J6Probe%' OR ProcessName LIKE 'VBox%' OR ProcessName LIKE 'VirtualBox%'"
 Register-CimIndicationEvent -Query ("SELECT * FROM Win32_ProcessStartTrace WHERE "+$filter) -SourceIdentifier $ids[0]
 Register-CimIndicationEvent -Query ("SELECT * FROM Win32_ProcessStopTrace WHERE "+$filter) -SourceIdentifier $ids[1]
 if(@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'}).Count){throw 'VirtualBox active'}
 [IO.File]::WriteAllText("$PSScriptRoot\ready.json",(@{PID=$PID;Utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json))
 $end=[DateTime]::UtcNow.AddSeconds(45)
 while([DateTime]::UtcNow -lt $end){
  for($i=0;$i -lt 2;$i++){
   foreach($ev in @(Get-Event -SourceIdentifier $ids[$i] -ErrorAction SilentlyContinue)){
    $n=$ev.SourceEventArgs.NewEvent;if($null -eq $n){throw 'Missing event data'}
    $r=@{Kind=@('start','stop')[$i];Name=[string]$n.ProcessName;PID=[int]$n.ProcessID;NativeFileTime=[string]$n.TIME_CREATED;ReceivedUtc=[DateTime]::UtcNow.ToString('o')}
    [IO.File]::AppendAllText("$PSScriptRoot\events.jsonl",(($r|ConvertTo-Json -Compress)+"`n"))
    if([string]$n.ProcessName -match '^(VBox|VirtualBox)'){throw 'VirtualBox event'}
    Remove-Event -EventIdentifier $ev.EventIdentifier
   }
  }
  Wait-Event -Timeout 1|Out-Null
 }
 [IO.File]::WriteAllText("$PSScriptRoot\complete.json",'{"Status":"COMPLETED"}')
}catch{[IO.File]::WriteAllText("$PSScriptRoot\failure.json",(@{Error=$_.Exception.Message}|ConvertTo-Json));exit 1}
finally{foreach($id in $ids){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue;Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue|Remove-Event -ErrorAction SilentlyContinue}}
