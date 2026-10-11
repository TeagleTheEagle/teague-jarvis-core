param([ValidateSet('before','after')][string]$Phase)
$ErrorActionPreference='Stop';$r=$PSScriptRoot
$prior=Join-Path (Split-Path $r) 'stage6-dry2-execution-20260920\host-after.json'
$known=@((Get-Content -LiteralPath $prior -Raw|ConvertFrom-Json).identities|ForEach-Object {@{pid=$_.pid;created=$_.created}})
if($Phase -eq 'after'){$known+=@(Get-Content -LiteralPath (Join-Path $r 'known-identities.json') -Raw|ConvertFrom-Json)}
$all=@(Get-CimInstance Win32_Process)
$observations=@(foreach($x in $known){$m=@($all|Where-Object ProcessId -eq $x.pid);if(!$m){@{pid=$x.pid;created=$x.created;status='ABSENT_CURRENT'}}else{foreach($p in $m){$created=$p.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString();@{pid=$x.pid;created=$x.created;currentCreated=$created;status=$(if($created -eq $x.created){'MATCHING_LIVE'}else{'PID_REUSED_UNRELATED'})}}}})
$scope=@($all|Where-Object { $_.Name -match '^(VBox|VirtualBox|J6Probe|J6KernelTrace)' -or ($_.Name -in 'python.exe','pwsh.exe' -and ($_.CommandLine -like '*b675935592fe41d48968e22be8cc6641*' -or $_.CommandLine -like '*a0e59a0a26ca41d3885c6c6b0e3d7a25*')) }|ForEach-Object {@{pid=$_.ProcessId;name=$_.Name;created=$_.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString();image=$_.ExecutablePath}})
$sessions=& 'C:\Windows\System32\logman.exe' query -ets 2>&1;$status=$LASTEXITCODE;$ours=@($sessions|Where-Object {$_ -match 'J6Kernel-'})
$live=@($observations|Where-Object status -eq 'MATCHING_LIVE')
@{utc=[datetime]::UtcNow.ToString('o');identities=$observations;matchingLive=$live;scopedProcesses=$scope;traceQueryExit=$status;traceSessions=$ours}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $r ('host-'+$Phase+'.json'))
@{identities=$known.Count;matchingLive=$live.Count;scopedProcesses=$scope.Count;traceQueryExit=$status;traceSessions=$ours.Count}|ConvertTo-Json
if($live.Count -or $scope.Count -or $status -ne 0 -or $ours.Count){exit 1}
