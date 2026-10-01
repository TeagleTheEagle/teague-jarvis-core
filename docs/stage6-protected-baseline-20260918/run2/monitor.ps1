param([Parameter(Mandatory=$true)][string]$EvidenceRoot)
$ErrorActionPreference='Stop'
$expected='C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-protected-baseline-20260918\run2'
if($EvidenceRoot -cne $expected){throw 'Unexpected evidence location'}
$begin=[DateTime]::UtcNow
$startId='JarvisBaselineStart-'+[guid]::NewGuid().ToString('N')
$stopId='JarvisBaselineStop-'+[guid]::NewGuid().ToString('N')
$violations=0
$events=0
function Save-State($name,$value){
    $target=Join-Path $EvidenceRoot $name
    $temp=$target+'.tmp'
    [IO.File]::WriteAllText($temp,($value|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    if([IO.File]::Exists($target)){[IO.File]::Move($temp,$target,$true)}else{[IO.File]::Move($temp,$target)}
}
function Drain-Events {
    foreach($id in @($startId,$stopId)){
        foreach($event in @(Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue)){
            $n=$event.SourceEventArgs.NewEvent
            $kind='stop';if($id -eq $startId){$kind='start';$script:violations++}
            $row=[ordered]@{Kind=$kind;ProcessName=[string]$n.ProcessName;PID=[int]$n.ProcessID;ObservedUtc=[DateTime]::UtcNow.ToString('o');NativeTime=[string]$n.TIME_CREATED}
            [IO.File]::AppendAllText((Join-Path $EvidenceRoot 'process-events.jsonl'),(($row|ConvertTo-Json -Compress)+"`n"))
            $script:events++
            Remove-Event -EventIdentifier $event.EventIdentifier
        }
    }
}
try {
    $filter="ProcessName LIKE 'VBox%' OR ProcessName LIKE 'VirtualBox%'"
    Register-CimIndicationEvent -Namespace root/cimv2 -Query ("SELECT * FROM Win32_ProcessStartTrace WHERE "+$filter) -SourceIdentifier $startId
    Register-CimIndicationEvent -Namespace root/cimv2 -Query ("SELECT * FROM Win32_ProcessStopTrace WHERE "+$filter) -SourceIdentifier $stopId
    $initial=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'}|Select-Object Name,ProcessId,CreationDate)
    if($initial.Count){throw 'VirtualBox processes present before capture'}
    $service=@(Get-CimInstance Win32_Service|Where-Object{$_.Name -match '^VBox'}|Select-Object Name,State,ProcessId)
    if(@($service|Where-Object{$_.State -eq 'Running'}).Count){throw 'VirtualBox service running'}
    Drain-Events
    if($violations){throw 'VirtualBox start during monitor setup'}
    Save-State 'monitor-ready.json' ([ordered]@{StartedUtc=$begin.ToString('o');ReadyUtc=[DateTime]::UtcNow.ToString('o');MonitorPID=$PID;Mechanism='WMI process start and stop trace';InitialProcesses=$initial;Services=$service})
    while($true){
        Drain-Events
        if($violations){throw 'VirtualBox process start detected'}
        if(([DateTime]::UtcNow-$begin).TotalMinutes -gt 60){throw 'Monitor exceeded bounded 60-minute lifetime'}
        Save-State 'monitor-heartbeat.json' ([ordered]@{Utc=[DateTime]::UtcNow.ToString('o');Events=$events;Violations=$violations;State='ACTIVE'})
        if(Test-Path -LiteralPath (Join-Path $EvidenceRoot 'collector-finished.json')){break}
        Wait-Event -Timeout 1 | Out-Null
    }
    Start-Sleep -Seconds 2
    Drain-Events
    $final=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match '^(VBox|VirtualBox)'}|Select-Object Name,ProcessId,CreationDate)
    if($violations -or $final.Count){throw 'VirtualBox activity at completion'}
    Save-State 'monitor-final.json' ([ordered]@{Status='PASS';StartedUtc=$begin.ToString('o');EndedUtc=[DateTime]::UtcNow.ToString('o');Events=$events;Violations=$violations;FinalProcesses=$final})
} catch {
    Save-State 'monitor-failure.json' ([ordered]@{Status='BLOCKED';Utc=[DateTime]::UtcNow.ToString('o');Error=$_.Exception.Message;Events=$events;Violations=$violations})
    exit 1
} finally {
    foreach($id in @($startId,$stopId)){Unregister-Event -SourceIdentifier $id -ErrorAction SilentlyContinue; Get-Event -SourceIdentifier $id -ErrorAction SilentlyContinue|Remove-Event -ErrorAction SilentlyContinue}
}
