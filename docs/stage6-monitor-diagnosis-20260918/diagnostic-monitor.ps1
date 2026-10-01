$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$startId='JarvisDiagStart-'+[guid]::NewGuid().ToString('N')
$stopId='JarvisDiagStop-'+[guid]::NewGuid().ToString('N')
$timer=[Diagnostics.Stopwatch]::StartNew()
$seq=0;$violations=0;$events=0
function Log($name,$row){[IO.File]::AppendAllText((Join-Path $root $name),(($row|ConvertTo-Json -Compress -Depth 6)+"`n"))}
function State($name,$row){$p=Join-Path $root $name;$tmp=$p+'.tmp';[IO.File]::WriteAllText($tmp,($row|ConvertTo-Json -Depth 6));[IO.File]::Move($tmp,$p,$true)}
try{
    $filter="ProcessName LIKE 'VBox%' OR ProcessName LIKE 'VirtualBox%' OR ProcessName = 'Stage6EventProbe.exe'"
    Register-CimIndicationEvent -Namespace root/cimv2 -Query ("SELECT * FROM Win32_ProcessStartTrace WHERE "+$filter) -SourceIdentifier $startId
    Register-CimIndicationEvent -Namespace root/cimv2 -Query ("SELECT * FROM Win32_ProcessStopTrace WHERE "+$filter) -SourceIdentifier $stopId
    $initial=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'})
    if($initial.Count){throw 'VirtualBox present'}
    State 'ready.json' @{PID=$PID;Utc=[DateTime]::UtcNow.ToString('o');StopwatchFrequency=[Diagnostics.Stopwatch]::Frequency;Priority=(Get-Process -Id $PID).PriorityClass.ToString();VirtualBoxCount=$initial.Count}
    while($timer.Elapsed.TotalSeconds -lt 420){
        $loopStart=[Diagnostics.Stopwatch]::GetTimestamp();$wall=[DateTime]::UtcNow
        foreach($id in @($startId,$stopId)){
            foreach($ev in @(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue)){
                $n=$ev.SourceEventArgs.NewEvent
                if($null -eq $n){throw 'CIM event has no NewEvent (possible subscription error)'}
                $kind='stop';if($id -eq $startId){$kind='start'}
                if([string]$n.ProcessName -match '^(VBox|VirtualBox)'){$violations++}
                Log 'events.jsonl' @{Kind=$kind;Name=[string]$n.ProcessName;PID=[int]$n.ProcessID;NativeFileTime=[string]$n.TIME_CREATED;ReceivedUtc=[DateTime]::UtcNow.ToString('o');ReceivedTicks=[Diagnostics.Stopwatch]::GetTimestamp()}
                $events++;Remove-Event -EventIdentifier $ev.EventIdentifier
            }
        }
        if($violations){throw 'Unexpected VirtualBox event'}
        $drained=[Diagnostics.Stopwatch]::GetTimestamp()
        $seq++
        State 'heartbeat.json' @{Utc=[DateTime]::UtcNow.ToString('o');Ticks=[Diagnostics.Stopwatch]::GetTimestamp();Sequence=$seq;Events=$events;Violations=$violations;PID=$PID}
        $written=[Diagnostics.Stopwatch]::GetTimestamp()
        Log 'timings.jsonl' @{Sequence=$seq;WallStart=$wall.ToString('o');LoopTicks=$loopStart;DrainedTicks=$drained;WrittenTicks=$written;ProcessCPU=(Get-Process -Id $PID).TotalProcessorTime.TotalSeconds}
        if(Test-Path -LiteralPath (Join-Path $root 'stop.json')){break}
        $beforeWait=[Diagnostics.Stopwatch]::GetTimestamp();Wait-Event -Timeout 1|Out-Null
        Log 'waits.jsonl' @{Sequence=$seq;BeforeTicks=$beforeWait;AfterTicks=[Diagnostics.Stopwatch]::GetTimestamp()}
    }
    if($timer.Elapsed.TotalSeconds -ge 420){throw 'Diagnostic lifetime bound reached'}
    State 'monitor-result.json' @{Status='COMPLETED';Events=$events;Violations=$violations;Sequences=$seq;EndedUtc=[DateTime]::UtcNow.ToString('o')}
}catch{State 'monitor-failure.json' @{Error=$_.Exception.Message;Utc=[DateTime]::UtcNow.ToString('o');Violations=$violations};exit 1}
finally{foreach($id in @($startId,$stopId)){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue;Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue|Remove-Event -ErrorAction SilentlyContinue}}
