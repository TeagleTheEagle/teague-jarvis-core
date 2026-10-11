$ErrorActionPreference='Stop'
$prior=Join-Path (Split-Path $PSScriptRoot) 'stage6-dual-cleanup-20260920'
$known=Get-Content -LiteralPath (Join-Path $prior 'known-identities.json') -Raw|ConvertFrom-Json
$all=@(Get-CimInstance Win32_Process)
$live=@(foreach($x in $known){foreach($p in @($all|Where-Object ProcessId -eq $x.pid)){if($p.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString() -eq $x.created){@{pid=$x.pid;created=$x.created;image=$p.ExecutablePath}}}})
$scope=@($all|Where-Object { $_.Name -match '^(VBox|VirtualBox|J6Probe|J6KernelTrace)' -or ($_.Name -in 'python.exe','pwsh.exe' -and $_.CommandLine -like '*a0e59a0a26ca41d3885c6c6b0e3d7a25*') }|ForEach-Object {@{pid=$_.ProcessId;name=$_.Name;created=$_.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString();image=$_.ExecutablePath}})
$sessions=& 'C:\Windows\System32\logman.exe' query -ets 2>&1
$code=$LASTEXITCODE
$ours=@($sessions|Where-Object {$_ -match 'J6Kernel-'})
$result=@{utc=[datetime]::UtcNow.ToString('o');knownIdentitiesChecked=$known.Count;matchingLive=$live;scopedProcesses=$scope;etwQueryExit=$code;remainingDiagnosticTraceSessions=$ours;changesPerformed=$false}
$result|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'host.json')
@{known=$known.Count;matchingLive=$live.Count;scopedProcesses=$scope.Count;diagnosticSessions=$ours.Count;queryExit=$code}|ConvertTo-Json
