$ErrorActionPreference='Stop'
$r=$PSScriptRoot
$expected=Get-Content -LiteralPath (Join-Path $r 'known-identities.json') -Raw|ConvertFrom-Json
$all=@(Get-CimInstance Win32_Process)
$observations=@(foreach($x in $expected){
 $m=@($all|Where-Object ProcessId -eq $x.pid)
 if(!$m){@{pid=$x.pid;expectedCreated=$x.created;status='ABSENT_CURRENT';historicalExit=$x.kernelExit}}
 else {foreach($p in $m){$created=$p.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString();@{pid=$x.pid;expectedCreated=$x.created;currentCreated=$created;image=$p.ExecutablePath;status=$(if($created -eq $x.created){'MATCHING_IDENTITY_LIVE'}else{'PID_REUSED_UNRELATED'})}}}
})
$scope=@($all|Where-Object { $_.Name -match '^(VBox|VirtualBox|J6Probe|J6KernelTrace)' -or ($_.Name -in 'python.exe','pwsh.exe' -and $_.CommandLine -like '*a0e59a0a26ca41d3885c6c6b0e3d7a25*') }|ForEach-Object {@{pid=$_.ProcessId;parent=$_.ParentProcessId;name=$_.Name;image=$_.ExecutablePath;created=$_.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString()}})
$sessions=& 'C:\Windows\System32\logman.exe' query -ets 2>&1
$sessionExit=$LASTEXITCODE
$matching=@($sessions|Where-Object {$_ -match 'J6Kernel-'})
@{utc=[datetime]::UtcNow.ToString('o');identityObservations=$observations;matchingLive=@($observations|Where-Object status -eq 'MATCHING_IDENTITY_LIVE');scopedProcesses=$scope;etwQueryExit=$sessionExit;remainingJ6KernelSessions=$matching}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $r 'host-final.json')
@{identities=$expected.Count;matchingLive=@($observations|Where-Object status -eq 'MATCHING_IDENTITY_LIVE').Count;scopedProcesses=$scope.Count;etwQueryExit=$sessionExit;remainingJ6KernelSessions=$matching.Count}|ConvertTo-Json
